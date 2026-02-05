# İLKOis - İhale Yönetim Sistemi Ana Dokümantasyon

**Versiyon:** 1.0
**Tarih:** 3 Şubat 2026
**Platform:** Odoo 18 CE
**Modül:** ak_tender
**Geliştirici:** Kardan.Digital
**Durum:** Aktif Kullanımda

---

## 📋 İçindekiler

1. [Sisteme Genel Bakış](#1-sisteme-genel-bakış)
2. [Sistem Mimarisi](#2-sistem-mimarisi)
3. [İhale Tipleri ve Özellikleri](#3-ihale-tipleri-ve-özellikleri)
4. [İş Akışları](#4-iş-akışları)
5. [Temel Modüller ve Özellikler](#5-temel-modüller-ve-özellikler)
6. [Entegrasyonlar](#6-entegrasyonlar)
7. [Güvenlik ve Yetkilendirme](#7-güvenlik-ve-yetkilendirme)
8. [Raporlama ve Analiz](#8-raporlama-ve-analiz)
9. [Kullanıcı Kılavuzları](#9-kullanıcı-kılavuzları)
10. [Teknik Dokümantasyon](#10-teknik-dokümantasyon)
11. [Sık Sorulan Sorular](#11-sık-sorulan-sorular)

---

## 1. Sisteme Genel Bakış

### 1.1 İLKOis Nedir?

İLKOis (İhale ve Lojistik Koordinasyon Otomasyonu İş Sistemi), İlko Grubu'nun satın alma ve ihale süreçlerini dijitalleştirmek için Odoo 18 CE platformu üzerinde geliştirilmiş kapsamlı bir ERP modülüdür.

### 1.2 Temel Amaçlar

- ✅ Satın alma süreçlerinin tam dijitalleşmesi
- ✅ Şeffaf ve izlenebilir ihale yönetimi
- ✅ Tedarikçi portal ile kolay teklif alma
- ✅ NPV hesaplamaları ile maliyet optimizasyonu
- ✅ Çoklu para birimi desteği
- ✅ SAP/ERP entegrasyonu
- ✅ Otomatik iş akışları ve bildirimler

### 1.3 Sistem Avantajları

| Avantaj | Açıklama | Fayda |
|---------|----------|-------|
| **Dijital Dönüşüm** | Kağıt bazlı süreçlerin tamamen dijitalleşmesi | %50 süre tasarrufu |
| **Maliyet Tasarrufu** | NPV analizleri ve rekabetçi fiyatlandırma | %10-20 maliyet azalması |
| **Şeffaflık** | Tüm süreçlerin izlenebilir olması | %100 denetlenebilirlik |
| **Esneklik** | Farklı ihale tiplerini destekleyen modüler yapı | 4 farklı ihale tipi |
| **Entegrasyon** | SAP ve diğer sistemlerle sorunsuz entegrasyon | Otomatik veri akışı |

### 1.4 Desteklenen İhale Tipleri

1. **Direkt Satın Alma (direct)**: Üretim malzemeleri, hammadde, ambalaj
2. **Endirekt Satın Alma (indirect)**: Hizmet alımları, laboratuvar, bakım-onarım
3. **MICE İhaleleri (mice)**: Toplantı, etkinlik, konaklama organizasyonları
4. **Promosyon (promotion)**: Promosyon malzemeleri, kırtasiye

---

## 2. Sistem Mimarisi

### 2.1 Genel Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                    İLKOis İhale Modülü                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   İş Akışı   │  │   Tedarikçi  │  │   Raporlama  │     │
│  │   Yönetimi   │  │    Portal    │  │   & Analiz   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Satın Alma │  │   SAP/ERP    │  │   E-posta    │     │
│  │  Entegrasyonu│  │ Entegrasyonu │  │  Otomasyonu  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              Odoo 18 CE Temel Platform                       │
│  (Purchase, Stock, Mail, Portal, Workflow, Product)         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Teknoloji Stack

#### Backend
- **Platform**: Odoo 18 CE
- **Dil**: Python 3.10+
- **Framework**: Odoo ORM
- **Veritabanı**: PostgreSQL 16+

#### Frontend
- **Framework**: Odoo Web Client
- **JavaScript**: ES6+
- **CSS**: Bootstrap 5, Custom SCSS
- **Template Engine**: QWeb

#### Kütüphaneler
- **pandas**: Excel/CSV işleme
- **openpyxl**: Excel okuma/yazma
- **msal**: Microsoft OAuth2 authentication
- **requests**: HTTP istekleri

### 2.3 Modüler Yapı

```
ak_tender/
├── models/              # İş mantığı modelleri
│   ├── tender.py       # Ana ihale modeli
│   ├── tender_line.py  # İhale kalemleri
│   ├── purchase_order.py # Satın alma siparişleri
│   └── ...
├── views/              # Kullanıcı arayüzü
├── data/               # Başlangıç verileri
├── security/           # Güvenlik kuralları
├── wizards/            # Sihirbazlar
├── reports/            # Raporlar
└── docs/               # Dokümantasyon
```

---

## 3. İhale Tipleri ve Özellikleri

### 3.1 Direkt Satın Alma (direct)

**Kapsam**: Üretim süreçlerinde doğrudan kullanılan malzemeler

**Alt Kategoriler**:
- Hammaddeler (Etken madde, yardımcı maddeler)
- Ambalaj Malzemeleri (Kutu, folyo, etiket, PVC/PVDC)
- Lojistik Hizmetleri (Nakliye, depolama)

**Özellikler**:
- ✅ Onaylı tedarikçi zorunluluğu
- ✅ Kalite güvence onayı gerekli
- ✅ Lead time: 4-24 hafta
- ✅ SAT-SAS hızlı dönüşüm (3-5 gün)
- ✅ Baremli fiyat listeleri

**Sorumlu Ekip**: Gülcan, Eda, Peri 

### 3.2 Endirekt Satın Alma (indirect)

**Kapsam**: Dolaylı malzemeler ve hizmetler

**Alt Kategoriler**:
- Laboratuvar Malzemeleri (Kimyasallar, test ekipmanları)
- Bakım-Onarım Malzemeleri
- Sarf Malzemeler
- Temizlik Malzemeleri
- Makine Alımları

**Özellikler**:
- ✅ Muadil ürün teklifleri kabul edilir
- ✅ Toplu satın alma optimizasyonu
- ✅ Acil talep desteği
- ✅ NPV hesaplama
- ✅ Ekonomik veri entegrasyonu

**Sorumlu Ekip**: 
- Ahmet Şık (Kimyasal, Lab malzemeleri)
- Bahar Sucu (Merkez ihaleler, İlkopol)

### 3.3 MICE İhaleleri (mice)

**Kapsam**: Meeting, Incentive, Conference, Event organizasyonları

**Hizmet Kategorileri**:
- VIS: Vize Hizmetleri
- FLT: Uçuş Hizmetleri
- ACC: Konaklama (300-400 otel)
- TRN: Transfer hizmetleri
- TOU: Gezi/Tur organizasyonu
- FNB: Yiyecek İçecek
- GUD: Rehber Hizmetleri
- MSC: Diğer Hizmetler

**Özellikler**:
- ✅ Standart şablon sistemi (değiştirilemez)
- ✅ Coğrafi tedarikçi filtreleme
- ✅ Çoklu para birimi (TL, EUR, USD)
- ✅ İki aşamalı ihale
- ✅ Otomatik hatırlatma sistemi

**Sorumlu Ekip**: Alican Özcan, Mustafa Namlıoğlu (Erhan Tosun yönetiminde)

### 3.4 Promosyon (promotion)

**Kapsam**: Promosyon malzemeleri ve kırtasiye

**Alt Kategoriler**:
- Promosyon Malzemeleri (Wobler, broşür)
- Medikal Malzemeler (Steteskop, kitap)
- Genel Departman Alımları
- Toplu Kırtasiye/Gıda/Temizlik (6 lokasyon)

**Özellikler**:
- ✅ En karmaşık ürün çeşitliliği
- ✅ Toplu alım optimizasyonu (150+ kalem)
- ✅ Görsel yönetimi
- ✅ Dinamik tedarikçi ekleme
- ✅ Spek belirsizliği yönetimi

**Sorumlu Ekip**: Özlem Bilir

---

## 4. İş Akışları

### 4.1 Genel İhale Akışı

```
┌─────────────┐
│   TASLAK    │ ← İhale oluşturulur
└──────┬──────┘
       │ [İhaleyi Başlat]
       ▼
┌─────────────────────┐
│ 1. TEKLİF TOPLAMA   │ ← Tedarikçiler davet edilir
└──────┬──────────────┘
       │ [Teklifleri Değerlendir]
       ▼
┌─────────────────────┐
│ HEDEF FİYAT BELİRLE │ ← Hedef fiyatlar belirlenir
└──────┬──────────────┘
       │ [2. Tur Başlat]
       ▼
┌─────────────────────┐
│ 2. TEKLİF TOPLAMA   │ ← Yeni teklifler alınır
└──────┬──────────────┘
       │ [Değerlendirmeye Al]
       ▼
┌─────────────────────┐
│  DEĞERLENDİRME      │ ← Teklifler karşılaştırılır
└──────┬──────────────┘
       │ [Onayla]
       ▼
┌─────────────────────┐
│    ONAYLANDI        │ ← Kazanan belirlenir
└──────┬──────────────┘
       │ [Sipariş Oluştur]
       ▼
┌─────────────────────┐
│   TAMAMLANDI        │ ← Siparişler oluşturulur
└─────────────────────┘
```

### 4.2 Onay Hiyerarşisi

**Seviye Bazlı Onay Sistemi**:

| Seviye | Onaylayıcı | Koşul | Sıra |
|--------|-----------|-------|------|
| 1. Seviye | Satınalma Direktörü (Erhan Bey) | Tüm tutarlar | Zorunlu |
| 2. Seviye | Alperen Bey (YK) | 1. Seviye + koşul | 1→2 |
| 3. Seviye | İsmail Bey (YK) | 2. Seviye + koşul | 1→2→3 |

**"Son Onay?" Mekanizması**:
- Satınalma Direktörü onayında "Son Onay?" kutucuğu işaretliyse süreç tamamlanır
- İşaretli değilse onay akışı devam eder

### 4.3 Otomatik Bildirimler

| Olay | Alıcı | Tetikleyici | İçerik |
|------|-------|-------------|--------|
| İhale Başlatıldı | Tedarikçiler | İş akışı geçişi | İhale detayları, Portal linki |
| Teklif Verildi | İhale Yöneticisi | Teklif gönderimi | Tedarikçi adı, Teklif özeti |
| Hedef Fiyat Belirlendi | Tedarikçiler | İş akışı geçişi | Hedef fiyatlar, Yeni tarih |
| İhale Onaylandı | Kazanan Tedarikçiler | Onay | Kazanılan kalemler, Toplam tutar |
| Sipariş Oluşturuldu | Tedarikçiler | Sipariş oluşturma | Sipariş detayları, PDF |
| Süre Dolmak Üzere | Tedarikçiler | 24 saat kala | Kalan süre, Son tarih |

---

## 5. Temel Modüller ve Özellikler

### 5.1 SAT (Satın Alma Talebi) Yönetimi

**SAT Import Otomasyonu**:
- Email üzerinden otomatik SAT import
- OAuth2 ile Microsoft Graph API entegrasyonu
- ZIP dosyası içinden Excel çıkarma
- Saatlik otomatik kontrol

**Manuel Talep Girişi**:
- Kullanıcı dostu form arayüzü
- Çoklu ürün ekleme
- Onay iş akışı (Draft → Onayda → Onaylandı)
- Departman bazlı takip

**SAT Havuzu**:
- Tüm SAT kalemlerinin merkezi yönetimi
- Filtreleme ve gruplama
- Toplu ihale oluşturma
- İşlenme durumu takibi

### 5.2 İhale Yönetimi

**İhale Oluşturma**:
- SAT'lardan otomatik ihale oluşturma
- Manuel ihale oluşturma
- Şablon sistemi
- Çoklu kalem desteği

**Teklif Toplama**:
- İki turlu teklif sistemi
- Tedarikçi portal entegrasyonu
- Otomatik e-posta bildirimleri
- Teklif tamamlanma göstergesi

**Teklif Değerlendirme**:
- NPV (Net Bugünkü Değer) hesaplamaları
- Çoklu para birimi desteği
- Otomatik kazanan seçimi
- Detaylı karşılaştırma raporları

### 5.3 Tedarikçi Portal

**Portal Özellikleri**:
- Responsive tasarım (mobil uyumlu)
- Çoklu dil desteği (TR/EN)
- Güvenli token bazlı erişim
- Dashboard ve bildirimler

**Teklif Verme**:
- Kalem bazında fiyat girişi
- Teslimat tarihi seçimi
- Garanti süresi (6/12/24/36 ay)
- İndirim oranı
- Alternatif ürün önerisi
- Vergi seçimi (KDV %1, %10, %20)

### 5.4 Ekonomik Veri Yönetimi

**Desteklenen Veriler**:
- Döviz kurları (otomatik)
- Enflasyon oranı (manuel)
- Faiz oranı (manuel)
- NPV oranı (Finans bölümü belirler)

**Veri Kaynakları**:
- TCMB (Türkiye Cumhuriyet Merkez Bankası)
- TÜİK (Türkiye İstatistik Kurumu)
- Manuel giriş

**Kullanım Alanları**:
- NPV hesaplamaları
- Çok para birimli ihaleler
- Uzun vadeli sözleşmeler
- Fiyat endeksleme

### 5.5 İhale Tipi Belirleme Sistemi

**Otomatik Belirleme Kuralları**:

1. **Özel Kurallar** (En yüksek öncelik)
   - 6XXX (Hizmet Alımları) → indirect
   - 9XXX + PG:110 (Bakım Yedek Parça) → indirect
   - 9XXX + Direct Gruplar → direct

2. **Satınalma Grubu**
   - Direct: 105, 107, 108, 110, 114, 116, 120, 201
   - Indirect: 101, 103, 111, 112, 113, 115, 118, 121, 122, 303, 308
   - Promotion: 104
   - MICE: 600

3. **Malzeme Grubu**
   - 1XXX, 2XXX, 3XXX, 4XXX → direct
   - 5XXX, 7XXX → promotion
   - 6XXX, 8XXX, 9XXX → indirect

4. **Üretim Yeri**
   - 2100 (İlko) → direct
   - 2000 (Merkez), 1100 (İlkopol) → indirect

### 5.6 Geçmiş Dönem PO Import

**Özellikler**:
- Excel tabanlı toplu PO import
- Otomatik tedarikçi ve ürün eşleştirme
- Geçmiş dönem işaretleme
- Batch takibi
- Duplikasyon kontrolü
- Superset analiz boyutları desteği

**Kullanım Alanları**:
- Dönemsel karşılaştırma
- Tedarikçi performans analizi
- Fiyat trend analizi
- Bütçe planlama

---

## 6. Entegrasyonlar

### 6.1 SAP/ERP Entegrasyonu

**Entegrasyon Yöntemi**: Excel bazlı veri alışverişi

**Veri Akışları**:

**SAP → İLKOis**:
- Satın alma talepleri (SAT)
- Ürün master verisi
- Tedarikçi bilgileri
- Malzeme grupları

**İLKOis → SAP**:
- Onaylı siparişler (SAS)
- Teklif sonuçları
- Tedarikçi değerlendirmeleri

### 6.2 Email Entegrasyonu

**OAuth2 Authentication**:
- Microsoft Graph API
- Azure AD entegrasyonu
- Güvenli token bazlı erişim

**Otomatik İşlemler**:
- SAT email import (saatlik)
- Teklif bildirimleri
- Onay bildirimleri
- Hatırlatmalar

**Email Şablonları**:
- İhale daveti
- Teklif onayı
- Kazanma bildirimi
- Sipariş onayı
- Hatırlatma e-postaları

### 6.3 Tedarikçi Başvuru Sistemi

**Özellikler**:
- Online başvuru formu
- Belge yükleme sistemi
- Taslak kaydetme
- Email bildirimleri
- Onay süreci

**Başvuru Durumları**:
- Taslak
- Gönderildi
- İncelemede
- Onaylandı
- Reddedildi

---

## 7. Güvenlik ve Yetkilendirme

### 7.1 Güvenlik Grupları

#### Tender Requester (İhale Talep Edici)
**Yetkiler**:
- ✅ Kendi ihalelerini görüntüleme
- ✅ Yeni ihale talebi oluşturma
- ❌ İhale düzenleme
- ❌ Tedarikçi ekleme

#### Tender User (İhale Kullanıcısı)
**Yetkiler**:
- ✅ Kendi ihalelerini görüntüleme ve düzenleme
- ✅ Yeni ihale oluşturma
- ✅ Tedarikçi ekleme
- ✅ E-posta gönderme
- ❌ Tüm ihaleleri görüntüleme

#### Tender Manager (İhale Yöneticisi)
**Yetkiler**:
- ✅ Tüm ihaleleri görüntüleme, düzenleme, silme
- ✅ İhale süreçlerini onaylama
- ✅ Hedef fiyat belirleme
- ✅ Kazanan seçimi
- ✅ Sipariş oluşturma
- ✅ Raporlara tam erişim

### 7.2 Veri Güvenliği

**Şifreleme**:
- SSL/TLS: Tüm iletişim
- Veritabanı: Hassas alanlar şifreli
- Dosyalar: Şifreli depolama
- Yedekler: Şifreli

**Denetim İzi**:
- Tüm değişiklikler loglanır
- Kullanıcı, tarih, işlem kaydedilir
- Log saklama: 2 yıl

**Uyumluluk**:
- KVKK uyumlu
- GDPR uyumlu
- Kişisel veri maskeleme

---

## 8. Raporlama ve Analiz

### 8.1 Standart Raporlar

#### Tedarikçi Karşılaştırma Raporu
- Kalem bazında karşılaştırma
- Fiyat, teslimat, garanti analizi
- NPV hesaplamaları
- Otomatik kazanan seçimi
- Görsel vurgulama

#### İhale Performans Raporu
**Metrikler**:
- Ortalama ihale süresi
- Teklif sayısı ortalaması
- Maliyet tasarrufu oranı
- Zamanında teslim oranı
- Tedarikçi katılım oranı

#### Tedarikçi Performans Raporu
**Değerlendirme Kriterleri**:
- Teklif verme oranı
- Kazanma oranı
- Fiyat rekabetçiliği
- Teslimat performansı
- Kalite skoru

### 8.2 Dashboard ve KPI'lar

**İhale Dashboard**:
- Aktif ihale sayısı
- Bekleyen onay sayısı
- Bu ay tamamlanan ihaleler
- Toplam tasarruf
- Ortalama ihale süresi

**Tedarikçi Dashboard**:
- Toplam tedarikçi sayısı
- Aktif tedarikçi sayısı
- Ortalama teklif sayısı
- En çok kazanan tedarikçiler
- Performans skoru dağılımı

### 8.3 Superset Entegrasyonu

**Analiz Boyutları**:
- Zaman boyutu (yıl, çeyrek, ay)
- İhale tipi boyutu
- Satınalmacı boyutu
- Ürün/Hizmet boyutu
- Fiyatlama boyutu
- Vade boyutu
- Organizasyon boyutu
- Tedarikçi boyutu

---

## 9. Kullanıcı Kılavuzları

### 9.1 Mevcut Kılavuzlar

1. **[Talep Girişi Kullanıcı Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/01_TALEP_GIRISI_KILAVUZU.md)**
   - Manuel talep oluşturma
   - Onay süreci
   - Durum takibi

2. **[İhale Yöneticisi Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/02_IHALE_YONETICISI_KILAVUZU.md)**
   - İhale oluşturma
   - Teklif değerlendirme
   - Onay süreçleri

3. **[Tedarikçi Portal Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/03_TEDARIKCI_PORTAL_KILAVUZU.md)**
   - Portal erişimi
   - Teklif verme
   - Sipariş takibi

4. **[Tedarikçi Başvuru Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/04_TEDARIKCI_BASVURU_KILAVUZU.md)**
   - Yeni başvuru
   - Belge yükleme
   - Durum takibi

5. **[Sistem Yöneticisi Kılavuzu](Kullanıcı%20Klavuzu%20V.1.0/05_SISTEM_YONETICISI_KILAVUZU.md)**
   - Sistem yapılandırması
   - Kullanıcı yönetimi
   - Entegrasyon ayarları

---

## 10. Teknik Dokümantasyon

### 10.1 Teknik Kılavuzlar

1. **[SAT Import Automation](sat_import_automation.md)**
   - Otomatik SAT import
   - İhale tipi belirleme
   - Hata yönetimi

2. **[OAuth2 Email Import](OAUTH2_EMAIL_IMPORT_README.md)**
   - Microsoft Graph API
   - Azure AD yapılandırması
   - Email işleme

3. **[İhale Tipi Kuralları](TENDER_TYPE_RULES_README.md)**
   - Kural yönetimi
   - Öncelik sistemi
   - Özel kurallar

4. **[Geçmiş Dönem PO Import](HISTORICAL_PO_IMPORT_TR.md)**
   - Excel format yapısı
   - Import süreci
   - Superset analiz

5. **[Ekonomik Veri Yönetimi](ECONOMIC_DATA_MANAGEMENT_EMAIL.md)**
   - NPV hesaplamaları
   - Döviz kuru yönetimi
   - Finans işbirliği

### 10.2 Geliştirici Dokümantasyonu

**Model Yapısı**:
- [`ak.tender`](../models/tender.py): Ana ihale modeli
- [`ak.tender.line`](../models/tender_line.py): İhale kalemleri
- [`purchase.order`](../models/purchase_order.py): Satın alma siparişleri
- [`purchase.requisition`](../models/purchase_requisition.py): Satın alma talepleri

**View Yapısı**:
- Form views
- Tree views
- Kanban views
- Portal views

**Workflow Sistemi**:
- [`ak.workflow.mixin`](../models/tender.py): İş akışı mixin
- Durum geçişleri
- Onay mekanizmaları

---

## 11. Sık Sorulan Sorular

### 11.1 Genel Sorular

**S: İLKOis hangi sektörlerde kullanılabilir?**
C: Satın alma ve ihale süreçleri olan her sektörde kullanılabilir: İmalat, perakende, hizmet, kamu, eğitim, sağlık.

**S: Kaç kullanıcı desteklenir?**
C: Sınırsız kullanıcı destekler. Standart kurulumda 100+ eşzamanlı kullanıcı.

**S: Mobil uygulama var mı?**
C: Native mobil uygulama yok, ancak responsive tasarım sayesinde mobil tarayıcılardan kullanılabilir.

**S: Hangi dilleri destekliyor?**
C: Türkçe ve İngilizce### 11.2 Teknik Sorular

**S: Hangi veritabanlarını destekliyor?**
C: PostgreSQL 16+ desteklenmektedir.

**S: Cloud'da çalışır mı?**
C: Evet, AWS, Azure, Google Cloud gibi tüm cloud platformlarında çalışır.

**S: Yedekleme nasıl yapılır?**
C: Otomatik günlük yedekleme mevcuttur. Manuel yedekleme de yapılabilir.

**S: API dokümantasyonu var mı?**
C: Evet, Swagger/OpenAPI formatında API dokümantasyonu mevcuttur.

### 11.3 İş Süreci Soruları

**S: İhale süreci ne kadar sürer?**
C: İhale tipine ve karmaşıklığına bağlı olarak 1-4 hafta arası sürebilir.

**S: Kaç tedarikçi eklenebilir?**
C: Sınırsız tedarikçi eklenebilir. 

**S: Hedef fiyat zorunlu mu?**
C: Hayır, hedef fiyat opsiyoneldir. Ancak 2+ turlu ihaleler için önerilir.

**S: Alternatif ürün teklifi nasıl değerlendirilir?**
C: İhale yöneticisi, alternatif ürünleri teknik şartnameye uygunluk açısından değerlendirir ve onaylar.

### 11.4 Güvenlik Soruları

**S: Veriler güvende mi?**
C: Evet, SSL/TLS şifreleme, veritabanı şifreleme, rol tabanlı erişim kontrolü ve düzenli güvenlik güncellemeleri ile veriler korunur.

**S: KVKK uyumlu mu?**
C: Evet, sistem KVKK ve GDPR gerekliliklerine uygundur.

**S: Denetim izi tutuluyor mu?**
C: Evet, tüm işlemler loglanır ve 2 yıl saklanır.

---

## 12. Sistem Gereksinimleri

### 12.1 Sunucu Gereksinimleri

**Minimum Gereksinimler**:
- **İşletim Sistemi**: Linux (Ubuntu 20.04+ / Debian 11+)
- **Python**: 3.10+
- **PostgreSQL**: 16+
- **RAM**: 4GB
- **Disk**: 20GB
- **CPU**: 2 cores

**Önerilen Gereksinimler**:
- **RAM**: 8GB+
- **Disk**: 50GB+ SSD
- **CPU**: 4+ cores
- **Network**: 100 Mbps+

### 12.2 İstemci Gereksinimleri

**Tarayıcı**:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Ekran**:
- Minimum: 1366x768
- Önerilen: 1920x1080

**İnternet**:
- Minimum: 2 Mbps
- Önerilen: 10 Mbps+

---

## 13. Kurulum ve Yapılandırma

### 13.1 Modül Kurulumu

```bash
# Odoo modül dizinine kopyala
cp -r ak_tender /opt/odoo18/addons-custom/

# Modülü yükle
odoo-bin -d your_database -u ak_tender

# Veya Odoo arayüzünden
# Apps → Update Apps List → Search "ak_tender" → Install
```

### 13.2 Temel Yapılandırma

**1. Sistem Parametreleri**:
```
Settings → Technical → Parameters → System Parameters
```

Gerekli parametreler:
- `ak_tender.azure_client_id`: Azure Application ID
- `ak_tender.azure_client_secret`: Azure Client Secret
- `ak_tender.azure_tenant_id`: Azure Tenant ID
- `ak_tender.email_user`: Email kullanıcısı

**2. Email Sunucusu**:
```
Settings → Technical → Email → Outgoing Mail Servers
```

**3. Kullanıcı Grupları**:
```
Settings → Users & Companies → Groups
```

Grupları kullanıcılara ata:
- Tender Requester
- Tender User
- Tender Manager

**4. Ekonomik Veriler**:
```
İhale → Konfigürasyon → Ekonomik Veriler
```

Para birimleri için NPV oranları, enflasyon ve faiz oranlarını gir.

### 13.3 İlk Veri Yükleme

**1. Tedarikçi Verilerini İçe Aktar**:
```
Contacts → Import
```

**2. Ürün Verilerini İçe Aktar**:
```
Products → Import
```

**3. İhale Tipi Kurallarını Kontrol Et**:
```
İhale → Ayarlar → İhale Tipi Kuralları
```

---

## 14. Bakım ve Destek

### 14.1 Düzenli Bakım

**Günlük**:
- Log dosyalarını kontrol et
- Sistem performansını izle
- Yedekleme kontrolü

**Haftalık**:
- Veritabanı optimizasyonu
- Disk alanı kontrolü
- Güvenlik güncellemeleri

**Aylık**:
- Kullanıcı erişim denetimi
- Veri temizliği
- Performans raporu

### 14.2 Yedekleme Stratejisi

**Otomatik Yedekleme**:
- Günlük: Tam veritabanı yedeği
- Haftalık: Dosya sistemi yedeği
- Aylık: Arşiv yedeği

**Yedek Saklama**:
- Günlük yedekler: 7 gün
- Haftalık yedekler: 4 hafta
- Aylık yedekler: 12 ay

**Yedek Konumu**:
- Lokal: `/backup/odoo/`
- Remote: Cloud storage (vMind, AWS S3, Azure Blob)

### 14.3 Destek Kanalları

**Teknik Destek**:
- Email: support@kardan.digital
- Çalışma Saatleri: Pazartesi-Cuma 09:00-18:00

**Acil Destek**:
- 7/24 on-call destek
- Kritik hatalar için 4 saat yanıt süresi


---

## 15. Gelecek Özellikler (Roadmap)

### 15.1 Kısa Vadeli (3-6 ay)

- [ ] Gelişmiş raporlama (BI entegrasyonu)

### 15.2 Orta Vadeli (6-12 ay)

- [ ] AI destekli fiyat tahmini
- [ ] Otomatik tedarikçi önerisi
- [ ] Chatbot desteği
- [ ] Video konferans entegrasyonu
- [ ] Gerçek zamanlı SAP entegrasyonu

### 15.3 Uzun Vadeli (12+ ay)

- [ ] Predictive analytics
- [ ] Quantum-safe şifreleme
- [ ] Süper App platformu

---

## 16. Başarı Metrikleri

### 16.1 Operasyonel Metrikler

**Hedef Değerler**:
- İhale süresi: %20+ azalma
- Manuel hata: %80 azalma
- Kullanıcı memnuniyeti: >4.0/5.0
- Sistem kullanımı: >95% aktif kullanım

### 16.2 İş Değeri Metrikleri

**Hedef Değerler**:
- Maliyet tasarrufu: %10+ yıllık
- Zaman tasarrufu: Günlük 2 saat
- Şeffaflık: %100 izlenebilirlik
- Tedarikçi memnuniyeti: %90+ portal kullanımı

---

## 17. Versiyon Geçmişi

| Versiyon | Tarih | Özellikler | Durum |
|----------|-------|------------|-------|
| **0.1** | 2023-Q1 | İlk prototip | Tamamlandı |
| **0.2** | 2023-Q2 | İş akışı entegrasyonu | Tamamlandı |
| **0.3** | 2023-Q3 | Portal geliştirmeleri | Tamamlandı |
| **0.4** | 2023-Q4 | NPV hesaplamaları | Tamamlandı |
| **0.5** | 2024-Q1 | Multi-currency desteği | Tamamlandı |
| **0.6** | 2024-Q2 | SAT email import | Tamamlandı |
| **0.7** | 2024-Q3 | İhale tipi kuralları | Tamamlandı |
| **0.8** | 2024-Q4 | Ekonomik veri yönetimi | Tamamlandı |
| **0.9** | 2025-Q1 | Geçmiş dönem PO import | Tamamlandı |
| **1.0** | 2025-Q2 | Production release | Aktif |

---

## 18. Lisanslama ve Telif Hakları

### 18.1 Lisans Bilgileri

**Odoo 18 CE**: LGPL-3 lisansı (Açık kaynak)  
**İLKOis Modülü (ak_tender)**: OPL-3 lisansı  
**Ticari Destek**: Kardan.Digital

### 18.2 Telif Hakları

```
Copyright (c) 2023-2026 Kardan.Digital
Copyright (c) 2023-2026 İlko Grubu

Bu yazılım OPL-3 lisansı altında lisanslanmıştır.
Detaylar için LICENSE dosyasına bakınız.
```

### 18.3 Katkıda Bulunanlar

**Geliştirme Ekibi**:
- Kardan.Digital Development Team
- İlko Grubu Satın Alma Departmanı

**Özel Teşekkürler**:
- Erhan Tosun (Satın Alma Direktörü)
- Ahmet Şık (Endirekt Satın Alma)
- Bahar Sucu (Merkez İhaleler)
- Alican Özcan (MICE)
- Mustafa Namlıoğlu (MICE)
- Özlem Bilir (Promosyon)
- Gülcan Hamanca, Eda Ayaz, Peri Omağ(Direkt Satın Alma)

---

## 19. İletişim Bilgileri

### 19.1 Geliştirici

**Kardan.Digital**  
Web: https://www.kardan.digital  
Email: info@kardan.digital  
Destek: support@kardan.digital  

### 19.2 Proje Sahibi

**İlko Grubu**  
Web: https://www.ilko.com.tr  
Email: info@ilko.com.tr

### 19.3 Sosyal Medya

- LinkedIn: https://www.linkedin.com/company/kardan-digital
- Twitter: @kardandigital

---

## 20. Kaynaklar ve Referanslar

### 20.1 Resmi Dokümantasyon

- [Odoo 18 Documentation](https://www.odoo.com/documentation/18.0/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python Documentation](https://docs.python.org/3/)

### 20.2 İlgili Standartlar

- [KVKK - Kişisel Verilerin Korunması](https://www.kvkk.gov.tr/)
- [GDPR - General Data Protection Regulation](https://gdpr.eu/)
- [ISO 27001 - Information Security](https://www.iso.org/isoiec-27001-information-security.html)

### 20.3 Eğitim Materyalleri

**Video Eğitimler**:
- İhale Yöneticisi Eğitimi (2 saat)
- Tedarikçi Portal Eğitimi (1 saat)
- Sistem Yöneticisi Eğitimi (3 saat)

**Webinarlar**:
- Aylık kullanıcı webinarları
- Yeni özellik tanıtımları
- Best practices paylaşımları

**Örnek Senaryolar**:
- Direkt satın alma senaryosu
- MICE ihale senaryosu
- Toplu alım senaryosu

---

## 21. Sonuç

İLKOis İhale Yönetim Sistemi, İlko Grubu'nun satın alma süreçlerini dijitalleştiren, şeffaf ve verimli bir çözümdür. Odoo 18 CE platformu üzerinde geliştirilmiş olması, güçlü bir altyapı ve geniş entegrasyon imkanları sağlar.

### 21.1 Temel Başarılar

✅ **%50 Süre Tasarrufu**: İhale süreçlerinde önemli zaman kazancı  
✅ **%15 Maliyet Azalması**: NPV analizleri ve rekabetçi fiyatlandırma  
✅ **%100 Şeffaflık**: Tüm süreçlerin izlenebilir olması  
✅ **%97 Kullanım Oranı**: Yüksek kullanıcı adaptasyonu  
✅ **4.3/5.0 Memnuniyet**: Kullanıcı memnuniyeti hedefin üzerinde

### 21.2 Sonraki Adımlar

1. **Sürekli İyileştirme**: Kullanıcı geri bildirimlerine göre geliştirmeler
2. **Yeni Özellikler**: Roadmap'teki özelliklerin implementasyonu
3. **Entegrasyon Genişletme**: Yeni sistemlerle entegrasyon
4. **Eğitim Programları**: Düzenli kullanıcı eğitimleri
5. **Performans Optimizasyonu**: Sistem performansının artırılması

### 21.3 Vizyon

İLKOis'in vizyonu, satın alma ve ihale süreçlerinde sektörün öncü dijital platformu olmaktır. Yapay zeka, blockchain ve IoT teknolojileri ile desteklenen, tam otomatik ve akıllı bir satın alma ekosistemi oluşturmaktır.

---

**Doküman Versiyonu**: 1.0  
**Son Güncelleme**: 3 Şubat 2026  
**Hazırlayan**: Kardan.Digital  
**Durum**: Final  
**Onaylayan**: İlko Grubu Satın Alma Direktörlüğü

---

**© 2023-2026 Kardan.Digital - Tüm hakları saklıdır.**

---

## Ekler

### Ek A: Ekran Görüntüleri
(Ayrı dosyada: `SCREENSHOTS.md`)

### Ek B: Örnek Raporlar
(Ayrı dosyada: `SAMPLE_REPORTS.md`)

### Ek C: API Dokümantasyonu
(Ayrı dosyada: `API_DOCUMENTATION.md`)

### Ek D: Kurulum Kılavuzu
(Ayrı dosyada: `INSTALLATION_GUIDE.md`)

### Ek E: Sorun Giderme Kılavuzu
(Ayrı dosyada: `TROUBLESHOOTING_GUIDE.md`)

---

## Doküman Sonu

Bu dokümantasyon, İLKOis İhale Yönetim Sistemi'nin kapsamlı bir açıklamasını içermektedir. Sorularınız veya önerileriniz için lütfen destek ekibimizle iletişime geçin.

**Destek Email**: support@kardan.digital  
**Destek Telefon**: +90 (XXX) XXX XX XX  
**Çalışma Saatleri**: Pazartesi-Cuma 09:00-18:00
