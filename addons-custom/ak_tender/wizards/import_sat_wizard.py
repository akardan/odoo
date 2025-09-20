# -*- coding: utf-8 -*-

import base64
import io
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

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

    def _process_sat_data(self, workbook, stats):
        """ILP(300) sayfasından ihale tanımlarını işle"""
        # Sayfa kontrolü ve veri okuma
        sheet_name = self.sheet_name
        
        if hasattr(workbook, 'sheetnames'):  # openpyxl
            if sheet_name not in workbook.sheetnames:
                raise UserError(_(f'{sheet_name} sayfası bulunamadı'))
            rows = list(workbook[sheet_name].iter_rows(values_only=True))
        else:  # xlrd
            if sheet_name not in workbook.sheet_names():
                raise UserError(_(f'{sheet_name} sayfası bulunamadı'))
            sheet = workbook.sheet_by_name(sheet_name)
            rows = [sheet.row_values(i) for i in range(sheet.nrows)]

        if len(rows) <= 1:
            raise UserError(_(f'{sheet_name} sayfası boş'))

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
            # İndeks 18: Talep tarihi (şu an kullanılmıyor)
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
        vals = {
            'name': data.get('name') or f"SAT-{data.get('erp_pr_id')}",
            'erp_pr_id': data.get('erp_pr_id'),
            'erp_company_code': data.get('company_code'),
            'erp_plant_code': data.get('plant_code'),
            'required_delivery_date': data.get('required_delivery_date'),
            'start_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now(),  # Varsayılan olarak şu anki tarih, gerçek uygulamada değiştirilmeli
            'tender_type': 'direct',  # Varsayılan olarak direkt satın alma
        }
        
        # Öncelikle mal grubuna göre tender_type belirle
        material_group = data.get('material_group')
        if material_group:
            # Etken Madde, Yardımcı Madde, Pellet Etken Madde
            if material_group.startswith('1000'):
                vals['tender_type'] = 'direct'
            # Granül/Bulk, Tablet/kapsül, Kaplı Tablet, vb.
            elif material_group.startswith('2000'):
                vals['tender_type'] = 'direct'
            # Katı Ürünler, Likit Ürünler, vb.
            elif material_group.startswith('3000'):
                vals['tender_type'] = 'direct'
            # PVC, Alüminyum Folyo, Şişe, vb.
            elif material_group.startswith('4000'):
                vals['tender_type'] = 'direct'
            # Promosyon
            elif material_group.startswith('5000'):
                vals['tender_type'] = 'promotion'
            # Fason İşçilik, Laboratuar Test, Eğitim-Danışmanlık, vb.
            elif material_group.startswith('6000'):
                vals['tender_type'] = 'indirect'
            # Tanıtım Numuneleri, Tanıtım Malzemeleri
            elif material_group.startswith('7000'):
                vals['tender_type'] = 'promotion'
            # Satış Hizmet
            elif material_group.startswith('8000'):
                vals['tender_type'] = 'indirect'
            # Demirbaş, Yedek Parça, vb.
            elif material_group.startswith('9000'):
                vals['tender_type'] = 'indirect'
        
        # Mal grubu belirlenemezse, üretim yerine göre tender_type belirle
        if not material_group:
            production_location = data.get('production_location')
            if production_location:
                if production_location == '2100':  # İlko
                    vals['tender_type'] = 'direct'
                elif production_location == '2000':  # Merkez
                    vals['tender_type'] = 'indirect'
                elif production_location == '1100':  # İlkopol
                    vals['tender_type'] = 'indirect'
        
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
            uom = self.env['uom.uom'].search([('name', '=', data.get('unit_of_measure'))], limit=1)
            if uom:
                line_vals['uom_id'] = uom.id
                _logger.info(f"Birim bulundu: {uom.name} (ID: {uom.id})")
            else:
                _logger.warning(f"Birim bulunamadı: {data.get('unit_of_measure')}")
        
        # İhale kalemi oluştur
        _logger.info(f"İhale kalemi oluşturuluyor: {line_vals}")
        tender_line = self.env['ak.tender.line'].sudo().create(line_vals)
        _logger.info(f"İhale kalemi oluşturuldu: {tender_line.name} (ID: {tender_line.id})")
        return tender_line

    def _find_or_create_product(self, data):
        """Ürünü bul, yoksa oluştur"""
        product = False
        
        # Kullanıcı geri bildirimine göre:
        # G kolonu (indeks 6) "Malzeme" malzeme kodunu içeriyor (material_code alanında)
        # H kolonu (indeks 7) "Kısa metin" malzeme adına karşılık geliyor (name alanında)
        material_code = data.get('material_code')  # Malzeme kodu
        material_name = data.get('name')  # Malzeme adı
        
        _logger.info(f"Ürün aranıyor: Kod={material_code}, Ad={material_name}, Data={data}")
        
        if not material_code:
            _logger.warning(f"Malzeme kodu bulunamadı: {data}")
            return None
            
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
                    uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
                    if not uom:
                        # Birim bulunamadıysa, referans birim olarak 'Adet' birimini kullan
                        reference_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
                        if not reference_uom:
                            reference_uom = self.env['uom.uom'].search([('name', '=', 'Adet')], limit=1)
                        
                        if reference_uom:
                            # Yeni birim oluştur
                            try:
                                uom = self.env['uom.uom'].sudo().create({
                                    'name': uom_name,
                                    'category_id': reference_uom.category_id.id,
                                    'uom_type': 'reference',
                                    'rounding': 0.01,
                                    'factor': 1.0,
                                })
                                _logger.info(f"Yeni birim oluşturuldu: {uom.name} (ID: {uom.id})")
                            except Exception as e:
                                _logger.error(f"Birim oluşturma hatası: {str(e)}")
                                # Birim oluşturulamadıysa, varsayılan birimi kullan
                                uom = reference_uom
                        else:
                            _logger.warning(f"Referans birim bulunamadı, birim oluşturulamadı: {uom_name}")
                    
                    if uom:
                        product_vals['uom_id'] = uom.id
                        product_vals['uom_po_id'] = uom.id
                        _logger.info(f"Ürün birimi ayarlandı: {uom.name} (ID: {uom.id})")
                    else:
                        _logger.warning(f"Birim bulunamadı ve oluşturulamadı: {uom_name}")
                
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