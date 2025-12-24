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
            'MALZEME_GRUBU': ['100', '100', '200'],
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
                    'SAP Malzeme Grubu',
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
                    'Evet',    # MALZEME_GRUBU
                    'Evet',    # MIKTAR
                    'Evet',    # BIRIM
                    'Evet',    # BIRIM_FIYAT
                    'Evet',    # PARA_BIRIMI
                    'Hayır',   # TOPLAM_TUTAR
                    'Evet',    # VADE
                    'Hayır',   # IHALE_TIPI
                    'Evet',    # SIRKET_KODU
                    'Evet',    # TESIS
                    'Evet',    # SATIN_ALMACI
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
            'MALZEME_ADI', 'MALZEME_GRUBU', 'MIKTAR', 'BIRIM',
            'BIRIM_FIYAT', 'PARA_BIRIMI', 'VADE', 'SIRKET_KODU',
            'TESIS', 'SATIN_ALMACI'
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
        
        for order_no, order_lines in grouped:
            try:
                self._process_order(order_no, order_lines, import_batch, stats)
            except Exception as e:
                error_msg = f"Sipariş {order_no}: {str(e)}"
                _logger.error(error_msg)
                stats['errors'].append(error_msg)
                stats['skipped'] += len(order_lines)
        
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
        
        # Para birimini bul
        currency = self._get_currency(first_line.get('PARA_BIRIMI', 'TRY'))
        
        # Ödeme vadesini bul
        payment_term = self._get_payment_term(first_line.get('VADE'))
        
        # Sipariş tarihini parse et
        order_date = self._parse_date(first_line.get('SIPARIS_TARIHI'))
        
        # PO oluştur veya güncelle
        po_vals = {
            'partner_id': partner.id,
            'date_order': order_date,
            'currency_id': currency.id,
            'is_historical_import': True,
            'import_batch': import_batch,
            'notes': first_line.get('NOTLAR', ''),
        }
        
        if payment_term:
            po_vals['payment_term_id'] = payment_term.id
        
        # İhale tipi
        tender_type = first_line.get('IHALE_TIPI', '').lower()
        if tender_type in ['direct', 'indirect', 'promotion', 'service']:
            po_vals['tender_type'] = tender_type
        
        if existing_po:
            existing_po.write(po_vals)
            purchase_order = existing_po
            stats['updated_po'] += 1
        else:
            po_vals['name'] = str(order_no)
            purchase_order = PurchaseOrder.create(po_vals)
            stats['created_po'] += 1
        
        # Satırları ekle
        for idx, line_data in order_lines.iterrows():
            self._create_order_line(purchase_order, line_data, stats)
        
        # Siparişi onayla (istenirse)
        if self.confirm_orders and purchase_order.state == 'draft':
            purchase_order.button_confirm()

    def _create_order_line(self, purchase_order, line_data, stats):
        """Sipariş satırı oluştur"""
        POLine = self.env['purchase.order.line']
        
        # Ürünü bul veya oluştur
        product = self._get_or_create_product(line_data)
        
        # Birim bul
        uom = self._get_uom(line_data.get('BIRIM', 'AD'))
        
        # Teslimat tarihini parse et
        date_planned = self._parse_date(line_data.get('TESLIMAT_TARIHI'))
        if not date_planned:
            date_planned = purchase_order.date_order
        
        line_vals = {
            'order_id': purchase_order.id,
            'product_id': product.id,
            'name': str(line_data.get('MALZEME_ADI', product.name)),
            'product_qty': float(line_data.get('MIKTAR', 1.0)),
            'product_uom': uom.id,
            'price_unit': float(line_data.get('BIRIM_FIYAT', 0.0)),
            'date_planned': date_planned,
        }
        
        POLine.create(line_vals)
        stats['created_lines'] += 1

    def _get_or_create_partner(self, line_data):
        """Tedarikçiyi bul veya oluştur"""
        Partner = self.env['res.partner']
        
        vendor_code = line_data.get('TEDARIKCI_KODU', '').strip()
        vendor_name = line_data.get('TEDARIKCI_ADI', '').strip()
        
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
            partner_vals = {
                'name': vendor_name,
                'ref': vendor_code if vendor_code else False,
                'supplier_rank': 1,
                'company_type': 'company',
            }
            return Partner.create(partner_vals)
        else:
            raise ValidationError(
                _('Tedarikçi bulunamadı: %s. Lütfen önce tedarikçiyi oluşturun veya "Yeni Tedarikçi Oluştur" seçeneğini işaretleyin.') % vendor_name
            )

    def _get_or_create_product(self, line_data):
        """Ürünü bul veya oluştur"""
        Product = self.env['product.product']
        
        product_code = line_data.get('MALZEME_KODU', '').strip()
        product_name = line_data.get('MALZEME_ADI', '').strip()
        
        if not product_name:
            raise ValidationError(_('Malzeme adı zorunludur'))
        
        # Önce koda göre ara
        if product_code:
            product = Product.search([('default_code', '=', product_code)], limit=1)
            if product:
                return product
        
        # İsme göre ara
        product = Product.search([('name', '=', product_name)], limit=1)
        if product:
            return product
        
        # Oluştur
        if self.create_products:
            product_vals = {
                'name': product_name,
                'default_code': product_code if product_code else False,
                'type': 'product',
                'purchase_ok': True,
            }
            return Product.create(product_vals)
        else:
            raise ValidationError(
                _('Ürün bulunamadı: %s. Lütfen önce ürünü oluşturun veya "Yeni Ürün Oluştur" seçeneğini işaretleyin.') % product_name
            )

    def _get_currency(self, currency_code):
        """Para birimini bul"""
        if not currency_code:
            return self.env.company.currency_id
        
        currency = self.env['res.currency'].search([
            ('name', '=', currency_code.upper())
        ], limit=1)
        
        return currency if currency else self.env.company.currency_id

    def _get_payment_term(self, payment_term_text):
        """Ödeme vadesini  bul"""
        if not payment_term_text:
            return False
        
        PaymentTerm = self.env['account.payment.term']
        
        # İsme göre ara
        term = PaymentTerm.search([
            ('name', 'ilike', payment_term_text)
        ], limit=1)
        
        return term if term else False

    def _get_uom(self, uom_text):
        """Ölçü birimini bul"""
        if not uom_text:
            return self.env.ref('uom.product_uom_unit')
        
        Uom = self.env['uom.uom']
        
        # Yaygın kısaltmaları eşle
        uom_mapping = {
            'AD': 'Units',
            'ADET': 'Units',
            'KG': 'kg',
            'LT': 'L',
            'LITRE': 'L',
            'M': 'm',
            'METRE': 'm',
        }
        
        search_name = uom_mapping.get(uom_text.upper(), uom_text)
        
        uom = Uom.search([
            '|', ('name', '=', search_name),
            ('name', 'ilike', uom_text)
        ], limit=1)
        
        return uom if uom else self.env.ref('uom.product_uom_unit')

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
