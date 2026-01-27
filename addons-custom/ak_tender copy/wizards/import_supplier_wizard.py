# -*- coding: utf-8 -*-

import base64
import io
import logging
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


class SupplierImportWizard(models.TransientModel):
    _name = 'import.supplier.wizard'
    _description = 'Tedarikçi İmport Wizard'

    excel_file = fields.Binary(string='Excel Dosyası', required=True)
    file_name = fields.Char(string='Dosya Adı')
    import_mode = fields.Selection([
        ('basic', 'Temel Bilgiler'),
        ('detailed', 'Detaylı İmport')
    ], string='İmport Modu', default='basic', required=True)
    update_existing = fields.Boolean(string='Mevcut Kayıtları Güncelle', default=True)

    def action_import_suppliers(self):
        """Excel'den tedarikçileri içe aktar"""
        self.ensure_one()
        
        if not self.excel_file:
            raise UserError(_('Lütfen bir Excel dosyası seçin.'))

        stats = self._init_stats()
        
        try:
            workbook = self._read_excel_file()
            supplier_mapping = self._process_suppliers(workbook, stats)
            
            # Tedarikçi işlemede hata varsa, banka ve e-posta işlemeyi atla
            if stats['supplier']['errors'] == 0:
                # E-posta işleme her zaman yapılsın
                self._process_emails(workbook, supplier_mapping, stats)
                
                # Banka hesapları sadece detaylı modda işlensin
                if self.import_mode == 'detailed':
                    self._process_bank_accounts(workbook, supplier_mapping, stats)
            else:
                _logger.warning(f"Tedarikçi işlemede {stats['supplier']['errors']} hata var, banka ve e-posta işleme atlanıyor.")
            
            # İşlem sonunda detaylı log
            _logger.info(f"İmport istatistikleri: {stats}")
            _logger.info(f"Toplam işlenen: {stats['supplier']['processed']}, "
                        f"Oluşturulan: {stats['supplier']['created']}, "
                        f"Güncellenen: {stats['supplier']['updated']}, "
                        f"Atlanan: {stats['supplier']['skipped']}, "
                        f"Hatalı: {stats['supplier']['errors']}")
            
            # Hata varsa uyarı göster
            if stats['supplier']['errors'] > 0:
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
            'supplier': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'bank': {'processed': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0},
            'email': {'processed': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
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
                raise UserError(_('Desteklenmeyen dosya formatı'))
        except Exception as e:
            raise UserError(f"Excel dosyası okunamadı: {str(e)}")

    def _process_suppliers(self, workbook, stats):
        """SATICIANAVERI sayfasından tedarikçileri işle"""
        supplier_mapping = {}
        
        # Sayfa kontrolü ve veri okuma
        if hasattr(workbook, 'sheetnames'):  # openpyxl
            if 'SATICIANAVERI' not in workbook.sheetnames:
                raise UserError(_('SATICIANAVERI sayfası bulunamadı'))
            rows = list(workbook['SATICIANAVERI'].iter_rows(values_only=True))
        else:  # xlrd
            if 'SATICIANAVERI' not in workbook.sheet_names():
                raise UserError(_('SATICIANAVERI sayfası bulunamadı'))
            sheet = workbook.sheet_by_name('SATICIANAVERI')
            rows = [sheet.row_values(i) for i in range(sheet.nrows)]

        if len(rows) <= 1:
            raise UserError(_('SATICIANAVERI sayfası boş'))

        # Veri satırlarını işle (başlık atla)
        for row_idx, row in enumerate(rows[1:], start=2):
            stats['supplier']['processed'] += 1
            
            try:
                if not row or not any(str(cell).strip() for cell in row if cell):
                    stats['supplier']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} boş, atlanıyor")
                    continue

                supplier_data = self._extract_supplier_data(row)
                
                if not supplier_data.get('name'):
                    stats['supplier']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} isim yok, atlanıyor: {supplier_data}")
                    continue
                
                # Satıcı alanı (code) kontrolü - boşsa atla
                if not supplier_data.get('code'):
                    stats['supplier']['skipped'] += 1
                    _logger.info(f"Satır {row_idx} Satıcı kodu yok, atlanıyor: {supplier_data}")
                    continue

                partner_id = self._create_update_supplier(supplier_data, stats)
                if partner_id:
                    # Tedarikçi kodu ile eşleştirme
                    if supplier_data.get('code'):
                        supplier_code = str(supplier_data['code']).strip()
                        if supplier_code:
                            supplier_mapping[supplier_code] = partner_id
                            _logger.info(f"Tedarikçi eşleştirme eklendi: Kod={supplier_code}, ID={partner_id}")
                    
                    # Adres numarası ile de eşleştirme (MAILADRESI sayfası için)
                    if supplier_data.get('address_no'):
                        address_no = str(supplier_data['address_no']).strip()
                        if address_no:
                            supplier_mapping[address_no] = partner_id
                            _logger.info(f"Adres no ile eşleştirme eklendi: Adres No={address_no}, ID={partner_id}")

            except Exception as e:
                _logger.error(f"Satır {row_idx} hatası: {str(e)}, Data: {supplier_data}")
                stats['supplier']['errors'] += 1

        return supplier_mapping

    def _extract_supplier_data(self, row):
        """Satırdan tedarikçi verilerini çıkar"""
        def safe_get(index, default=''):
            try:
                value = row[index] if len(row) > index and row[index] is not None else default
                return str(value).strip() if value else default
            except:
                return default

        def safe_int(index, default=''):
            try:
                value = row[index] if len(row) > index and row[index] is not None else None
                if isinstance(value, (int, float)):
                    return str(int(value))
                return str(value).strip() if value else default
            except:
                return default

        return {
            'sap_code': safe_int(0),
            'code': safe_int(1),
            'name': safe_get(2),
            'country_code': safe_get(3, 'TR'),
            'city': safe_get(4),
            'district': safe_get(5),
            'zip': safe_get(6),
            'region': safe_get(7),
            'street': safe_get(8),
            'tax_office': safe_get(9),
            'vat': safe_get(10),
            'phone': safe_get(11),
            'phone2': safe_get(12),
            'address_no': safe_get(13),
            'supplier_type': safe_get(14),
            'sa_certificate': safe_get(15),
            'registration_date': safe_get(16),
            'approval_status': safe_get(17),
        }

    def _create_update_supplier(self, data, stats):
        """Tedarikçi oluştur veya güncelle"""
        # Mevcut kayıt ara - Sadece şirket olarak ara
        base_domain = [('is_company', '=', True)]
        
        # is_supplier veya supplier_rank kullanma
        
        # Farklı kriterlere göre arama yapalım
        or_domains = []
        
        # Satıcı kodu ile ara (ref alanı)
        if data.get('code'):
            or_domains.append([('ref', '=', data['code'])])
            or_domains.append([('ref', 'ilike', data['code'])])
            
        # Vergi numarası ile ara
        if data.get('vat'):
            vat_value = data['vat']
            # Sadece rakamları al
            digits_only = ''.join(c for c in str(vat_value) if c.isdigit())
            
            # Tam olarak 10 hane olacak şekilde ayarla
            if len(digits_only) > 10:
                digits_only = digits_only[:10]  # İlk 10 rakamı al
            elif len(digits_only) < 10:
                # 10 haneden azsa, başına 0 ekleyerek 10 haneye tamamla
                digits_only = digits_only.zfill(10)
                
            or_domains.append([('vat', '=', digits_only)])
            
        # İsim ile ara
        if data.get('name'):
            or_domains.append([('name', '=', data['name'])])
            or_domains.append([('name', 'ilike', data['name'])])
            
        # Telefon ile ara
        if data.get('phone'):
            formatted_phone = self._format_phone_number(data['phone'])
            or_domains.append([('phone', '=', formatted_phone)])
            or_domains.append([('phone', 'ilike', data['phone'])])
            
        # Mobil telefon ile ara
        if data.get('phone2'):
            formatted_mobile = self._format_phone_number(data['phone2'])
            or_domains.append([('mobile', '=', formatted_mobile)])
            or_domains.append([('mobile', 'ilike', data['phone2'])])
            
        # Arama kriterlerini birleştir - doğru domain oluşturma
        if or_domains:
            # Önce tüm OR koşullarını düzgün bir şekilde birleştir
            final_domain = []
            
            # Her bir OR koşulu için bir '|' ekle (son koşul hariç)
            for i in range(len(or_domains) - 1):
                final_domain.append('|')
                final_domain.extend(or_domains[i])
                
            # Son OR koşulunu ekle (önüne '|' koymadan)
            if or_domains:
                final_domain.extend(or_domains[-1])
                
            # Base domain'i ekle
            domain = final_domain + base_domain
        else:
            domain = base_domain
            
        _logger.info(f"Tedarikçi arama domain: {domain}")
        
        existing = self.env['res.partner'].search(domain, limit=1)
        
        if existing:
            _logger.info(f"Mevcut tedarikçi bulundu: {existing.name} (ID: {existing.id})")
        else:
            _logger.info(f"Tedarikçi bulunamadı: {data.get('name')}")

        vals = self._prepare_supplier_vals(data)

        try:
            # Ref alanı kontrolü - Satıcı kodu yoksa işleme
            if not vals.get('ref'):
                _logger.warning(f"Ref alanı boş, kayıt atlanıyor: {data.get('name')}")
                stats['supplier']['skipped'] += 1
                return False
                
            if existing:
                if self.update_existing:
                    _logger.info(f"Tedarikçi güncelleniyor: {existing.name}")
                    existing.write(vals)
                    stats['supplier']['updated'] += 1
                    return existing.id
                else:
                    _logger.info(f"Tedarikçi güncelleme devre dışı, atlıyor: {existing.name}")
                    stats['supplier']['skipped'] += 1
                    return existing.id  # Yine de ID'yi döndür, çünkü banka ve e-posta için gerekli
            else:
                _logger.info(f"Yeni tedarikçi oluşturuluyor: {data.get('name')} (Ref: {vals.get('ref')})")
                try:
                    # Odoo'da gerekli olabilecek ek alanları kontrol et
                    required_fields = ['name', 'ref']
                    for field in required_fields:
                        if field not in vals or not vals[field]:
                            _logger.warning(f"Gerekli alan eksik: {field}")
                    
                    # Hata ayıklama için tüm değerleri logla
                    _logger.info(f"Oluşturulacak değerler: {vals}")
                    
                    # Partner oluştur
                    # Odoo'nun create metodunu doğrudan çağırmak yerine, ORM'nin create metodunu kullan
                    # Bu, bazı doğrulama hatalarını önleyebilir
                    partner = self.env['res.partner'].sudo().create(vals)
                    stats['supplier']['created'] += 1
                    return partner.id
                except Exception as e:
                    _logger.error(f"Tedarikçi oluşturma hatası: {str(e)}, Değerler: {vals}")
                    # Hata mesajını daha detaylı incele
                    import traceback
                    _logger.error(f"Hata detayı: {traceback.format_exc()}")
                    stats['supplier']['errors'] += 1
                    return False
        except Exception as e:
            _logger.error(f"Tedarikçi işleme hatası: {str(e)}, Data: {data}")
            stats['supplier']['errors'] += 1
            return False

    def _prepare_supplier_vals(self, data):
        """Tedarikçi için değerleri hazırla"""
        vals = {
            'name': data['name'],
            'is_company': True,
            'lang': 'tr_TR',  # Varsayılan dil Türkçe
        }
        
        # Odoo 18'de tedarikçi sınıflandırması değişmiş olabilir
        # Hem supplier_rank hem de is_supplier alanlarını deneyelim
        try:
            # Önce is_supplier alanını deneyelim
            partner_model = self.env['res.partner']
            if hasattr(partner_model, 'is_supplier'):
                vals['is_supplier'] = True
            else:
                # Yoksa supplier_rank kullan
                vals['supplier_rank'] = 1
                vals['customer_rank'] = 0
        except Exception as e:
            _logger.error(f"Tedarikçi sınıflandırma hatası: {str(e)}")
            # Varsayılan olarak supplier_rank kullan
            vals['supplier_rank'] = 1
            vals['customer_rank'] = 0

        # Referans kodu - Satıcı alanını kullan
        if data.get('code'):
            vals['ref'] = data['code']

        # Adres bilgileri
        if data.get('street'):
            vals['street'] = data['street']
        if data.get('city'):
            vals['city'] = data['city']
        if data.get('zip'):
            vals['zip'] = data['zip']

        # Ülke - Hata durumunda varsayılan Türkiye kullan
        try:
            country_id = self._get_or_create_country(data.get('country_code'))
            if country_id:
                vals['country_id'] = country_id
            else:
                # Varsayılan olarak Türkiye
                turkey = self.env['res.country'].search([('code', '=', 'TR')], limit=1)
                if turkey:
                    vals['country_id'] = turkey.id
        except Exception as e:
            _logger.error(f"Ülke işleme hatası: {str(e)}")
            # Ülke hatası olsa bile devam et

        # İl/Eyalet - Hata durumunda atla
        try:
            if 'country_id' in vals:
                state_id = self._get_or_create_state(data.get('city'), vals['country_id'])
                if state_id:
                    vals['state_id'] = state_id
        except Exception as e:
            _logger.error(f"İl/Eyalet işleme hatası: {str(e)}")
            # İl/Eyalet hatası olsa bile devam et

        # İletişim
        if data.get('phone'):
            vals['phone'] = self._format_phone_number(data['phone'])
        if data.get('phone2'):
            vals['mobile'] = self._format_phone_number(data['phone2'])

        # Vergi
        if data.get('vat'):
            try:
                # Peppol endpoint için VAT numarasını düzenle
                vat_value = data['vat']
                # Sadece rakamları al
                digits_only = ''.join(c for c in str(vat_value) if c.isdigit())
                
                # Tam olarak 10 hane olacak şekilde ayarla
                if len(digits_only) > 10:
                    digits_only = digits_only[:10]  # İlk 10 rakamı al
                elif len(digits_only) < 10:
                    # 10 haneden azsa, başına 0 ekleyerek 10 haneye tamamla
                    digits_only = digits_only.zfill(10)
                    
                vals['vat'] = digits_only
            except Exception as e:
                _logger.error(f"VAT işleme hatası: {str(e)}, VAT: {data.get('vat')}")
                # VAT hatası olsa bile devam et, sadece VAT alanını atla

        # Detaylı mod - yorum alanı
        if self.import_mode == 'detailed':
            comment_parts = []
            # Şirket kodunu yorum alanına eklemeye gerek yok
            if data.get('tax_office'):
                comment_parts.append(f"Vergi Dairesi: {data['tax_office']}")
            if data.get('supplier_type'):
                comment_parts.append(f"Tedarikçi Türü: {data['supplier_type']}")
            if data.get('district'):
                comment_parts.append(f"Semt: {data['district']}")
            
            if comment_parts:
                vals['comment'] = '\n'.join(comment_parts)

        return vals

    def _get_or_create_country(self, country_code):
        """Ülke bul, yoksa boş geç"""
        if not country_code:
            return False
        
        try:
            country = self.env['res.country'].sudo().search([('code', '=', country_code)], limit=1)
            return country.id if country else False
        except Exception as e:
            _logger.error(f"Ülke arama hatası: {str(e)}, Ülke kodu: {country_code}")
            return False

    def _get_or_create_state(self, city_name, country_id):
        """İl/Eyalet bul, yoksa boş geç"""
        if not city_name or not country_id:
            return False
        
        try:
            state = self.env['res.country.state'].sudo().search([
                ('name', 'ilike', city_name),
                ('country_id', '=', country_id)
            ], limit=1)
            
            return state.id if state else False
        except Exception as e:
            _logger.error(f"İl/Eyalet arama hatası: {str(e)}, Şehir: {city_name}, Ülke ID: {country_id}")
            return False
        
    def _format_phone_number(self, phone):
        """Telefon numarasını (999) 999 9999 formatına dönüştür"""
        if not phone:
            return phone
            
        # Sadece rakamları al
        digits = ''.join(c for c in str(phone) if c.isdigit())
        
        # Başta 0 varsa kaldır
        if digits and digits[0] == '0':
            digits = digits[1:]
            
        # Yeterli rakam yoksa orijinal değeri döndür
        if len(digits) < 10:
            return phone
            
        # Son 10 rakamı al (fazlaysa)
        if len(digits) > 10:
            digits = digits[-10:]
            
        # (999) 999 9999 formatına dönüştür
        formatted = f"({digits[0:3]}) {digits[3:6]} {digits[6:10]}"
        return formatted

    def _process_bank_accounts(self, workbook, supplier_mapping, stats):
        """SATICIBANKA sayfasını işle"""
        try:
            # Sayfa kontrolü
            if hasattr(workbook, 'sheetnames'):  # openpyxl
                if 'SATICIBANKA' not in workbook.sheetnames:
                    return
                rows = list(workbook['SATICIBANKA'].iter_rows(values_only=True))
            else:  # xlrd
                if 'SATICIBANKA' not in workbook.sheet_names():
                    return
                sheet = workbook.sheet_by_name('SATICIBANKA')
                rows = [sheet.row_values(i) for i in range(sheet.nrows)]

            # Satırları işle
            for row in rows[1:]:  # Başlık atla
                stats['bank']['processed'] += 1
                try:
                    self._process_bank_row(row, supplier_mapping, stats)
                except Exception as e:
                    _logger.error(f"Banka satırı hatası: {str(e)}")
                    stats['bank']['errors'] += 1

        except Exception as e:
            _logger.error(f"Banka işleme hatası: {str(e)}")

    def _process_bank_row(self, row, supplier_mapping, stats):
        """Banka satırını işle"""
        if not row or len(row) < 4:
            stats['bank']['skipped'] += 1
            return

        try:
            # Tedarikçi kodunu güvenli bir şekilde çıkar
            if isinstance(row[0], (int, float)):
                supplier_code = str(int(row[0]))
            elif row[0]:
                supplier_code = str(row[0]).strip()
            else:
                supplier_code = ''
        except Exception as e:
            _logger.error(f"Tedarikçi kodu çıkarma hatası: {str(e)}, Değer: {row[0]}")
            supplier_code = ''
        account_number = str(row[3]).strip() if row[3] else ''
        
        if not supplier_code or not account_number:
            stats['bank']['skipped'] += 1
            _logger.info(f"Banka satırı atlanıyor: Tedarikçi kodu veya hesap numarası boş")
            return
            
        if supplier_code not in supplier_mapping:
            stats['bank']['skipped'] += 1
            _logger.warning(f"Banka satırı atlanıyor: Tedarikçi kodu ({supplier_code}) eşleştirme tablosunda bulunamadı")
            _logger.debug(f"Mevcut eşleştirmeler: {supplier_mapping.keys()}")
            return

        partner_id = supplier_mapping[supplier_code]
        
        # Mevcut hesap kontrolü
        existing = self.env['res.partner.bank'].search([
            ('partner_id', '=', partner_id),
            ('acc_number', '=', account_number)
        ], limit=1)

        if existing:
            stats['bank']['skipped'] += 1
        else:
            try:
                self.env['res.partner.bank'].create({
                    'partner_id': partner_id,
                    'acc_number': account_number,
                })
                stats['bank']['created'] += 1
            except Exception as e:
                _logger.error(f"Banka hesabı oluşturma hatası: {str(e)}")
                stats['bank']['errors'] += 1

    def _process_emails(self, workbook, supplier_mapping, stats):
        """MAILADRESI sayfasını işle"""
        try:
            # Sayfa kontrolü
            if hasattr(workbook, 'sheetnames'):  # openpyxl
                if 'MAILADRESI' not in workbook.sheetnames:
                    return
                rows = list(workbook['MAILADRESI'].iter_rows(values_only=True))
            else:  # xlrd
                if 'MAILADRESI' not in workbook.sheet_names():
                    return
                sheet = workbook.sheet_by_name('MAILADRESI')
                rows = [sheet.row_values(i) for i in range(sheet.nrows)]

            # Satırları işle
            for row in rows[1:]:  # Başlık atla
                stats['email']['processed'] += 1
                try:
                    self._process_email_row(row, supplier_mapping, stats)
                except Exception as e:
                    _logger.error(f"E-posta satırı hatası: {str(e)}")
                    stats['email']['errors'] += 1

        except Exception as e:
            _logger.error(f"E-posta işleme hatası: {str(e)}")

    def _process_email_row(self, row, supplier_mapping, stats):
        """E-posta satırını işle"""
        if not row or len(row) < 2:
            stats['email']['skipped'] += 1
            return

        try:
            # Tedarikçi kodunu güvenli bir şekilde çıkar
            if isinstance(row[0], (int, float)):
                supplier_code = str(int(row[0]))
            elif row[0]:
                supplier_code = str(row[0]).strip()
            else:
                supplier_code = ''
                
            email = str(row[1]).strip() if row[1] else ''
        except Exception as e:
            _logger.error(f"E-posta satırı veri çıkarma hatası: {str(e)}, Satır: {row}")
            stats['email']['errors'] += 1
            return
        
        if not supplier_code or not email:
            stats['email']['skipped'] += 1
            _logger.info(f"E-posta satırı atlanıyor: Tedarikçi kodu veya e-posta boş")
            return
            
        if supplier_code not in supplier_mapping:
            stats['email']['skipped'] += 1
            _logger.warning(f"E-posta satırı atlanıyor: Tedarikçi kodu ({supplier_code}) eşleştirme tablosunda bulunamadı")
            return

        partner_id = supplier_mapping[supplier_code]
        
        try:
            partner = self.env['res.partner'].sudo().browse(partner_id)
            
            if partner.exists():
                # E-posta formatını doğrula
                if '@' in email and '.' in email:
                    partner.write({'email': email})
                    stats['email']['updated'] += 1
                else:
                    _logger.warning(f"Geçersiz e-posta formatı: {email}, Tedarikçi: {partner.name}")
                    stats['email']['skipped'] += 1
            else:
                _logger.warning(f"Tedarikçi bulunamadı: ID={partner_id}, Kod={supplier_code}")
                stats['email']['skipped'] += 1
        except Exception as e:
            _logger.error(f"E-posta güncelleme hatası: {str(e)}, E-posta: {email}, Tedarikçi ID: {partner_id}")
            stats['email']['errors'] += 1

    def _show_success_message(self, stats):
        """Başarı mesajını göster"""
        if self.import_mode == 'basic':
            message = _(
                f"Temel İmport Tamamlandı!\n\n"
                f"Tedarikçi: İşlenen: {stats['supplier']['processed']}, "
                f"Oluşturulan: {stats['supplier']['created']}, "
                f"Güncellenen: {stats['supplier']['updated']}, "
                f"Atlanan: {stats['supplier']['skipped']}, "
                f"Hatalı: {stats['supplier']['errors']}\n\n"
                f"E-posta: İşlenen: {stats['email']['processed']}, "
                f"Güncellenen: {stats['email']['updated']}, "
                f"Atlanan: {stats['email']['skipped']}, "
                f"Hatalı: {stats['email']['errors']}"
            )
        else:
            message = _(
                f"Detaylı İmport Tamamlandı!\n\n"
                f"Tedarikçi: İşlenen: {stats['supplier']['processed']}, "
                f"Oluşturulan: {stats['supplier']['created']}, "
                f"Güncellenen: {stats['supplier']['updated']}, "
                f"Atlanan: {stats['supplier']['skipped']}, "
                f"Hatalı: {stats['supplier']['errors']}\n\n"
                f"Banka: İşlenen: {stats['bank']['processed']}, "
                f"Oluşturulan: {stats['bank']['created']}, "
                f"Atlanan: {stats['bank']['skipped']}, "
                f"Hatalı: {stats['bank']['errors']}\n\n"
                f"E-posta: İşlenen: {stats['email']['processed']}, "
                f"Güncellenen: {stats['email']['updated']}, "
                f"Atlanan: {stats['email']['skipped']}, "
                f"Hatalı: {stats['email']['errors']}"
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İmport Başarılı'),
                'message': message,
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }