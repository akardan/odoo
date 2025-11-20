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
    error_log = fields.Html(string='Hata Detayları', readonly=True)
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('done', 'Tamamlandı'),
    ], default='draft')

    COLUMN_INDICES = {
        'erp_pr_id': 0,
        'sequence': 1,
        'processing_status': 2,
        'deletion_indicator': 3,
        'item_type': 4,
        'account_assignment_type': 5,
        'material_code': 6,
        'name': 7,
        'quantity': 8,
        'unit_of_measure': 9,
        'delivery_date_type': 10,
        'required_delivery_date': 11,
        'request_date': 12,
        'material_group': 13,
        'plant_code': 14,  # O kolonu - Üretim yeri (aynı zamanda şirket kodu için kullanılıyor)
        'storage_location': 15,
        'purchasing_group': 16,
        'requester': 17,
        'requirement_number': 18,
        'vendor_preferred': 19,
        'vendor_fixed': 20,
        'delivering_production_location': 21,
        'purchasing_organization': 22,
        'framework_agreement': 23,
        'purchasing_info_record': 24,
        'requester_comment': 25,
        'manufacturer_part_number': 26,
        'pr_count': 27,
        'po_number': 28,
        'approval_indicator': 29,
        'approval_date': 30,
        'erp_requester': 31,
    }
    
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
                    df = pd.DataFrame(data_rows[1:], columns=data_rows[0], dtype=str)
                elif len(data_rows) == 1:
                    df = pd.DataFrame(columns=data_rows[0], dtype=str)
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
        
        # Sabit kolon indeksleri
        column_map = self.COLUMN_INDICES
        _logger.info(f"Excel başlık satırı: {rows[0][:20]}")  # İlk 20 kolon
        _logger.info(f"Kolon indeksleri: {column_map}")
        
        # Debug bilgilerini text formatında error_details'e ekle
        error_details.append("\n=== DEBUG BİLGİLERİ ===\n")
        error_details.append(f"Excel başlık (ilk 10): {rows[0][:10]}\n")
        error_details.append(f"Bulunan kolonlar ({len(column_map)}): {', '.join(list(column_map.keys()))}\n")
        error_details.append(f"Toplam satır: {len(rows)-1}\n")
        error_details.append("\n--- İlk 3 Satırın Datası ---\n")
        
        # İlk 3 satırın verilerini debug için logla
        debug_row_count = 0

        for row_idx, row in enumerate(rows[1:], start=2):
            # İlk 3 satırı debug için logla
            if debug_row_count < 3:
                _logger.info(f"Satır {row_idx} verisi (ilk 20 kolon): {row[:20]}")
                debug_row_count += 1
            stats['lines']['processed'] += 1
            
            try:
                if not row or not any(str(cell).strip() for cell in row if cell):
                    stats['lines']['skipped'] += 1
                    continue

                sat_data = self._extract_sat_data(row, column_map)
                
                # İlk 3 satırın extract edilen datasını logla ve error_details'e ekle
                if row_idx <= 4:  # İlk 3 veri satırı (satır 2,3,4)
                    debug_msg = f"\nSatır {row_idx}:\n" \
                                f"  SAT: {sat_data.get('erp_pr_id')}\n" \
                                f"  İşleme Durumu: '{sat_data.get('processing_status')}'\n" \
                                f"  Malzeme: {sat_data.get('material_code')}\n" \
                                f"  Tanım: {sat_data.get('name')[:50] if sat_data.get('name') else 'N/A'}\n" \
                                f"  Talep Tarihi: {sat_data.get('request_date')}\n" \
                                f"  Teslim Tarihi: {sat_data.get('required_delivery_date')}\n"
                    _logger.info(f"Satır {row_idx}: SAT={sat_data.get('erp_pr_id')}, Status={sat_data.get('processing_status')}")
                    error_details.append(debug_msg)
                
                # SAT numarası kontrolü
                if not sat_data.get('erp_pr_id'):
                    stats['lines']['skipped'] += 1
                    if row_idx <= 10:  # İlk 10 satır için detay
                        error_details.append(f"⚠ Satır {row_idx}: SAT numarası eksik\n")
                    continue
                
                # İşleme durumu kontrolü - 'N' olanları işle
                processing_status = sat_data.get('processing_status', '')
                if processing_status != 'N':
                    stats['lines']['skipped'] += 1
                    if row_idx <= 10:  # İlk 10 satır için detay
                        error_details.append(f"✗ Satır {row_idx} - SAT {sat_data.get('erp_pr_id')}: İşleme durumu '{processing_status}' != 'N', atlandı\n")
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
            stats['error_log'] = ''.join(error_details[:100])  # İlk 100 hatayı göster
    

    def _extract_sat_data(self, row, column_map):
        """Satırdan SAT verilerini çıkar - sabit indeksleri kullanarak"""
        def safe_get(index, default=''):
            """Belirtilen indeksten field'ı al"""
            try:
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).replace('\x00', '').strip()
            except IndexError:
                _logger.warning(f"IndexError: Kolon indeksi {index} satırda bulunamadı. Varsayılan değer kullanılıyor.")
                return default
            except Exception as e:
                _logger.error(f"safe_get hata: Index {index}, Hata: {str(e)}")
                return default

        def safe_float(index, default=0.0):
            """Belirtilen indeksten float field'ı al"""
            try:
                value = row[index] if len(row) > index and row[index] is not None else None
                return float(value) if value else default
            except IndexError:
                _logger.warning(f"IndexError: Kolon indeksi {index} satırda bulunamadı. Varsayılan değer kullanılıyor.")
                return default
            except Exception as e:
                _logger.error(f"safe_float hata: Index {index}, Hata: {str(e)}")
                return default
                
        def safe_date(index, default=None):
            """Belirtilen indeksten date field'ı al"""
            try:
                value = row[index] if len(row) > index and row[index] is not None else None
                _logger.debug(f"safe_date: Index {index} için gelen değer: '{value}' (type: {type(value)})")
                if value is None or (isinstance(value, str) and not value.strip()):
                    _logger.debug(f"safe_date: Index {index} için değer boş veya sadece boşluk, varsayılan dönülüyor.")
                    return default
                if pd and pd.isna(value):
                    _logger.debug(f"safe_date: Index {index} için pd.isna(value) True, varsayılan dönülüyor.")
                    return default
                
                if isinstance(value, datetime):
                    _logger.debug(f"safe_date: Index {index} için datetime objesi, date'e çevriliyor: {value.date()}")
                    return value.date()
                elif isinstance(value, (int, float)):
                    try:
                        # Excel'in 1900-01-01'i 1 olarak kabul ettiği varsayımıyla
                        # Python'da 1900-01-01'den itibaren gün sayısını hesaplayalım.
                        # Excel'de 1900-01-01 = 1, Python'da datetime(1900,1,1).toordinal() = 730120
                        # Excel'den gelen sayıya 730119 ekleyerek Python ordinal değerini buluruz.
                        # Ancak Excel'in 1900-02-29 hatası nedeniyle, 60'tan büyük sayılar için 1 gün daha çıkarırız.
                        excel_date = float(value)
                        
                        # Sadece tam sayı kısmını al (saat/dakika bilgisini at)
                        excel_date = int(excel_date)
                        
                        if excel_date > 60: # 1900-03-01'den sonraki tarihler için
                            excel_date -= 1 # Excel'in 1900-02-29 hatasını düzelt
                        
                        # Excel'in başlangıç tarihi 1899-12-30'dur (0. gün)
                        parsed_date = datetime(1899, 12, 30) + timedelta(days=excel_date)
                        _logger.debug(f"safe_date: Index {index} için '{value}' (Excel float) değeri başarıyla parse edildi: {parsed_date.date()}")
                        return parsed_date.date()
                    except Exception as e:
                        _logger.warning(f"safe_date: Index {index} için '{value}' (Excel float) değeri parse edilemedi: {str(e)}")
                        return default
                elif isinstance(value, str):
                    value_str = value.strip()
                    for fmt in ['%Y%m%d', '%d.%m.%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d', '%Y-%m-%dT%H:%M:%S.%f']:
                        try:
                            parsed_date = datetime.strptime(value_str, fmt).date()
                            _logger.debug(f"safe_date: Index {index} için '{value}' değeri '{fmt}' formatıyla başarıyla parse edildi: {parsed_date}")
                            return parsed_date
                        except ValueError:
                            continue
                    _logger.warning(f"safe_date: Index {index} için '{value_str}' değeri hiçbir formatla parse edilemedi.")
                return default
                # Eğer buraya kadar gelindiyse, değer işlenememiştir.
                if value is not None:
                    _logger.warning(f"safe_date: Index {index} için '{value}' (type: {type(value)}) değeri işlenemedi.")
                return default
            except IndexError:
                _logger.warning(f"IndexError: Kolon indeksi {index} satırda bulunamadı. Varsayılan değer kullanılıyor.")
                return default
            except Exception as e:
                _logger.error(f"safe_date hata: Index {index}, Hata: {str(e)}")
                return default
        
        def safe_approval_indicator(index, default=''):
            """
            approval_indicator için özel fonksiyon
            SAP'den datetime gelebiliyor ama Selection field bekliyor ('X', 'Z', '2')
            """
            try:
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
            except IndexError:
                _logger.warning(f"IndexError: Kolon indeksi {index} satırda bulunamadı. Varsayılan değer kullanılıyor.")
                return default
            except Exception as e:
                _logger.error(f"safe_approval_indicator hata: Index {index}, Hata: {str(e)}")
                return default

        return {
            'erp_pr_id': safe_get(self.COLUMN_INDICES.get('erp_pr_id')),
            'sequence': safe_get(self.COLUMN_INDICES.get('sequence')),
            'processing_status': safe_get(self.COLUMN_INDICES.get('processing_status')),
            'deletion_indicator': safe_get(self.COLUMN_INDICES.get('deletion_indicator')),
            'item_type': safe_get(self.COLUMN_INDICES.get('item_type')),
            'account_assignment_type': safe_get(self.COLUMN_INDICES.get('account_assignment_type')),
            'material_code': safe_get(self.COLUMN_INDICES.get('material_code')),
            'name': safe_get(self.COLUMN_INDICES.get('name')),
            'quantity': safe_float(self.COLUMN_INDICES.get('quantity'), 0.0),
            'unit_of_measure': safe_get(self.COLUMN_INDICES.get('unit_of_measure')),
            'delivery_date_type': safe_get(self.COLUMN_INDICES.get('delivery_date_type')),
            'required_delivery_date': safe_date(self.COLUMN_INDICES.get('required_delivery_date')),
            'request_date': safe_date(self.COLUMN_INDICES.get('request_date')),
            'material_group': safe_get(self.COLUMN_INDICES.get('material_group')),
            'plant_code': safe_get(self.COLUMN_INDICES.get('plant_code')),
            'storage_location': safe_get(self.COLUMN_INDICES.get('storage_location')),
            'purchasing_group': safe_get(self.COLUMN_INDICES.get('purchasing_group')),
            'requester': safe_get(self.COLUMN_INDICES.get('requester')),
            'requirement_number': safe_get(self.COLUMN_INDICES.get('requirement_number')),
            'vendor_preferred': safe_get(self.COLUMN_INDICES.get('vendor_preferred')),
            'vendor_fixed': safe_get(self.COLUMN_INDICES.get('vendor_fixed')),
            'delivering_production_location': safe_get(self.COLUMN_INDICES.get('delivering_production_location')),
            'purchasing_organization': safe_get(self.COLUMN_INDICES.get('purchasing_organization')),
            'framework_agreement': safe_get(self.COLUMN_INDICES.get('framework_agreement')),
            'purchasing_info_record': safe_get(self.COLUMN_INDICES.get('purchasing_info_record')),
            'requester_comment': safe_get(self.COLUMN_INDICES.get('requester_comment')),
            'manufacturer_part_number': safe_get(self.COLUMN_INDICES.get('manufacturer_part_number')),
            'pr_count': safe_get(self.COLUMN_INDICES.get('pr_count')),
            'po_number': safe_get(self.COLUMN_INDICES.get('po_number')),
            'approval_indicator': safe_approval_indicator(self.COLUMN_INDICES.get('approval_indicator')),
            'approval_date': safe_date(self.COLUMN_INDICES.get('approval_date')),
            'erp_requester': safe_get(self.COLUMN_INDICES.get('erp_requester')),
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
        
        # Şirket kodunu belirle: company_code varsa onu kullan, yoksa plant_code'dan türet
        company_code = data.get('company_code')
        if not company_code and data.get('plant_code'):
            # SAP'de genellikle şirket kodu plant code'un ilk 4 karakteridir
            plant_code = str(data.get('plant_code'))
            company_code = plant_code[:4] if len(plant_code) >= 4 else plant_code
        
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
            'erp_company_code': company_code,
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
            'vendor_preferred': data.get('vendor_preferred'),
            'vendor_fixed': data.get('vendor_fixed'),
            'requester_comment': data.get('requester_comment'),
            'pr_count': data.get('pr_count'),
            'po_number': data.get('po_number'),
            'approval_date': data.get('approval_date'),
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