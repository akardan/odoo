# MICE İhale Tasarım Dokümanı

Bu doküman, mevcut `ak_tender` modülüne MICE (Meeting, Incentive, Conference, Event) ihaleleri için gerekli geliştirmelerin entegrasyon planını içerir.

## 1. Veri Modeli Değişiklikleri

### 1.1. Yeni Master Data Modelleri

Mevcut `tender_type` Selection alanını Many2one model tabanlı bir yapıya dönüştürmek ve esnekliği artırmak için aşağıdaki modeller eklenecektir:

#### `ak.tender.type` (İhale Tipi)
- `name`: Char (Direkt, Endirekt, MICE, Sigorta, Promosyon, Servis)
- `code`: Char (direct, indirect, mice, insurance, promotion, service)
- `sequence`: Integer
- `active`: Boolean

** Muvcut kayıtların yeni yapıya göre güncellenmesi gerekir! **

#### `ak.tender.sub.type` (İhale Alt Tipi)
- `name`: Char (Örn: MICE için; Konaklama, Organizasyon, Ulaşım)
- `code`: Char
- `tender_type_id`: Many2one (`ak.tender.type`)
- `active`: Boolean

#### `ak.tender.line.category` (Satır Kategorisi)
- `name`: Char (Örn: Oda Tipi, Yemek Planı, Ekipman)
- `code`: Char
- `tender_type_id`: Many2one (`ak.tender.type`)
- `active`: Boolean

### 1.2. Mevcut Model Uzantıları

#### `ak.tender` (İhale)
- `tender_type_id`: Many2one (`ak.tender.type`) - *Mevcut `tender_type` Selection alanı ile senkronize çalışacak veya yerini alacak.*
- `tender_sub_type_id`: Many2one (`ak.tender.sub.type`)
- `total_person_count`: Integer (Toplam Kişi)
- `vip_person_count`: Integer (VIP Kişi Sayısı)
- `current_supplier_id`: Many2one (`res.partner`)
- `current_total_amount`: Monetary

#### `ak.tender.line` (İhale Kalemi)
- `line_category_id`: Many2one (`ak.tender.line.category`)
- `line_spec_data`: Json (Özel MICE verilerini saklamak için)
- `line_summary`: Text (JSON verisinden üretilen özet)
- `is_mice_line`: Boolean (MICE özel alanlarını göstermek için)
- `alternative_group_id`: Integer (Alternatif teklifleri gruplamak için: Örn. Otel A Alternatifi, Otel B Alternatifi)

## 2. MICE Özel Alanları (JSON UI)

`ak.tender.line` üzerinde MICE ihalelerine özel alanlar, `line_spec_data` JSON alanını besleyen computed/inverse field'lar olarak tasarlanacaktır. Karmaşık alternatif senaryoları (Lokasyon > Otel > Pansiyon Tipi) için:

- `mice_location_id`: Many2one (`res.country.state` veya `res.country`)
- `mice_hotel_id`: Many2one (`res.partner`, domain: is_hotel=True)
- `mice_room_type`: Selection (Single, Double, Triple, Suite)
- `mice_meal_plan`: Selection (BB, HB, FB, AI, UAI)
- `mice_view_type`: Selection (Sea, Garden, City, Mountain)
- `mice_amenities`: Char (Ekstra hizmetler)
- `mice_transport_type`: Selection (Uçak, Otobüs, VIP Transfer)
- `mice_event_type`: Selection (Toplantı, Gala, Kokteyl)
- `mice_technical_detail`: Char (Teknik detay: Örn. M2, Adet, Teknik Özellik)
- `mice_is_technical`: Boolean (Teknik başlığı altındaki kalemleri işaretlemek için)
- `is_alternative`: Boolean (Bu satır bir alternatif mi?)
- `service_route`: Char (Servis Güzergahı)
- `service_capacity`: Integer (Koltuk Sayısı)
- `service_distance`: Float (Tek Yön Mesafe KM)
- `service_payment_term_alt`: Selection (Vadeye göre alternatif fiyatlandırma için vade seçimi)

## 3. Kullanıcı Arayüzü (UI) Tasarımı

### 3.1. İhale Formu
- `tender_type_id` seçimine göre dinamik alanlar (`service_start_date`, `vip_person_count` vb.) görünür/gizli olacaktır.
- Odoo 18 `invisible` ve `column_invisible` syntax'ı kullanılacaktır.

### 3.2. İhale Kalemleri Listesi
- MICE ihalelerinde `days` ve `hotel_partner_id` alanları ön planda olacaktır.
- JSON tabanlı MICE detayları için satır içinde veya bir pop-up formda özel alanlar sunulacaktır.

## 4. İş Akışı ve Hesaplamalar

- **Hedef Fiyat:** MICE ihalelerinde `Birim Fiyat * Miktar * Gün` formülü korunacak ve geliştirilecektir.
- **NPV Hesaplama:** `ak.tender.economic.data` üzerinden gelen oranlarla teklif karşılaştırma ekranında NPV değerleri gösterilecektir.
- **Vade Farkı ve NPV Analizi:**
    - Servis ihalelerinde farklı vadelerle gelen teklifler, `ak.tender.economic.data` modelindeki güncel faiz/enflasyon oranları kullanılarak "Net Bugünkü Değer" (NPV) üzerinden otomatik olarak normalize edilecektir.
    - Sistem, 60 gün ve 90 gün vadeli teklifleri bugünkü değerine indirgeyerek hangisinin daha avantajlı olduğunu otomatik olarak hesaplayıp karşılaştırma ekranında sunacaktır.
- **Teklif Karşılaştırma (MICE Özel):**
    - Teklif karşılaştırma ekranında satırlar `alternative_group_id` (Alternatif Grubu) bazında gruplanacaktır.
    - Her alternatif grubu (Örn: Antalya Otel A, Kıbrıs Otel B) yan yana sütunlar halinde gösterilerek toplam maliyet ve teknik detay karşılaştırması yapılacaktır.
    - JSON alanındaki kritik veriler (Pansiyon tipi, oda tipi vb.) karşılaştırma tablosunda "Teknik Detay" sütunu olarak özetlenecektir.

## 5. Uygulama Planı (7 Gün)

1. **1-2. Gün:** Master data modellerinin ve temel extension alanlarının oluşturulması.
2. **3. Gün:** JSON UI mantığının (computed/inverse fields) kurulması.
3. **4-5. Gün:** View'ların Odoo 18 standartlarına göre güncellenmesi.
4. **6. Gün:** MICE özel hesaplama mantığının (NPV, Hedef Fiyat) entegrasyonu.
5. **7. Gün:** Test ve dokümantasyon.
