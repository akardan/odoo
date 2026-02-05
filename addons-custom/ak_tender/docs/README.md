# İLKOis İhale Yönetim Sistemi - Dokümantasyon

**Versiyon:** 1.0  
**Tarih:** 3 Şubat 2026  
**Platform:** Odoo 18 CE  
**Modül:** ak_tender

---

## 📚 Dokümantasyon Yapısı

Bu klasör, İLKOis İhale Yönetim Sistemi'nin tüm dokümantasyonunu içermektedir.

---

## 🎯 Ana Dokümantasyon

### [ANA_DOKUMAN.md](ANA_DOKUMAN.md)
**Kapsamlı Ana Dokümantasyon**

İLKOis sisteminin tüm yönlerini kapsayan ana referans dokümanı:
- Sistem mimarisi
- İhale tipleri ve özellikleri
- İş akışları
- Temel modüller
- Entegrasyonlar
- Güvenlik ve yetkilendirme
- Raporlama ve analiz
- Teknik detaylar

**Hedef Kullanıcı:** Tüm paydaşlar, yöneticiler, geliştiriciler

---

## 👥 Kullanıcı Kılavuzları

### [Kullanıcı Klavuzu V.1.0/](Kullanıcı%20Klavuzu%20V.1.0/)

Rol bazlı detaylı kullanıcı kılavuzları:

#### 1. [Talep Girişi Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/01_TALEP_GIRISI_KILAVUZU.md)
- **Hedef:** Tüm çalışanlar
- **İçerik:** Manuel talep oluşturma, onay süreci, durum takibi

#### 2. [İhale Yöneticisi Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/02_IHALE_YONETICISI_KILAVUZU.md)
- **Hedef:** İhale yöneticileri, Satın alma uzmanları
- **İçerik:** İhale oluşturma, teklif değerlendirme, onay süreçleri

#### 3. [Tedarikçi Portal Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/03_TEDARIKCI_PORTAL_KILAVUZU.md)
- **Hedef:** Tedarikçiler
- **İçerik:** Portal erişimi, teklif verme, sipariş takibi

#### 4. [Tedarikçi Başvuru Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/04_TEDARIKCI_BASVURU_KILAVUZU.md)
- **Hedef:** Yeni tedarikçiler
- **İçerik:** Başvuru süreci, belge yükleme, durum takibi

#### 5. [Sistem Yöneticisi Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/05_SISTEM_YONETICISI_KILAVUZU.md)
- **Hedef:** Sistem yöneticileri, IT ekibi
- **İçerik:** Sistem yapılandırması, kullanıcı yönetimi, entegrasyon ayarları

---

## 🔧 Teknik Dokümantasyon

### Entegrasyon ve Otomasyon

#### [SAT Import Automation](sat_import_automation.md)
- Otomatik SAT import süreci
- İhale tipi belirleme kuralları
- Excel format yapısı
- Hata yönetimi

#### [OAuth2 Email Import](OAUTH2_EMAIL_IMPORT_README.md)
- Microsoft Graph API entegrasyonu
- Azure AD yapılandırması
- Email işleme süreci
- Güvenlik notları

#### [Purchase Order Group Integration](purchase_order_group_integration.md)
- Alternatif teklif yönetimi (kaldırıldı)
- Geçiş kılavuzu

### Veri Yönetimi

#### [Geçmiş Dönem PO Import](HISTORICAL_PO_IMPORT_TR.md)
- Excel format yapısı
- Import süreci
- Superset analiz boyutları
- Kullanım örnekleri

#### [Ekonomik Veri Yönetimi](ECONOMIC_DATA_MANAGEMENT_EMAIL.md)
- NPV hesaplamaları
- Döviz kuru yönetimi
- Finans bölümü işbirliği
- Veri kaynakları

### İş Kuralları

#### [İhale Tipi Kuralları](TENDER_TYPE_RULES_README.md)
- Model tabanlı kural yönetimi
- Öncelik sistemi
- Özel kurallar
- SAT entegrasyonu

---

## 📊 Analiz ve İyileştirme Dokümanları

### [Erhan Tosun Quick Wins Summary](ERHAN_TOSUN_QUICK_WINS_SUMMARY.md)
- Hızlı iyileştirmeler özeti
- Öncelik matrisi
- Implementasyon planı
- Beklenen sonuçlar

### [Erhan Tosun UX Improvements](ERHAN_TOSUN_UX_IMPROVEMENTS_TECHNICAL_ANALYSIS.md)
- UX iyileştirmeleri teknik analizi
- 17 maddelik talep listesi
- Çözüm önerileri
- Test senaryoları

### [İLKOis Presentation Document](ILKOIS_PRESENTATION_DOCUMENT.md)
- Detaylı sunum dokümanı
- Sistem özellikleri
- Kullanıcı arayüzü
- Test ortamı bilgileri

---

## 📖 Kavramsal Analiz

### [İLKOis Kavramsal Analiz Dokümanı V1.1](İLKOis%20-%20Kavramsal%20Analiz%20Dokümanı%20%20V1.1.txt)
- İş alanı analizi
- Mevcut durum analizi
- Kavramsal model
- İş süreçleri analizi
- Paydaş analizi
- Risk analizi
- Sonuç ve öneriler

---

## 🗂️ Dokümantasyon Kategorileri

### Kullanıcı Rolüne Göre

| Rol | Önerilen Dokümanlar |
|-----|---------------------|
| **Departman Çalışanı** | Talep Girişi Kılavuzu |
| **Satın Alma Uzmanı** | Talep Girişi, İhale Yöneticisi Kılavuzları |
| **İhale Yöneticisi** | İhale Yöneticisi, Sistem Yöneticisi Kılavuzları |
| **Tedarikçi** | Tedarikçi Portal, Tedarikçi Başvuru Kılavuzları |
| **Sistem Yöneticisi** | Sistem Yöneticisi Kılavuzu, Tüm Teknik Dokümanlar |
| **Üst Yönetim** | Ana Doküman, Presentation Document |
| **Geliştirici** | Ana Doküman, Tüm Teknik Dokümanlar |

### İçerik Tipine Göre

#### 📘 Kullanım Kılavuzları
- Adım adım talimatlar
- Ekran görüntüleri
- Örnek senaryolar
- Sık sorulan sorular

#### 🔧 Teknik Dokümanlar
- API dokümantasyonu
- Entegrasyon kılavuzları
- Veri modelleri
- Güvenlik yapılandırması

#### 📊 Analiz Dokümanları
- İş gereksinimleri
- Kullanıcı geri bildirimleri
- İyileştirme önerileri
- Performans metrikleri

#### 📋 Referans Dokümanları
- Sistem mimarisi
- İş akışları
- Veri yapıları
- Konfigürasyon ayarları

---

## 🔍 Hızlı Erişim

### Sık Kullanılan Konular

**İhale Oluşturma:**
- [İhale Yöneticisi Kılavuzu - Bölüm 2](Kullanıcı%20Klavuzu%20V.1.0/02_IHALE_YONETICISI_KILAVUZU.md#2-ihale-oluşturma)

**Teklif Verme:**
- [Tedarikçi Portal Kılavuzu - Bölüm 4](Kullanıcı%20Klavuzu%20V.1.0/03_TEDARIKCI_PORTAL_KILAVUZU.md#4-teklif-verme)

**SAT Import:**
- [SAT Import Automation](sat_import_automation.md)

**Email Yapılandırması:**
- [OAuth2 Email Import](OAUTH2_EMAIL_IMPORT_README.md)

**NPV Hesaplamaları:**
- [Ekonomik Veri Yönetimi](ECONOMIC_DATA_MANAGEMENT_EMAIL.md)

---

## 📝 Dokümantasyon Standartları

### Dosya Adlandırma

- **Türkçe Dokümanlar**: BÜYÜK_HARF_ALT_ÇIZGI.md
- **İngilizce Dokümanlar**: lowercase_underscore.md
- **Kullanıcı Kılavuzları**: 0X_AÇIKLAYICI_AD_KILAVUZU.md

### Versiyon Kontrolü

Her dokümanda bulunması gerekenler:
- Versiyon numarası
- Son güncelleme tarihi
- Hazırlayan
- Değişiklik geçmişi

### Markdown Formatı

- Başlıklar: # ## ### hiyerarşisi
- Kod blokları: ```language
- Tablolar: Markdown table formatı
- Linkler: [Metin](url)
- Vurgulama: **kalın**, *italik*, `kod`

---

## 🔄 Güncelleme Politikası

### Güncelleme Sıklığı

- **Majör Güncellemeler**: Yeni versiyon çıkışında
- **Minör Güncellemeler**: Özellik eklendiğinde
- **Düzeltmeler**: Hata tespit edildiğinde

### Versiyon Numaralandırma

- **X.0**: Majör değişiklikler
- **X.Y**: Minör değişiklikler
- **X.Y.Z**: Düzeltmeler

---

## 💡 Katkıda Bulunma

### Dokümantasyon İyileştirme

Dokümantasyonu geliştirmek için:

1. Eksik bilgileri bildirin
2. Anlaşılmayan bölümleri işaretleyin
3. Yeni örnek senaryolar önerin
4. İyileştirme önerileri gönderin

### İletişim

**Dokümantasyon Sorumlusu:**
- Email: docs@kardan.digital

**Teknik Destek:**
- Email: support@kardan.digital
- Çalışma Saatleri: Pazartesi-Cuma 09:00-18:00

---

## 📊 Dokümantasyon İstatistikleri

| Kategori | Dosya Sayısı | Toplam Sayfa |
|----------|--------------|--------------|
| Ana Doküman | 1 | 50+ |
| Kullanıcı Kılavuzları | 5 | 100+ |
| Teknik Dokümanlar | 6 | 60+ |
| Analiz Dokümanları | 3 | 80+ |
| **TOPLAM** | **15** | **290+** |

---

## 🔗 İlgili Kaynaklar

### Resmi Dokümantasyon
- [Odoo 18 Documentation](https://www.odoo.com/documentation/18.0/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Eğitim Materyalleri
- Video eğitimler
- Webinarlar
- Örnek senaryolar

### Topluluk
- Forum
- Stack Overflow
- LinkedIn grubu

---

## 📅 Son Güncellemeler

| Tarih | Doküman | Değişiklik |
|-------|---------|------------|
| 2026-02-03 | ANA_DOKUMAN.md | İlk versiyon oluşturuldu |
| 2026-02-03 | Kullanıcı Kılavuzları | 5 kılavuz oluşturuldu |
| 2026-02-03 | README.md | Dokümantasyon indeksi oluşturuldu |

---

**Son Güncelleme**: 3 Şubat 2026  
**Versiyon**: 1.0  
**Hazırlayan**: Kardan.Digital  
**Durum**: Aktif

---

**© 2023-2026 Kardan.Digital - Tüm hakları saklıdır.**
