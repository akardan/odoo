# -*- coding: utf-8 -*-

import base64
import io
import logging
import tempfile
import os
import zipfile
import xml.etree.ElementTree as ET
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None

def _install_pandas():
    global pd
    if pd:
        return True
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas', 'xlrd==1.2.0', 'openpyxl', 'lxml'])
        import pandas as pd
        return True
    except Exception as e:
        _logger.error(f"pandas kurulum hatası: {str(e)}")
        return False


class SatToPoolImportWizard(models.TransientModel):
    """SAT'ları Purchase Requisition Havuzuna Import Eden Wizard"""
    _name = 'import.sat.to.pool.wizard'
    _description = 'SAT Havuzu İmport Wizard'

    excel_file = fields.Binary(string='Excel Dosyası', required=True)
    file_name = fields.Char(string='Dosya Adı')
    sheet_name = fields.Char(string='Sayfa Adı', default='ILP(300)')
    update_existing = fields.Boolean(string='Mevcut Kayıtları Güncelle', default=True)
    error_log = fields.Text(string='Hata Detayları', readonly=True)
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('done', 'Tamamlandı'),
    ], default='draft')
    
    def action_import_to_pool(self):
        """Excel'den SAT'ları havuza aktar"""
        self.ensure_one()
        
        if not self.excel_file:
            raise UserError(_('Lütfen bir Excel dosyası seçin.'))

        stats = self._init_stats()
        
        try:
            # Excel dosyasını oku
            workbook = self._read_excel_file()
            
            # SAT verilerini işle
            self._process_sat_data(workbook, stats)
            
            # İşlem sonunda detaylı log
            _logger.info(f"İmport istatistikleri: {stats}")
            
            # Başarı mesajı oluştur
            message = _(
                'İmport tamamlandı!\n\n'
                'SAT Başlıkları:\n'
                '  - Oluşturulan: %s\n'
                '  - Güncellenen: %s\n\n'
                'SAT Kalemleri:\n'
                '  - İşlenen: %s\n'
                '  - Oluşturulan: %s\n'
                '  - Güncellenen: %s\n'
                '  - Atlanan: %s\n'
                '  - Hatalı: %s'
            ) % (
                stats['requisitions']['created'],
                stats['requisitions']['updated'],
                stats['lines']['processed'],
                stats['lines']['created'],
                stats['lines']['updated'],
                stats['lines']['skipped'],
                stats['lines']['errors']
            )
            
            if stats.get('error_log'):
                message += '\n\n' + _('Hata Detayları:\n%s') % stats['error_log']
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Başarılı'),
                    'message': message,
                    'sticky': True,
                    'type': 'success' if stats['lines']['errors'] == 0 else 'warning',
                }
            }
            
        except Exception as e:
            _logger.error(f"İmport hatası: {str(e)}", exc_info=True)
            import traceback
            error_detail = traceback.format_exc()
            _logger.error(f"Hata detayı: {error_detail}")
            self.write({
                'state': 'done',
                'error_log': f"FATAL ERROR:\n{str(e)}\n\n{error_detail}"
            })
            raise UserError(f"İmport sırasında hata oluştu: {str(e)}")

    def _init_stats(self):
        """İstatistik dictionary'sini başlat"""
        return {
            'requisitions': {'created': 0, 'updated': 0},
            'lines': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'error_log': ''
        }

    def _read_excel_file(self):
        """Excel dosyasını oku - xlsx, xls, XML Excel ve ZIP formatlarını destekler"""
        if not pd and not _install_pandas():
            raise UserError(_('pandas kütüphanesi gerekli'))
            
        data = base64.b64decode(self.excel_file)
        
        # ZIP dosya kontrolü
        if self._is_zip_file(data):
            _logger.info("ZIP dosyası tespit edildi, içindeki Excel dosyası çıkarılıyor")
            data = self._extract_excel_from_zip(data)
        
        # XML Excel formatı kontrol et
        data_start = data[:200].lower()
        is_xml = (b'<?xml' in data_start and 
                 (b'<workbook' in data_start or b'ss:workbook' in data_start or 
                  b'workbook' in data[:1000].lower()))
        
        if is_xml:
            _logger.info("XML Excel formatı tespit edildi")
            return self._read_xml_excel(data)
        
        # Normal Excel formatları (xlsx, xls)
        file_extension = self.file_name.split('.')[-1].lower() if self.file_name else 'xlsx'
        
        try:
            _logger.info(f"Excel dosyası pandas ile okunuyor: {file_extension}")
            
            # Önce otomatik engine ile dene
            try:
                return pd.read_excel(io.BytesIO(data), sheet_name=None)
            except Exception as auto_error:
                _logger.debug(f"Otomatik engine hatası: {auto_error}")
                
                # Manuel engine seçimi
                if file_extension == 'xls':
                    try:
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='xlrd')
                    except Exception:
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='openpyxl')
                else:
                    try:
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='openpyxl')
                    except Exception:
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='xlrd')
                        
        except Exception as e:
            raise UserError(f"Excel dosyası okunamadı. Hata: {str(e)}")
    
    def _read_xml_excel(self, data):
        """XML Excel formatını oku"""
        try:
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.xml') as temp_file:
                temp_file.write(data)
                temp_path = temp_file.name
            
            try:
                tree = ET.parse(temp_path)
                root = tree.getroot()
                
                ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
                
                worksheet = root.find('.//ss:Worksheet', ns)
                if worksheet is None:
                    worksheet = root.find('.//Worksheet')
                
                if worksheet is None:
                    raise UserError('XML dosyasında Worksheet bulunamadı')
                
                table = worksheet.find('.//ss:Table', ns)
                if table is None:
                    table = worksheet.find('.//Table')
                
                if table is None:
                    raise UserError('XML dosyasında Table bulunamadı')
                
                rows = table.findall('.//ss:Row', ns)
                if not rows:
                    rows = table.findall('.//Row')
                
                data_rows = []
                for row in rows:
                    row_data = []
                    cells = row.findall('.//ss:Cell', ns)
                    if not cells:
                        cells = row.findall('.//Cell')
                    
                    for cell in cells:
                        data_elem = cell.find('.//ss:Data', ns)
                        if data_elem is None:
                            data_elem = cell.find('.//Data')
                        
                        if data_elem is not None:
                            row_data.append(data_elem.text if data_elem.text else '')
                        else:
                            row_data.append('')
                    
                    if row_data:
                        data_rows.append(row_data)
                
                if len(data_rows) > 1:
                    df = pd.DataFrame(data_rows[1:], columns=data_rows[0])
                elif len(data_rows) == 1:
                    df = pd.DataFrame(columns=data_rows[0])
                else:
                    df = pd.DataFrame()
                
                sheet_name = worksheet.get('{urn:schemas-microsoft-com:office:spreadsheet}Name', 'Sheet1')
                if not sheet_name:
                    sheet_name = worksheet.get('Name', 'Sheet1')
                
                return {sheet_name: df}
                
            finally:
                os.unlink(temp_path)
                
        except ET.ParseError as e:
            raise UserError(f'XML parse hatası: {str(e)}')
        except Exception as e:
            raise UserError(f'XML Excel okunamadı: {str(e)}')
    
    def _is_zip_file(self, data):
        """Dosyanın ZIP olup olmadığını kontrol et"""
        return data.startswith(b'PK\x03\x04') or data.startswith(b'PK\x05\x06') or data.startswith(b'PK\x07\x08')
    
    def _extract_excel_from_zip(self, zip_data):
        """ZIP dosyasından Excel dosyasını çıkar"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                file_list = zip_file.namelist()
                _logger.info(f"ZIP içindeki dosyalar: {file_list}")
                
                excel_file = None
                for file_name in file_list:
                    if file_name.lower().endswith(('.xlsx', '.xls', '.xml')):
                        excel_file = file_name
                        break
                
                if not excel_file:
                    raise UserError(_('ZIP dosyasında Excel dosyası bulunamadı'))
                
                _logger.info(f"ZIP'den çıkarılan Excel dosyası: {excel_file}")
                
                with zip_file.open(excel_file) as excel_data:
                    return excel_data.read()
                    
        except zipfile.BadZipFile:
            raise UserError(_('Geçersiz ZIP dosyası'))
        except Exception as e:
            raise UserError(f'ZIP dosyası işlenemedi: {str(e)}')

    def _process_sat_data(self, workbook, stats):
        """ILP(300) sayfasından SAT verilerini işle"""
        sheet_name = self.sheet_name
        error_details = []
        
        _logger.info(f"Mevcut sayfalar: {list(workbook.keys())}")
        if sheet_name not in workbook:
            sheet_name = list(workbook.keys())[0]
            _logger.info(f"'{self.sheet_name}' bulunamadı, '{sheet_name}' sayfası kullanılıyor")
        
        df = workbook[sheet_name]
        if df.empty:
            raise UserError(_(f'{sheet_name} sayfası boş'))
        
        rows = [df.columns.tolist()] + df.values.tolist()
        
        # Kolon mapping'ini başlık satırından oluştur
        header_row = rows[0]
        column_map = self._build_column_map(header_row)
        _logger.info(f"Kolon mapping: {column_map}")

        for row_idx, row in enumerate(rows[1:], start=2):
            stats['lines']['processed'] += 1
            
            try:
                if not row or not any(str(cell).strip() for cell in row if cell):
                    stats['lines']['skipped'] += 1
                    continue

                sat_data = self._extract_sat_data(row, column_map)
                
                # SAT numarası kontrolü
                if not sat_data.get('erp_pr_id'):
                    stats['lines']['skipped'] += 1
                    error_details.append(f"Satır {row_idx}: SAT numarası eksik")
                    continue
                
                # İşleme durumu kontrolü - 'N' olanları işle
                if sat_data.get('processing_status') != 'N':
                    stats['lines']['skipped'] += 1
                    continue
                
                # Silme göstergesi kontrolü
                if sat_data.get('deletion_indicator') == 'X':
                    stats['lines']['skipped'] += 1
                    continue

                # Havuza ekle
                self._add_to_pool(sat_data, stats)
                
            except Exception as e:
                error_msg = f"Satır {row_idx} - SAT: {sat_data.get('erp_pr_id', 'N/A')}/{sat_data.get('erp_pr_item', 'N/A')}: {str(e)}"
                _logger.error(error_msg)
                error_details.append(error_msg)
                stats['lines']['errors'] += 1
        
        # Hata detaylarını kaydet
        if error_details:
            stats['error_log'] = '\n'.join(error_details[:100])  # İlk 100 hatayı göster
    
    def _build_column_map(self, header_row):
        """Başlık satırından kolon mapping'i oluştur"""
        # Türkçe ve İngilizce başlık eşleşmeleri
        column_patterns = {
            'erp_pr_id': ['SAT Numarası', 'SAT No', 'PR Number', 'Satınalma Talebi'],
            'sequence': ['Kalem', 'Kalem No', 'Item', 'Sıra'],
            'processing_status': ['İşleme Durumu', 'Durum', 'Status', 'Processing Status'],
            'deletion_indicator': ['Silme', 'Silme Göstergesi', 'Deletion', 'Del.Ind'],
            'item_type': ['Kalem Tipi', 'Item Type', 'Tip'],
            'account_assignment_type': ['Hesap Atama', 'Account Assignment', 'Acc.Assgmt'],
            'material_code': ['Malzeme', 'Malzeme Kodu', 'Material', 'Material Code'],
            'name': ['Malzeme Tanımı', 'Tanım', 'Description', 'Material Description', 'Kısa Metin'],
            'unit_of_measure': ['Ölçü Birimi', 'Birim', 'Unit', 'UoM'],
            'delivery_date_type': ['Teslimat Tarihi Tipi', 'Delivery Date Type'],
            'required_delivery_date': ['Teslimat Tarihi', 'Delivery Date', 'Talep Tarihi'],
            'material_group': ['Mal Grubu', 'Material Group', 'MG'],
            'approval_indicator': ['Onay', 'Onay Göstergesi', 'Approval', 'Approval Indicator'],
            'plant_code': ['Üretim Yeri', 'Tesis', 'Plant', 'Plant Code'],
            'purchasing_group': ['Satınalma Grubu', 'SA Grubu', 'Purchasing Group', 'Pur.Group'],
            'quantity': ['Miktar', 'Quantity', 'Qty'],
            'company_code': ['Şirket', 'Şirket Kodu', 'Company', 'Company Code'],
            'request_date': ['Talep Tarihi', 'Request Date', 'Oluşturma Tarihi'],
            'requester': ['Talep Eden', 'Requester', 'Oluşturan'],
            'requirement_number': ['Gereksinim No', 'Requirement', 'Req.No'],
            'delivering_production_location': ['Teslim Yeri', 'Delivery Location', 'Del.Location'],
            'purchasing_organization': ['Satınalma Organizasyonu', 'Pur.Org', 'Purchasing Org'],
            'framework_agreement': ['Çerçeve Anlaşma', 'Framework Agreement', 'Outline Agreement'],
            'purchasing_info_record': ['Satınalma Bilgi Kaydı', 'Info Record', 'Pur.Info Record'],
            'manufacturer_part_number': ['Üretici Parça No', 'Manufacturer Part', 'Mfr Part No'],
        }
        
        column_map = {}
        
        # Her başlık için index bul
        for idx, header in enumerate(header_row):
            if not header:
                continue
            
            header_str = str(header).strip()
            
            # Her field için pattern'leri kontrol et
            for field_name, patterns in column_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in header_str.lower():
                        column_map[field_name] = idx
                        _logger.info(f"Kolon bulundu: {field_name} = Index {idx} ({header_str})")
                        break
                if field_name in column_map:
                    break
        
        # Eksik kritik kolonları kontrol et
        required_fields = ['erp_pr_id', 'sequence', 'material_code', 'name']
        missing_fields = [f for f in required_fields if f not in column_map]
        if missing_fields:
            _logger.warning(f"Eksik kritik kolonlar: {missing_fields}")
        
        return column_map

    def _extract_sat_data(self, row, column_map):
        """Satırdan SAT verilerini çıkar - kolon mapping kullanarak"""
        def safe_get(field_name, default=''):
            """Kolon mapping'den field'ı al"""
            try:
                if field_name not in column_map:
                    return default
                index = column_map[field_name]
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).strip() if value else default
            except:
                return default

        def safe_float(field_name, default=0.0):
            """Kolon mapping'den float field'ı al"""
            try:
                if field_name not in column_map:
                    return default
                index = column_map[field_name]
                value = row[index] if len(row) > index and row[index] is not None else None
                return float(value) if value else default
            except:
                return default
                
        def safe_date(field_name, default=None):
            """Kolon mapping'den date field'ı al"""
            try:
                if field_name not in column_map:
                    return default
                index = column_map[field_name]
                value = row[index] if len(row) > index and row[index] is not None else None
                if not value:
                    return default
                
                if isinstance(value, datetime):
                    return value.date()
                elif isinstance(value, str):
                    for fmt in ['%Y%m%d', '%d.%m.%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(value, fmt).date()
                        except ValueError:
                            continue
                return default
            except:
                return default
        
        def safe_approval_indicator(field_name, default=''):
            """
            approval_indicator için özel fonksiyon
            SAP'den datetime gelebiliyor ama Selection field bekliyor ('X', 'Z', '2')
            """
            try:
                if field_name not in column_map:
                    return default
                index = column_map[field_name]
                value = row[index] if len(row) > index and row[index] is not None else None
                if not value:
                    return default
                
                # Datetime ise boş dön (Selection field datetime kabul etmez)
                if isinstance(value, datetime):
                    return default
                
                # String ise ve datetime formatında ise boş dön
                value_str = str(value).strip()
                if 'T' in value_str or '-' in value_str:  # datetime formatı
                    return default
                
                # Geçerli değerler: 'X', 'Z', '2'
                if value_str in ['X', 'Z', '2']:
                    return value_str
                
                return default
            except:
                return default

        return {
            'erp_pr_id': safe_get('erp_pr_id'),
            'sequence': safe_get('sequence'),
            'processing_status': safe_get('processing_status'),
            'deletion_indicator': safe_get('deletion_indicator'),
            'item_type': safe_get('item_type'),
            'account_assignment_type': safe_get('account_assignment_type'),
            'material_code': safe_get('material_code'),
            'name': safe_get('name'),
            'unit_of_measure': safe_get('unit_of_measure'),
            'delivery_date_type': safe_get('delivery_date_type'),
            'required_delivery_date': safe_date('required_delivery_date'),
            'material_group': safe_get('material_group'),
            'approval_indicator': safe_approval_indicator('approval_indicator'),
            'plant_code': safe_get('plant_code'),
            'purchasing_group': safe_get('purchasing_group'),
            'quantity': safe_float('quantity', 0.0),
            'company_code': safe_get('company_code'),
            'request_date': safe_date('request_date'),
            'requester': safe_get('requester'),
            'requirement_number': safe_get('requirement_number'),
            'delivering_production_location': safe_get('delivering_production_location'),
            'purchasing_organization': safe_get('purchasing_organization'),
            'framework_agreement': safe_get('framework_agreement'),
            'purchasing_info_record': safe_get('purchasing_info_record'),
            'manufacturer_part_number': safe_get('manufacturer_part_number'),
        }

    def _add_to_pool(self, data, stats):
        """SAT kalemini havuza ekle"""
        erp_pr_id = data.get('erp_pr_id')
        erp_pr_item = data.get('sequence')
        
        # Purchase requisition (SAT header) ara veya oluştur
        requisition = self.env['purchase.requisition'].search([
            ('erp_pr_id', '=', erp_pr_id)
        ], limit=1)
        
        if not requisition:
            _logger.info(f"Yeni SAT havuzu oluşturuluyor: {erp_pr_id}")
            requisition = self.env['purchase.requisition'].sudo().create({
                'erp_pr_id': erp_pr_id,
                'processing_status': 'N',
            })
            stats['requisitions']['created'] += 1
        
        # Purchase requisition line ara veya oluştur
        existing_line = self.env['purchase.requisition.line'].search([
            ('requisition_id', '=', requisition.id),
            ('erp_pr_item', '=', erp_pr_item)
        ], limit=1)
        
        try:
            # Ürünü bul veya oluştur
            product = self._find_or_create_product(data)
            
            if not product:
                _logger.error(f"Ürün bulunamadı: {data}")
                stats['lines']['errors'] += 1
                return False
            
            # Line values hazırla
            line_vals = self._prepare_line_vals(requisition, product, data)
            
            if existing_line:
                if self.update_existing:
                    existing_line.write(line_vals)
                    stats['lines']['updated'] += 1
                else:
                    stats['lines']['skipped'] += 1
            else:
                self.env['purchase.requisition.line'].sudo().create(line_vals)
                stats['lines']['created'] += 1
                
        except Exception as e:
            _logger.error(f"SAT kalemi işleme hatası: {str(e)}")
            stats['lines']['errors'] += 1
            return False

    def _prepare_line_vals(self, requisition, product, data):
        """Purchase requisition line values hazırla"""
        # Birim bul
        uom = product.uom_po_id or product.uom_id
        if data.get('unit_of_measure'):
            uom_name = data.get('unit_of_measure')
            uom_mapping = {
                'ADT': 'Adet',
                'KG': 'kg',
            }
            search_name = uom_mapping.get(uom_name, uom_name)
            found_uom = self.env['uom.uom'].search([('name', '=', search_name)], limit=1)
            if found_uom:
                uom = found_uom
        
        return {
            'requisition_id': requisition.id,
            'product_id': product.id,
            'product_qty': data.get('quantity') or 1.0,
            'product_uom_id': uom.id,
            'price_unit': 0.0,  # Havuzda fiyat yok
            
            # SAP alanları
            'erp_pr_item': data.get('sequence'),
            'line_processing_status': 'N',
            'deletion_indicator': data.get('deletion_indicator') == 'X',
            'item_type': data.get('item_type'),
            'account_assignment_type': data.get('account_assignment_type'),
            'material_code': data.get('material_code'),
            'material_group': data.get('material_group'),
            'purchasing_group': data.get('purchasing_group'),
            'erp_company_code': data.get('company_code'),
            'erp_plant_code': data.get('plant_code'),
            'erp_requester': data.get('requester'),
            'request_date': data.get('request_date'),
            'required_delivery_date': data.get('required_delivery_date'),
            'requirement_number': data.get('requirement_number'),
            'framework_agreement': data.get('framework_agreement'),
            'purchasing_info_record': data.get('purchasing_info_record'),
            'manufacturer_part_number': data.get('manufacturer_part_number'),
            'approval_indicator': data.get('approval_indicator'),
            'delivery_date_type': data.get('delivery_date_type'),
            'delivering_production_location': data.get('delivering_production_location'),
            'purchasing_organization': data.get('purchasing_organization'),
        }

    def _find_or_create_product(self, data):
        """Ürünü bul, yoksa oluştur"""
        material_code = data.get('material_code')
        material_name = data.get('name')
        
        if not material_code:
            material_code = self._generate_material_code()
            
        # Önce kod ile ara
        product = self.env['product.product'].search([
            ('default_code', '=', material_code)
        ], limit=1)
        
        if product:
            return product
        
        # İsim ile ara
        if material_name:
            product = self.env['product.product'].search([
                ('name', '=', material_name)
            ], limit=1)
            if product:
                return product
        
        # Yeni ürün oluştur
        try:
            product = self.env['product.product'].sudo().create({
                'name': material_name or f"Ürün {material_code}",
                'default_code': material_code,
                'type': 'consu',
                'purchase_ok': True,
                'sale_ok': False,
            })
            return product
        except Exception as e:
            _logger.error(f"Ürün oluşturma hatası: {str(e)}")
            return False

    def _generate_material_code(self):
        """Yeni malzeme kodu oluştur"""
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'product.material.code')
        ], limit=1)
        
        if not sequence:
            sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Malzeme Kodu',
                'code': 'product.material.code',
                'implementation': 'standard',
                'prefix': '',
                'padding': 9,
                'number_increment': 1,
                'number_next': 900000001,
            })
        
        return sequence.next_by_id()

    def _show_success_message(self, stats):
        """Başarı mesajı göster"""
        message = _(
            'İmport tamamlandı!\n\n'
            'SAT Başlıkları:\n'
            '  - Oluşturulan: %s\n'
            '  - Güncellenen: %s\n\n'
            'SAT Kalemleri:\n'
            '  - İşlenen: %s\n'
            '  - Oluşturulan: %s\n'
            '  - Güncellenen: %s\n'
            '  - Atlanan: %s\n'
            '  - Hatalı: %s'
        ) % (
            stats['requisitions']['created'],
            stats['requisitions']['updated'],
            stats['lines']['processed'],
            stats['lines']['created'],
            stats['lines']['updated'],
            stats['lines']['skipped'],
            stats['lines']['errors']
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Başarılı'),
                'message': message,
                'sticky': True,
                'type': 'success' if stats['lines']['errors'] == 0 else 'warning',
            }
        }