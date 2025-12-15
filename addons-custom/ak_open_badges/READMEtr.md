# Dijital Sertifikalar & Rozetler

## Genel Bakış

**Dijital Sertifikalar & Rozetler**, dijital sertifikalar ve Açık Rozetler (Open Badges) yönetimi ve verme işlemleri için kapsamlı bir Odoo 18 modülüdür. Modül, [Open Badges 2.0 Spesifikasyonu](https://www.imsglobal.org/sites/default/files/Badges/OBv2p0Final/index.html) ile tamamen uyumludur ve dijital kimlik bilgilerini oluşturma, verme ve doğrulama için eksiksiz bir çözüm sunar.

![Versiyon](https://img.shields.io/badge/versiyon-18.0.1.0-blue)
![Lisans](https://img.shields.io/badge/lisans-LGPL--3-green)
![Odoo](https://img.shields.io/badge/Odoo-18.0%20CE-purple)

**Geliştirici:** Kardan.Digital  
**Website:** [https://kardan.digital](https://kardan.digital)

---

## Dijital Sertifika vs. Geleneksel Sertifika

### Geleneksel (Kağıt) Sertifikalar:
- 📄 Fiziksel belge olarak basılır ve saklanır
- ✋ Elle teslim edilir veya posta ile gönderilir
- 📦 Fiziksel alan gerektirir ve zamanla yıpranabilir
- ❌ Kaybolabilir, yırtılabilir veya tahrif edilebilir
- 🕐 Doğrulama zor ve zaman alıcıdır
- 💰 Basım, kağıt ve kargo maliyetleri yüksektir
- 🌍 Paylaşımı ve uluslararası tanınması sınırlıdır

### Dijital Sertifikalar (Bu Modül):
- 💻 Elektronik format (PDF + metadata)
- ⚡ Anında e-posta ile teslim edilir
- ☁️ Bulutta saklanır, fiziksel alan gerektirmez
- 🔒 Kriptografik imzalarla korunur ve sahteciliğe karşı güvenlidir
- ✅ QR kod ile saniyeler içinde doğrulanabilir
- 🆓 Sıfır basım maliyeti, sınırsız kopyalama
- 🌐 Küresel olarak paylaşılabilir ve Open Badges 2.0 standardı ile evrensel tanınırlık
- 📊 Otomatik raporlama ve takip
- 🔄 Güncellenebilir ve iptal edilebilir
- 🎯 LinkedIn, dijital CV ve profesyonel platformlara entegre edilebilir

**Kısacası:** Dijital sertifikalar, geleneksel sertifikaların tüm işlevselliğini sunmanın yanı sıra güvenlik, doğrulanabilirlik, maliyet etkinliği ve erişilebilirlik açısından önemli avantajlar sağlar.

---

## Özellikler

### 🏆 Temel İşlevsellik
- **Open Badges 2.0 Uyumlu** - Uluslararası Open Badges spesifikasyonu ile tam uyumluluk
- **Dijital Sertifika Verme** - Profesyonel dijital sertifikalar oluşturma ve verme
- **Rozet Yönetimi** - Özel kriterlerle rozet şablonları tasarlama ve yönetme
- **Çok Dilli Destek** - Sertifikalar için birincil ve ikincil dil desteği
- **Doğrulama Sistemi** - QR kod tabanlı sertifika doğrulama

### 🎯 Rozet Yönetimi
- **Rozet Sınıfları** - Özel kriterlerle tekrar kullanılabilir rozet şablonları oluşturma
- **Rozet Verenler** - Markalama ve imzalarla veren kuruluşları yönetme
- **Rozet Tipleri** - Rozetleri kategorize etme (Başarı, Katılım, Yetkinlik vb.)
- **Rozet Etiketleri** - Rozetleri özel etiketlerle organize etme
- **Rozet Hizalamaları** - Rozetleri eğitim çerçeveleri ve standartlarıyla ilişkilendirme

### 🔐 Güvenlik & Doğrulama
- **Kriptografik İmzalama** - Rozet özgünlüğü için RSA tabanlı dijital imzalar
- **QR Kod Doğrulama** - QR kodlar aracılığıyla hızlı doğrulama
- **Açık Anahtar Altyapısı** - Verenler için otomatik anahtar çifti oluşturma
- **Hashlenmiş Alıcı Kimlikleri** - Gizliliği koruyan alıcı tanımlama
- **Benzersiz Rozet ID'leri** - Her rozet için UUID tabanlı benzersiz tanımlayıcılar

### 📄 Sertifika Oluşturma
- **PDF Sertifikalar** - Profesyonel PDF sertifika üretimi
- **Özel Şablonlar** - Özel arka planlarla çoklu sertifika şablonları
- **Özel Fontlar** - Özel TrueType fontları desteği (PT Sans, Pirata One, Ephesis)
- **İkili İmza** - İki imzalı sertifikalar için destek
- **İki Dilli Sertifikalar** - İki dilde sertifika desteği

### 🔗 Entegrasyon
- **Etkinlik Entegrasyonu** - Etkinlik katılımcıları için rozet verme
- **E-Öğrenme Entegrasyonu** - Kurs tamamlama için rozet ödüllendirme (website_slides)
- **İletişim Yönetimi** - Rozetleri kişiler/partnerlerle ilişkilendirme
- **E-posta Bildirimleri** - Sertifikaların otomatik e-posta ile iletimi

### 📊 Raporlama & Yönetim
- **Rozet Raporları** - Verilen rozetler için raporlar oluşturma
- **Kanıt Takibi** - Rozet iddialarına kanıt ekleme
- **Aktivite Takibi** - Posta entegrasyonu ile tam denetim izi
- **Toplu İşlemler** - Birden fazla alıcıya sertifika verme

---

## Kurulum

### Ön Koşullar

Aşağıdaki Odoo modüllerinin yüklü olduğundan emin olun:
- `base`
- `mail`
- `web`
- `event`
- `website_event`
- `website_slides`
- `contacts`

### Python Bağımlılıkları

Modül aşağıdaki Python paketlerini gerektirir:

```bash
pip install cryptography reportlab
```

### Kurulum Adımları

1. Modülü Odoo eklentiler dizininize kopyalayın:
   ```bash
   cp -r ak_open_badges /opt/odoo18/addons-custom/
   ```

2. Eklenti listesini güncelleyin:
   - **Uygulamalar** menüsüne gidin
   - **Uygulama Listesini Güncelle**'ye tıklayın
   - "Digital Certificates & Badges" arayın

3. Modülü kurun:
   - Modül kartında **Kur**'a tıklayın

---

## Yapılandırma

### 1. Rozet Veren Yapılandırma

**Sertifikalar > Yapılandırma > Verenler** bölümüne gidin

1. Yeni bir veren kaydı oluşturun
2. Gerekli bilgileri doldurun:
   - Ad (çevrilebilir)
   - Açıklama (çevrilebilir)
   - URL (veren web sitesi)
   - E-posta (iletişim e-postası)
   - Veren Logosu
   - Veren İmzası (opsiyonel)
   - Veren Ünvanı (örn. "Müdür", "CEO")

3. Kriptografik anahtarlar oluşturun:
   - RSA anahtarları oluşturmak için **Anahtar Çifti Oluştur** düğmesine tıklayın
   - Açık anahtar rozet doğrulama için kullanılacak
   - Özel anahtar imzalama için kullanılır (yalnızca yöneticiler)

### 2. Rozet Tipleri Oluşturma

**Sertifikalar > Yapılandırma > Rozet Tipleri** bölümüne gidin

Rozetleriniz için kategoriler oluşturun (örnekler dahil):
- Başarı Rozeti
- Katılım Rozeti
- Yetkinlik Rozeti
- Tamamlama Sertifikası
- Başarı Sertifikası

### 3. Rozet Sınıfları (Şablonlar) Oluşturma

**Sertifikalar > Rozet Sınıfları** bölümüne gidin

1. Yeni bir rozet sınıfı oluşturun
2. Yapılandırın:
   - **Ad** - Rozet başlığı (çevrilebilir)
   - **Açıklama** - Rozet açıklaması (çevrilebilir)
   - **Rozet Tipi** - Rozet kategorisi seçin
   - **Veren** - Veren kuruluşu seçin
   - **Görsel** - Rozet görselini yükleyin (PNG önerilir)
   - **Kriterler** - Rozeti kazanma kriterlerini tanımlayın
   - **Birincil Dil** - Sertifika için ana dil
   - **İkincil Dil** - Opsiyonel ikinci dil
   - **Etiketler** - İlgili etiketleri ekleyin

### 4. Sertifika Şablonlarını Yapılandırma

Modül, özel arka planlar ve fontlarla önceden yapılandırılmış sertifika şablonları içerir. Şablonları şurada özelleştirebilirsiniz:
- [`data/certificate_template.xml`](data/certificate_template.xml:1)

### 5. Sistem Parametreleri

Doğru rozet doğrulaması için temel URL'yi yapılandırın:
- **Ayarlar > Teknik > Parametreler > Sistem Parametreleri**'ne gidin
- `web.base.url` parametresinin domaininize doğru ayarlandığından emin olun

---

## Kullanım

### Rozet Verme

#### Manuel Verme

**Sertifikalar > Rozet İddiaları** bölümüne gidin

1. **Oluştur**'a tıklayın
2. Seçin:
   - **Sertifika Sınıfı** - Kullanılacak rozet şablonu
   - **Alıcı** - Kişiler/partnerlerden seçin
   - **Veriliş Tarihi** - Varsayılan olarak mevcut tarih
   - **Son Kullanma Tarihi** - Opsiyonel son kullanma
   - **Kanıt** - Destekleyici kanıt ekleyin (opsiyonel)
   - **Dil** - Sertifika dilini seçin

3. **Kaydet**'e tıklayın
4. Sertifikayı oluşturmak için **Rozet Ver**'e tıklayın
5. Alıcıyı bilgilendirmek için **E-posta ile Rozet Gönder**'e tıklayın

#### Toplu Verme

Birden fazla rozet vermek için (örn. kurs tamamlama):
1. Etkinlikler veya E-Öğrenme modülleriyle entegrasyonu kullanın
2. Otomatik rozet verme için otomasyon kurallarını yapılandırın
3. Etkinlik katılımcılarından veya kurs tamamlamalarından toplu olarak rozetler oluşturun

### Rozet Doğrulama

#### QR Kod Doğrulama

1. Sertifikadaki QR kodu tarayın
2. Doğrulama sayfası şunları gösterecektir:
   - Rozet detayları
   - Alıcı bilgileri
   - Veriliş tarihi ve son kullanma
   - Veren bilgileri
   - Doğrulama durumu

#### Manuel Doğrulama

Şu adrese gidin: `https://sizdomain.com/badge/verify/<badge_uid>`

### Rozet Detaylarını Görüntüleme

Genel rozet sayfası: `https://sizdomain.com/badge/<badge_uid>`

Bu sayfa şunları gösterir:
- Rozet sınıfı bilgileri
- Veriliş detayları
- Doğrulama durumu
- Kanıt (varsa)
- Open Badges JSON-LD metaverileri

### Sertifikaları İndirme

Alıcılar sertifikalarını PDF formatında indirebilir:
- Rozet detay sayfasından
- E-posta bildiriminden
- Partner portalı üzerinden

---

## Teknik Detaylar

### Modeller

#### [`badge.issuer`](models/badge_issuer.py:1)
Kriptografik anahtar çiftleriyle rozet veren kuruluşları yönetir.

**Ana Alanlar:**
- `name`, `description` - Çevrilebilir veren bilgileri
- `url`, `email` - İletişim bilgileri
- `public_key`, `private_key` - İmzalama için RSA anahtar çifti
- `signature`, `image` - Markalama varlıkları

#### [`badge.class`](models/badge_class.py:1)
Kriterler ve metaverilerle rozet şablonlarını tanımlar.

**Ana Alanlar:**
- `name`, `description` - Çevrilebilir rozet bilgileri
- `badge_type_id` - Rozet kategorisi
- `issuer_id` - Veren kuruluş
- `criteria_url`, `criteria_narrative` - Kazanma kriterleri
- `primary_lang`, `secondary_lang` - Dil ayarları

#### [`badge.assertion`](models/badge_assertion.py:1)
Belirli alıcılara verilmiş rozetleri temsil eder.

**Ana Alanlar:**
- `badge_class_id` - Rozet şablonu
- `recipient_id` - Rozet alıcısı (partner)
- `issuance_date`, `expiration_date` - Geçerlilik süresi
- `uid` - Benzersiz rozet tanımlayıcısı
- `verification_key` - Kriptografik doğrulama
- `state` - Rozet durumu (taslak, verildi, iptal edildi)

#### [`badge.type`](models/badge_type.py:1)
Rozetleri tiplere göre kategorize eder.

#### [`badge.tag`](models/badge_tag.py:1)
Rozet organizasyonu için etiketleme işlevselliği sağlar.

#### [`badge.alignment`](models/badge_alignment.py:1)
Rozetleri eğitim çerçeveleri ve standartlarıyla ilişkilendirir.

#### [`badge.evidence`](models/badge_evidence.py:1)
Rozet iddialarına destekleyici kanıtlar ekler.

### Kontrolörler

#### [`main.py`](controllers/main.py:1)
Şunlar için web rotalarını yönetir:
- Rozet doğrulama sayfaları
- Genel rozet görüntüleme
- QR kod oluşturma
- Open Badges uyumluluğu için JSON-LD uç noktaları

### Güvenlik

[`security/open_badges_security.xml`](security/open_badges_security.xml:1) içinde tanımlanan kullanıcı grupları:
- **Rozet Kullanıcısı** - Rozetleri görüntüleyebilir
- **Rozet Yöneticisi** - Rozet oluşturabilir ve verebilir
- **Rozet Yöneticisi** - Veren yönetimi dahil tam erişim

Erişim hakları [`security/ir.model.access.csv`](security/ir.model.access.csv:1) içinde yapılandırılmıştır

### Raporlar

Şunlarla PDF sertifika oluşturma:
- Özel arka planlar (desen şablonları)
- Özel fontlar ([`static/fonts/`](static/fonts/) içinde TrueType fontları)
- Doğrulama için QR kodlar
- İki dilli destek
- İkili imzalar

Rapor şablonları: [`reports/badge_reports.xml`](reports/badge_reports.xml:1)

### Veri Dosyaları

- [`data/badge_sequence.xml`](data/badge_sequence.xml:1) - Sertifika numaralandırma dizileri
- [`data/badge_type_data.xml`](data/badge_type_data.xml:1) - Varsayılan rozet tipleri
- [`data/certificate_template.xml`](data/certificate_template.xml:1) - Sertifika şablonları
- [`data/mail_template_data.xml`](data/mail_template_data.xml:1) - E-posta şablonları

### Görünümler

- [`views/badge_issuer_views.xml`](views/badge_issuer_views.xml:1) - Veren yönetimi
- [`views/badge_class_views.xml`](views/badge_class_views.xml:1) - Rozet şablonu yönetimi
- [`views/badge_assertion_views.xml`](views/badge_assertion_views.xml:1) - Rozet verme
- [`views/templates.xml`](views/templates.xml:1) - Web sitesi şablonları
- [`views/menu_views.xml`](views/menu_views.xml:1) - Menü yapısı

---

## Open Badges 2.0 Uyumluluğu

Bu modül Open Badges 2.0 spesifikasyonunu tamamen uygular:

### JSON-LD Desteği
Tüm rozetler şu adreslerde erişilebilir uygun JSON-LD metaverileri içerir:
- Rozet sınıfı: `/badge/class/<id>/json`
- Rozet iddiası: `/badge/<uid>/json`
- Veren: `/badge/issuer/<id>/json`

### Gerekli Özellikler
- `@context`: "https://w3id.org/openbadges/v2"
- `type`: Assertion, BadgeClass veya Issuer
- `id`: Benzersiz tanımlayıcı URL
- `badge`: BadgeClass'a bağlantı
- `recipient`: Hashlenmiş veya düz alıcı kimliği
- `issuedOn`: ISO 8601 tarih-saat
- `verification`: Doğrulama yöntemi ve imza

### Doğrulama Yöntemleri
- Barındırılan doğrulama (birincil yöntem)
- RSA imzalarıyla imzalı rozetler
- Açık anahtar doğrulama

---

## Uluslararasılaştırma

Modül şunlar için çeviriler içerir:
- **İngilizce** (en_US) - [`i18n/en_US.po`](i18n/en_US.po:1)
- **Türkçe** (tr_TR) - [`i18n/tr.po`](i18n/tr.po:1)

Kullanıcıya yönelik tüm dizeler çevrilebilir. Sertifikalar birincil ve ikincil dillerle iki dilli çıktıyı destekler.

---

## Özelleştirme

### Özel Sertifika Arka Planları

[`static/src/img/`](static/src/img/) dizinine özel arka plan görüntüleri ekleyin ve bunları sertifika şablonlarında referans gösterin.

### Özel Fontlar

TrueType fontlarını (.ttf) [`static/fonts/`](static/fonts/) dizinine ekleyin ve bunları sertifika oluşturma kodunda kaydedin.

### Özel Rozet Kriterleri

Rozet sınıflarında özel kriterler tanımlayın ve rozet iddiası modellerinde doğrulama mantığını uygulayın.

### Diğer Modüllerle Entegrasyon

Modül şunlarla entegre edilmek üzere genişletilebilir:
- İK modülleri (çalışan eğitim sertifikaları)
- Satış (müşteri sertifikasyonu)
- Projeler (proje tamamlama rozetleri)
- Özel modüller (alana özgü rozetler)

---

## Sorun Giderme

### Sertifikalar Oluşturulmuyor

1. Python bağımlılıklarının yüklü olduğunu doğrulayın:
   ```bash
   pip install cryptography reportlab
   ```

2. Font dizini için dosya izinlerini kontrol edin
3. Temel URL'nin doğru yapılandırıldığını doğrulayın

### Doğrulama Çalışmıyor

1. `web.base.url` sistem parametresinin ayarlandığından emin olun
2. HTTPS kullanılıyorsa SSL sertifikasını kontrol edin
3. Rozet UID'sinin doğru olduğunu doğrulayın

### E-posta Gönderilmiyor

1. Odoo'da giden posta sunucusunu yapılandırın
2. [`data/mail_template_data.xml`](data/mail_template_data.xml:1) içinde e-posta şablonunu kontrol edin
3. Alıcı e-posta adreslerini doğrulayın

---

## Lisans

Bu modül **LGPL-3** (GNU Lesser General Public License v3.0) altında lisanslanmıştır

---

## Katkıda Bulunanlar

**Geliştirici:** Kardan.Digital  
**E-posta:** info@kardan.digital  
**Website:** https://kardan.digital

### Bağımlılıklar
- **Odoo** - Açık kaynak ERP platformu
- **ReportLab** - PDF oluşturma kütüphanesi
- **Cryptography** - Python kriptografi araç seti
- **Open Badges** - IMS Global Learning Consortium spesifikasyonu

---

## Destek

Destek, hata raporları veya özellik istekleri için:
- Ziyaret edin: https://kardan.digital
- E-posta: info@kardan.digital

---

## Değişiklik Günlüğü

### Versiyon 18.0.1.0
- Odoo 18 CE için ilk sürüm
- Open Badges 2.0 uyumluluğu
- Çok dilli sertifika desteği
- QR kod doğrulama sistemi
- Etkinlik ve e-öğrenme entegrasyonu
- Rozetlerin kriptografik imzalanması
- Özel şablonlarla PDF sertifika oluşturma

---

## Ekran Görüntüleri

Modül şunları içerir:
- Modern rozet yönetimi arayüzü
- Profesyonel sertifika şablonları
- Mobil uyumlu doğrulama sayfaları
- Kapsamlı raporlama panoları

Ekran görüntüleri ve demolar için Odoo Uygulamalar Mağazası'ndaki modülü ziyaret edin veya Kardan.Digital ile iletişime geçin.
