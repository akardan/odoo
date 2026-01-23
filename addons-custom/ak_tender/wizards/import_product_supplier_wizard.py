# -*- coding: utf-8 -*-

import base64
import io
import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    _logger.debug('Cannot import openpyxl')
    openpyxl = None

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot import xlrd')
    xlrd = None


class ProductSupplierImportWizard(models.TransientModel):
    _name = 'import.product.supplier.wizard'
    _description = 'Ürün ve Tedarikçi/Üretici İmport Wizard'

    excel_file = fields.Binary(string='Excel Dosyası', required=True)
    file_name = fields.Char(string='Dosya Adı')
    update_existing = fields.Boolean(string='Mevcut Kayıtları Güncelle', default=True)
    create_products = fields.Boolean(string='Ürünleri Oluştur', default=True,
                                     help='Ürün kayıtlarını oluştur/güncelle')
    create_partners = fields.Boolean(string='Partnerleri Oluştur', default=True,
                                     help='Tedarikçi ve üretici kayıtlarını oluştur/güncelle')
    create_supplier_info = fields.Boolean(string='Tedarikçi Bilgilerini Oluştur', default=True,
                                          help='Ürün-tedarikçi/üretici ilişkilerini oluştur')
    import_tag = fields.Char(
        string='İmport Etiketi',
        help='Oluşturulan kayıtları etiketlemek için kullanılır',
        default=lambda self: f"Onaylı_Tedarikçi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    def action_import_product_suppliers(self):
        """Excel'den ürün, tedarikçi ve üretici bilgilerini içe aktar"""
        self.ensure_one()
        
        if not self.excel_file:
            raise UserError(_('Lütfen bir Excel dosyası seçin.'))

        stats = self._init_stats()
        
        try:
            workbook = self._read_excel_file()
            
            # Önce partnerleri oluştur (hem tedarikçi hem üretici)
            partner_mapping = {}
            if self.create_partners:
                partner_mapping = self._process_partners(workbook, stats)
            
            # Sonra ürünleri oluştur
            product_mapping = {}
            if self.create_products:
                product_mapping = self._process_products(workbook, stats)
            
            # Son olarak ürün-tedarikçi/üretici ilişkilerini oluştur
            if self.create_supplier_info and product_mapping and partner_mapping:
                self._process_supplier_info(workbook, product_mapping, partner_mapping, stats)
            
            _logger.info(f"İmport istatistikleri: {stats}")
            
            return self._show_success_message(stats)
            
        except Exception as e:
            _logger.error(f"İmport hatası: {str(e)}", exc_info=True)
            raise UserError(f"İmport sırasında hata oluştu: {str(e)}")

    def _init_stats(self):
        """İstatistik dictionary'sini başlat"""
        return {
            'product': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'partner': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'supplier_info': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        }

    def _read_excel_file(self):
        """Excel dosyasını oku"""
        data = base64.b64decode(self.excel_file)
        file_extension = self.file_name.split('.')[-1].lower() if self.file_name else 'xlsx'
        
        try:
            if file_extension == 'xlsx' and openpyxl:
                return openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            elif file_extension == 'xls' and xlrd:
                return xlrd.open_workbook(file_contents=data)
            else:
                raise UserError(_('Desteklenmeyen dosya formatı. Lütfen .xlsx veya .xls dosyası yükleyin.'))
        except Exception as e:
            raise UserError(f"Excel dosyası okunamadı: {str(e)}")

    def _get_sheet_rows(self, workbook, sheet_name):
        """Belirtilen sayfadan satırları al"""
        if hasattr(workbook, 'sheetnames'):  # openpyxl
            _logger.info(f"Excel sayfaları: {workbook.sheetnames}")
            # İlk sayfayı kullan
            if workbook.sheetnames:
                first_sheet = workbook.sheetnames[0]
                _logger.info(f"İlk sayfa kullanılıyor: {first_sheet}")
                return list(workbook[first_sheet].iter_rows(values_only=True))
            return None
        else:  # xlrd
            sheet_names = workbook.sheet_names()
            _logger.info(f"Excel sayfaları: {sheet_names}")
            # İlk sayfayı kullan
            if sheet_names:
                first_sheet = sheet_names[0]
                _logger.info(f"İlk sayfa kullanılıyor: {first_sheet}")
                sheet = workbook.sheet_by_name(first_sheet)
                return [sheet.row_values(i) for i in range(sheet.nrows)]
            return None

    def _process_partners(self, workbook, stats):
        """Excel'den tedarikçi ve üreticileri işle"""
        rows = self._get_sheet_rows(workbook, 'Sheet1')
        
        if not rows:
            _logger.warning('Excel sayfası boş veya bulunamadı')
            return {}
            
        _logger.info(f"Toplam {len(rows)} satır okundu")
        
        if len(rows) <= 2:
            _logger.warning(f'Sadece {len(rows)} satır var, veri yok')
            return {}

        partner_mapping = {}
        
        # Satırları işle (ilk 2 satır başlık, 3. satırdan başla)
        for row_idx, row in enumerate(rows[2:], start=3):
            if not row or not any(str(cell).strip() for cell in row if cell):
                _logger.debug(f"Satır {row_idx} boş, atlanıyor")
                continue

            _logger.info(f"Satır {row_idx} işleniyor: {row[:8]}")  # İlk 8 sütunu logla
            
            try:
                # Tedarikçi bilgilerini işle
                supplier_data = self._extract_partner_data(row, 'supplier')
                _logger.info(f"Tedarikçi verisi: {supplier_data}")
                if supplier_data and supplier_data.get('ref'):
                    partner_id = self._create_update_partner(supplier_data, stats)
                    if partner_id:
                        partner_mapping[supplier_data['ref']] = partner_id
                
                # Üretici bilgilerini işle
                manufacturer_data = self._extract_partner_data(row, 'manufacturer')
                _logger.info(f"Üretici verisi: {manufacturer_data}")
                if manufacturer_data and manufacturer_data.get('ref'):
                    partner_id = self._create_update_partner(manufacturer_data, stats)
                    if partner_id:
                        partner_mapping[manufacturer_data['ref']] = partner_id
                        
            except Exception as e:
                _logger.error(f"Satır {row_idx} partner işleme hatası: {str(e)}")
                stats['partner']['errors'] += 1

        return partner_mapping

    def _extract_partner_data(self, row, partner_type):
        """Satırdan partner verilerini çıkar"""
        def safe_get(index, default=''):
            try:
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).strip() if value else default
            except:
                return default

        if partner_type == 'supplier':
            # Onaylı Tedarikçi No/Ad sütunları (sütun 4 ve 5)
            ref = safe_get(4)  # Tedarikçi No
            name = safe_get(4)  # Tedarikçi Ad (aynı sütunda)
            
            # Eğer format "kod-isim" şeklindeyse ayır
            if '-' in name:
                parts = name.split('-', 1)
                ref = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else name
            
            if not ref or not name:
                return None
                
            return {
                'ref': ref,
                'name': name,
                'partner_type': 'supplier'
            }
        else:  # manufacturer
            # Onaylı Üretici No/Ad sütunları (sütun 5 ve 6)
            ref = safe_get(5)  # Üretici No
            name = safe_get(5)  # Üretici Ad (aynı sütunda)
            
            # Eğer format "kod-isim" şeklindeyse ayır
            if '-' in name:
                parts = name.split('-', 1)
                ref = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else name
            
            if not ref or not name:
                return None
                
            return {
                'ref': ref,
                'name': name,
                'partner_type': 'manufacturer'
            }

    def _create_update_partner(self, data, stats):
        """Partner oluştur veya güncelle"""
        stats['partner']['processed'] += 1
        
        # Mevcut kayıt ara
        existing = self.env['res.partner'].search([
            ('ref', '=', data['ref']),
            ('is_company', '=', True)
        ], limit=1)

        vals = {
            'name': data['name'],
            'ref': data['ref'],
            'is_company': True,
            'supplier_rank': 1,
        }

        try:
            if existing:
                if self.update_existing:
                    existing.write(vals)
                    stats['partner']['updated'] += 1
                    return existing.id
                else:
                    stats['partner']['skipped'] += 1
                    return existing.id
            else:
                partner = self.env['res.partner'].create(vals)
                
                # Import tag'i ekle
                if self.import_tag:
                    self._add_tag_to_partner(partner, self.import_tag)
                
                stats['partner']['created'] += 1
                return partner.id
        except Exception as e:
            _logger.error(f"Partner işleme hatası: {str(e)}, Data: {data}")
            stats['partner']['errors'] += 1
            return False
    
    def _add_tag_to_partner(self, partner, tag_name):
        """Partner'a tag ekle"""
        try:
            # Tag'i bul veya oluştur
            tag = self.env['res.partner.category'].search([
                ('name', '=', tag_name)
            ], limit=1)
            
            if not tag:
                tag = self.env['res.partner.category'].create({
                    'name': tag_name
                })
            
            # Tag'i partner'a ekle
            partner.write({
                'category_id': [(4, tag.id)]
            })
        except Exception as e:
            _logger.error(f"Tag ekleme hatası: {str(e)}, Partner: {partner.name}, Tag: {tag_name}")

    def _process_products(self, workbook, stats):
        """Excel'den ürünleri işle"""
        rows = self._get_sheet_rows(workbook, 'Sheet1')
        
        if not rows or len(rows) <= 2:
            _logger.warning('Sheet1 sayfası boş veya bulunamadı')
            return {}

        product_mapping = {}
        
        # Satırları işle (ilk 2 satır başlık, 3. satırdan başla)
        for row_idx, row in enumerate(rows[2:], start=3):
            if not row or not any(str(cell).strip() for cell in row if cell):
                continue

            try:
                product_data = self._extract_product_data(row)
                
                if not product_data.get('default_code'):
                    stats['product']['skipped'] += 1
                    continue

                product_id = self._create_update_product(product_data, stats)
                if product_id:
                    product_mapping[product_data['default_code']] = product_id
                    
            except Exception as e:
                _logger.error(f"Satır {row_idx} ürün işleme hatası: {str(e)}")
                stats['product']['errors'] += 1

        return product_mapping

    def _extract_product_data(self, row):
        """Satırdan ürün verilerini çıkar"""
        def safe_get(index, default=''):
            try:
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).strip() if value else default
            except:
                return default

        return {
            'categ_name': safe_get(0),  # Malzeme Tipi
            'default_code': safe_get(1),  # Malzeme No
            'name': safe_get(2),  # Malzeme Adı
            'synonym_name': safe_get(3),  # Sinonim İsim
        }

    def _create_update_product(self, data, stats):
        """Ürün oluştur veya güncelle"""
        stats['product']['processed'] += 1
        
        # Ürün adı kontrolü
        if not data.get('name'):
            _logger.warning(f"Ürün adı yok, atlıyor: {data}")
            stats['product']['skipped'] += 1
            return False
        
        # Mevcut kayıt ara
        existing = self.env['product.product'].search([
            ('default_code', '=', data['default_code'])
        ], limit=1)

        # Kategori bul veya oluştur
        category_id = False
        if data.get('categ_name'):
            try:
                category = self.env['product.category'].search([
                    ('name', '=', data['categ_name'])
                ], limit=1)
                if not category:
                    category = self.env['product.category'].create({
                        'name': data['categ_name']
                    })
                category_id = category.id
            except Exception as e:
                _logger.error(f"Kategori oluşturma hatası: {str(e)}, Kategori: {data.get('categ_name')}")
                # Kategori hatası olsa bile devam et

        vals = {
            'name': data['name'],
            'type': 'consu',
            'purchase_ok': True,
        }
        
        # default_code sadece varsa ekle
        if data.get('default_code'):
            vals['default_code'] = data['default_code']
        
        if category_id:
            vals['categ_id'] = category_id
            
        # x_synonym_name alanını sadece model destekliyorsa ekle
        if data.get('synonym_name'):
            try:
                # Alan var mı kontrol et
                if 'x_synonym_name' in self.env['product.template']._fields:
                    vals['x_synonym_name'] = data['synonym_name']
                else:
                    _logger.warning("x_synonym_name alanı product.template modelinde bulunamadı")
            except Exception as e:
                _logger.warning(f"x_synonym_name alanı eklenirken hata: {str(e)}")

        try:
            if existing:
                if self.update_existing:
                    # default_code güncelleme sırasında çıkar (unique olabilir)
                    update_vals = vals.copy()
                    if 'default_code' in update_vals:
                        del update_vals['default_code']
                    existing.product_tmpl_id.write(update_vals)
                    stats['product']['updated'] += 1
                    return existing.product_tmpl_id.id
                else:
                    stats['product']['skipped'] += 1
                    return existing.product_tmpl_id.id
            else:
                product_tmpl = self.env['product.template'].create(vals)
                
                # Import tag'i ekle
                if self.import_tag:
                    self._add_tag_to_product(product_tmpl, self.import_tag)
                
                stats['product']['created'] += 1
                return product_tmpl.id
        except Exception as e:
            _logger.error(f"Ürün işleme hatası: {str(e)}, Data: {data}, Vals: {vals}")
            import traceback
            _logger.error(f"Traceback: {traceback.format_exc()}")
            stats['product']['errors'] += 1
            return False
    
    def _add_tag_to_product(self, product, tag_name):
        """Ürüne tag ekle"""
        try:
            # Tag'i bul veya oluştur (product.tag modeli kullanılıyor)
            ProductTag = self.env['product.tag']
            tag = ProductTag.search([
                ('name', '=', tag_name)
            ], limit=1)
            
            if not tag:
                tag = ProductTag.create({
                    'name': tag_name
                })
            
            # Tag'i ürüne ekle
            product.write({
                'product_tag_ids': [(4, tag.id)]
            })
        except Exception as e:
            _logger.error(f"Ürün tag ekleme hatası: {str(e)}, Ürün: {product.name}, Tag: {tag_name}")

    def _process_supplier_info(self, workbook, product_mapping, partner_mapping, stats):
        """Ürün-tedarikçi/üretici ilişkilerini işle"""
        rows = self._get_sheet_rows(workbook, 'Sheet1')
        
        if not rows or len(rows) <= 2:
            return

        # Satırları işle (ilk 2 satır başlık, 3. satırdan başla)
        for row_idx, row in enumerate(rows[2:], start=3):
            if not row or not any(str(cell).strip() for cell in row if cell):
                continue

            try:
                # Her satırda bir ürün için birden fazla tedarikçi/üretici olabilir
                self._create_supplier_info_records(row, product_mapping, partner_mapping, stats)
                    
            except Exception as e:
                _logger.error(f"Satır {row_idx} supplier info işleme hatası: {str(e)}")
                stats['supplier_info']['errors'] += 1

    def _create_supplier_info_records(self, row, product_mapping, partner_mapping, stats):
        """Bir satır için supplier info kayıtları oluştur"""
        def safe_get(index, default=''):
            try:
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).strip() if value else default
            except:
                return default

        product_code = safe_get(1)  # Malzeme No
        supplier_ref = safe_get(4)  # Tedarikçi No/Ad
        manufacturer_ref = safe_get(5)  # Üretici No/Ad
        is_approved = safe_get(7, 'A') == 'A'  # Onaylı sütunu
        
        # Ürün ID'sini al
        product_tmpl_id = product_mapping.get(product_code)
        if not product_tmpl_id:
            _logger.warning(f"Ürün bulunamadı: {product_code}")
            return

        # Tedarikçi kaydı oluştur
        if supplier_ref and '-' in supplier_ref:
            supplier_code = supplier_ref.split('-')[0].strip()
            supplier_name = supplier_ref.split('-', 1)[1].strip() if '-' in supplier_ref else supplier_ref
            partner_id = partner_mapping.get(supplier_code)
            
            if partner_id:
                self._create_update_supplier_info(
                    product_tmpl_id, partner_id, 'supplier',
                    supplier_code, supplier_name, is_approved, stats
                )

        # Üretici kaydı oluştur
        if manufacturer_ref and '-' in manufacturer_ref:
            manufacturer_code = manufacturer_ref.split('-')[0].strip()
            manufacturer_name = manufacturer_ref.split('-', 1)[1].strip() if '-' in manufacturer_ref else manufacturer_ref
            partner_id = partner_mapping.get(manufacturer_code)
            
            if partner_id:
                self._create_update_supplier_info(
                    product_tmpl_id, partner_id, 'manufacturer',
                    manufacturer_code, manufacturer_name, is_approved, stats
                )

    def _create_update_supplier_info(self, product_tmpl_id, partner_id, partner_type,
                                     product_code, product_name, is_approved, stats):
        """Supplier info kaydı oluştur veya güncelle"""
        stats['supplier_info']['processed'] += 1
        
        # Mevcut kayıt ara
        existing = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', product_tmpl_id),
            ('partner_id', '=', partner_id),
            ('partner_type', '=', partner_type)
        ], limit=1)

        vals = {
            'product_tmpl_id': product_tmpl_id,
            'partner_id': partner_id,
            'partner_type': partner_type,
            'product_code': product_code,
            'product_name': product_name,
            'is_approved': is_approved,
        }

        try:
            if existing:
                if self.update_existing:
                    existing.write(vals)
                    stats['supplier_info']['updated'] += 1
                else:
                    stats['supplier_info']['skipped'] += 1
            else:
                self.env['product.supplierinfo'].create(vals)
                stats['supplier_info']['created'] += 1
        except Exception as e:
            _logger.error(f"Supplier info işleme hatası: {str(e)}, Vals: {vals}")
            stats['supplier_info']['errors'] += 1

    def _show_success_message(self, stats):
        """Başarı mesajını göster"""
        message = (
            f"İmport Tamamlandı\n\n"
            f"Ürünler:\n"
            f"  İşlenen: {stats['product']['processed']}\n"
            f"  Oluşturulan: {stats['product']['created']}\n"
            f"  Güncellenen: {stats['product']['updated']}\n"
            f"  Atlanan: {stats['product']['skipped']}\n"
            f"  Hatalı: {stats['product']['errors']}\n\n"
            f"Partnerler (Tedarikçi/Üretici):\n"
            f"  İşlenen: {stats['partner']['processed']}\n"
            f"  Oluşturulan: {stats['partner']['created']}\n"
            f"  Güncellenen: {stats['partner']['updated']}\n"
            f"  Atlanan: {stats['partner']['skipped']}\n"
            f"  Hatalı: {stats['partner']['errors']}\n\n"
            f"Tedarikçi/Üretici Bilgileri:\n"
            f"  İşlenen: {stats['supplier_info']['processed']}\n"
            f"  Oluşturulan: {stats['supplier_info']['created']}\n"
            f"  Güncellenen: {stats['supplier_info']['updated']}\n"
            f"  Atlanan: {stats['supplier_info']['skipped']}\n"
            f"  Hatalı: {stats['supplier_info']['errors']}"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İmport Başarılı'),
                'message': message,
                'type': 'success',
                'sticky': True,
            }
        }
