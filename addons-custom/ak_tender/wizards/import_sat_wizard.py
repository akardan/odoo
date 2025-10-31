# -*- coding: utf-8 -*-

import base64
import io
import logging
import tempfile
import os
import zipfile
import xml.etree.ElementTree as ET
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import msal
    import requests
except ImportError:
    msal = None
    requests = None

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

def _install_msal_and_requests():
    """Microsoft OAuth2 için gerekli kütüphaneleri yükle"""
    global msal, requests
    if msal and requests:
        return True
    import subprocess
    import sys
    try:
        _logger.info("msal ve requests kütüphaneleri yükleniyor...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'msal', 'requests'])
        import msal
        import requests
        _logger.info("msal ve requests başarıyla yüklendi")
        return True
    except Exception as e:
        _logger.error(f"msal/requests kurulum hatası: {str(e)}")
        return False


class SatImportWizard(models.TransientModel):
    _name = 'import.sat.wizard'
    _description = 'İhale Tanımı (SAT) İmport Wizard'

    excel_file = fields.Binary(string='Excel Dosyası', required=True)
    file_name = fields.Char(string='Dosya Adı')
    sheet_name = fields.Char(string='Sayfa Adı', default='ILP(300)')
    update_existing = fields.Boolean(string='Mevcut Kayıtları Güncelle', default=True)
    
    def action_import_sat(self):
        """Excel'den ihale tanımlarını (SAT) içe aktar"""
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
            _logger.info(f"Toplam işlenen: {stats['sat']['processed']}, "
                        f"Oluşturulan: {stats['sat']['created']}, "
                        f"Güncellenen: {stats['sat']['updated']}, "
                        f"Atlanan: {stats['sat']['skipped']}, "
                        f"Hatalı: {stats['sat']['errors']}")
            
            # Hata varsa uyarı göster
            if stats['sat']['errors'] > 0:
                _logger.error("Bazı kayıtlar hata aldı. Lütfen log dosyasını kontrol edin.")
            
            return self._show_success_message(stats)
            
        except Exception as e:
            _logger.error(f"İmport hatası: {str(e)}", exc_info=True)
            # Hata mesajını daha detaylı incele
            import traceback
            _logger.error(f"Hata detayı: {traceback.format_exc()}")
            raise UserError(f"İmport sırasında hata oluştu: {str(e)}")

    def _init_stats(self):
        """İstatistik dictionary'sini başlat"""
        return {
            'sat': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
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
        
        # XML Excel formatı kontrol et - daha kapsamlı kontrol
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
                    # XLS için xlrd engine
                    try:
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='xlrd')
                    except Exception as xlrd_error:
                        _logger.debug(f"xlrd engine hatası: {xlrd_error}")
                        # Son çare olarak openpyxl dene
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='openpyxl')
                else:
                    # XLSX için openpyxl engine
                    try:
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='openpyxl')
                    except Exception as openpyxl_error:
                        _logger.debug(f"openpyxl engine hatası: {openpyxl_error}")
                        # Son çare olarak xlrd dene
                        return pd.read_excel(io.BytesIO(data), sheet_name=None, engine='xlrd')
                        
        except Exception as e:
            raise UserError(f"Excel dosyası okunamadı. Desteklenen formatlar: .xlsx, .xls, XML Excel. Hata: {str(e)}")
    
    def _read_xml_excel(self, data):
        """XML Excel formatını oku"""
        
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.xml') as temp_file:
                temp_file.write(data)
                temp_path = temp_file.name
            
            try:
                tree = ET.parse(temp_path)
                root = tree.getroot()
                
                # Namespace tanımla
                ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
                
                # Worksheet bul
                worksheet = root.find('.//ss:Worksheet', ns)
                if worksheet is None:
                    # Namespace olmadan dene
                    worksheet = root.find('.//Worksheet')
                
                if worksheet is None:
                    raise UserError('XML dosyasında Worksheet bulunamadı')
                
                # Table bul
                table = worksheet.find('.//ss:Table', ns)
                if table is None:
                    table = worksheet.find('.//Table')
                
                if table is None:
                    raise UserError('XML dosyasında Table bulunamadı')
                
                rows = table.findall('.//ss:Row', ns)
                if not rows:
                    rows = table.findall('.//Row')
                
                # Veriyi oku
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
                    
                    if row_data:  # Boş satırları atlama
                        data_rows.append(row_data)
                
                # DataFrame oluştur
                if len(data_rows) > 1:
                    df = pd.DataFrame(data_rows[1:], columns=data_rows[0])
                elif len(data_rows) == 1:
                    df = pd.DataFrame(columns=data_rows[0])
                else:
                    df = pd.DataFrame()
                
                # Worksheet adını al
                sheet_name = worksheet.get('{urn:schemas-microsoft-com:office:spreadsheet}Name', 'Sheet1')
                if not sheet_name:
                    sheet_name = worksheet.get('Name', 'Sheet1')
                
                return {sheet_name: df}
                
            finally:
                # Geçici dosyayı sil
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
                # ZIP içindeki dosyaları listele
                file_list = zip_file.namelist()
                _logger.info(f"ZIP içindeki dosyalar: {file_list}")
                
                # Excel dosyası ara (.xlsx, .xls, .xml uzantılı)
                excel_file = None
                for file_name in file_list:
                    if file_name.lower().endswith(('.xlsx', '.xls', '.xml')):
                        excel_file = file_name
                        break
                
                if not excel_file:
                    raise UserError(_('ZIP dosyasında Excel dosyası bulunamadı'))
                
                _logger.info(f"ZIP'den çıkarılan Excel dosyası: {excel_file}")
                
                # Excel dosyasını çıkar
                with zip_file.open(excel_file) as excel_data:
                    return excel_data.read()
                    
        except zipfile.BadZipFile:
            raise UserError(_('Geçersiz ZIP dosyası'))
        except Exception as e:
            raise UserError(f'ZIP dosyası işlenemedi: {str(e)}')

    def _process_sat_data(self, workbook, stats):
        """ILP(300) sayfasından ihale tanımlarını işle"""
        # Sayfa kontrolü ve veri okuma
        sheet_name = self.sheet_name
        
        # pandas DataFrame dict
        _logger.info(f"Mevcut sayfalar: {list(workbook.keys())}")
        if sheet_name not in workbook:
            # İlk mevcut sayfayı kullan
            sheet_name = list(workbook.keys())[0]
            _logger.info(f"'{self.sheet_name}' bulunamadı, '{sheet_name}' sayfası kullanılıyor")
        
        df = workbook[sheet_name]
        if df.empty:
            raise UserError(_(f'{sheet_name} sayfası boş'))
        
        # DataFrame'i rows formatına çevir
        rows = [df.columns.tolist()] + df.values.tolist()

        # Veri satırlarını işle (başlık atla)
        for row_idx, row in enumerate(rows[1:], start=2):
            stats['sat']['processed'] += 1
            
            try:
                if not row or not any(str(cell).strip() for cell in row if cell):
                    stats['sat']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} boş, atlanıyor")
                    continue

                # Satırdan veri çıkar
                sat_data = self._extract_sat_data(row)
                
                # Detaylı log için tüm veriyi göster
                _logger.info(f"Satır {row_idx} verisi: {sat_data}")
                
                # SAT numarası kontrolü - boşsa atla
                if not sat_data.get('erp_pr_id'):
                    stats['sat']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} SAT numarası yok, atlanıyor: {sat_data}")
                    continue
                
                # İşleme durumu kontrolü - 'N' (işlenmedi) olanları işle
                if sat_data.get('processing_status') != 'N':
                    stats['sat']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} işleme durumu 'N' değil, atlanıyor: {sat_data}")
                    continue
                
                # Silme göstergesi kontrolü - 'X' (silindi) olanları atla
                #TODO: Silme işlemi için özel bir işlem gerekecek. İhale kaydını İptal statüsüne alacağız. şimdilik atla.
                if sat_data.get('deletion_indicator') == 'X':
                    stats['sat']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} silme göstergesi 'X', atlanıyor: {sat_data}")
                    continue
                
                # Tüm kontrolleri geçti, işleme devam et
                _logger.info(f"Satır {row_idx} işleniyor: SAT={sat_data.get('erp_pr_id')}, İşleme Durumu={sat_data.get('processing_status')}")

                # İhale oluştur veya güncelle
                self._create_update_tender(sat_data, stats)
                
            except Exception as e:
                _logger.error(f"Satır {row_idx} hatası: {str(e)}")
                stats['sat']['errors'] += 1

    def _extract_sat_data(self, row):
        """Satırdan SAT verilerini çıkar"""
        def safe_get(index, default=''):
            try:
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).strip() if value else default
            except:
                return default

        def safe_float(index, default=0.0):
            try:
                value = row[index] if len(row) > index and row[index] is not None else None
                return float(value) if value else default
            except:
                return default
                
        def safe_date(index, default=None):
            try:
                value = row[index] if len(row) > index and row[index] is not None else None
                if not value:
                    return default
                
                # Tarih formatını kontrol et ve dönüştür
                if isinstance(value, datetime):
                    return value.date()
                elif isinstance(value, str):
                    # Farklı tarih formatlarını dene
                    for fmt in ['%Y%m%d', '%d.%m.%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(value, fmt).date()
                        except ValueError:
                            continue
                return default
            except:
                return default

        # Excel sütunlarını Odoo alanlarına eşleştir
        # Kullanıcı geri bildirimine göre sütun eşleştirmelerini güncelliyoruz
        return {
            'erp_pr_id': safe_get(0),  # Satınalma talebi (SAT numarası)
            'sequence': safe_get(1),  # SAT kalemi
            'processing_status': safe_get(2),  # İşleme durumu (N işlenmedi, B SaS oluşturuldu, K Sözleşme oluşturuldu)
            'deletion_indicator': safe_get(3),  # Silme göstergesi (X silindi, boş işlem görmedi)
            'item_type': safe_get(4),  # Kalem tipi (0 Normal, 1 Sınır, 2 Konsinye, 3 Fason üretim)
            'account_assignment_type': safe_get(5),  # Hesap tayini tipi (K Masraf yeri, A Duran varlıklar, C Müşteri siparişi, F Sipariş)
            'material_code': safe_get(6),  # Malzeme kodu
            'name': safe_get(7),  # Kısa metin (malzeme adı)
            'unit_of_measure': safe_get(8),  # Ölçü birimi
            'delivery_date_type': safe_get(9),  # Teslimat tarihi tipi
            'required_delivery_date': safe_date(10),  # Teslimat tarihi
            'material_group': safe_get(11),  # Mal grubu
            'approval_indicator': safe_get(12),  # Onay göstergesi (X onay da, Z onay tamamlandı)
            'plant_code': safe_get(14),  # Depo yeri
            'purchasing_group': safe_get(15),  # Satınalma grubu
            'quantity': safe_float(16, 0.0),  # Talep miktarı
            'company_code': safe_get(17),  # Üretim yeri (İlko 2100, Merkez 2000, ilkopol 1100)
            'request_date': safe_date(18),  # Talep tarihi
            # İndeks 19: Yaratıldı (şu an kullanılmıyor)
            # İndeks 20: Talep eden (şu an kullanılmıyor)
            'requirement_number': safe_get(21),  # İhtiyaç numarası
            # İndeks 22: İstenen satıcı (şu an kullanılmıyor)
            # İndeks 23: Sabit satıcı (şu an kullanılmıyor)
            'delivering_production_location': safe_get(24),  # Teslimatı yapan ÜY
            'purchasing_organization': safe_get(25),  # SA organizasyonu
            'framework_agreement': safe_get(26),  # Çerçeve sözleşme
            # İndeks 27: Sözleşme kalemi (şu an kullanılmıyor)
            'purchasing_info_record': safe_get(28),  # SA bilgi kaydı
            'manufacturer_part_number': safe_get(29),  # Üretc.parça no.mlz.
            # İndeks 30: SAT sayısı (şu an kullanılmıyor)
            # İndeks 31: Satınalma siparişi (şu an kullanılmıyor)
        }

    def _create_update_tender(self, data, stats):
        """İhale oluştur veya güncelle"""
        # Mevcut ihale kaydını ara
        existing = self.env['ak.tender'].search([('erp_pr_id', '=', data['erp_pr_id'])], limit=1)
        
        if existing:
            _logger.info(f"Mevcut ihale bulundu: {existing.name} (ID: {existing.id})")
        else:
            _logger.info(f"İhale bulunamadı: {data.get('erp_pr_id')}")

        vals = self._prepare_tender_vals(data)

        try:
            if existing:
                if self.update_existing:
                    _logger.info(f"İhale güncelleniyor: {existing.name}")
                    existing.write(vals)
                    
                    # Önce ürünü bul veya oluştur
                    product = self._find_or_create_product(data)
                    
                    # Ürün bulunamadıysa veya oluşturulamadıysa hata ver
                    if not product:
                        _logger.error(f"Ürün bulunamadı veya oluşturulamadı: {data}")
                        stats['sat']['errors'] += 1
                        return existing.id
                    
                    # Mevcut ihale kalemini ara
                    existing_line = self.env['ak.tender.line'].search([
                        ('tender_id', '=', existing.id),
                        ('sequence', '=', int(data.get('sequence')) if data.get('sequence') and data.get('sequence').isdigit() else 10)
                    ], limit=1)
                    
                    if existing_line:
                        # Mevcut ihale kalemini güncelle
                        _logger.info(f"İhale kalemi güncelleniyor: {existing_line.name}")
                        existing_line.write({
                            'product_id': product.id,
                            'name': data.get('name') or product.name,
                            'quantity': data.get('quantity') or 1.0,
                            'required_delivery_date': data.get('required_delivery_date'),
                        })
                    else:
                        # Yeni ihale kalemi oluştur
                        _logger.info(f"Yeni ihale kalemi oluşturuluyor: {data.get('name')}")
                        self._create_tender_line(existing, data)
                    
                    stats['sat']['updated'] += 1
                    return existing.id
                else:
                    _logger.info(f"İhale güncelleme devre dışı, atlıyor: {existing.name}")
                    stats['sat']['skipped'] += 1
                    return existing.id
            else:
                _logger.info(f"Yeni ihale oluşturuluyor: {data.get('name')} (SAT: {data.get('erp_pr_id')})")
                try:
                    # İhale oluştur
                    tender = self.env['ak.tender'].sudo().create(vals)
                    
                    # İhale kalemi oluştur
                    self._create_tender_line(tender, data)
                    
                    stats['sat']['created'] += 1
                    return tender.id
                except Exception as e:
                    _logger.error(f"İhale oluşturma hatası: {str(e)}, Değerler: {vals}")
                    import traceback
                    _logger.error(f"Hata detayı: {traceback.format_exc()}")
                    stats['sat']['errors'] += 1
                    return False
        except Exception as e:
            _logger.error(f"İhale işleme hatası: {str(e)}, Data: {data}")
            stats['sat']['errors'] += 1
            return False

    def _prepare_tender_vals(self, data):
        """İhale için değerleri hazırla"""
        request_date = data.get('request_date')
        
        start_date = fields.Datetime.now()
        
        # Bitiş tarihi = Başlangıç tarihi + 1 hafta
        end_date = start_date + timedelta(days=7)
        
        vals = {
            'name': data.get('erp_pr_id').lstrip('0') if data.get('erp_pr_id') else False,  # İhale adı olarak SAT numarasını kullan, baştaki sıfırları at
            'erp_pr_id': data.get('erp_pr_id'),
            'erp_company_code': data.get('company_code'),
            'erp_plant_code': data.get('plant_code'),
            'required_delivery_date': data.get('required_delivery_date'),
            'request_date': request_date,  # Talep tarihi
            'start_date': start_date,  # Başlangıç tarihi
            'end_date': end_date,  # Bitiş tarihi (başlangıç + 1 hafta)
            'tender_type': 'direct',  # Varsayılan olarak direkt satın alma
        }
        
        # Model-based tender type determination
        # Use the tender.type.matrix model to determine tender type
        matrix_model = self.env['tender.type.matrix']
        
        material_group = data.get('material_group')
        purchasing_group = data.get('purchasing_group')
        production_location = data.get('production_location')
        
        # Determine tender type using the matrix model
        result = matrix_model.determine_tender_type(
            material_group=material_group,
            purchasing_group=purchasing_group,
            production_location=production_location
        )
        
        # Set tender type from result
        vals['tender_type'] = result.get('tender_type', 'indirect')
        
        # Log the decision for debugging
        _logger.info(
            "Tender type determined: %s (Source: %s) for SAT: %s, MG: %s, PG: %s, PL: %s",
            result.get('tender_type'),
            result.get('decision_source'),
            data.get('sat_number'),
            material_group,
            purchasing_group,
            production_location
        )
        
        # Add notes if available
        if result.get('notes'):
            notes = '\n'.join(result.get('notes', []))
            if vals.get('description'):
                vals['description'] += f"\n\n[Tender Type Decision]\n{notes}"
            else:
                vals['description'] = f"[Tender Type Decision]\n{notes}"
        
        return vals

    def _create_tender_line(self, tender, data):
        """İhale kalemi oluştur"""
        # Önce ürünü bul veya oluştur
        _logger.info(f"Ürün aranıyor veya oluşturuluyor: {data.get('material_code')} - {data.get('name')}")
        product = self._find_or_create_product(data)
        
        # Ürün bulunamadıysa veya oluşturulamadıysa hata ver
        if not product:
            _logger.error(f"Ürün bulunamadı veya oluşturulamadı: {data}")
            raise UserError(_(f"Ürün bulunamadı veya oluşturulamadı: {data.get('name')} (Kod: {data.get('material_code')})"))
        
        _logger.info(f"Ürün bulundu: {product.name} (ID: {product.id}, Kod: {product.default_code})")
        
        # Excel'den gelen sequence değerini kullan
        sequence = data.get('sequence')
        if sequence and sequence.isdigit():
            sequence = int(sequence)
        else:
            sequence = 10  # Varsayılan değer
        
        line_vals = {
            'tender_id': tender.id,
            'sequence': sequence,
            'display_type': 'product',
            'product_id': product.id,
            'name': data.get('name') or product.name,
            'quantity': data.get('quantity') or 1.0,
            'required_delivery_date': data.get('required_delivery_date'),
        }
        
        # Birim bilgisi varsa ekle
        if data.get('unit_of_measure'):
            uom_name = data.get('unit_of_measure')
            
            # Birim adı eşleştirmesi
            uom_mapping = {
                'ADT': 'Adet',  # ADT, Adet'in Türkçe kısaltmasıdır
                'KG': 'kg',     # Kilogram
            }
            
            # Eşleştirme varsa, eşleşen adı kullan
            search_name = uom_mapping.get(uom_name, uom_name)
            _logger.info(f"Birim aranıyor: {uom_name} -> {search_name}")
            
            # Önce eşleşen adla ara
            uom = self.env['uom.uom'].search([('name', '=', search_name)], limit=1)
            
            # Bulunamadıysa orijinal adla ara
            if not uom and search_name != uom_name:
                uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
            
            # Hala bulunamadıysa, varsayılan birim olarak 'Adet' birimini kullan
            if not uom:
                _logger.warning(f"Birim bulunamadı: {uom_name}, varsayılan birim kullanılıyor")
                uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
                if not uom:
                    uom = self.env['uom.uom'].search([('name', '=', 'Adet')], limit=1)
            
            if uom:
                line_vals['uom_id'] = uom.id
                _logger.info(f"Birim bulundu: {uom.name} (ID: {uom.id})")
            else:
                _logger.warning(f"Birim bulunamadı: {uom_name}")
        
        # İhale kalemi oluştur
        _logger.info(f"İhale kalemi oluşturuluyor: {line_vals}")
        tender_line = self.env['ak.tender.line'].sudo().create(line_vals)
        _logger.info(f"İhale kalemi oluşturuldu: {tender_line.name} (ID: {tender_line.id})")
        return tender_line

    def _generate_material_code(self):
        """Yeni malzeme kodu oluştur - Odoo sequence kullanarak"""
        
        # Sequence var mı kontrol et, yoksa oluştur
        sequence = self.env['ir.sequence'].search([
            ('code', '=', 'product.material.code')
        ], limit=1)
        
        if not sequence:
            _logger.info("Material code sequence oluşturuluyor")
            sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Malzeme Kodu',
                'code': 'product.material.code',
                'implementation': 'standard',
                'prefix': '',
                'padding': 9,  # 9 hane = 9xxxxxxxx
                'number_increment': 1,
                'number_next': 900000001,
            })
        
        # Yeni kod al
        new_code = sequence.next_by_id()
        _logger.info(f"Yeni malzeme kodu oluşturuldu: {new_code}")
        return new_code
    
    def _find_or_create_product(self, data):
        """Ürünü bul, yoksa oluştur"""
        product = False
        
        # Kullanıcı geri bildirimine göre:
        # G kolonu (indeks 6) "Malzeme" malzeme kodunu içeriyor (material_code alanında)
        # H kolonu (indeks 7) "Kısa metin" malzeme adına karşılık geliyor (name alanında)
        material_code = data.get('material_code')  # Malzeme kodu
        material_name = data.get('name')  # Malzeme adı
        
        _logger.info(f"Ürün aranıyor: Kod={material_code}, Ad={material_name}, Data={data}")
        
        # Malzeme kodu boşsa, yeni bir kod oluştur
        if not material_code:
            _logger.warning(f"Malzeme kodu boş, yeni kod oluşturuluyor")
            material_code = self._generate_material_code()
            _logger.info(f"Yeni malzeme kodu oluşturuldu: {material_code}")
            
        # Önce malzeme kodu ile ürün ara (default_code)
        product = self.env['product.product'].search([
            ('default_code', '=', material_code)
        ], limit=1)
        
        if product:
            _logger.info(f"Ürün kodu ile bulundu: {product.name} (ID: {product.id}, Kod: {product.default_code})")
        
        # Ürün bulunamadıysa ve malzeme adı varsa, isim ile ara
        if not product and material_name:
            product = self.env['product.product'].search([
                ('name', '=', material_name)
            ], limit=1)
            if product:
                _logger.info(f"Ürün adı ile bulundu: {product.name} (ID: {product.id}, Kod: {product.default_code})")
        
        # Ürün bulunamadıysa, yeni ürün oluştur
        if not product:
            _logger.info(f"Ürün bulunamadı, yeni ürün oluşturuluyor: Kod={material_code}, Ad={material_name}")
            
            # Tüm veri alanlarını kontrol et
            for key, value in data.items():
                _logger.info(f"Data alanı: {key}={value}")
            try:
                product_vals = {
                    'name': material_name or f"Ürün {material_code}",
                    'default_code': material_code,
                    'type': 'consu',  # 'product' değeri bu Odoo kurulumunda geçerli değil, 'consu' kullanıyoruz
                    'purchase_ok': True,
                    'sale_ok': False,
                }
                
                # Birim bilgisi varsa ekle
                uom_name = data.get('unit_of_measure')  # Ölçü birimi
                if uom_name:
                    # Birim adı eşleştirmesi
                    uom_mapping = {
                        'ADT': 'Adet',  # ADT, Adet'in Türkçe kısaltmasıdır
                        'KG': 'kg',     # Kilogram
                    }
                    
                    # Eşleştirme varsa, eşleşen adı kullan
                    search_name = uom_mapping.get(uom_name, uom_name)
                    _logger.info(f"Birim aranıyor: {uom_name} -> {search_name}")
                    
                    # Önce eşleşen adla ara
                    uom = self.env['uom.uom'].search([('name', '=', search_name)], limit=1)
                    
                    # Bulunamadıysa orijinal adla ara
                    if not uom and search_name != uom_name:
                        uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                    
                    # Hala bulunamadıysa, varsayılan birim olarak 'Adet' birimini kullan
                    if not uom:
                        _logger.warning(f"Birim bulunamadı: {uom_name}, varsayılan birim kullanılıyor")
                        uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
                        if not uom:
                            uom = self.env['uom.uom'].search([('name', '=', 'Adet')], limit=1)
                    
                    if uom:
                        product_vals['uom_id'] = uom.id
                        product_vals['uom_po_id'] = uom.id
                        _logger.info(f"Ürün birimi ayarlandı: {uom.name} (ID: {uom.id})")
                    else:
                        _logger.warning(f"Birim bulunamadı: {uom_name}")
                
                # Mal grubu varsa kategori bul veya oluştur
                material_group = data.get('material_group')
                if material_group:
                    category = self._find_or_create_category(material_group)
                    if category:
                        product_vals['categ_id'] = category.id
                    else:
                        _logger.warning(f"Kategori bulunamadı veya oluşturulamadı: {material_group}")
                
                # Ürün oluştur
                _logger.info(f"Ürün oluşturuluyor: {product_vals}")
                product = self.env['product.product'].sudo().create(product_vals)
                _logger.info(f"Yeni ürün oluşturuldu: {product.name} (ID: {product.id}, Kod: {product.default_code})")
            except Exception as e:
                _logger.error(f"Ürün oluşturma hatası: {str(e)}")
                import traceback
                _logger.error(f"Hata detayı: {traceback.format_exc()}")
                # Ürün oluşturulamadıysa None döndür
                return None
        
        return product

    def _find_or_create_category(self, material_group):
        """Mal grubuna göre kategori bul veya oluştur"""
        # Mal grubu formatını kontrol et
        if not material_group or not isinstance(material_group, str):
            _logger.warning(f"Geçersiz mal grubu: {material_group}")
            return None
        
        # Mal grubu kodunu temizle
        material_group = material_group.strip()
        _logger.info(f"Kategori aranıyor: {material_group}")
        
        # Kategori ara
        category = self.env['product.category'].search([
            ('name', '=', material_group)
        ], limit=1)
        
        if category:
            _logger.info(f"Kategori bulundu: {category.name} (ID: {category.id})")
        
        # Kategori bulunamadıysa oluştur
        if not category:
            _logger.info(f"Kategori bulunamadı, yeni kategori oluşturuluyor: {material_group}")
            try:
                parent_category = self.env.ref('product.product_category_all')
                _logger.info(f"Üst kategori: {parent_category.name} (ID: {parent_category.id})")
                
                category = self.env['product.category'].sudo().create({
                    'name': material_group,
                    'parent_id': parent_category.id,
                })
                _logger.info(f"Yeni kategori oluşturuldu: {category.name} (ID: {category.id})")
            except Exception as e:
                _logger.error(f"Kategori oluşturma hatası: {str(e)}")
                import traceback
                _logger.error(f"Hata detayı: {traceback.format_exc()}")
                return None
        
        return category

    def _show_success_message(self, stats):
        """Başarı mesajı göster"""
        message = _(
            "İmport tamamlandı.\n"
            "Toplam işlenen: {processed}\n"
            "Oluşturulan: {created}\n"
            "Güncellenen: {updated}\n"
            "Atlanan: {skipped}\n"
            "Hatalı: {errors}"
        ).format(
            processed=stats['sat']['processed'],
            created=stats['sat']['created'],
            updated=stats['sat']['updated'],
            skipped=stats['sat']['skipped'],
            errors=stats['sat']['errors']
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İhale Tanımı (SAT) İmport'),
                'message': message,
                'sticky': True,
                'type': 'success' if stats['sat']['errors'] == 0 else 'warning',
            }
        }

    def _get_microsoft_access_token(self):
        """
        Microsoft Graph API için OAuth2 access token al
        
        Microsoft Entra (Azure AD) üzerinden OAuth2 authentication kullanarak
        access token alır. Basic authentication yerine modern OAuth2 kullanır.
        """
        if not msal and not _install_msal_and_requests():
            raise UserError(_('msal kütüphanesi yüklenemedi. Lütfen manuel olarak "pip install msal requests" komutunu çalıştırın.'))
        
        # Azure AD credentials - System parameters'dan al
        client_id = self.env['ir.config_parameter'].sudo().get_param('ak_tender.azure_client_id', '')
        client_secret = self.env['ir.config_parameter'].sudo().get_param('ak_tender.azure_client_secret', '')
        tenant_id = self.env['ir.config_parameter'].sudo().get_param('ak_tender.azure_tenant_id', '')
        
        if not all([client_id, client_secret, tenant_id]):
            raise UserError(_(
                'Azure AD credentials eksik. Lütfen aşağıdaki system parameters\'ı ayarlayın:\n'
                '- ak_tender.azure_client_id\n'
                '- ak_tender.azure_client_secret\n'
                '- ak_tender.azure_tenant_id'
            ))
        
        _logger.info(f"Microsoft OAuth2 token alınıyor - Tenant: {tenant_id}")
        
        # MSAL authority URL
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        # Scopes - Microsoft Graph API için
        scopes = ["https://graph.microsoft.com/.default"]
        
        try:
            # Confidential client application oluştur
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )
            
            # Access token al (client credentials flow)
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                _logger.info("Microsoft OAuth2 token başarıyla alındı")
                return result["access_token"]
            else:
                error_msg = result.get("error_description", result.get("error", "Bilinmeyen hata"))
                _logger.error(f"Token alınamadı: {error_msg}")
                raise UserError(_(f"Microsoft OAuth2 token alınamadı: {error_msg}"))
                
        except Exception as e:
            _logger.error(f"OAuth2 token alma hatası: {str(e)}", exc_info=True)
            raise UserError(_(f"OAuth2 authentication hatası: {str(e)}"))

    @api.model
    def import_sat_from_email(self):
        """
        Email kutusundan SAT dosyalarını oku ve import et
        
        Microsoft Graph API ve OAuth2 kullanarak ilkoisdata@ilko.com.tr
        email kutusunu kontrol eder ve "ME5A Günlük Rapor Sonuçları" konulu
        yeni gelen mailleri bulur. Ekindeki "ME5A Günlük Rapor Sonuçları.ZIP"
        isimli dosyayı alır ve import işlemine devam eder.
        
        NOT: Microsoft'un "Improving Security" kapsamında Basic Authentication
        devre dışı bırakılmıştır. Bu nedenle OAuth2 kullanılması zorunludur.
        """
        if not (msal and requests) and not _install_msal_and_requests():
            raise UserError(_('msal ve requests kütüphaneleri yüklenemedi. Lütfen manuel olarak "pip install msal requests" komutunu çalıştırın.'))
        
        stats = {'sat': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}}
        processed_emails = 0
        
        try:
            # OAuth2 access token al
            access_token = self._get_microsoft_access_token()
            
            # Email kullanıcısı
            email_user = self.env['ir.config_parameter'].sudo().get_param(
                'ak_tender.email_user',
                'ilkoisdata@ilko.com.tr'
            )
            
            _logger.info(f"Microsoft Graph API ile email okunuyor: {email_user}")
            
            # Microsoft Graph API endpoint
            graph_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages"
            
            # Headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Okunmamış ve "ME5A Günlük Rapor Sonuçları" konulu emailleri ara
            # $filter: OData query syntax kullanarak filtreleme
            # isRead eq false: okunmamış emailler
            # contains(subject, '...'): konu içeren emailler
            params = {
                '$filter': "isRead eq false and contains(subject, 'ME5A Günlük Rapor Sonuçları')",
                '$select': 'id,subject,from,receivedDateTime,hasAttachments',
                '$orderby': 'receivedDateTime desc',
                '$top': 50  # Son 50 email
            }
            
            _logger.info("Okunmamış emailler aranıyor...")
            response = requests.get(graph_url, headers=headers, params=params)
            
            if response.status_code != 200:
                _logger.error(f"Email listesi alınamadı: {response.status_code} - {response.text}")
                raise UserError(_(f"Email listesi alınamadı: {response.status_code}"))
            
            messages = response.json().get('value', [])
            _logger.info(f"{len(messages)} adet okunmamış 'ME5A Günlük Rapor Sonuçları' konulu email bulundu")
            
            if not messages:
                _logger.info("İşlenecek yeni email bulunamadı")
                return stats
            
            # Her bir emaili işle
            for message in messages:
                try:
                    message_id = message.get('id')
                    subject = message.get('subject', '')
                    from_addr = message.get('from', {}).get('emailAddress', {}).get('address', '')
                    received_date = message.get('receivedDateTime', '')
                    has_attachments = message.get('hasAttachments', False)
                    
                    _logger.info(f"Email işleniyor: ID={message_id}")
                    _logger.info(f"Konu: {subject}")
                    _logger.info(f"Gönderen: {from_addr}")
                    _logger.info(f"Tarih: {received_date}")
                    
                    if not has_attachments:
                        _logger.warning(f"Email'de ek yok: ID={message_id}")
                        # Okundu olarak işaretle
                        self._mark_email_as_read(email_user, message_id, access_token)
                        continue
                    
                    # Ekleri al
                    attachments_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages/{message_id}/attachments"
                    attachments_response = requests.get(attachments_url, headers=headers)
                    
                    if attachments_response.status_code != 200:
                        _logger.error(f"Ekler alınamadı: {attachments_response.status_code}")
                        continue
                    
                    attachments = attachments_response.json().get('value', [])
                    _logger.info(f"{len(attachments)} adet ek bulundu")
                    
                    # Ekleri kontrol et
                    attachment_found = False
                    for attachment in attachments:
                        filename = attachment.get('name', '')
                        _logger.info(f"Ek dosya: {filename}")
                        
                        # "ME5A Günlük Rapor Sonuçları.ZIP" dosyasını ara
                        # Büyük/küçük harf duyarsız karşılaştırma
                        if filename.lower() == 'me5a günlük rapor sonuçları.zip':
                            _logger.info(f"Hedef ZIP dosyası bulundu: {filename}")
                            attachment_found = True
                            
                            # Dosya içeriğini al (base64 encoded)
                            content_bytes = attachment.get('contentBytes', '')
                            
                            if not content_bytes:
                                _logger.error(f"Dosya içeriği alınamadı: {filename}")
                                continue
                            
                            # Base64 decode
                            file_data = base64.b64decode(content_bytes)
                            _logger.info(f"Dosya boyutu: {len(file_data)} bytes")
                            
                            # Import et
                            _logger.info(f"Import işlemi başlatılıyor: {filename}")
                            file_stats = self.import_sat_from_file(
                                file_data=file_data,
                                file_name=filename,
                                sheet_name='ILP(300)',
                                update_existing=True
                            )
                            
                            # İstatistikleri birleştir
                            for key in stats['sat']:
                                stats['sat'][key] += file_stats['sat'][key]
                            
                            _logger.info(f"Dosya import edildi: {filename}, İstatistikler: {file_stats}")
                            
                            # Emaili okundu olarak işaretle
                            self._mark_email_as_read(email_user, message_id, access_token)
                            
                            processed_emails += 1
                            break  # Bu emaildeki diğer ekleri kontrol etmeye gerek yok
                    
                    if not attachment_found:
                        _logger.warning(f"Email'de 'ME5A Günlük Rapor Sonuçları.ZIP' dosyası bulunamadı: ID={message_id}")
                        # Yine de okundu olarak işaretle ki bir daha işlenmesin
                        self._mark_email_as_read(email_user, message_id, access_token)
                                
                except Exception as e:
                    _logger.error(f"Email işleme hatası: ID={message.get('id', 'unknown')}, Hata: {str(e)}", exc_info=True)
                    stats['sat']['errors'] += 1
            
            _logger.info(f"Email import tamamlandı. İşlenen email sayısı: {processed_emails}, İstatistikler: {stats}")
            return stats
            
        except Exception as e:
            _logger.error(f"Email import hatası: {str(e)}", exc_info=True)
            raise UserError(_(f"Email import hatası: {str(e)}"))
    
    def _mark_email_as_read(self, email_user, message_id, access_token):
        """Email'i okundu olarak işaretle"""
        try:
            update_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages/{message_id}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            data = {
                'isRead': True
            }
            
            response = requests.patch(update_url, headers=headers, json=data)
            
            if response.status_code == 200:
                _logger.info(f"Email okundu olarak işaretlendi: ID={message_id}")
            else:
                _logger.warning(f"Email okundu olarak işaretlenemedi: {response.status_code} - {response.text}")
                
        except Exception as e:
            _logger.error(f"Email işaretleme hatası: {str(e)}", exc_info=True)

    # Reusable function for automated jobs
    @api.model
    def import_sat_from_file(self, file_data, file_name, sheet_name='ILP(300)', update_existing=True):
        """
        Automated import function for SAT data from Excel file
        
        Args:
            file_data (bytes): The binary content of the Excel file
            file_name (str): The name of the file
            sheet_name (str): The name of the sheet to import from
            update_existing (bool): Whether to update existing records
            
        Returns:
            dict: Statistics about the import process
        """
        stats = {
            'sat': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        }
        
        try:
            # Create a temporary wizard record
            wizard = self.create({
                'excel_file': base64.b64encode(file_data),
                'file_name': file_name,
                'sheet_name': sheet_name,
                'update_existing': update_existing,
            })
            
            # Read the Excel file
            workbook = wizard._read_excel_file()
            
            # Process the SAT data
            wizard._process_sat_data(workbook, stats)
            
            # Log the results
            _logger.info(f"Automated import statistics: {stats}")
            
            return stats
        except Exception as e:
            _logger.error(f"Automated import error: {str(e)}", exc_info=True)
            return stats