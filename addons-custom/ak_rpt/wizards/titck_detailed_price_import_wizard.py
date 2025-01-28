from odoo import models, fields, api, _
import base64
import io
import pandas as pd
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class TitckDetailedPriceImport(models.TransientModel):
    _name = 'titck.detailed.price.import'
    _description = 'TITCK Detailed Price Import Wizard'

    import_file = fields.Binary(string='Excel File', required=True)
    file_name = fields.Char(string='File Name')

    def _process_excel_data(self):
        """Determine file type and process Excel data accordingly"""
        try:
            file_data = base64.b64decode(self.import_file)
            excel_data = io.BytesIO(file_data)
            
            # Get all sheet names
            xls = pd.ExcelFile(excel_data)
            sheet_names = xls.sheet_names

            # Check if it's a Detailed Price List
            if 'AKTİF ÜRÜNLER LİSTESİ' in sheet_names:
                df = pd.read_excel(
                    excel_data,
                    sheet_name='AKTİF ÜRÜNLER LİSTESİ',
                    skiprows=1,
                    header=0
                )
                return {'type': 'price_list', 'data': df}
                
            # Check if it's an EK4A file
            elif 'EK-4A' in sheet_names:
                df = pd.read_excel(
                    excel_data,
                    sheet_name='EK-4A',
                    skiprows=2,
                    header=0
                )
                return {'type': 'ek4a', 'data': df}
                
            else:
                raise UserError(_('Unsupported file format. The file must be either a Detailed Price List or an EK4A file.'))
                
        except Exception as e:
            raise UserError(_('Error reading Excel file: %s') % str(e))

    def _update_products(self, df):
        """GTIN'e göre ürünleri güncelle"""
        Product = self.env['product.template']
        Pricelist = self.env['product.pricelist']
        PricelistItem = self.env['product.pricelist.item']
        # _logger.info("Ürün güncelleme işlemi başlatılıyor. Toplam işlenecek kayıt: %s", len(df))
        
        # İşlem detaylarını tutmak için dictionary
        update_stats = {
            'total_records': len(df),
            'products_found': 0,
            'products_not_found': 0,
            'products_updated': 0,
            'field_updates': {
                'list_price': 0,
                'atc_id': 0,
                'equivalent_status_id': 0,
                'reference_status_id': 0,
                'fdk_agok_status_id': 0,
                'price_decree_reason_id': 0,
                'sales_price_type_id': 0,
                'inhaler_product_group_id': 0,
                'inhaler_resistance_group_id': 0,
                'inhaler_device_code_id': 0,
                'imported': 0,
                'active_ingredients': 0,
                'active_ingredients_amount': 0,
                'active_ingredients_uom': 0,
                'package_amount': 0,
                'prescription_type_id': 0,
                'its_movement_status': 0,

                # New pricelist item fields
                'source_country': 0,
                'actual_source_country': 0,
                'real_source_price': 0,
                'calculation_source_price': 0,
                'source_price_euro': 0,
                # 'euro_rate': 0,
                'depot_price_wo_vat': 0,
                'depot_sales_price_wo_vat': 0,
                'pharmacy_sales_price_wo_vat': 0,
                'retail_price_w_vat': 0,
                'change_description': 0,
                
            },
            'pricelists_created': 0,
            'pricelist_items_created': 0,
            'errors': []
        }

        # Kolon isimlerini bir kere bul
        try: 
            columns = {
                'price_col': [col for col in df.columns if 'KDV DAHIL PERAKENDE SATIS TL FIYATI' in col][0],
                'atc_col': [col for col in df.columns if 'ATC KODU' in col][0],
                'equiv_col': [col for col in df.columns if 'ESDEGERI' in col][0],
                'ref_col': [col for col in df.columns if 'REFERANS DURUMU' in col][0],
                'fdk_col': [col for col in df.columns if "FDK'DA FİYAT ARTIŞI ALAN ÜRÜNLER:1" in col][0],
                'decree_col': [col for col in df.columns if "FIYAT KARARNAMESI GEREGI" in col][0],
                'price_type_col': [col for col in df.columns if 'Hastane ürünü:1' in col][0],
                'imported_col': [col for col in df.columns if 'ITHAL' in col][0],
                'inhaler_group_col': [col for col in df.columns if 'INHALER URUN GRUBU' in col][0],
                'inhaler_resistance_col': [col for col in df.columns if 'DIRENC GRUBU' in col][0],
                'inhaler_device_col': [col for col in df.columns if 'CIHAZ KODU' in col][0],
                'active_ingredients_col': [col for col in df.columns if 'ETKIN MADDE' in col][0],
                'active_ingredients_amount_col': [col for col in df.columns if 'BIRIM MIKTAR' in col][0],
                'active_ingredients_uom_col': [col for col in df.columns if 'BIRIM CINSI' in col][0],
                'package_amount_col': [col for col in df.columns if 'AMBALAJ MIKTARI' in col][0],
                'prescription_col': [col for col in df.columns if 'RECETE' in col][0],
                'its_movement_col': [col for col in df.columns if "İTS'de hareket olmayan ürün:0,\nİTS'de hareket olan ürün:1,\nITS'de Bildirim Zorunluluğu Olmayan Ürün:2" in col][0],

                # New columns for pricelist items
                'changed_this_week_col': [col for col in df.columns if 'BU HAFTA DEGISIKLIK YAPILANLAR=1' in col][0],
                'effective_date_col': [col for col in df.columns if 'GECERLILIK TARIHI' in col][0],
                'source_country_col': [col for col in df.columns if 'KAYNAK ULKE' in col][0],
                'actual_source_country_col': [col for col in df.columns if 'HESAPLAMA ICIN KULLANILAN KAYNAK ULKE' in col][0],
                'real_source_price_col': [col for col in df.columns if 'GERCEK KAYNAK FIYAT (GKF) (€)' in col][0],
                'calculation_source_price_col': [col for col in df.columns if 'HESAPLAMA ICIN KULLANILAN GKF' in col][0],
                'source_price_euro_col': [col for col in df.columns if 'KAYNAK FIYAT \n(€)' in col][0],
                # 'euro_rate_col': [col for col in df.columns if '1 € =' in col][0],
                'depot_price_wo_vat_col': [col for col in df.columns if 'KDV HARIC DEPOCUYA SATIS TL FIYATI' in col][0],
                'depot_sales_wo_vat_col': [col for col in df.columns if '(**)KDV HARIC             DEPOCU SATIS TL FIYATI' in col][0],
                'pharmacy_sales_wo_vat_col': [col for col in df.columns if '(***) KDV HARIC                  ECZACI SATIS                 TL FIYATI' in col][0],
                'retail_price_w_vat_col': [col for col in df.columns if 'KDV DAHIL PERAKENDE SATIS TL FIYATI' in col][0],
                'change_description_col': [col for col in df.columns if 'ACIKLAMA ' in col][0],
                'last_operation_col' : [col for col in df.columns if 'DEGISIKLIK TARIHINDE YAPILAN SON ISLEM' in col][0],

                'product_name_col': [col for col in df.columns if 'ILAC ADI' in col][0],
                'barcode_col': [col for col in df.columns if 'BARKOD' in col][0],
                'manufacturer_col': [col for col in df.columns if 'FIRMA ADI' in col][0],
                'active_status_col': [col for col in df.columns if 'DURUM' in col][0],

                'company_gln_col': [col for col in df.columns if 'FİRMA GLN' in col][0],
                'company_name_col': [col for col in df.columns if 'FIRMA ADI' in col][0],
                'company_tax_id_col': [col for col in df.columns if 'FİRMA VERGİ NO' in col][0],
            }
            # _logger.info("Kolon eşleştirmeleri başarılı: %s", columns)
        except Exception as e:
            _logger.error("Kolon eşleştirme hatası: %s", str(e))
            raise UserError(_('Kolon eşleştirme hatası: %s') % str(e))

        # Get pharmaceutical product category
        category = self.env['product.category'].search([('name', '=', 'İlaç')], limit=1)
        if not category:
            category = self.env['product.category'].create({'name': 'İlaç'})

        # Get pharmaceutical industry
        industry = self.env['res.partner.industry'].search([('name', '=', 'İlaç')], limit=1)
        if not industry:
            industry = self.env['res.partner.industry'].create({'name': 'İlaç'})


        # Referans verileri önbelleğe al
        # _logger.info("Referans veriler önbelleğe alınıyor...")
        cache = {
            'atc'           : {x.code: x.id for x in self.env['product.atc'].search([])},
            'equivalent'    : {x.code: x.id for x in self.env['equivalent.status'].search([])},
            'reference'     : {x.code: x.id for x in self.env['reference.status'].search([])},
            'fdk'           : {x.code: x.id for x in self.env['fdk.agok.status'].search([])},
            'decree'        : {x.code: x.id for x in self.env['price.decree.reason'].search([])},
            'price_type'    : {x.code: x.id for x in self.env['sales.price.type'].search([])},
            'inhaler_group' : {x.code: x.id for x in self.env['inhaler.product.group'].search([])},
            'resistance'    : {x.code: x.id for x in self.env['inhaler.resistance.group'].search([])},
            'device'        : {x.code: x.id for x in self.env['inhaler.device.code'].search([])},
            'prescription'  : {x.name: x.id for x in self.env['prescription.type'].search([])},
            'pricelists': {},
        }
        
        # Pre-load existing pharmaceutical pricelists into cache
        existing_pricelists = Pricelist.search([('is_pharma_pricelist', '=', True)])
        for pricelist in existing_pricelists:
            cache['pricelists'][pricelist.effective_date] = pricelist


        # Tüm GTIN'leri bir kerede al
        all_gtins = ['0' + str(x).split('.')[0].strip() for x in df['BARKOD']]
        products_dict = {p.gtin: p for p in Product.search([('gtin', 'in', all_gtins)])}
        
        update_stats['products_found'] = len(products_dict)
        update_stats['products_not_found'] = len(all_gtins) - len(products_dict)

        batch_updates = []
        
        # Sort DataFrame by changed_this_week column (True values first)
        df = df.sort_values(by=[columns['changed_this_week_col']], ascending=False)

        
        for _, row in df.iterrows():
            try:
                # Get manufacturer information using GLN
                company_gln = str(row[columns['company_gln_col']]).split('.')[0].strip()
                company_name = str(row[columns['company_name_col']]).strip()
                company_tax_id = str(row[columns['company_tax_id_col']]).strip()
                manufacturer = False
                
                if company_gln:
                    # First try to find by GLN number
                    manufacturer = self.env['res.partner'].search([
                        ('gln_number', '=', company_gln),
                        ('is_company', '=', True)
                    ], limit=1)
                    
                    # If not found by GLN, try to find by company name
                    if not manufacturer and company_name:
                        manufacturer = self.env['res.partner'].search([
                            ('name', '=', company_name),
                            ('is_company', '=', True)
                        ], limit=1)
                        
                    if manufacturer:
                        # Update tax ID if it's empty or different
                        if company_tax_id and (not manufacturer.vat or manufacturer.vat != company_tax_id):
                            manufacturer.write({'vat': company_tax_id})
                            _logger.info(f"Updated Tax ID for {manufacturer.name} to: {company_tax_id}")
                    else:
                        # Create new manufacturer if not found
                        manufacturer = self.env['res.partner'].create({
                            'name': company_name,
                            'gln_number': company_gln,
                            'vat': company_tax_id if company_tax_id else False,
                            'is_company': True,
                            'company_type': 'company',
                            'active': True,
                            'industry_id': industry.id if industry else False,
                            'barcode': company_gln,
                        })
                        _logger.info(f"New stakeholder added: {company_name} ({company_gln}) with Tax ID: {company_tax_id}")
                
                gtin = '0' + str(row['BARKOD']).split('.')[0].strip()
                product = products_dict.get(gtin)
                
                if not product:
                    # Prepare product values
                    drug_name = str(row[columns['product_name_col']]).strip()
                    imported = str(row[columns['imported_col']]).strip() == 'ITHAL'
                    active_status = str(row[columns['active_status_col']]).strip() == 'AKTIF'
                    barcode = str(row[columns['barcode_col']]).strip()

                    # Create product
                    product = Product.create({
                        'name': drug_name,
                        'gtin': gtin,
                        'barcode': barcode,
                        'manufacturer_id': manufacturer.id if manufacturer else False,
                        'imported': imported,
                        'active_status': active_status,
                        'type': 'consu',
                        'categ_id': category.id,
                        'message_partner_ids': [(4, manufacturer.id)] if manufacturer else False,
                    })

                    # Create supplier info if manufacturer exists
                    if manufacturer:
                        self.env['product.supplierinfo'].create({
                            'partner_id': manufacturer.id,
                            'product_tmpl_id': product.id,
                        })

                    products_dict[gtin] = product
                    _logger.info(f"Created new product: {drug_name} (GTIN: {gtin})")

                # Continue with pricelist item creation...
                
                # Check if product needs price update
                has_price_records = bool(PricelistItem.search_count([
                    ('product_tmpl_id', '=', product.id),
                    ('depot_price_wo_vat', '=', float(str(row[columns['depot_price_wo_vat_col']]).strip() or 0) ),
                    ('pricelist_id.is_pharma_pricelist', '=', True)
                ]))
                
                changed_this_week_raw = str(row[columns['changed_this_week_col']]).split('.')[0].strip()
                changed_this_week = changed_this_week_raw == '1'

                if changed_this_week or not has_price_records:
                    # Get or create appropriate pricelist
                    effective_date = pd.Timestamp(row[columns['effective_date_col']]).date()
                    # Get or create pricelist from cache
                    pricelist = cache['pricelists'].get(effective_date)                
                    
                    if not pricelist:
                        pricelist = Pricelist.search([
                            ('is_pharma_pricelist', '=', True),
                            ('effective_date', '=', effective_date)
                        ], limit=1)
                        
                        if not pricelist:
                            pricelist = Pricelist.create({
                                'name': f"Pharmaceutical Pricelist {effective_date}",
                                'is_pharma_pricelist': True,
                                'effective_date': effective_date
                            })
                            cache['pricelists'][effective_date] = pricelist
                            update_stats['pricelists_created'] += 1

                    # Create pricelist item
                    item_values = {
                        'product_tmpl_id': product.id,
                        'pricelist_id': pricelist.id,
                        'changed_this_week': changed_this_week,
                        'source_country': str(row[columns['source_country_col']]).strip(),
                        'actual_source_country': str(row[columns['actual_source_country_col']]).strip(),
                        'real_source_price': float(str(row[columns['real_source_price_col']]).strip() or 0),
                        'calculation_source_price': float(str(row[columns['calculation_source_price_col']]).strip() or 0),
                        'source_price_euro': float(str(row[columns['source_price_euro_col']]).strip() or 0),
                        # 'euro_rate': float(str(row[columns['euro_rate_col']]).replace('1 € =', '').strip() or 0),
                        'depot_price_wo_vat': float(str(row[columns['depot_price_wo_vat_col']]).strip() or 0),
                        'depot_sales_price_wo_vat': float(str(row[columns['depot_sales_wo_vat_col']]).strip() or 0),
                        'pharmacy_sales_price_wo_vat': float(str(row[columns['pharmacy_sales_wo_vat_col']]).strip() or 0),
                        'retail_price_w_vat': float(str(row[columns['retail_price_w_vat_col']]).strip() or 0),
                        'change_description' : str(row[columns['change_description_col']]).strip(),
                        'last_operation': str(row[columns['last_operation_col']]).strip(),
                    }

                    PricelistItem.create(item_values)
                    update_stats['pricelist_items_created'] += 1

                updates = {}
            
                # Fiyat kontrolü
                price = float(row[columns['price_col']])
                if product.list_price != price:
                    updates['list_price'] = price
                    update_stats['field_updates']['list_price'] += 1

                # ATC kodu kontrolü
                atc_code = str(row[columns['atc_col']]).strip()
                if product.atc_id.id != cache['atc'].get(atc_code):
                    updates['atc_id'] = cache['atc'].get(atc_code)
                    update_stats['field_updates']['atc_id'] += 1

                # Eşdeğerlik durumu kontrolü   
                equiv_status = str(row[columns['equiv_col']]).split('.')[0].strip()
                if product.equivalent_status_id.id != cache['equivalent'].get(equiv_status):
                    updates['equivalent_status_id'] = cache['equivalent'].get(equiv_status)
                    update_stats['field_updates']['equivalent_status_id'] += 1

                # Referans durumu kontrolü
                ref_status = str(row[columns['ref_col']]).split('.')[0].strip()
                if product.reference_status_id.id != cache['reference'].get(ref_status):
                    updates['reference_status_id'] = cache['reference'].get(ref_status)
                    update_stats['field_updates']['reference_status_id'] += 1

                # FDK AGÖK durumu kontrolü
                fdk_status = str(row[columns['fdk_col']]).split('.')[0].strip()
                if  fdk_status.lower() not in ['nan', ''] and product.fdk_agok_status_id.id != cache['fdk'].get(fdk_status):
                    updates['fdk_agok_status_id'] = cache['fdk'].get(fdk_status)
                    update_stats['field_updates']['fdk_agok_status_id'] += 1

                # Fiyat kararı gerekçesi kontrolü
                price_decree = str(row[columns['decree_col']]).split('.')[0].strip()
                if product.price_decree_reason_id.id != cache['decree'].get(price_decree):
                    updates['price_decree_reason_id'] = cache['decree'].get(price_decree)
                    update_stats['field_updates']['price_decree_reason_id'] += 1

                # Satış fiyatı tipi kontrolü
                price_type = str(row[columns['price_type_col']]).split('.')[0].strip()
                if product.sales_price_type_id.id != cache['price_type'].get(price_type):
                    updates['sales_price_type_id'] = cache['price_type'].get(price_type)
                    update_stats['field_updates']['sales_price_type_id'] += 1

                # İnhaler ürün grubu kontrolü
                inhaler_group = str(row[columns['inhaler_group_col']]).strip()
                if inhaler_group.lower() not in ['nan', ''] and product.inhaler_product_group_id.id != cache['inhaler_group'].get(inhaler_group):
                    updates['inhaler_product_group_id'] = cache['inhaler_group'].get(inhaler_group)
                    update_stats['field_updates']['inhaler_product_group_id'] += 1

                # İnhaler direnç grubu kontrolü
                resistance_code = str(row[columns['inhaler_resistance_col']]).split('.')[0].strip()
                if resistance_code.lower() not in ['nan', ''] and product.inhaler_resistance_group_id.id != cache['resistance'].get(resistance_code):
                    updates['inhaler_resistance_group_id'] = cache['resistance'].get(resistance_code)
                    update_stats['field_updates']['inhaler_resistance_group_id'] += 1

                # İnhaler cihaz kodu kontrolü
                device_code = str(row[columns['inhaler_device_col']]).strip()
                if device_code.lower() not in ['nan', ''] and product.inhaler_device_code_id.id != cache['device'].get(device_code):
                    updates['inhaler_device_code_id'] = cache['device'].get(device_code)
                    update_stats['field_updates']['inhaler_device_code_id'] += 1

                # İthal/İmal durumu kontrolü
                imported = str(row[columns['imported_col']]).strip() == 'ITHAL'
                if product.imported != imported:
                    updates['imported'] = imported
                    update_stats['field_updates']['imported'] += 1

                # Active Ingredient check
                active_ingredients = str(row[columns['active_ingredients_col']]).strip()
                if product.active_ingredients != active_ingredients:
                    updates['active_ingredients'] = active_ingredients
                    update_stats['field_updates']['active_ingredients'] += 1

                # Active Ingredients Amount check
                active_ingredients_amount = str(row[columns['active_ingredients_amount_col']]).strip()
                if product.active_ingredients_amount != active_ingredients_amount and active_ingredients_amount.lower() not in ['nan', '']:
                    updates['active_ingredients_amount'] = active_ingredients_amount
                    update_stats['field_updates']['active_ingredients_amount'] += 1

                # Active Ingredients UOM check
                active_ingredients_uom = str(row[columns['active_ingredients_uom_col']]).strip()
                if product.active_ingredients_uom != active_ingredients_uom and active_ingredients_uom.lower() not in ['nan', '']:
                    updates['active_ingredients_uom'] = active_ingredients_uom
                    update_stats['field_updates']['active_ingredients_uom'] += 1

                # Package Amount check
                package_amount = str(row[columns['package_amount_col']]).strip()
                if product.package_amount != package_amount:
                    updates['package_amount'] = package_amount
                    update_stats['field_updates']['package_amount'] += 1

                # Prescription Type check
                prescription = str(row[columns['prescription_col']]).strip()
                if prescription and prescription.lower() not in ['nan', '']:
                    prescription_id = cache['prescription'].get(prescription)
                    if product.prescription_type_id.id != prescription_id:
                        updates['prescription_type_id'] = prescription_id
                        update_stats['field_updates']['prescription_type_id'] += 1

                # ITS hareket durumu kontrolü
                its_status = str(row[columns['its_movement_col']]).split('.')[0].strip()
                if its_status and its_status != 'nan':
                    if product.its_movement_status != its_status:
                        updates['its_movement_status'] = its_status
                        update_stats['field_updates']['its_movement_status'] += 1
                        
                    
                        
                if updates:
                    batch_updates.append((product.id, updates))
                    if len(batch_updates) >= 200:
                        self._process_batch_updates(batch_updates)
                        update_stats['products_updated'] += len(batch_updates)
                        batch_updates = []

            except Exception as e:
                error_msg = f"GTIN: {gtin} - Hata: {str(e)}"
                _logger.error(error_msg)
                update_stats['errors'].append(error_msg)

        # Kalan güncellemeleri işle
        if batch_updates:
            self._process_batch_updates(batch_updates)
            update_stats['products_updated'] += len(batch_updates)

        # Sonuç raporunu hazırla ve göster
        self._show_import_results(update_stats)
        return update_stats['products_updated']

    def _process_ek4a_data(self, df):
        """Process EK4A data and update corresponding records"""
        Product = self.env['product.template']
        update_stats = {
            'total_records': len(df),
            'products_found': 0,
            'products_not_found': 0,
            'products_updated': 0,
            'field_updates': {
                'public_no': 0,
                'equivalent_drug_group': 0,
                'therapeutic_ref_group': 0,
                'list_entry_date': 0,
                'activation_date': 0,
                'deactivation_date': 0,
                'discount_status': 0,
                'price_range_discounts': 0,
                'special_discount': 0,
                'pharmacy_discount': 0,
                'depot_price_range_4_discount_rate': 0,
                'depot_price_range_3_discount_rate': 0,
                'depot_price_range_2_discount_rate': 0,
                'depot_price_range_1_discount_rate': 0,
            },
            'errors': []
        }

        try:
            columns = {
                'barcode_col': [col for col in df.columns if 'Güncel Barkod' in col][0],
                'public_no_col': [col for col in df.columns if 'Kamu No' in col][0],
                'equivalent_group_col': [col for col in df.columns if 'Eşdeğer İlaç Grubu' in col][0],
                'therapeutic_group_col': [col for col in df.columns if 'Terapötik Referans Grubu' in col][0],
                'entry_date_col': [col for col in df.columns if 'Listeye Giriş Tarihi' in col][0],
                'activation_date_col': [col for col in df.columns if 'Aktiflenme Tarihi' in col][0],
                'deactivation_date_col': [col for col in df.columns if 'Pasiflenme Tarihi' in col][0],
                'discount_status_col': [col for col in df.columns if 'Uygulanan İndirim Oranlarına Esas Durumu' in col][0],
                'special_discount_col': [col for col in df.columns if 'Özel İskonto' in col][0],
                'pharmacy_discount_col': [col for col in df.columns if 'Eczacı İskonto Oranı' in col][0],
                'price_range_4_col': [col for col in df.columns if 'Depocuya Satış  Fiyatı\n91,17 TL ve üzeri ise' in col][0],
                'price_range_3_col': [col for col in df.columns if 'Depocuya Satış  Fiyatı \n60,52 (dahil)-91,16 TL (dahil) arasında ise' in col][0],
                'price_range_2_col': [col for col in df.columns if 'Depocuya Satış  Fiyatı \n31,62 TL (dahil)-60,51 TL (dahil) arasında ise' in col][0],
                'price_range_1_col': [col for col in df.columns if 'Depocuya Satış Fiyatı \n31,61 TL ve altında ise' in col][0],
                
            }
        except Exception as e:
            raise UserError(_('Column mapping error: %s') % str(e))

        all_gtins = ['0' + str(x).split('.')[0].strip() for x in df[columns['barcode_col']]]
        products_dict = {p.gtin: p for p in Product.search([('gtin', 'in', all_gtins)])}

        update_stats['products_found'] = len(products_dict)
        update_stats['products_not_found'] = len(all_gtins) - len(products_dict)

        for _, row in df.iterrows():
            try:
                gtin = '0' + str(row[columns['barcode_col']]).split('.')[0].strip()
                product = products_dict.get(gtin)

                if not product:
                    continue

                updates = {}

                # Process text fields
                for field, column in [
                    ('public_no', 'public_no_col'),
                    ('equivalent_drug_group', 'equivalent_group_col'),
                    ('therapeutic_ref_group', 'therapeutic_group_col'),
                    ('discount_status', 'discount_status_col')
                ]:
                    value = str(row[columns[column]]).strip()
                    if value and value.lower() not in ['nan', '']:
                        if getattr(product, field) != value:
                            updates[field] = value
                            update_stats['field_updates'][field] += 1

                # Process date fields
                for field, column in [
                    ('list_entry_date', 'entry_date_col'),
                    ('activation_date', 'activation_date_col'),
                    ('deactivation_date', 'deactivation_date_col')
                ]:
                    try:
                        date_value = row[columns[column]]
                        # Check if date is valid (not NaT, not NaN, not empty)
                        if pd.notna(date_value) and date_value:
                            date_value = pd.Timestamp(date_value).date()
                            if getattr(product, field) != date_value:
                                updates[field] = date_value
                                update_stats['field_updates'][field] += 1
                    except (ValueError, TypeError):
                        _logger.warning(f"Invalid date value for {field}: {row[columns[column]]}")
                        continue
                # Process discount fields
                for field, column in [
                    ('special_discount', 'special_discount_col'),
                    ('pharmacy_discount', 'pharmacy_discount_col'),
                    ('depot_price_range_4_discount_rate', 'price_range_4_col'),
                    ('depot_price_range_3_discount_rate', 'price_range_3_col'),
                    ('depot_price_range_2_discount_rate', 'price_range_2_col'),
                    ('depot_price_range_1_discount_rate', 'price_range_1_col')
                ]:
                    try:
                        value = float(str(row[columns[column]]).strip() or 0)
                        if getattr(product, field) != value:
                            updates[field] = value
                            update_stats['field_updates'][field] += 1
                    except (ValueError, TypeError):
                        pass

                if updates:
                    product.write(updates)
                    update_stats['products_updated'] += 1

            except Exception as e:
                error_msg = f"GTIN: {gtin} - Error: {str(e)}"
                _logger.error(error_msg)
                update_stats['errors'].append(error_msg)

        self._show_import_results(update_stats)
        return update_stats['products_updated']
    
    def _process_batch_updates(self, batch_updates):
        """Toplu güncellemeleri işle"""
        for product_id, updates in batch_updates:
            self.env['product.template'].browse(product_id).write(updates) 
        
    def _show_import_results(self, stats):
        """İmport sonuçlarını göster"""
        message = f"""
        İmport İşlemi Tamamlandı
        
        Toplam Kayıt: {stats['total_records']}
        Bulunan Ürün: {stats['products_found']}
        Bulunamayan Ürün: {stats['products_not_found']}
        Güncellenen Ürün: {stats['products_updated']}
                
        """
        
        if stats['errors']:
            message += "\nHatalar:\n" + "\n".join(stats['errors'][:10])
            if len(stats['errors']) > 10:
                message += f"\n... ve {len(stats['errors']) - 10} hata daha"
        
        # _logger.info(message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İmport Tamamlandı'),
                'message': message,
                'type': 'success',
                'sticky': True,
            }
        }

    def action_import(self):
        """Import action'ı çalıştır"""
        try:
            file_info = self._process_excel_data()
            type = file_info['type']
            df = file_info['data']

            if type == 'price_list':
                updated_records = self._update_products(df)
                message = _(f'Updated {updated_records} products from Price List')
            elif type == 'ek4a':
                updated_records = self._process_ek4a_data(df)
                message = _(f'Updated {updated_records} records from EK4A list')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Completed'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_('Import sırasında hata oluştu: %s') % str(e))