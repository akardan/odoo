# İhale Modülü (ak_tender)

## Genel Bakış

Bu modül, çok aşamalı satın alma ihale süreçlerini Odoo üzerinde yönetmek için tasarlanmıştır. Modül, iş akışı (workflow) tabanlı bir yaklaşım kullanarak ihale süreçlerini yönetir ve ihale ile satın alma siparişi işlevselliğinde sürekli iyileştirmeler yapılmıştır.

## Özellikler

- ERP Entegrasyon (simülasyon)
- SAT içe aktar Fonksiyonelliği
- Çok Aşamalı İhale Süreci (1. Teklif Toplama, Hedef Fiyat, 2. Teklif Toplama)
- Tedarikçi Portal Entegrasyonu (veri girişi temsili)
- Onay Mekanizması entegrasyonu (Approvals modülü ile)
- Hedef Fiyat Belirleme Sihirbazı (sunucu eylemi ile erişim)
- Satın Alma Siparişi Oluşturma ve Toplu E-posta Gönderme Sunucu Eylemleri
- İş Akışı Geçiş Sihirbazında eylemlerin görüntülenmesi
- Raporlama ve Analiz altyapısı
- İhale tiplerine göre ilerleme çubuğu renklendirmesi
- İhale Kalemleri yönetimi
- Odoo'nun temel satın alma (purchase.order) modülü ile entegrasyon
- Farklı ihale tipleri için görsel yönetim özellikleri (direct, indirect, mice, promotion)
- İhale şablonları (tüm ihale tipleri için)
- Toplu satın alma optimizasyonu (indirect ve promotion ihaleleri için)
- Acil talep desteği (indirect ve promotion ihaleleri için)
- Ekonomik veri entegrasyonu (promotion ihaleleri için)
- Dinamik tedarikçi ekleme fonksiyonu
- Coğrafi tedarikçi filtreleme
- Tedarikçi Karşılaştırma Raporu (en düşük fiyat vurgulama ve NPV hesaplama)
- Gelişmiş Portal Arayüzü (tedarikçiler için teklif düzenleme)
- NPV (Net Bugünkü Değer) hesaplamaları
- Garanti süresi yönetimi
- Rol tabanlı erişim kontrolü (RBAC) ile güvenlik yönetimi

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
- `approved`: Onaylandı
- `done`: Tamamlandı
- `cancel`: İptal Edildi

### İş Akışı Geçişleri

İhale durumları arasındaki geçişler, iş akışı tanımında belirtilen geçişler (transitions) üzerinden gerçekleştirilir. Her geçiş, belirli koşullara bağlı olabilir ve geçiş sırasında çeşitli aksiyonlar tetiklenebilir.

## Teknik Notlar

### Deprecated Fields

- `state` alanı artık kullanılmamaktadır. Bunun yerine `workflow_current_state_id` ve `workflow_state` alanları kullanılmalıdır.
- `tender_results` yerine `purchase_order_ids` kullanılmaktadır.

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

## Gelişmiş Portal Arayüzü

Tedarikçiler için geliştirilmiş portal arayüzü, aşağıdaki özelliklere sahiptir:

- Teklif fiyatlarını doğrudan portal üzerinden düzenleme
- Teslimat tarihlerini belirleme
- Garanti süresi seçimi
- İndirim oranı belirtme
- Alternatif malzeme önerileri sunma
- Vergi seçimi yapabilme
- Toplu değişiklik kaydetme
- İhale listesi ve teklif formu şablonları kaldırıldı, ilgili Odoo sayfalara yönlendirme yapıldı.

## NPV Hesaplamaları

NPV (Net Bugünkü Değer) hesaplamaları, farklı tedarikçilerden gelen tekliflerin finansal karşılaştırmasını yapmak için kullanılır. Bu özellik, aşağıdaki avantajları sağlar:

- Farklı ödeme koşullarına göre bölünmüş ödeme desteği ile NPV hesaplamaları
- Uzun vadeli satın almalarda gerçek maliyeti hesaplama
- İskonto oranı belirleme ve ekonomik faktörleri dikkate alma