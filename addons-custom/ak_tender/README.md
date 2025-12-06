# İhale Modülü (ak_tender)

## Genel Bakış

Bu modül, çok aşamalı satın alma ihale süreçlerini Odoo 18 CE üzerinde yönetmek için tasarlanmıştır. Modül, iş akışı (workflow) tabanlı bir yaklaşım kullanarak ihale süreçlerini yönetir ve ihale ile satın alma siparişi işlevselliğinde sürekli iyileştirmeler yapılmıştır.

## Özellikler

### Temel Özellikler
- ERP Entegrasyon (simülasyon)
- SAT içe aktar Fonksiyonelliği (gelişmiş hata yönetimi ile)
- Çok Aşamalı İhale Süreci (1. Teklif Toplama, Hedef Fiyat, 2. Teklif Toplama)
- Tedarikçi Portal Entegrasyonu (gelişmiş düzenleme özellikleri)
- Onay Mekanizması entegrasyonu (Approvals modülü ile)
- Hedef Fiyat Belirleme Sihirbazı (sunucu eylemi ile erişim)
- Satın Alma Siparişi Oluşturma ve Toplu E-posta Gönderme Sunucu Eylemleri
- Gelişmiş İş Akışı Geçiş Wizard'ı (Türkçe arayüz)
- Raporlama ve Analiz altyapısı
- İhale tiplerine göre ilerleme çubuğu renklendirmesi
- İhale Kalemleri yönetimi (bölüm ve not desteği)
- Odoo'nun temel satın alma (purchase.order) modülü ile entegrasyon
- Farklı ihale tipleri için görsel yönetim özellikleri (direct, indirect, mice, promotion)
- İhale şablonları (tüm ihale tipleri için)
- Toplu satın alma optimizasyonu (indirect ve promotion ihaleleri için)
- Acil talep desteği (indirect ve promotion ihaleleri için)
- Ekonomik veri entegrasyonu (promotion ihaleleri için)
- Dinamik tedarikçi ekleme fonksiyonu
- Coğrafi tedarikçi filtreleme
- Rol tabanlı erişim kontrolü (RBAC) ile güvenlik yönetimi

### Tedarikçi Başvuru Sistemi
- Web tabanlı tedarikçi başvuru formu
- IBAN validasyonu ve doküman yükleme zorunluluğu
- 4 zorunlu doküman tipi (Vergi Levhası, İmza Sirküleri, Ticaret Sicil, Banka Bilgisi)
- Doküman önizleme özelliği (PDF ve görsel dosyalar)
- Otomatik partner kaydı ve güncelleme (VKN kontrolü ile)
- Portal kullanıcı oluşturma otomasyonu
- E-posta bildirimleri (başvuru onayı, teklif çağrısı, teklif hatırlatıcısı)
- Türkçe arayüz ve hata mesajları

### Portal ve Teklif Yönetimi
- Gelişmiş Portal Arayüzü (tedarikçiler için teklif düzenleme)
- Teklif durumu takibi (offer_status: not_submitted, submitted)
- Toplu değişiklik kaydetme
- Ek dosya görüntüleme özellikleri:
  - Dosya tipine göre renkli ikonlar (PDF, Word, Excel, PowerPoint, Resim)
  - Modal önizleme ekranı (XL boyut)
  - Tam ekran görüntüleme modu
  - Türkçe karakter desteği (RFC 5987 standardı)
  - PDF'ler için inline görüntüleme
- Alternatif malzeme önerileri sunma
- Vergi seçimi yapabilme
- Garanti süresi yönetimi
- Teslimat tarihi belirleme
- İndirim oranı belirtme

### Karşılaştırma ve Raporlama
- Tedarikçi Karşılaştırma Raporu
- En düşük fiyat vurgulama
- NPV (Net Bugünkü Değer) hesaplamaları
- Ödeme koşullarına göre bölünmüş ödeme desteği
- Gecikme günleri hesaplaması
- Kazanan siparişler işlevselliği
- SAT durumu görselleştirme (iptal/teklif verildi/beklemede)

### Validasyon ve Hata Yönetimi
- UoM kategori validasyonu (SAT içe aktarma)
- Para birimi senkronizasyonu (ihale-ihale kalemleri arası)
- Sessiz hata engelleme (detaylı loglama ve kullanıcı bildirimi)
- Odoo 18 uyumluluğu (notify_by_email parametresi kaldırıldı)

## Güvenlik Grupları

Modül, aşağıdaki güvenlik gruplarını içerir:

### Tender Requester (İhale Talep Edici)
- Kendi oluşturduğu ihaleleri görüntüleyebilir
- Yeni ihale talepleri oluşturabilir
- Mevcut ihaleleri düzenleyemez veya silemez
- Kendi ihalelerine ait ihale kalemlerini oluşturabilir

### Tender User (İhale Kullanıcısı)
- Kendi oluşturduğu ihaleleri görüntüleyebilir ve düzenleyebilir
- Yeni ihale oluşturabilir
- İhaleleri silemez
- Tender Requester grubunun tüm yetkilerine sahiptir

### Tender Manager (İhale Yöneticisi)
- Tüm ihaleleri görüntüleyebilir, düzenleyebilir ve silebilir
- Tüm ihale kalemlerini yönetebilir
- İhale süreçlerini onaylayabilir
- Tender User grubunun tüm yetkilerine sahiptir

## İş Akışı (Workflow) Entegrasyonu

Bu modül, `ak_workflow` modülü ile entegre çalışır. İhale süreçleri, tanımlanmış iş akışları üzerinden yönetilir. Her ihale, bir iş akışı tanımına (workflow definition) sahiptir ve bu tanım üzerinden durumlar (states) ve geçişler (transitions) yönetilir.

### İhale Durumları

İhale sürecinde aşağıdaki durumlar bulunabilir:

- `draft`: Taslak
- `first_tender_round`: 1. Teklif Toplama
- `target_price_set`: Hedef Fiyat Belirlendi
- `new_tender_round`: Yeni Teklif Toplama
- `evaluation`: Değerlendirme
- `approval`: Onayda
- `completed`: Tamamlandı
- `cancel`: İptal Edildi

### İş Akışı Geçişleri

İhale durumları arasındaki geçişler, iş akışı tanımında belirtilen geçişler (transitions) üzerinden gerçekleştirilir. Her geçiş, belirli koşullara bağlı olabilir ve geçiş sırasında çeşitli aksiyonlar tetiklenebilir.

## Teknik Notlar

### Deprecated Fields

- `state` alanı artık kullanılmamaktadır. Bunun yerine `workflow_current_state_id` ve `workflow_state` alanları kullanılmalıdır.
- `tender_results` yerine `purchase_order_ids` kullanılmaktadır.
- `notify_by_email` ve `email_from` parametreleri Odoo 18'de kaldırılmıştır (message_post metodundan).

### İş Akışı Kullanımı

İş akışı geçişleri, `execute_transition` metodu ile gerçekleştirilir:

```python
# Örnek geçiş kodu
transition = self.env['ak.workflow.transition'].search([
    ('from_state_id', '=', tender.workflow_current_state_id.id),
    ('to_state_id.code', '=', 'target_state_code')
], limit=1)

if transition:
    tender.execute_transition(transition.id, "Geçiş açıklaması")
```

### İş Akışı Geçmişi

- Her durum geçişi otomatik olarak kaydedilir
- `end_time` alanı stored olarak tutulur (performans için)
- `expected_duration` alanı durumun varsayılan süresinden hesaplanır
- `elapsed_time` negatif değer almayacak şekilde düzeltildi
- İlk durum (örn: Draft) için otomatik geçmiş kaydı oluşturulur

### SAT (Satın Alma Talebi) Oluşturma

#### Hibrit Oluşturma Yöntemi
Yeni tur teklifleri için hibrit yöntem kullanılır (`_create_line_from_tender_with_previous`):
- Her zaman ihale kalemlerini baz alır (ihale tanımı değişikliklerini yansıtır)
- Tedarikçinin önceki teklif verilerini birleştirir (fiyat, para birimi, indirim, teslimat tarihi, vergiler)
- İhale değişikliklerinin yeni turlara yansımasını sağlar
- Tedarikçi verilerini korur

```python
# Hibrit yöntem kullanımı
for line in tender.tender_line_ids:
    if line.display_type not in ('line_section', 'line_note'):
        # Ürün satırı için SAT oluştur
        po_line = self._create_line_from_tender_with_previous(line, po)
```

### Display Type (Bölüm ve Not Satırları)

- `display_type` alanı Odoo 18 standardına uygun hale getirildi
- Ürün satırları için `display_type=False` (varsayılan)
- Bölüm satırları için `display_type='line_section'`
- Not satırları için `display_type='line_note'`
- Widget: `product_label_section_and_note_field_o2m`

### Validasyon ve Hata Yönetimi

#### UoM Validasyonu
SAT içe aktarma sırasında UoM kategori uyumsuzluğu kontrol edilir:
```python
# UoM kategori kontrolü
if product.uom_id.category_id != uom.category_id:
    raise UserError(f"UoM kategori uyumsuzluğu: {product.name}")
```

#### Para Birimi Senkronizasyonu
İhale kalemlerinin para birimi otomatik olarak ihale para birimiyle senkronize edilir:
```python
@api.onchange('currency_id')
def _onchange_currency_id(self):
    if self.currency_id:
        self.tender_line_ids.write({'currency_id': self.currency_id.id})
```

## Kurulum

Bu modül, aşağıdaki bağımlılıklara sahiptir:

- base
- purchase
- stock
- mail
- contacts
- product
- portal
- ak_workflow
- sale

## Geliştirme

### Yeni Durum Ekleme

Yeni bir durum eklemek için, ilgili iş akışı tanımına yeni bir durum eklenmeli ve gerekli geçişler tanımlanmalıdır.

### Yeni Geçiş Ekleme

Yeni bir geçiş eklemek için, ilgili iş akışı tanımına yeni bir geçiş eklenmeli ve gerekli aksiyonlar tanımlanmalıdır.

### Güvenlik Grupları ve Kuralları Ekleme

Yeni güvenlik grupları veya kuralları eklemek için:

1. `security/security_groups.xml` dosyasında yeni gruplar tanımlanır
2. `security/security_rules.xml` dosyasında yeni kurallar tanımlanır
3. `security/ir.model.access.csv` dosyasında erişim hakları tanımlanır
4. `__manifest__.py` dosyasında bu dosyalar data listesine eklenir

## İhale Tipleri

Modül, aşağıdaki ihale tiplerini desteklemektedir:

- `direct`: Direkt Satın Alma
  - ERP kodu zorunluluğu
  - Tedarik süresi kısıtlaması
  - Muadil ürün kabul edilmez

- `indirect`: Endirekt Satın Alma
  - Toplu satın alma optimizasyonu
  - Muadil ürün teklifleri
  - Acil talep desteği

- `mice`: MICE İhaleler
  - Hizmet kategorisi şablonları
  - Şablon değişiklik kısıtlamaları
  - Coğrafi tedarikçi filtreleme

- `promotion`: Promosyon ve Kırtasiye
  - Toplu satın alma optimizasyonu
  - Acil talep desteği
  - Ekonomik veri entegrasyonu

## İhale Şablonları

İhale şablonları, benzer ihaleler için tekrar kullanılabilir yapılar oluşturmanıza olanak tanır. Şablonlar, ihale satırlarını, coğrafi filtreleri ve diğer ayarları içerebilir.

### Şablon Özellikleri

- Farklı ihale tipleri için şablon oluşturma
- Bölümler, notlar ve ürün satırları ekleme
- Şablon kilitleme mekanizması
- Coğrafi filtreleme (ülke, il, şehir)

### Şablon Kullanımı

Şablonlar, ihale formunda "Şablon Uygula" butonu ile uygulanabilir. Şablon uygulandığında, şablondaki satırlar ihaleye otomatik olarak eklenir ve coğrafi bilgiler güncellenir.

```python
# Şablon uygulama örneği
tender.action_apply_template()
```

## Coğrafi Filtreleme

Coğrafi filtreleme, ihalelerin belirli bölgelere özgü olmasını sağlar. Bu özellik, özellikle MICE ihaleleri için kullanışlıdır.

- Ülke, il ve şehir bazında filtreleme
- Şablonlarda coğrafi kısıtlama tanımlama
- Şablon uygulandığında coğrafi bilgilerin otomatik güncellenmesi

## Toplu Satın Alma Optimizasyonu

Toplu satın alma optimizasyonu, birden fazla satın alma talebini tek bir ihalede birleştirmenizi sağlar. Bu özellik, indirect ve promotion ihaleleri için kullanılabilir.

## Acil Talep Desteği

Acil talep desteği, acil durumlar için hızlı ihale süreçleri oluşturmanızı sağlar. Bu özellik, indirect ve promotion ihaleleri için kullanılabilir.

## Ekonomik Veri Entegrasyonu

Ekonomik veri entegrasyonu, döviz kurları ve enflasyon gibi ekonomik faktörleri ihale değerlendirmesinde dikkate almanızı sağlar. Bu özellik, özellikle promotion ihaleleri için kullanışlıdır.

## Tedarikçi Karşılaştırma Raporu

Tedarikçi karşılaştırma raporu, farklı tedarikçilerden gelen teklifleri yan yana karşılaştırmanızı sağlar. Bu rapor, aşağıdaki özelliklere sahiptir:

- Ürün bazında fiyat karşılaştırması
- En düşük fiyatlı tekliflerin otomatik vurgulanması
- Gelişmiş NPV (Net Bugünkü Değer) hesaplamaları ve rapor stil iyileştirmeleri
- Teslimat tarihi ve garanti süresi karşılaştırması
- Alternatif malzeme önerilerinin görüntülenmesi
- Toplam fiyat karşılaştırması ve otomatik seçim önerisi

## Tedarikçi Başvuru Sistemi

Tedarikçi başvuru sistemi, yeni tedarikçilerin sisteme kaydolmasını sağlar ve otomatik onay süreçleri içerir.

### Başvuru Formu Özellikleri
- Web tabanlı başvuru formu (`/tender/supplier/register`)
- Zorunlu alanlar ve validasyon kuralları
- IBAN formatı kontrolü
- 4 zorunlu doküman tipi:
  - Vergi Levhası
  - İmza Sirküleri
  - Ticaret Sicil Gazetesi
  - Banka Bilgisi (Kaşeli)
- Doküman önizleme özelliği (PDF ve görsel dosyalar için)
- Otomatik sıra numarası oluşturma

### Onay Süreci
1. Tedarikçi başvuru formunu doldurur ve dokümanları yükler
2. İhale yöneticisi başvuruyu gözden geçirir
3. Onay sonrası otomatik işlemler:
   - VKN kontrolü ile mevcut partner aranır
   - Mevcut partner varsa güncellenir, yoksa yeni partner oluşturulur
   - İletişim kişisi partner'a child olarak eklenir
   - Portal kullanıcı hesabı oluşturulur
   - Başarılı kayıt e-postası gönderilir

### Teknik Detaylar
```python
# Partner oluşturma veya güncelleme
existing_partner = self.env['res.partner'].search([
    ('vat', '=', application.vat_number)
], limit=1)

if existing_partner:
    # Mevcut partner'ı güncelle
    existing_partner.write({...})
else:
    # Yeni partner oluştur
    partner = self.env['res.partner'].sudo().create({...})
```

### E-posta Şablonları
- Başvuru onayı mesajı
- Teklif çağrısı bildirimi
- Teklif hatırlatıcı mesajı
- Türkçe içerik desteği

## Gelişmiş Portal Arayüzü

Tedarikçiler için geliştirilmiş portal arayüzü, aşağıdaki özelliklere sahiptir:

### Teklif Düzenleme
- Teklif fiyatlarını doğrudan portal üzerinden düzenleme
- Teslimat tarihlerini belirleme
- Garanti süresi seçimi
- İndirim oranı belirtme
- Alternatif malzeme önerileri sunma
- Vergi seçimi yapabilme
- Toplu değişiklik kaydetme
- Teklif durumu takibi (offer_status: not_submitted, submitted)

### Ek Dosya Yönetimi
Portal üzerinde ek dosyaları görüntüleme ve indirme özellikleri:

#### Dosya Tipi İkonları
- PDF dosyaları: Kırmızı icon (fa-file-pdf-o)
- Word dosyaları: Mavi icon (fa-file-word-o)
- Excel dosyaları: Yeşil icon (fa-file-excel-o)
- PowerPoint dosyaları: Turuncu icon (fa-file-powerpoint-o)
- Resim dosyaları: Mor icon (fa-file-image-o)
- Diğer dosyalar: Kahverengi metin icon (fa-file-text-o)

#### Önizleme Özellikleri
- Modal önizleme penceresi (XL boyut, %95 genişlik)
- iframe yüksekliği: 90vh (minimum 800px)
- Tam ekran görüntüleme modu
  - Fullscreen API ile cross-browser destek
  - iframe'i tam ekrana alma (modal yerine)
  - Expand/compress icon değişimi
- PDF inline görüntüleme (tarayıcıda açılır)
- Türkçe karakter desteği (RFC 5987 standardı ile encoding)
- Access token ile güvenli erişim

#### Teknik Uygulama
```javascript
// Tam ekran modu
function toggleFullscreen() {
    var iframe = document.querySelector('.preview-iframe');
    if (!document.fullscreenElement) {
        if (iframe.requestFullscreen) {
            iframe.requestFullscreen();
        } else if (iframe.webkitRequestFullscreen) {
            iframe.webkitRequestFullscreen();
        }
    } else {
        document.exitFullscreen();
    }
}
```

```python
# Türkçe karakter desteği
from odoo.http import content_disposition

headers = [
    ('Content-Type', mimetype),
    ('Content-Disposition', content_disposition(
        attachment.name,
        disposition_type='inline'
    ))
]
```

### Görsel İyileştirmeler
- Dikdörtgen şekilli dosya butonları (border-radius: 8px)
- Büyük renkli ikonlar (3em boyut)
- Responsive tasarım
- Kolay tıklanabilir alanlar
- SAT durumu görselleştirme:
  - İptal edilen: Kırmızı badge (danger)
  - Teklif verilmiş: Yeşil badge (success)
  - Teklif verilmemiş: Gri badge (muted)

## NPV Hesaplamaları

NPV (Net Bugünkü Değer) hesaplamaları, farklı tedarikçilerden gelen tekliflerin finansal karşılaştırmasını yapmak için kullanılır. Bu özellik, aşağıdaki avantajları sağlar:

- Farklı ödeme koşullarına göre bölünmüş ödeme desteği ile NPV hesaplamaları
- Uzun vadeli satın almalarda gerçek maliyeti hesaplama
- İskonto oranı belirleme ve ekonomik faktörleri dikkate alma

## Son Güncellemeler (Git Commit Geçmişi)

### PDF ve Dosya Yönetimi İyileştirmeleri
- **PDF Ek Görüntüleme**: Türkçe karakterli dosya adlarında encoding sorunu düzeltildi (RFC 5987)
- **Inline Görüntüleme**: PDF'ler tarayıcıda açılacak şekilde `disposition_type='inline'` kullanımı
- **Tam Ekran Modu**: iframe tam ekran görüntüleme özelliği eklendi
- **Modal Boyutlandırma**: Önizleme modalı XL boyuta çıkarıldı (%95 genişlik, 90vh yükseklik)
- **Dosya Tipi İkonları**: Renkli ve büyük ikonlar (PDF, Word, Excel, PowerPoint, Resim)
- **Buton Tasarımı**: Dikdörtgen şekilli butonlar (border-radius: 8px)

### Teklif ve SAT Yönetimi
- **Teklif Durumu Takibi**: `offer_status` alanı stored field'e dönüştürüldü
- **Yeni Tur Teklifleri**: Oluşturulurken otomatik olarak 'not_submitted' durumuna geçiş
- **SAT Oluşturma Düzeltmesi**: Display type kontrolü iyileştirildi
- **Tedarikçi Kolon Başlıkları**: Firma adı gösterimi düzeltildi (FIRMA - KİŞİ - PO_NO formatı)
- **SAT Görselleştirme**: İptal/teklif durumlarına göre renkli badge'ler

### İş Akışı ve Geçiş İyileştirmeleri
- **Wizard Türkçeleştirme**: İş akışı geçiş wizard'ı tamamen Türkçeleştirildi
- **Geçiş Kısıtlaması**: Sadece initial state'den geçiş yapılabilir hale getirildi
- **Detaylı Loglama**: PO line oluşturma için gelişmiş loglama eklendi

### Tedarikçi Başvuru Sistemi
- **IBAN Validasyonu**: Başvuru gönderiminde IBAN format kontrolü
- **Doküman Önizleme**: PDF viewer widget ile doküman önizleme
- **Partner Yönetimi**: VKN kontrolü ile duplicate partner önleme
- **Portal Kullanıcı**: Otomatik portal kullanıcı oluşturma ve yetkilendirme
- **E-posta Bildirimleri**: Başvuru onayı ve teklif çağrısı için email şablonları

### Teknik İyileştirmeler
- **UoM Validasyonu**: SAT import esnasında UoM kategori uyumsuzluğu kontrolü
- **Para Birimi Senkronizasyonu**: Tender ve tender line'lar arası currency sync
- **Odoo 18 Uyumluluğu**: `notify_by_email` parametresi kaldırıldı
- **Display Type Düzeltmesi**: Section ve note satırları için Odoo 18 standardı
- **Workflow Geçmişi**: İlk durum için otomatik history kaydı ve end_time stored field