# -*- coding: utf-8 -*-

import base64
import io
import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None


class ImportHistoricalPOWizard(models.TransientModel):
    _name = 'import.historical.po.wizard'
    _description = 'Geçmiş Dönem Satınalma Siparişleri İmport Wizard'

    excel_file = fields.Binary(
        string='Excel Dosyası',
        help="Geçmiş dönem PO verilerini içeren Excel dosyasını yükleyin"
    )
    file_name = fields.Char(
        string='Dosya Adı',
        default='Gecmis_Donem_PO_Import.xlsx'
    )
    
    create_partners = fields.Boolean(
        string='Yeni Tedarikçi Oluştur',
        default=True,
        help="Excel'de olmayan tedarikçileri otomatik oluştur"
    )
    
    create_products = fields.Boolean(
        string='Yeni Ürün Oluştur',
        default=False,
        help="Excel'de olmayan ürünleri otomatik oluştur"
    )
    
    skip_duplicates = fields.Boolean(
        string='Duplikaları Atla',
        default=True,
        help="Aynı sipariş numarası varsa atla"
    )
    
    confirm_orders = fields.Boolean(
        string='Siparişleri Onayla',
        default=False,
        help="Import edilen siparişleri otomatik onayla (RFQ -> Purchase Order)"
    )

    def _install_pandas(self):
        """Pandas kütüphanesini yükle"""
        global pd
        if pd:
            return True
        import subprocess
        import sys
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                'pandas', 'openpyxl', 'xlrd'
            ])
            import pandas as pd
            return True
        except Exception as e:
            raise UserError(_("Pandas kurulum hatası: %s") % str(e))

    def action_import_master_data(self):
        """Excel'den Material Group ve Purchasing Group verilerini import et"""
        self.ensure_one()
        
        if not self.excel_file:
            raise UserError(_('Lütfen bir Excel dosyası seçin.'))
        
        if not pd:
            self._install_pandas()
        
        # Excel dosyasını oku
        try:
            excel_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(excel_data), sheet_name='Geçmiş_PO')
        except Exception as e:
            raise UserError(_('Excel dosyası okunamadı: %s') % str(e))
        
        # İstatistikler
        stats = {
            'total_rows': len(df),
            'material_groups': {'created': 0, 'existing': 0, 'codes': set()},
            'purchasing_groups': {'created': 0, 'existing': 0, 'codes': set()},
            'errors': []
        }
        
        # MALZEME_GRUBU verilerini topla
        if 'MALZEME_GRUBU' in df.columns:
            for idx, row in df.iterrows():
                mg_raw = row.get('MALZEME_GRUBU')
                if pd.notna(mg_raw):
                    mg_code = str(mg_raw).strip()[:4] if len(str(mg_raw)) >= 4 else str(mg_raw).strip()
                    if mg_code:
                        stats['material_groups']['codes'].add(mg_code)
        
        # SAG verilerini topla
        if 'SAG' in df.columns:
            for idx, row in df.iterrows():
                sag_raw = row.get('SAG')
                if pd.notna(sag_raw):
                    sag_code = str(sag_raw).strip()
                    if sag_code:
                        stats['purchasing_groups']['codes'].add(sag_code)
        
        # Material Group'ları oluştur
        for mg_code in stats['material_groups']['codes']:
            try:
                mg_record = self._get_or_create_material_group_record(mg_code)
                if mg_record:
                    if mg_record.id:
                        # Yeni oluşturuldu mu kontrol et (basit kontrol)
                        if 'Tanımsız' in mg_record.name:
                            stats['material_groups']['created'] += 1
                        else:
                            stats['material_groups']['existing'] += 1
            except Exception as e:
                error_msg = f"Material Group {mg_code}: {str(e)}"
                _logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Purchasing Group'ları oluştur
        for sag_code in stats['purchasing_groups']['codes']:
            try:
                pg_record = self._get_or_create_purchasing_group_record(sag_code)
                if pg_record:
                    if pg_record.id:
                        # Yeni oluşturuldu mu kontrol et
                        if 'Tanımsız' in pg_record.name:
                            stats['purchasing_groups']['created'] += 1
                        else:
                            stats['purchasing_groups']['existing'] += 1
            except Exception as e:
                error_msg = f"Purchasing Group {sag_code}: {str(e)}"
                _logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # Commit yap
        self.env.cr.commit()
        
        # Sonuç mesajı
        return self._show_master_data_import_result(stats)
    
    def _get_or_create_material_group_record(self, mg_code):
        """Material Group kaydını bul veya oluştur (import için)"""
        MaterialGroup = self.env['tender.type.material.group']
        
        # Önce ara
        mg_record = MaterialGroup.search([('code', '=', mg_code)], limit=1)
        if mg_record:
            return mg_record
        
        # Yoksa oluştur
        return self._create_material_group(mg_code)
    
    def _get_or_create_purchasing_group_record(self, sag_code):
        """Purchasing Group kaydını bul veya oluştur (import için)"""
        PurchasingGroup = self.env['tender.type.purchasing.group']
        
        # Önce ara
        pg_record = PurchasingGroup.search([('code', '=', sag_code)], limit=1)
        if pg_record:
            return pg_record
        
        # Yoksa oluştur
        try:
            existing_undefined = PurchasingGroup.search([
                ('name', 'ilike', 'Tanımsız SAG')
            ])
            next_number = len(existing_undefined) + 1
            pg_name = f"Tanımsız SAG {next_number}"
            
            pg_vals = {
                'code': sag_code,
                'name': pg_name,
                'description': f'Geçmiş PO import\'undan otomatik oluşturuldu',
                'active': True,
            }
            
            pg_record = PurchasingGroup.create(pg_vals)
            _logger.info(f"Yeni Purchasing Group oluşturuldu: {sag_code} - {pg_name}")
            return pg_record
        except Exception as e:
            _logger.error(f"Purchasing Group oluşturulamadı ({sag_code}): {str(e)}")
            return False
    
    def _show_master_data_import_result(self, stats):
        """Master data import sonucunu göster"""
        message = _(
            "Master Data İmport Tamamlandı!\n\n"
            "Toplam Satır: %d\n\n"
            "Material Groups:\n"
            "  - Toplam Benzersiz Kod: %d\n"
            "  - Yeni Oluşturulan: %d\n"
            "  - Mevcut: %d\n\n"
            "Purchasing Groups:\n"
            "  - Toplam Benzersiz Kod: %d\n"
            "  - Yeni Oluşturulan: %d\n"
            "  - Mevcut: %d\n"
        ) % (
            stats['total_rows'],
            len(stats['material_groups']['codes']),
            stats['material_groups']['created'],
            stats['material_groups']['existing'],
            len(stats['purchasing_groups']['codes']),
            stats['purchasing_groups']['created'],
            stats['purchasing_groups']['existing']
        )
        
        if stats['errors']:
            message += _("\n\nHatalar (%d):\n") % len(stats['errors'])
            message += "\n".join(stats['errors'][:10])
            if len(stats['errors']) > 10:
                message += _("\n... ve %d hata daha") % (len(stats['errors']) - 10)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Master Data İmport Sonucu'),
                'message': message,
                'type': 'success' if not stats['errors'] else 'warning',
                'sticky': True,
            }
        }
    
    def action_download_template(self):
        """Excel template dosyasını indir"""
        self.ensure_one()
        
        # Template verilerini hazırla
        template_data = {
            'SIPARIS_NO': ['4500123456', '4500123456', '4500123457'],
            'KALEM_NO': ['10', '20', '10'],
            'SIPARIS_TARIHI': ['2023-01-15', '2023-01-15', '2023-02-20'],
            'TEDARIKCI_KODU': ['T001', 'T001', 'T002'],
            'TEDARIKCI_ADI': ['ABC Tedarik A.Ş.', 'ABC Tedarik A.Ş.', 'XYZ Ltd. Şti.'],
            'MALZEME_KODU': ['MAL001', 'MAL002', 'MAL003'],
            'MALZEME_ADI': ['Buğday Unu', 'Şeker', 'Ayçiçek Yağı'],
            'MALZEME_GRUBU': ['1000-01', '6000-01', '9000-01'],
            'SAG': ['105', '110', '101'],
            'MIKTAR': [1000, 500, 2000],
            'BIRIM': ['KG', 'KG', 'LT'],
            'BIRIM_FIYAT': [15.50, 25.00, 45.75],
            'PARA_BIRIMI': ['TRY', 'TRY', 'TRY'],
            'TOPLAM_TUTAR': [15500, 12500, 91500],
            'VADE': ['30 Gün', '30 Gün', '60 Gün'],
            'IHALE_TIPI': ['direct', 'direct', 'indirect'],
            'SIRKET_KODU': ['2100', '2100', '2100'],
            'TESIS': ['İlko Merkez', 'İlko Merkez', 'İlko Fabrika'],
            'SATIN_ALMACI': ['Ahmet Yılmaz', 'Ahmet Yılmaz', 'Mehmet Kaya'],
            'SAG': ['105', '110', '101'],
            'TESLIMAT_TARIHI': ['2023-02-15', '2023-02-15', '2023-03-25'],
            'NOTLAR': ['', 'Acil sipariş', '']
        }
        
        if not pd:
            self._install_pandas()
        
        # DataFrame oluştur
        df = pd.DataFrame(template_data)
        
        # Excel'e yaz
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Geçmiş_PO', index=False)
            
            # Açıklamalar sayfası
            instructions = {
                'Alan Adı': list(template_data.keys()),
                'Açıklama': [
                    'SAP Sipariş Numarası',
                    'SAP Kalem Numarası',
                    'Sipariş Tarihi (YYYY-MM-DD formatında)',
                    'Tedarikçi SAP Kodu',
                    'Tedarikçi Ünvanı',
                    'Malzeme SAP Kodu',
                    'Malzeme Açıklaması',
                    'SAP Malzeme Grubu (ör: 1000-01, 6000-01)',
                    'SAP Satınalma Grubu (ör: 101, 105, 110)',
                    'Sipariş Miktarı',
                    'Ölçü Birimi (KG, LT, AD, vb.)',
                    'Birim Fiyat',
                    'Para Birimi (TRY, USD, EUR)',
                    'Toplam Tutar (Hesaplanan)',
                    'Ödeme Vadesi (örn: 30 Gün, 60 Gün)',
                    'İhale Tipi (direct/indirect/promotion/mice)',
                    'SAP Şirket Kodu (2100, 2000, 1100)',
                    'Tesis/Depo Adı',
                    'Satınalmacı Adı',
                    'Teslimat Tarihi (YYYY-MM-DD)',
                    'Ek Notlar'
                ],
                'Zorunlu': [
                    'Evet',    # SIPARIS_NO
                    'Hayır',   # KALEM_NO
                    'Evet',    # SIPARIS_TARIHI
                    'Evet',    # TEDARIKCI_KODU
                    'Evet',    # TEDARIKCI_ADI
                    'Hayır',   # MALZEME_KODU
                    'Evet',    # MALZEME_ADI
                    'Hayır',   # MALZEME_GRUBU
                    'Hayır',   # SAG
                    'Evet',    # MIKTAR
                    'Evet',    # BIRIM
                    'Evet',    # BIRIM_FIYAT
                    'Evet',    # PARA_BIRIMI
                    'Hayır',   # TOPLAM_TUTAR
                    'Evet',    # VADE
                    'Hayır',   # IHALE_TIPI
                    'Evet',    # SIRKET_KODU
                    'Hayır',   # TESIS
                    'Hayır',   # SATIN_ALMACI
                    'Hayır',   # TESLIMAT_TARIHI
                    'Hayır'    # NOTLAR
                ]
            }
            df_instructions = pd.DataFrame(instructions)
            df_instructions.to_excel(writer, sheet_name='Açıklamalar', index=False)
        
        output.seek(0)
        excel_data = base64.b64encode(output.read())
        
        # Dosyayı indir
        attachment = self.env['ir.attachment'].create({
            'name': 'Gecmis_Donem_PO_Import_Sablonu.xlsx',
            'type': 'binary',
            'datas': excel_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def action_import_po(self):
        """Excel'den geçmiş dönem PO'ları import et"""
        self.ensure_one()
        
        if not self.excel_file:
            raise UserError(_('Lütfen bir Excel dosyası seçin.'))
        
        if not pd:
            self._install_pandas()
        
        # Excel dosyasını oku
        try:
            excel_data = base64.b64decode(self.excel_file)
            df = pd.read_excel(io.BytesIO(excel_data), sheet_name='Geçmiş_PO')
        except Exception as e:
            raise UserError(_('Excel dosyası okunamadı: %s') % str(e))
        
        # Zorunlu kolonları kontrol et
        required_columns = [
            'SIPARIS_NO', 'SIPARIS_TARIHI', 'TEDARIKCI_KODU', 'TEDARIKCI_ADI',
            'MALZEME_ADI', 'MIKTAR', 'BIRIM',
            'BIRIM_FIYAT', 'PARA_BIRIMI', 'VADE', 'SIRKET_KODU'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise UserError(
                _('Excel dosyasında eksik zorunlu kolonlar var:\n%s') % ', '.join(missing_columns)
            )
        
        # Boş zorunlu alanları kontrol et
        empty_required = []
        for col in required_columns:
            if df[col].isna().any():
                empty_rows = df[df[col].isna()].index.tolist()
                empty_required.append(f"{col}: Satır {', '.join(map(str, [r+2 for r in empty_rows]))}")
        
        if empty_required:
            raise UserError(
                _('Aşağıdaki zorunlu alanlarda boş değerler var:\n\n%s') % '\n'.join(empty_required)
            )
        
        # İstatistikler
        stats = {
            'total': len(df),
            'created_po': 0,
            'updated_po': 0,
            'created_lines': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Import batch ID
        import_batch = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Satırları grupla (aynı sipariş numarasına göre)
        grouped = df.groupby('SIPARIS_NO')
        
        # Process edilecek siparişleri listele
        order_list = list(grouped)
        total_orders = len(order_list)
        
        for idx, (order_no, order_lines) in enumerate(order_list, 1):
            try:
                self._process_order(order_no, order_lines, import_batch, stats)
                
                # Her 20 siparişte bir commit yap (daha küçük batch, daha az timeout riski)
                if idx % 20 == 0:
                    self.env.cr.commit()
                    _logger.info(f"Progress: {idx}/{total_orders} siparişler işlendi")
                    
            except Exception as e:
                # Hata durumunda sadece log tut, devam et
                error_msg = f"Sipariş {order_no}: {str(e)}"
                _logger.error(error_msg, exc_info=True)
                stats['errors'].append(error_msg)
                stats['skipped'] += len(order_lines)
                continue
        
        # Son batch'i commit et
        self.env.cr.commit()
        
        # Import sonrası UOM düzeltmesi yap
        fix_stats = self._fix_incorrect_uoms_after_import(import_batch)
        if fix_stats:
            stats['uom_fixed'] = fix_stats['fixed']
            stats['uom_checked'] = fix_stats['checked']
        
        # Sonuç mesajı
        return self._show_import_result(stats)

    def _process_order(self, order_no, order_lines, import_batch, stats):
        """Tek bir siparişi işle"""
        PurchaseOrder = self.env['purchase.order']
        
        # İlk satırdan header bilgilerini al
        first_line = order_lines.iloc[0]
        
        # Mevcut siparişi kontrol et
        existing_po = PurchaseOrder.search([
            ('name', '=', str(order_no))
        ], limit=1)
        
        if existing_po and self.skip_duplicates:
            stats['skipped'] += len(order_lines)
            return
        
        # Tedarikçiyi bul veya oluştur
        partner = self._get_or_create_partner(first_line)
        
        # SAG (Satınalma Grubu) bilgisini al ve kontrol et
        purchasing_group = str(first_line.get('SAG', '')).strip() if pd.notna(first_line.get('SAG')) else ''
        if purchasing_group:
            # SAG kaydının sistemde olup olmadığını kontrol et, yoksa oluştur
            self._get_or_create_purchasing_group(purchasing_group)
        
        # Para birimini bul
        currency = self._get_currency(str(first_line.get('PARA_BIRIMI', 'TRY')))
        
        # Ödeme vadesini bul
        payment_term = self._get_payment_term(str(first_line.get('VADE', '')))
        
        # Sipariş tarihini parse et
        order_date = self._parse_date(first_line.get('SIPARIS_TARIHI'))
        
        # Ana şirketi kullan
        company = self.env.company

        # Depo ve Operasyon Tipini bul - purchase_stock modülü için ZORUNLU
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not warehouse:
            raise UserError(_("%s şirketi için tanımlı bir depo bulunamadı. Lütfen önce bir depo oluşturun.") % company.name)
            
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', warehouse.id)
        ], limit=1)
        
        if not picking_type:
            raise UserError(_("%s deposu için 'Incoming' tipi operasyon bulunamadı.") % warehouse.name)

        # PO oluştur veya güncelle
        po_vals = {
            'partner_id': partner.id,
            'company_id': company.id,
            'date_order': order_date,
            'currency_id': currency.id,
            'picking_type_id': picking_type.id,  # ZORUNLU - purchase_stock modülü için
            'is_historical_import': True,
            'import_batch': import_batch,
            'purchasing_group': purchasing_group,  # SAG bilgisini kaydet
            'notes': str(first_line.get('NOTLAR', '')),
        }
        
        if payment_term:
            po_vals['payment_term_id'] = payment_term.id
        
        # İhale tipi
        tender_type = str(first_line.get('IHALE_TIPI', '')).lower()
        if tender_type in ['direct', 'indirect', 'promotion', 'service']:
            po_vals['tender_type'] = tender_type
        
        # Context ile tracking'i devre dışı bırak
        ctx = dict(self.env.context, tracking_disable=True, mail_create_nolog=True)
        
        if existing_po:
            # Mevcut siparişi güncelle
            # Eğer sipariş kilitliyse (locked/done state), önce draft'a çek
            if existing_po.state in ('purchase', 'done'):
                # Kilitli siparişi draft'a çekmek için button_draft kullan
                try:
                    existing_po.button_draft()
                except:
                    # Eğer draft'a çekilemiyorsa, bu siparişi atla
                    raise ValidationError(
                        _('Sipariş %s kilitli durumda ve draft\'a çekilemiyor. Lütfen manuel olarak kontrol edin.') % order_no
                    )
            
            # Mevcut satırları sil (artık draft durumda olduğu için silinebilir)
            existing_po.order_line.unlink()
            existing_po.with_context(ctx).write(po_vals)
            purchase_order = existing_po
            stats['updated_po'] += 1
        else:
            po_vals['name'] = str(order_no)
            purchase_order = PurchaseOrder.with_context(ctx).create(po_vals)
            stats['created_po'] += 1
        
        # Satırları ekle
        for idx, line_data in order_lines.iterrows():
            self._create_order_line(purchase_order, line_data, currency, stats)
        
        # Siparişi onayla (istenirse)
        if self.confirm_orders and purchase_order.state == 'draft':
            purchase_order.button_confirm()

    def _create_order_line(self, purchase_order, line_data, currency, stats):
        """Sipariş satırı oluştur"""
        POLine = self.env['purchase.order.line']
        
        # Ürünü bul veya oluştur
        product = self._get_or_create_product(line_data)
        
        # Birim bul
        uom = self._get_uom(str(line_data.get('BIRIM', 'AD')))
        
        # Eğer ürünün birimi ile Excel'deki birim farklı kategorideyse (örn: kg vs Adet)
        # Hata almamak için ürünün mevcut birimini kullan
        if product.uom_id.category_id != uom.category_id:
            uom = product.uom_id
        
        # Teslimat tarihini parse et
        date_planned = self._parse_date(line_data.get('TESLIMAT_TARIHI'))
        if not date_planned:
            date_planned = purchase_order.date_order
        
        # Miktar parse et - pandas zaten sayısal değer döndürür
        miktar_raw = line_data.get('MIKTAR', 1.0)
        if isinstance(miktar_raw, (int, float)):
            product_qty = float(miktar_raw)
        else:
            # String ise parse et
            product_qty = float(str(miktar_raw).split(' ')[0].replace(',', '.'))
        
        
        # Fiyat hesaplama: TOPLAM_TUTAR varsa öncelik ver, yoksa BIRIM_FIYAT kullan
        total_amount_excel = line_data.get('TOPLAM_TUTAR')
        unit_price_excel = line_data.get('BIRIM_FIYAT')
        
        # TOPLAM_TUTAR'ı parse et - pandas zaten sayısal değer döndürür
        if total_amount_excel is not None and not pd.isna(total_amount_excel):
            # Pandas Excel'den sayısal değer döndürür, string parse etmeye gerek yok
            if isinstance(total_amount_excel, (int, float)):
                total_amount = float(total_amount_excel)
            else:
                # Eğer string ise (nadir durum), sadece virgülü noktaya çevir
                total_amount = float(str(total_amount_excel).replace(',', '.'))
            
            if total_amount > 0 and product_qty > 0:
                # TOPLAM_TUTAR varsa, birim fiyatı buradan hesapla (en doğru yöntem)
                price_unit = total_amount / product_qty
            else:
                price_unit = 0.0
        elif unit_price_excel is not None and not pd.isna(unit_price_excel):
            # BIRIM_FIYAT'ı parse et - pandas zaten sayısal değer döndürür
            if isinstance(unit_price_excel, (int, float)):
                price_unit = float(unit_price_excel)
            else:
                # Eğer string ise, sadece virgülü noktaya çevir
                price_unit = float(str(unit_price_excel).replace(',', '.'))
        else:
            price_unit = 0.0
        
        line_vals = {
            'order_id': purchase_order.id,
            'product_id': product.id,
            'name': str(line_data.get('MALZEME_ADI', product.name)),
            'product_qty': product_qty,
            'product_uom': uom.id,
            'price_unit': price_unit,
            'line_price_unit': price_unit,  # ÖNEMLI: _compute_price_unit() bu alandan hesaplıyor
            'currency_id': purchase_order.currency_id.id,  # Para birimi
            'line_currency_id': currency.id,  # Para birimini de set et
            'date_planned': date_planned,
            'taxes_id': [(5, 0, 0)], # Geçmiş verilerde vergi olmasın
        }
        
        # Satırı oluştur
        new_line = POLine.create(line_vals)
        
        # Güvenlik için: Eğer hala fiyat sıfırsa, zorla yaz
        if new_line.price_unit != price_unit and price_unit > 0:
            new_line.write({
                'price_unit': price_unit,
                'line_price_unit': price_unit,
            })
        
        stats['created_lines'] += 1

    def _get_or_create_partner(self, line_data):
        """Tedarikçiyi bul veya oluştur"""
        Partner = self.env['res.partner']
        
        vendor_code = str(line_data.get('TEDARIKCI_KODU', '')).strip()
        vendor_name = str(line_data.get('TEDARIKCI_ADI', '')).strip()
        
        if not vendor_name:
            raise ValidationError(_('Tedarikçi adı zorunludur'))
        
        # Önce koda göre ara
        if vendor_code:
            partner = Partner.search([('ref', '=', vendor_code)], limit=1)
            if partner:
                return partner
        
        # İsme göre ara
        partner = Partner.search([('name', '=', vendor_name)], limit=1)
        if partner:
            return partner
        
        # Oluştur
        if self.create_partners:
            tag = self.env['res.partner.category'].search([('name', '=', 'Geçmiş PO Import')], limit=1)
            if not tag:
                tag = self.env['res.partner.category'].create({'name': 'Geçmiş PO Import'})
            
            partner_vals = {
                'name': vendor_name,
                'ref': vendor_code if vendor_code else False,
                'supplier_rank': 1,
                'company_type': 'company',
                'category_id': [(4, tag.id)],
            }
            return Partner.create(partner_vals)
        else:
            raise ValidationError(
                _('Tedarikçi bulunamadı: %s. Lütfen önce tedarikçiyi oluşturun veya "Yeni Tedarikçi Oluştur" seçeneğini işaretleyin.') % vendor_name
            )

    def _get_or_create_product(self, line_data):
        """Ürünü bul veya oluştur - MALZEME_GRUBU bilgisini de işle"""
        Product = self.env['product.product']
        
        product_code = str(line_data.get('MALZEME_KODU', '')).strip()
        product_name = str(line_data.get('MALZEME_ADI', '')).strip()
        material_group = str(line_data.get('MALZEME_GRUBU', '')).strip() if pd.notna(line_data.get('MALZEME_GRUBU')) else ''
        
        if not product_name:
            raise ValidationError(_('Malzeme adı zorunludur'))
        
        # Önce koda göre ara
        if product_code and product_code != 'nan':
            product = Product.search([('default_code', '=', product_code)], limit=1)
            if product:
                # Ürün bulundu, MALZEME_GRUBU bilgisini güncelle (hem kategori hem de alan)
                self._update_product_material_group(product, material_group)
                return product
        
        # İsme göre ara
        if product_name and product_name != 'nan':
            product = Product.search([('name', '=', product_name)], limit=1)
            if product:
                # Ürün bulundu, MALZEME_GRUBU bilgisini güncelle
                self._update_product_material_group(product, material_group)
                return product
        
        # Oluştur
        if self.create_products:
            tag = self.env['product.tag'].search([('name', '=', 'Geçmiş PO Import')], limit=1)
            if not tag:
                tag = self.env['product.tag'].create({'name': 'Geçmiş PO Import'})

            # MALZEME_GRUBU'na göre kategori bul veya oluştur
            category_id = self._get_or_create_category(material_group) if material_group else False

            product_vals = {
                'name': product_name,
                'default_code': product_code if product_code else False,
                'type': 'consu',
                'purchase_ok': True,
                'product_tag_ids': [(4, tag.id)],
                'categ_id': category_id.id if category_id else False,
                'material_group': material_group if material_group else False,  # İlk 4 hane (BI raporlama için)
            }
            
            new_product = Product.create(product_vals)
            
            # MALZEME_GRUBU bilgisini log'la
            if material_group:
                _logger.info(f"Ürün oluşturuldu: {product_name} - Malzeme Grubu: {material_group}")
            
            return new_product
        else:
            raise ValidationError(
                _('Ürün bulunamadı: %s. Lütfen önce ürünü oluşturun veya "Yeni Ürün Oluştur" seçeneğini işaretleyin.') % product_name
            )
    
    def _update_product_material_group(self, product, material_group):
        """Ürünün MALZEME_GRUBU bilgisini güncelle (hem kategori hem de alan)
        
        material_group: İlk 4 hane (1000, 6000, 9000)
        """
        if not material_group or material_group == 'nan':
            return
        
        update_vals = {}
        
        # Kategoriyi güncelle
        category = self._get_or_create_category(material_group)
        if category and product.categ_id != category:
            update_vals['categ_id'] = category.id
        
        # Material group alanını güncelle (ilk 4 hane)
        if product.material_group != material_group:
            update_vals['material_group'] = material_group
        
        if update_vals:
            product.write(update_vals)
            _logger.info(f"Ürün güncellendi: {product.name} - Malzeme Grubu: {material_group}")
    
    def _get_or_create_category(self, material_group):
        """MALZEME_GRUBU'na göre kategori bul veya oluştur
        
        Material Group kaydından kategori oluşturur
        """
        if not material_group or material_group == 'nan':
            return False
        
        # İlk 4 karakteri al (ör: 1000, 6000, 9000)
        mg_code = material_group[:4] if len(material_group) >= 4 else material_group
        
        Category = self.env['product.category']
        MaterialGroup = self.env['tender.type.material.group']
        
        # Malzeme grubu kaydını bul veya oluştur
        mg_record = MaterialGroup.search([('code', '=', mg_code)], limit=1)
        if not mg_record:
            mg_record = self._create_material_group(mg_code)
        
        if not mg_record:
            return False
        
        # Kategori adı: "Kod - İsim" formatında
        category_name = f"{mg_record.code} - {mg_record.name}"
        
        # Kategoriyi ara
        category = Category.search([
            '|',
            ('name', '=', category_name),
            ('name', 'ilike', f"{mg_record.code} -")
        ], limit=1)
        
        if category:
            return category
        
        # Kategori yoksa oluştur
        try:
            # Ana kategori
            parent_category = Category.search([('name', '=', 'SAP Malzeme Grupları')], limit=1)
            if not parent_category:
                parent_category = Category.create({'name': 'SAP Malzeme Grupları'})
            
            category = Category.create({
                'name': category_name,
                'parent_id': parent_category.id,
            })
            _logger.info(f"Yeni kategori oluşturuldu: {category_name}")
            return category
        except Exception as e:
            _logger.warning(f"Kategori oluşturulamadı ({category_name}): {str(e)}")
            return False
    
    def _create_material_group(self, mg_code):
        """Yeni Material Group kaydı oluştur"""
        MaterialGroup = self.env['tender.type.material.group']
        
        try:
            # Kaç tane "Tanımsız" kaydı var kontrol et
            existing_undefined = MaterialGroup.search([
                ('name', 'ilike', 'Tanımsız')
            ])
            
            # Sıradaki numarayı bul
            next_number = len(existing_undefined) + 1
            mg_name = f"Tanımsız {next_number}"
            
            # Yeni Material Group oluştur
            mg_vals = {
                'code': mg_code,
                'name': mg_name,
                'description': f'Geçmiş PO import\'undan otomatik oluşturuldu',
                'active': True,
            }
            
            mg_record = MaterialGroup.create(mg_vals)
            _logger.info(
                f"Yeni Material Group oluşturuldu: {mg_code} - {mg_name} "
                f"(Excel'deki tam kod için ilk 4 hane kullanıldı)"
            )
            return mg_record
            
        except Exception as e:
            _logger.error(f"Material Group oluşturulamadı ({mg_code}): {str(e)}")
            return False
    
    def _get_or_create_purchasing_group(self, sag_code):
        """SAG kaydını bul veya oluştur"""
        if not sag_code or sag_code == 'nan':
            return False
        
        PurchasingGroup = self.env['tender.type.purchasing.group']
        
        # SAG kaydını ara
        pg_record = PurchasingGroup.search([('code', '=', sag_code)], limit=1)
        
        if pg_record:
            return pg_record
        
        # Yoksa yeni oluştur
        try:
            # Kaç tane "Tanımsız" SAG kaydı var kontrol et
            existing_undefined = PurchasingGroup.search([
                ('name', 'ilike', 'Tanımsız SAG')
            ])
            
            # Sıradaki numarayı bul
            next_number = len(existing_undefined) + 1
            pg_name = f"Tanımsız SAG {next_number}"
            
            # Yeni Purchasing Group oluştur
            pg_vals = {
                'code': sag_code,
                'name': pg_name,
                'description': f'Geçmiş PO import\'undan otomatik oluşturuldu',
                'active': True,
            }
            
            pg_record = PurchasingGroup.create(pg_vals)
            _logger.info(f"Yeni Purchasing Group oluşturuldu: {sag_code} - {pg_name}")
            return pg_record
            
        except Exception as e:
            _logger.error(f"Purchasing Group oluşturulamadı ({sag_code}): {str(e)}")
            return False

    def _get_currency(self, currency_code):
        """Para birimini bul"""
        if not currency_code or pd.isna(currency_code):
            return self.env.company.currency_id
        
        currency = self.env['res.currency'].search([
            ('name', '=', str(currency_code).upper().strip())
        ], limit=1)
        
        return currency if currency else self.env.company.currency_id

    def _get_payment_term(self, payment_term_text):
        """Ödeme vadesini  bul"""
        if not payment_term_text or pd.isna(payment_term_text):
            return False
        
        PaymentTerm = self.env['account.payment.term']
        
        # İsme göre ara
        term = PaymentTerm.search([
            ('name', 'ilike', str(payment_term_text).strip())
        ], limit=1)
        
        return term if term else False

    def _get_uom(self, uom_text):
        """Ölçü birimini bul"""
        if not uom_text or pd.isna(uom_text):
            return self.env.ref('uom.product_uom_unit')
        
        uom_text_original = str(uom_text).strip()
        uom_text_upper = uom_text_original.upper()
        
        # Yaygın kısaltmaları Odoo XML ID'leriyle eşle (en güvenli yöntem)
        uom_xmlid_mapping = {
            'AD': 'uom.product_uom_unit',
            'ADET': 'uom.product_uom_unit',
            'UNITS': 'uom.product_uom_unit',
            'KG': 'uom.product_uom_kgm',  # Odoo'da 'kg' olarak tanımlı
            'KILOGRAM': 'uom.product_uom_kgm',
            'G': 'uom.product_uom_gram',
            'GRAM': 'uom.product_uom_gram',
            'T': 'uom.product_uom_ton',
            'TON': 'uom.product_uom_ton',
            'LT': 'uom.product_uom_litre',
            'L': 'uom.product_uom_litre',
            'LITRE': 'uom.product_uom_litre',
            'M': 'uom.product_uom_meter',
            'METRE': 'uom.product_uom_meter',
            'METER': 'uom.product_uom_meter',
            'CM': 'uom.product_uom_cm',
            'MM': 'uom.product_uom_millimeter',
            'KM': 'uom.product_uom_km',
        }
        
        # Önce XML ID mapping'den ara (en güvenli)
        xmlid = uom_xmlid_mapping.get(uom_text_upper)
        if xmlid:
            try:
                uom = self.env.ref(xmlid, raise_if_not_found=False)
                if uom:
                    _logger.debug(f"UOM bulundu (XML ID): '{uom_text_original}' -> '{uom.name}' (ID: {xmlid})")
                    return uom
            except Exception as e:
                _logger.warning(f"UOM XML ID hatası ({xmlid}): {str(e)}")
        
        # XML ID'den bulunamadı, isim araması yap
        Uom = self.env['uom.uom']
        
        # Önce tam eşleşme ara (hem büyük hem küçük harf)
        uom = Uom.search([
            '|',
            ('name', '=', uom_text_upper),
            ('name', '=', uom_text_original.lower())
        ], limit=1)
        
        if uom:
            _logger.debug(f"UOM bulundu (tam eşleşme): '{uom_text_original}' -> '{uom.name}'")
            return uom
        
        # Tam eşleşme yok, ilike ile ara
        uom = Uom.search([
            '|',
            ('name', 'ilike', uom_text_upper),
            ('name', 'ilike', uom_text_original)
        ], limit=1)
        
        if uom:
            _logger.debug(f"UOM bulundu (ilike): '{uom_text_original}' -> '{uom.name}'")
            return uom
        
        # Hala bulunamadıysa, UYARI ver ve varsayılan döndür
        _logger.warning(
            f"UOM bulunamadı: '{uom_text_original}' (büyük harf: '{uom_text_upper}') "
            f"- Varsayılan 'Units' (Adet) kullanılıyor. "
            f"Lütfen sistemde bu UOM'u oluşturun veya mapping'e ekleyin."
        )
        return self.env.ref('uom.product_uom_unit')

    def _parse_date(self, date_value):
        """Tarih değerini parse et"""
        if pd.isna(date_value):
            return fields.Date.today()
        
        if isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            except:
                return fields.Date.today()
        
        return date_value

    def _fix_incorrect_uoms_after_import(self, import_batch):
        """Import sonrası yanlış UOM'ları düzelt
        
        Bu fonksiyon, bu import batch'inde oluşturulan satırları kontrol eder
        ve Units (Adet) olarak kaydedilmiş ama ürünün varsayılan birimi farklı olanları düzeltir.
        """
        _logger.info(f"Import batch {import_batch} için UOM düzeltmesi başlatılıyor...")
        
        # Units (Adet) birimini bul
        units_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not units_uom:
            _logger.warning("Units UOM bulunamadı, UOM düzeltmesi atlanıyor")
            return None
        
        # Bu batch'te oluşturulan ve Units birimi olan satırları bul
        affected_lines = self.env['purchase.order.line'].search([
            ('order_id.is_historical_import', '=', True),
            ('order_id.import_batch', '=', import_batch),
            ('product_uom', '=', units_uom.id),
        ])
        
        stats = {
            'checked': len(affected_lines),
            'fixed': 0,
            'skipped': 0,
        }
        
        if not affected_lines:
            _logger.info("Düzeltilecek UOM bulunamadı")
            return stats
        
        _logger.info(f"{len(affected_lines)} satır kontrol ediliyor...")
        
        for line in affected_lines:
            try:
                # Ürünün varsayılan birimini al
                correct_uom = line.product_id.uom_id
                
                # Eğer ürünün varsayılan birimi Units değilse, düzelt
                if correct_uom and correct_uom != units_uom:
                    # Kategori uyumluluğunu kontrol et
                    if correct_uom.category_id != units_uom.category_id:
                        line.write({'product_uom': correct_uom.id})
                        stats['fixed'] += 1
                        
                        _logger.info(
                            f"UOM düzeltildi - PO: {line.order_id.name}, "
                            f"Ürün: {line.product_id.name}, "
                            f"Eski: {units_uom.name}, Yeni: {correct_uom.name}"
                        )
                    else:
                        stats['skipped'] += 1
                else:
                    stats['skipped'] += 1
                    
            except Exception as e:
                _logger.error(
                    f"UOM düzeltme hatası - Satır {line.id} (PO: {line.order_id.name}): {str(e)}",
                    exc_info=True
                )
                stats['skipped'] += 1
        
        _logger.info(
            f"UOM düzeltmesi tamamlandı - Kontrol edilen: {stats['checked']}, "
            f"Düzeltilen: {stats['fixed']}, Atlanan: {stats['skipped']}"
        )
        
        return stats

    def _show_import_result(self, stats):
        """Import sonucunu göster"""
        message = _(
            "İmport Tamamlandı!\n\n"
            "Toplam Satır: %d\n"
            "Oluşturulan PO: %d\n"
            "Güncellenen PO: %d\n"
            "Oluşturulan Satır: %d\n"
            "Atlanan: %d\n"
        ) % (
            stats['total'],
            stats['created_po'],
            stats['updated_po'],
            stats['created_lines'],
            stats['skipped']
        )
        
        # UOM düzeltme bilgisi ekle
        if stats.get('uom_checked'):
            message += _(
                "\nUOM Düzeltmesi:\n"
                "  - Kontrol Edilen: %d\n"
                "  - Düzeltilen: %d\n"
            ) % (
                stats['uom_checked'],
                stats.get('uom_fixed', 0)
            )
        
        if stats['errors']:
            message += _("\n\nHatalar (%d):\n") % len(stats['errors'])
            message += "\n".join(stats['errors'][:10])
            if len(stats['errors']) > 10:
                message += _("\n... ve %d hata daha") % (len(stats['errors']) - 10)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İmport Sonucu'),
                'message': message,
                'type': 'success' if not stats['errors'] else 'warning',
                'sticky': True,
            }
        }
