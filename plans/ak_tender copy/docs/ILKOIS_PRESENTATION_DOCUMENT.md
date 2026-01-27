
# İLKOis İhale Yönetim Sistemi
## Detaylı Sunum Dokümanı

---

## 📋 İçindekiler

1. [Sisteme Genel Giriş](#1-sisteme-genel-giriş)
2. [Kullanıcı Arayüzü ve Temel Özellikler](#2-kullanıcı-arayüzü-ve-temel-özellikler)
3. [Test Ortamında Login ve Erişim Prosedürleri](#3-test-ortamında-login-ve-erişim-prosedürleri)
4. [İhale İş Akışı](#4-ihale-iş-akışı)
5. [Özellikler, Fonksiyonlar ve İşlemler](#5-özellikler-fonksiyonlar-ve-işlemler)
6. [Teknik Altyapı](#6-teknik-altyapı)
7. [Güvenlik ve Yetkilendirme](#7-güvenlik-ve-yetkilendirme)
8. [Raporlama ve Analiz](#8-raporlama-ve-analiz)
9. [Entegrasyonlar](#9-entegrasyonlar)
10. [Sık Sorulan Sorular](#10-sık-sorulan-sorular)

---

## 1. Sisteme Genel Giriş

### 1.1 İLKOis Nedir?

İLKOis (İhale ve Lojistik Koordinasyon Otomasyonu İş Sistemi), Odoo 18 CE platformu üzerinde geliştirilmiş, kurumsal satın alma ve ihale süreçlerini dijitalleştiren kapsamlı bir ERP modülüdür.

**Temel Amaç**: Satın alma ve ihale süreçlerini şeffaf, izlenebilir ve verimli hale getirmek.

### 1.2 Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                    İLKOis İhale Modülü                       │
│                      (ak_tender)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   İş Akışı   │  │   Tedarikçi  │  │   Raporlama  │     │
│  │   Yönetimi   │  │    Portal    │  │   & Analiz   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Satın Alma │  │     ERP      │  │   E-posta    │     │
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

### 1.3 Desteklenen İhale Tipleri

| İhale Tipi | Kod | Açıklama | Özel Özellikler |
|------------|-----|----------|-----------------|
| **Direkt Satın Alma** | `direct` | Standart ürün alımları | ERP kodu zorunlu, Muadil kabul edilmez, Tedarik süresi kısıtlaması |
| **Endirekt Satın Alma** | `indirect` | Dolaylı malzemeler | Toplu satın alma optimizasyonu, Muadil ürün teklifleri, Acil talep desteği |
| **MICE İhaleleri** | `mice` | Toplantı, etkinlik, konaklama | Hizmet kategorisi şablonları, Coğrafi tedarikçi filtreleme, Şablon değişiklik kısıtlamaları |
| **Promosyon** | `promotion` | Promosyon ve kırtasiye | Toplu satın alma optimizasyonu, Acil talep desteği, Ekonomik veri entegrasyonu |

### 1.4 Sistem Avantajları

✅ **Tam Dijitalleşme**: Kağıt bazlı süreçlerin tamamen dijital ortama taşınması  
✅ **Şeffaflık**: Tüm süreçlerin izlenebilir ve denetlenebilir olması  
✅ **Verimlilik**: Otomatik iş akışları ile süre ve maliyet tasarrufu  
✅ **Entegrasyon**: ERP ve diğer sistemlerle sorunsuz entegrasyon  
✅ **Esneklik**: Farklı ihale tiplerini destekleyen modüler yapı  
✅ **Güvenlik**: Rol tabanlı erişim kontrolü (RBAC)  
✅ **Ölçeklenebilirlik**: Büyüyen ihtiyaçlara uyum sağlayabilme  
✅ **Maliyet Tasarrufu**: Rekabetçi fiyatlandırma ve NPV hesaplamaları

---

## 2. Kullanıcı Arayüzü ve Temel Özellikler

### 2.1 Ana Menü Yapısı

```
İhale (Ana Menü)
├── İhaleler
│   ├── Tüm İhaleler
│   ├── Taslak İhaleler
│   ├── Aktif İhaleler
│   └── Tamamlanan İhaleler
├── Satın Alma Siparişleri
│   ├── Tüm Siparişler
│   ├── Bekleyen Siparişler
│   └── Onaylanan Siparişler
├── Yapılandırma
│   ├── İhale Şablonları
│   ├── Ekonomik Veriler
│   ├── Tedarikçi Yönetimi
│   └── Sistem Ayarları
└── Raporlar
    ├── Tedarikçi Karşılaştırma
    ├── İhale Analizi
    └── Performans Raporları
```

### 2.2 İhale Formu Arayüzü

#### 2.2.1 Üst Bilgi Bölümü
- **İhale Referansı**: Otomatik oluşturulan benzersiz numara (TND/2024/001)
- **İhale Adı**: Açıklayıcı başlık
- **İhale Tipi**: Direct, Indirect, MICE, Promotion
- **Para Birimi**: TRY, USD, EUR, vb.
- **Tarihler**: Başlangıç, bitiş, teslim tarihleri
- **Durum Göstergesi**: Görsel durum çubuğu

#### 2.2.2 İhale Kalemleri Sekmesi

**Satır Tipleri**:
- **Ürün/Hizmet Satırı**: Normal ihale kalemi
- **Bölüm Başlığı**: Kalemleri gruplamak için
- **Not Satırı**: Açıklama ve özel notlar için

**Kalem Bilgileri**:
- Ürün/Malzeme seçimi
- Miktar ve birim
- Hedef fiyat
- Teslim tarihi
- Tedarik süresi
- Zorunluluk durumu
- Alternatif kabul durumu
- Ekler (teknik şartname, resim, PDF)

#### 2.2.3 Tedarikçiler Sekmesi

**Tedarikçi Yönetimi**:
- Tedarikçi ekleme (manuel/toplu)
- Coğrafi filtreleme (ülke, il, şehir)
- Tedarikçi durumu takibi
- Toplu e-posta gönderimi
- Teklif durumu görüntüleme

#### 2.2.4 İş Akışı Sekmesi

**İş Akışı Bilgileri**:
- Mevcut durum
- Geçiş geçmişi
- Kullanılabilir geçişler
- Onay durumu
- İş akışı notları

### 2.3 Tedarikçi Portal Arayüzü

#### 2.3.1 Portal Ana Sayfa

**Dashboard Özellikleri**:
- Bekleyen ihaleler sayısı
- Teklif verilen ihaleler
- Kazanılan ihaleler
- Son aktiviteler
- Hızlı erişim butonları

#### 2.3.2 İhale Listesi

**Filtreleme Seçenekleri**:
- Durum bazlı (Aktif, Bekleyen, Tamamlanan)
- Tarih aralığı
- İhale tipi
- Arama

#### 2.3.3 Teklif Verme Formu

**Teklif Bilgileri**:
- Kalem bazında fiyat girişi
- Teslimat tarihi seçimi
- Garanti süresi (6, 12, 24, 36 ay)
- İndirim oranı
- Alternatif ürün önerisi
- Vergi seçimi (KDV %1, %10, %20)
- Toplu kaydetme özelliği

### 2.4 Görsel Özellikler

#### 2.4.1 Durum Renk Kodları

| Durum | Renk | İkon | Açıklama |
|-------|------|------|----------|
| Taslak | 🔵 Mavi | 📝 | Hazırlık aşaması |
| 1. Teklif Toplama | 🟡 Sarı | 📨 | İlk tur teklifler |
| Hedef Fiyat Belirlendi | 🟠 Turuncu | 🎯 | Hedef fiyatlar set edildi |
| 2. Teklif Toplama | 🟢 Yeşil | 📬 | İkinci tur teklifler |
| Değerlendirme | 🔴 Kırmızı | 📊 | Teklif değerlendirme |
| Onaylandı | ✅ Yeşil | ✓ | Onay alındı |
| Tamamlandı | ⚫ Siyah | 🏁 | Süreç tamamlandı |
| İptal | ⚪ Gri | ✗ | İptal edildi |

#### 2.4.2 İlerleme Göstergeleri

İhale tiplerine göre farklı renklerde ilerleme çubukları:
- **Direct**: Mavi tonları
- **Indirect**: Yeşil tonları
- **MICE**: Turuncu tonları
- **Promotion**: Mor tonları

---

## 3. Test Ortamında Login ve Erişim Prosedürleri

### 3.1 Sistem Gereksinimleri

#### 3.1.1 Sunucu Gereksinimleri
- **İşletim Sistemi**: Linux (Ubuntu 20.04+ / Debian 11+)
- **Python**: 3.10+
- **PostgreSQL**: 13+
- **RAM**: Minimum 4GB (Önerilen 8GB)
- **Disk**: Minimum 20GB
- **CPU**: 2+ cores

#### 3.1.2 İstemci Gereksinimleri
- **Tarayıcı**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Ekran Çözünürlüğü**: Minimum 1366x768 (Önerilen 1920x1080)
- **İnternet Bağlantısı**: Minimum 2 Mbps
- **JavaScript**: Etkin olmalı

### 3.2 Test Ortamı Erişim Bilgileri

#### 3.2.1 Sistem Adresleri
```
Test Ortamı URL: https://test.ilkois.com.tr
Veritabanı: ilkois_test
HTTP Port: 8069
Longpolling Port: 8071
```

#### 3.2.2 Test Kullanıcıları

| Rol | Kullanıcı Adı | Şifre | E-posta | Yetki Seviyesi |
|-----|---------------|-------|---------|----------------|
| **Sistem Yöneticisi** | admin | admin123 | admin@ilkois.com.tr | Tam Yetki |
| **İhale Yöneticisi** | ihale.yoneticisi | test123 | yonetici@ilkois.com.tr | İhale Yönetimi |
| **İhale Kullanıcısı** | ihale.kullanici | test123 | kullanici@ilkois.com.tr | İhale Oluşturma |
| **İhale Talep Edici** | ihale.talep | test123 | talep@ilkois.com.tr | Talep Oluşturma |
| **Tedarikçi 1** | tedarikci1 | test123 | tedarikci1@test.com | Portal Erişimi |
| **Tedarikçi 2** | tedarikci2 | test123 | tedarikci2@test.com | Portal Erişimi |

### 3.3 Login Prosedürü

#### 3.3.1 Backend Login (Çalışanlar İçin)

**Adım 1**: Tarayıcıda URL'yi Açın
```
https://test.ilkois.com.tr
```

**Adım 2**: Login Bilgilerini Girin
- E-posta veya Kullanıcı Adı
- Şifre
- Veritabanı: ilkois_test

**Adım 3**: Giriş Yapın
- "Giriş Yap" butonuna tıklayın
- İki faktörlü doğrulama (varsa)

**Adım 4**: Ana Ekran
- Dashboard görüntülenir
- Menü yapısı yüklenir
- Bildirimler kontrol edilir

#### 3.3.2 Portal Login (Tedarikçiler İçin)

**Adım 1**: Portal URL'sini Açın
```
https://test.ilkois.com.tr/my
veya
https://test.ilkois.com.tr/web/login
```

**Adım 2**: Portal Bilgilerini Girin
- E-posta adresi
- Şifre

**Adım 3**: Portal Ana Sayfa
- İhale listesi
- Sipariş listesi
- Profil bilgileri

### 3.4 İlk Giriş Kontrol Listesi

#### 3.4.1 Backend Kontrolleri
- [ ] Kullanıcı profili doğru yüklendi mi?
- [ ] Menü yapısı tam görünüyor mu?
- [ ] Yetki seviyesi doğru mu?
- [ ] Dil ayarı Türkçe mi?
- [ ] Zaman dilimi doğru mu? (Europe/Istanbul)
- [ ] Bildirimler çalışıyor mu?
- [ ] Arama fonksiyonu aktif mi?

#### 3.4.2 Portal Kontrolleri
- [ ] Portal ana sayfa yüklendi mi?
- [ ] İhale listesi görünüyor mu?
- [ ] Teklif verme formu açılıyor mu?
- [ ] Dosya yükleme çalışıyor mu?
- [ ] E-posta bildirimleri geliyor mu?

### 3.5 Güvenlik ve Oturum Yönetimi

#### 3.5.1 Oturum Ayarları
- **Oturum Süresi**: 8 saat
- **Otomatik Çıkış**: 30 dakika hareketsizlik sonrası
- **Çoklu Oturum**: Desteklenir (aynı kullanıcı farklı cihazlardan)
- **IP Kısıtlaması**: Test ortamında yok (Prod'da aktif)
- **Oturum Yenileme**: Otomatik

#### 3.5.2 Şifre Politikası
- Minimum 8 karakter
- En az 1 büyük harf
- En az 1 küçük harf
- En az 1 rakam
- Özel karakter önerilir
- Şifre geçmişi: Son 5 şifre kullanılamaz
- Şifre değiştirme: 90 günde bir (opsiyonel)

#### 3.5.3 Güvenlik Özellikleri
- SSL/TLS şifreleme
- CSRF koruması
- XSS koruması
- SQL injection koruması
- Brute force koruması
- Oturum token'ları

---

## 4. İhale İş Akışı

### 4.1 İş Akışı Genel Bakış

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

### 4.2 Detaylı İş Akışı Adımları

#### 4.2.1 Adım 1: İhale Oluşturma (TASLAK)

**Sorumlu**: İhale Kullanıcısı / İhale Yöneticisi

**İşlemler**:
1. İhale menüsünden "Yeni İhale" oluştur
2. Temel bilgileri gir:
   - İhale adı (örn: "2024 Q1 Ofis Malzemeleri")
   - İhale tipi seç (direct/indirect/mice/promotion)
   - Para birimi belirle (TRY/USD/EUR)
   - Başlangıç tarihi
   - Bitiş tarihi
   - Gerekli teslim tarihi
3. İhale kalemlerini ekle:
   - Ürün/hizmet seç veya yeni oluştur
   - Miktar ve birim belirle
   - Teslim tarihi belirle
   - Hedef fiyat (opsiyonel)
   - Özel şartlar ekle
4. Ek bilgileri gir:
   - Genel açıklama
   - Özel şartlar ve koşullar
   - Teknik şartname ekle
   - Resim/PDF ekle
5. Şablon kullan (opsiyonel):
   - Mevcut şablonlardan seç
   - Şablon uygula
   - Özelleştir
6. Kaydet

**Çıktı**: Taslak durumunda ihale kaydı oluşturulur

**Süre**: 15-30 dakika

#### 4.2.2 Adım 2: Tedarikçi Davet (1. TEKLİF TOPLAMA)

**Sorumlu**: İhale Kullanıcısı / İhale Yöneticisi

**İşlemler**:
1. İhale formunda "Tedarikçiler" sekmesine git
2. Tedarikçi ekle:
   - **Manuel Seçim**: Tedarikçi listesinden seç
   - **Toplu Ekleme**: Excel ile toplu import
   - **Coğrafi Filtreleme**: Ülke/il/şehir bazında filtrele (MICE için)
   - **Kategori Bazlı**: Ürün kategorisine göre otomatik seçim
3. Tedarikçi bilgilerini kontrol et:
   - İletişim bilgileri
   - E-posta adresi
   - Portal erişim durumu
4. E-posta şablonu hazırla:
   - Otomatik şablon kullan veya özelleştir
   - İhale detaylarını ekle
   - Portal erişim linkini ekle
   - Ek dosyaları ekle
5. Toplu e-posta gönder:
   - "Toplu E-posta Gönder" butonuna tıkla
   - Gönderim onayı
6. İş akışı geçişi:
   - "1. Teklif Toplamaya Başla" eylemini çalıştır
   - Durum güncellenir

**Çıktı**: 
- Tedarikçilere davet e-postaları gönderilir
- İhale durumu "1. Teklif Toplama" olur
- Portal'da ihale görünür hale gelir
- Satın alma talepleri (RFQ) oluşturulur

**Süre**: 10-15 dakika

#### 4.2.3 Adım 3: Teklif Verme (Tedarikçi Tarafı)

**Sorumlu**: Tedarikçi

**İşlemler**:
1. E-posta bildirimini al
2. Portal'a giriş yap:
   - E-posta linkinden veya direkt portal URL'den
   - Kullanıcı adı ve şifre ile giriş
3. "İhaleler" menüsünden aktif ihaleyi seç
4. İhale detaylarını incele:
   - İhale kalemleri
   - Miktarlar ve birimler
   - Teslim tarihleri
   - Özel şartlar
   - Teknik şartnameler
5. Her kalem için teklif ver:
   - **Birim Fiyat**: Teklif edilen fiyat
   - **Teslimat Tarihi**: Teslim edebileceği tarih
   - **Garanti Süresi**: 6/12/24/36 ay
   - **İndirim Oranı**: Yüzde cinsinden
   - **Alternatif Ürün**: Varsa alternatif öner
   - **Vergi**: KDV oranı seç (%1, %10, %20)
   - **Not**: Özel notlar ekle
6. Teklifleri kaydet:
   - "Kaydet" butonu ile ara kayıt
   - Değişiklik yapabilme
7. Teklifi gönder:
   - Tüm alanları kontrol et
   - "Teklifi Gönder" butonuna tıkla
   - Onay ver

**Çıktı**:
- Satın alma siparişi (RFQ) güncellenir
- Teklif durumu "Gönderildi" olur
- İhale yöneticisine bildirim gider
- Tedarikçiye onay e-postası gider

**Süre**: 30-60 dakika (ihale büyüklüğüne göre)

#### 4.2.4 Adım 4: Hedef Fiyat Belirleme

**Sorumlu**: İhale Yöneticisi

**İşlemler**:
1. Gelen teklifleri incele:
   - Teklif sayısını kontrol et
   - Eksik teklifleri tespit et
   - Fiyat aralıklarını gözden geçir
2. "Hedef Fiyat Belirle" sihirbazını aç:
   - İhale formunda "Eylem" menüsünden
   - Veya sunucu eylemi olarak
3. Her kalem için hedef fiyat belirle:
   - **En Düşük Teklifi Baz Al**: Otomatik seçim
   - **Manuel Fiyat Gir**: Özel fiyat belirle
   - **Yüzde İndirim Uygula**: Mevcut fiyata indirim
   - **Piyasa Fiyatı**: Piyasa araştırması sonucu
4. Hedef fiyatları gözden geçir:
   - Toplam bütçe kontrolü
   - Kalem bazında kontrol
   - Onay
5. Hedef fiyatları kaydet
6. İş akışı geçişi:
   - "Hedef Fiyat Belirlendi" durumuna geç

**Çıktı**:
- İhale kalemlerinde hedef fiyatlar güncellenir
- Durum "Hedef Fiyat Belirlendi" olur
- 2. tur için hazır hale gelir

**Süre**: 20-30 dakika

#### 4.2.5 Adım 5: 2. Teklif Toplama

**Sorumlu**: İhale Yöneticisi

**İşlemler**:
1. İş akışı geçişi:
   - "2. Teklif Toplamaya Başla" eylemini çalıştır
2. Tedarikçilere bildirim gönder:
   - Otomatik e-posta şablonu
   - Hedef fiyatlar paylaşılır (opsiyonel)
   - Yeni teklif istenir
   - Son tarih belirtilir
3. Tedarikçiler yeni tekliflerini verir:
   - Portal üzerinden güncelleme
   - Hedef fiyatlara göre revize
4. Teklif süresi takibi:
   - Süre dolmadan hatırlatma e-postaları
   - Son 24 saat uyarısı
5. Teklif süresi dolduğunda:
   - Otomatik veya manuel değerlendirmeye al

**Çıktı**:
- Tedarikçiler yeni teklifler verir
- Güncellenmiş satın alma siparişleri
- Durum "2. Teklif Toplama" olur

**Süre**: 3-7 gün (ihale süresine göre)

#### 4.2.6 Adım 6: Değerlendirme

**Sorumlu**: İhale Yöneticisi

**İşlemler**:
1. "Tedarikçi Karşılaştırma Raporu" oluştur:
   - İhale formunda "Yazdır" menüsünden
   - Veya "Raporlar" menüsünden
2. Teklifleri karşılaştır:
   - **Fiyat Karşılaştırması**: Kalem bazında en düşük fiyat
   - **NPV Hesaplamaları**: Net bugünkü değer analizi
   - **Teslimat Süreleri**: Teslim tarihi uygunluğu
   - **Garanti Koşulları**: Garanti süresi karşılaştırması
   - **Ödeme Koşulları**: Vade ve ödeme şartları
   - **Toplam Maliyet**: Genel toplam karşılaştırma
3. Kazanan tedarikçileri seç:
   - **Otomatik Seçim**: En düşük NPV'ye göre
   - **Manuel Seçim**: Özel kriterlere göre
   - **Karma Seçim**: Farklı kalemler için farklı tedarikçiler
4. Seçim kriterlerini belirle:
   - Fiyat ağırlığı: %60
   - Teslimat süresi: %20
   - Garanti: %10
   - Referanslar: %10
5. Seçimleri kaydet:
   - Kazanan satırları işaretle
   - Gerekçe ekle
6. İş akışı geçişi:
   - "Değerlendirme Tamamlandı" durumuna geç

**Çıktı**:
- Kazanan tedarikçiler belirlenir
- Değerlendirme raporu oluşturulur
- Karar gerekçeleri kaydedilir

**Süre**: 1-2 saat

#### 4.2.7 Adım 7: On

ay

**Sorumlu**: İhale Yöneticisi / Üst Yönetim

**İşlemler**:
1. Değerlendirme sonuçlarını incele:
   - Kazanan tedarikçiler
   - Toplam maliyet
   - Bütçe uygunluğu
2. Onay mekanizması:
   - **Otomatik Onay**: Belirli limitler için (örn: 50.000 TL altı)
   - **Manuel Onay**: Üst yönetim onayı gerekli
   - **Çok Aşamalı Onay**: Büyük ihaleler için
3. Onay belgelerini hazırla:
   - Karar özeti
   - Maliyet analizi
   - Gerekçe raporu
4. İş akışı geçişi:
   - "Onayla" eylemini çalıştır
5. Bildirimleri gönder:
   - Kazanan tedarikçilere
   - Kaybeden tedarikçilere (opsiyonel)
   - İlgili departmanlara

**Çıktı**:
- İhale durumu "Onaylandı" olur
- Kazanan tedarikçilere bildirim gider
- Onay belgesi oluşturulur

**Süre**: 1-3 gün (onay sürecine göre)

#### 4.2.8 Adım 8: Sipariş Oluşturma

**Sorumlu**: İhale Yöneticisi / Satın Alma Uzmanı

**İşlemler**:
1. "Satın Alma Siparişi Oluştur" eylemini çalıştır:
   - İhale formunda "Eylem" menüsünden
   - Veya sunucu eylemi olarak
2. Kazanan tekliflerden siparişler oluşturulur:
   - RFQ → Purchase Order dönüşümü
   - Sipariş detayları aktarılır
   - Teslimat bilgileri eklenir
   - Ödeme koşulları belirlenir
3. Siparişleri gözden geçir:
   - Fiyat kontrolü
   - Miktar kontrolü
   - Teslimat adresi
   - Ödeme şartları
4. Siparişleri onayla:
   - Her sipariş için onay
   - Toplu onay (opsiyonel)
5. Tedarikçilere sipariş bildirimi gönder:
   - Otomatik e-posta
   - Sipariş PDF'i ekte
6. İş akışı geçişi:
   - "Tamamlandı" durumuna geç

**Çıktı**:
- Onaylı satın alma siparişleri
- Tedarikçilere sipariş e-postaları
- İhale durumu "Tamamlandı"
- Stok hareketleri başlatılır

**Süre**: 30-60 dakika

### 4.3 İş Akışı Geçiş Matrisi

| Mevcut Durum | Geçiş Eylemi | Hedef Durum | Gerekli Yetki | Koşullar |
|--------------|--------------|-------------|---------------|----------|
| Taslak | İhaleyi Başlat | 1. Teklif Toplama | İhale Kullanıcısı | En az 1 kalem, En az 1 tedarikçi |
| 1. Teklif Toplama | Hedef Fiyat Belirle | Hedef Fiyat Belirlendi | İhale Yöneticisi | En az 1 teklif alınmış |
| Hedef Fiyat Belirlendi | 2. Tur Başlat | 2. Teklif Toplama | İhale Yöneticisi | Hedef fiyatlar belirlenmiş |
| 2. Teklif Toplama | Değerlendirmeye Al | Değerlendirme | İhale Yöneticisi | Teklif süresi dolmuş |
| Değerlendirme | Onayla | Onaylandı | İhale Yöneticisi | Kazananlar seçilmiş |
| Onaylandı | Sipariş Oluştur | Tamamlandı | İhale Yöneticisi | Onay alınmış |
| Herhangi | İptal Et | İptal Edildi | İhale Yöneticisi | - |

### 4.4 Otomatik Eylemler ve Bildirimler

#### 4.4.1 E-posta Bildirimleri

| Olay | Alıcı | Şablon | İçerik | Tetikleyici |
|------|-------|--------|--------|-------------|
| İhale Başlatıldı | Tedarikçiler | Davet E-postası | İhale detayları, Portal linki | İş akışı geçişi |
| Teklif Verildi | İhale Yöneticisi | Teklif Bildirimi | Tedarikçi adı, Teklif özeti | Teklif gönderimi |
| Hedef Fiyat Belirlendi | Tedarikçiler | 2. Tur Daveti | Hedef fiyatlar, Yeni tarih | İş akışı geçişi |
| İhale Onaylandı | Kazanan Tedarikçiler | Kazanma Bildirimi | Kazanılan kalemler, Toplam tutar | Onay |
| İhale Onaylandı | Kaybeden Tedarikçiler | Teşekkür E-postası | Katılım teşekkürü | Onay |
| Sipariş Oluşturuldu | Tedarikçiler | Sipariş Onayı | Sipariş detayları, PDF | Sipariş oluşturma |
| Süre Dolmak Üzere | Tedarikçiler | Hatırlatma | Kalan süre, Son tarih | 24 saat kala |

#### 4.4.2 Sistem Bildirimleri

- 🔔 **İhale süresi dolmak üzere**: 24 saat kala otomatik bildirim
- 🔔 **Yeni teklif alındı**: Anlık bildirim
- 🔔 **Hedef fiyat belirlendi**: Tüm ilgililere bildirim
- 🔔 **İhale onaylandı**: Kazanan ve kaybedenlere bildirim
- 🔔 **Sipariş oluşturuldu**: Tedarikçi ve satın alma ekibine bildirim
- 🔔 **Eksik teklif**: Teklif vermeyen tedarikçilere hatırlatma

---

## 5. Özellikler, Fonksiyonlar ve İşlemler

### 5.1 İhale Yönetimi Özellikleri

#### 5.1.1 Çok Aşamalı İhale Süreci

**Özellik**: İki turlu teklif toplama sistemi

**Avantajlar**:
- İlk turda piyasa fiyatlarını öğrenme
- Hedef fiyat belirleme imkanı
- İkinci turda daha rekabetçi fiyatlar
- Tedarikçilere adil fırsat

**Kullanım Senaryosu**:
```
1. Tur → Piyasa araştırması (5-10 tedarikçi)
2. Hedef Fiyat → Bütçe ve piyasa analizi
3. Tur → Nihai teklifler (3-5 tedarikçi)
```

#### 5.1.2 İhale Şablonları

**Özellik**: Tekrar eden ihaleler için şablon sistemi

**Şablon Tipleri**:
- **Ürün Şablonları**: Standart ürün listeleri
- **Hizmet Şablonları**: MICE kategorileri
- **Bölge Şablonları**: Coğrafi kısıtlamalar
- **Karma Şablonları**: Ürün + hizmet kombinasyonları

**Şablon Özellikleri**:
- Satır tipleri (ürün, bölüm, not)
- Coğrafi filtreler
- Varsayılan değerler
- Kilitleme mekanizması

**Kullanım**:
```python
# Şablon uygulama
tender.action_apply_template()
# Şablon oluşturma
template = env['ak.tender.template'].create({
    'name': 'Ofis Malzemeleri Şablonu',
    'tender_type': 'indirect',
    'line_ids': [...]
})
```

#### 5.1.3 Toplu Satın Alma Optimizasyonu

**Özellik**: Birden fazla talebi tek ihalede birleştirme

**Destekleyen İhale Tipleri**:
- Indirect (Endirekt Satın Alma)
- Promotion (Promosyon ve Kırtasiye)

**Avantajlar**:
- Miktar avantajı ile daha iyi fiyatlar
- Tek seferde çoklu departman ihtiyacı
- Lojistik maliyet tasarrufu
- Zaman tasarrufu

**Kullanım Senaryosu**:
```
Departman A: 100 adet kalem
Departman B: 50 adet kalem
Departman C: 75 adet kalem
→ Toplam: 225 adet kalem (tek ihale)
```

#### 5.1.4 Acil Talep Desteği

**Özellik**: Hızlandırılmış ihale süreci

**Özellikler**:
- Kısaltılmış teklif süresi
- Öncelikli işlem
- Otomatik bildirimler
- Hızlı onay mekanizması

**Kullanım Koşulları**:
- Stok kritik seviyede
- Üretim durması riski
- Acil proje ihtiyacı

#### 5.1.5 Coğrafi Tedarikçi Filtreleme

**Özellik**: Bölge bazlı tedarikçi seçimi

**Filtreleme Seviyeleri**:
- **Ülke**: Türkiye, Almanya, vb.
- **İl**: İstanbul, Ankara, İzmir, vb.
- **Şehir/İlçe**: Kadıköy, Çankaya, vb.

**Kullanım Alanları**:
- MICE ihaleleri (otel, toplantı salonu)
- Lojistik maliyeti yüksek ürünler
- Yerel tedarikçi tercihi

**Örnek**:
```
İhale: İstanbul Bölge Toplantısı
Filtre: Ülke=Türkiye, İl=İstanbul
Sonuç: Sadece İstanbul'daki oteller listelenir
```

### 5.2 Tedarikçi Portal Özellikleri

#### 5.2.1 Gelişmiş Teklif Formu

**Özellikler**:
- Kalem bazında fiyat girişi
- Teslimat tarihi seçimi
- Garanti süresi seçimi (6/12/24/36 ay)
- İndirim oranı belirtme
- Alternatif ürün önerisi
- Vergi seçimi (KDV %1, %10, %20)
- Toplu kaydetme
- Ara kayıt özelliği

**Validasyonlar**:
- Zorunlu alan kontrolü
- Fiyat formatı kontrolü
- Tarih kontrolü (geçmiş tarih girilmez)
- Miktar kontrolü

#### 5.2.2 Alternatif Ürün Önerisi

**Özellik**: Muadil ürün teklif edebilme

**Kullanım**:
```
Talep Edilen: Marka A - Model X
Alternatif: Marka B - Model Y
Gerekçe: Aynı özellikler, %20 daha ucuz
```

**Değerlendirme**:
- İhale yöneticisi onayı gerekli
- Teknik şartname uygunluğu
- Fiyat avantajı

#### 5.2.3 Belge Yönetimi

**Özellikler**:
- İhale belgelerini görüntüleme
- Teknik şartname indirme
- Sipariş belgelerini indirme
- Fatura yükleme (gelecek özellik)

### 5.3 Raporlama ve Analiz Özellikleri

#### 5.3.1 Tedarikçi Karşılaştırma Raporu

**Özellik**: Detaylı teklif karşılaştırma raporu

**Rapor İçeriği**:
- Kalem bazında fiyat karşılaştırması
- En düşük fiyat vurgulama (yeşil renk)
- NPV (Net Bugünkü Değer) hesaplamaları
- Teslimat tarihi karşılaştırması
- Garanti süresi karşılaştırması
- Toplam maliyet analizi
- Otomatik kazanan seçimi

**NPV Hesaplama Formülü**:
```
NPV = Σ (Ödeme / (1 + İskonto Oranı)^Dönem)

Örnek:
Fiyat: 10.000 TL
Vade: 90 gün
İskonto Oranı: %15
NPV = 10.000 / (1 + 0.15)^(90/365) = 9.650 TL
```

**Rapor Formatları**:
- HTML (ekran görüntüleme)
- PDF (yazdırma)
- Excel (veri analizi)

#### 5.3.2 İhale Analiz Raporları

**Raporlar**:
- İhale performans raporu
- Tedarikçi performans raporu
- Maliyet tasarrufu raporu
- Süre analizi raporu
- Kategori bazlı analiz

### 5.4 Entegrasyon Özellikleri

#### 5.4.1 ERP Entegrasyonu (Simülasyon)

**Özellik**: SAP/ERP sistemleri ile entegrasyon

**Entegrasyon Noktaları**:
- Ürün master verisi
- Tedarikçi master verisi
- Satın alma talepleri
- Sipariş aktarımı
- Fatura entegrasyonu

**Veri Akışı**:
```
ERP → İLKOis: Satın alma talepleri
İLKOis → ERP: Onaylı siparişler
ERP → İLKOis: Stok durumu
İLKOis → ERP: Teslim bilgileri
```

#### 5.4.2 SAT Email Import Otomasyonu

**Özellik**: Otomatik email işleme sistemi

**Çalışma Prensibi**:
1. Email kutusunu kontrol et (saatlik)
2. "ME5A Günlük Rapor Sonuçları" konulu emailleri bul
3. ZIP dosyasını indir
4. Excel dosyasını çıkar
5. Verileri import et
6. Email'i okundu işaretle

**Yapılandırma**:
```python
# Email ayarları
Email: ilkoisdata@ilko.com.tr
Server: mail.ilko.com.tr
Port: 993 (IMAP SSL)
Cron: Her 1 saatte bir
```

**Import Edilen Veriler**:
- Ürün bilgileri
- Fiyat bilgileri
- Stok durumu
- Tedarikçi bilgileri

#### 5.4.3 Onay Mekanizması Entegrasyonu

**Özellik**: Approvals modülü ile entegrasyon

**Onay Tipleri**:
- İhale başlatma onayı
- Hedef fiyat onayı
- Kazanan seçimi onayı
- Sipariş oluşturma onayı

**Onay Akışı**:
```
Talep → Yönetici Onayı → Müdür Onayı → Genel Müdür Onayı
```

**Limit Bazlı Onay**:
- 0-10.000 TL: Otomatik onay
- 10.000-50.000 TL: Yönetici onayı
- 50.000-100.000 TL: Müdür onayı
- 100.000+ TL: Genel müdür onayı

### 5.5 Özel Fonksiyonlar

#### 5.5.1 Dinamik Tedarikçi Ekleme

**Özellik**: İhale sırasında yeni tedarikçi ekleme

**Kullanım**:
```
1. İhale formunda "Tedarikçi Ekle" butonu
2. Yeni tedarikçi bilgilerini gir
3. Portal erişimi oluştur
4. Davet e-postası gönder
```

#### 5.5.2 Garanti Süresi Yönetimi

**Özellik**: Ürün garanti süresi takibi

**Garanti Seçenekleri**:
- 6 ay
- 12 ay (standart)
- 24 ay
- 36 ay
- Özel süre

**Garanti Değerlendirmesi**:
- Garanti süresi uzun = Daha yüksek puan
- NPV hesaplamasında dikkate alınır

#### 5.5.3 Gecikme Günleri Hesaplaması

**Özellik**: Teslimat gecikme takibi

**Hesaplama**:
```
Gecikme Günü = Gerçek Teslimat - Planlanan Teslimat

Örnek:
Planlanan: 01.01.2024
Gerçek: 05.01.2024
Gecikme: 4 gün
```

**Ceza Mekanizması**:
- 1-3 gün: Uyarı
- 4-7 gün: %1 ceza
- 8-15 gün: %3 ceza
- 15+ gün: %5 ceza + kara liste

#### 5.5.4 Ekonomik Veri Entegrasyonu

**Özellik**: Döviz kuru ve enflasyon verileri

**Kullanım Alanları**:
- NPV hesaplamaları
- Çok para birimli ihaleler
- Uzun vadeli sözleşmeler
- Fiyat endeksleme

**Veri Kaynakları**:
- TCMB (Türkiye Cumhuriyet Merkez Bankası)
- TÜİK (Türkiye İstatistik Kurumu)
- Manuel giriş

---

## 6. Teknik Altyapı

### 6.1 Teknoloji Stack

#### 6.1.1 Backend
- **Platform**: Odoo 18 CE
- **Dil**: Python 3.10+
- **Framework**: Odoo ORM
- **Veritabanı**: PostgreSQL 13+
- **Web Server**: Werkzeug (built-in)

#### 6.1.2 Frontend
- **Framework**: Odoo Web Client
- **JavaScript**: ES6+
- **CSS**: Bootstrap 5, Custom SCSS
- **Template Engine**: QWeb

#### 6.1.3 Kütüphaneler
- **pandas**: Excel/CSV işleme
- **BeautifulSoup4**: HTML parsing
- **openpyxl**: Excel okuma/yazma
- **reportlab**: PDF oluşturma
- **Pillow**: Resim işleme

### 6.2 Veritabanı Yapısı

#### 6.2.1 Ana Tablolar

**ak_tender (İhale)**
```sql
- id: integer (PK)
- name: varchar (İhale adı)
- reference: varchar (İhale referansı)
- tender_type: varchar (İhale tipi)
- currency_id: integer (FK)
- start_date: date
- end_date: date
- required_delivery_date: date
- workflow_current_state_id: integer (FK)
- create_uid: integer (FK)
- write_uid: integer (FK)
```

**ak_tender_line (İhale Kalemi)**
```sql
- id: integer (PK)
- tender_id: integer (FK)
- sequence: integer
- display_type: varchar
- product_id: integer (FK)
- name: text
- quantity: numeric
- uom_id: integer (FK)
- target_price: numeric
- currency_id: integer (FK)
```

**purchase_order (Satın Alma Siparişi)**
```sql
- id: integer (PK)
- name: varchar
- partner_id: integer (FK)
- tender_id: integer (FK)
- currency_id: integer (FK)
- state: varchar
- date_order: datetime
```

**purchase_order_line (Sipariş Kalemi)**
```sql
- id: integer (PK)
- order_id: integer (FK)
- tender_line_id: integer (FK)
- product_id: integer (FK)
- product_qty: numeric
- price_unit: numeric
- line_price_unit: numeric
- line_currency_id: integer (FK)
- npv_value: numeric
- warranty_months: integer
- discount_percent: numeric
```

### 6.3 API ve Entegrasyonlar

#### 6.3.1 REST API Endpoints

**İhale API**
```
GET    /api/tenders              # İhale listesi
GET    /api/tenders/{id}         # İhale detayı
POST   /api/tenders              # Yeni ihale
PUT    /api/tenders/{id}         # İhale güncelle
DELETE /api/tenders/{id}         # İhale sil
```

**Teklif API**
```
GET    /api/tenders/{id}/bids    # Teklifler
POST   /api/tenders/{id}/bids    # Teklif ver
PUT    /api/bids/{id}            # Teklif güncelle
```

#### 6.3.2 Webhook Entegrasyonları

**Bildirim Webhook'ları**:
- İhale başlatıldı
- Teklif alındı
- İhale onaylandı
- Sipariş oluşturuldu

### 6.4 Performans ve Ölçeklenebilirlik

#### 6.4.1 Performans Metrikleri
- Sayfa yükleme: < 2 saniye
- API yanıt süresi: < 500ms
- Rapor oluşturma: < 5 saniye
- Eşzamanlı kullanıcı: 100+

#### 6.4.2 Önbellekleme
- Statik dosyalar: CDN
- Veritabanı sorguları: Redis
- Oturum verileri: Redis
- Rapor önbellekleme: 1 saat

#### 6.4.3 Yedekleme Stratejisi
- Günlük otomatik yedek
- Haftalık tam yedek
- Aylık arşiv yedek
- Yedek saklama: 90 gün

---

## 7. Güvenlik ve Yetkilendirme

### 7.1 Güvenlik Grupları

#### 7.1.1 Tender Requester (İhale Talep Edici)

**Yetkiler**:
- ✅ Kendi ihalelerini görüntüleme
- ✅ Yeni ihale talebi oluşturma
- ✅ Kendi ihale kalemlerini oluşturma
- ❌ İhale düzenleme
- ❌ İhale silme
- ❌ Tedarikçi ekleme

**Kullanım Senaryosu**: Departman çalışanları, talep oluşturma

#### 7.1.2 Tender User (İhale Kullanıcısı)

**Yetkiler**:
- ✅ Kendi ihalelerini görüntüleme ve düzenleme
- ✅ Yeni ihale oluşturma
- ✅ Tedarikçi ekleme
- ✅ E-posta gönderme
- ❌ İhale silme
- ❌ Tüm ihaleleri görüntüleme

**Kullanım Senaryosu**: Satın alma uzmanları

#### 7.1.3 Tender Manager (İhale Yöneticisi)

**Yetkiler**:
- ✅ Tüm ihaleleri görüntüleme, düzenleme, silme
- ✅ Tüm ihale kalemlerini yönetme
- ✅ İhale süreçlerini onaylama
- ✅ Hedef fiyat belirleme
- ✅ Kazanan seçimi
- ✅ Sipariş oluşturma
- ✅ Raporlara tam erişim

**Kullanım Senaryosu**: Satın alma müdürleri, yöneticiler

### 7.2 Güvenlik Kuralları

#### 7.2.1 Kayıt Seviyesi Güvenlik (Record Rules)

**İhale Kuralları**:
```python
# Requester: Sadece kendi ihaleleri
domain = [('create_uid', '=', user.id)]

# User: Kendi ihaleleri
domain = [('create_uid', '=', user.id)]

# Manager: Tüm ihaleler
domain = []
```

#### 7.2.2 Alan Seviyesi Güvenlik (Field Level)

**Hassas Alanlar**:
- Hedef fiyat: Sadece Manager
- NPV değerleri: Sadece Manager
- Tedarikçi maliyetleri: Sadece Manager

### 7.3 Veri Güvenliği

#### 7.3.1 Şifreleme
- SSL/TLS: Tüm iletişim
- Veritabanı: Hassas alanlar şifreli
- Dosyalar: Şifreli depolama
- Yedekler: Şifreli

#### 7.3.2 Denetim İzi (Audit Trail)
- Tüm değişiklikler loglanır
- Kullanıcı, tarih, işlem kaydedilir
- Silme işlemleri geri alınamaz (soft delete)
- Log saklama: 2 yıl

#### 7.3.3 Veri Gizliliği
- KVKK uyumlu
- GDPR uyumlu
- Kişisel veri maskeleme
- Veri silme hakkı

---

## 8. Raporlama ve Analiz

### 8.1 Standart Raporlar

#### 8.1.1 Tedarikçi Karşılaştırma Raporu

**Rapor Özellikleri**:
- Kalem bazında karşılaştırma
- Fiyat, teslimat, garanti analizi
- NPV hesaplamaları
- Otomatik kazanan seçimi
- Görsel vurgulama (en düşük yeşil)

**Rapor Bölümleri**:
1. Özet bilgiler
2. Kalem bazında detay
3. Toplam maliyet karşılaştırması
4. NPV analizi
5. Öneriler

#### 8.1.2 İhale Performans Raporu

**Metrikler**:
- Ortalama ihale süresi
- Teklif sayısı ortalaması
- Maliyet tasarrufu oranı
- Zamanında teslim oranı
- Tedarikçi katılım oranı

#### 8.1.3 Tedarikçi Performans Raporu

**Değerlendirme Kriterleri**:
- Teklif verme oranı
- Kazanma oranı
- Fiyat rekabetçiliği
- Teslimat performansı
- Kalite skoru

### 8.2 Analitik Raporlar

#### 8.2.1 Maliyet Tasarrufu Analizi

**Hesaplama**:
```
Tasarruf = (İlk Teklif - Nihai Fiyat) / İlk Teklif * 100

Örnek:
İlk Teklif: 100.000 TL
Nihai Fiyat: 85.000 TL
Tasarruf: %15
```

#### 8.2.2 Kategori Bazlı Analiz

**Analizler**:
- Kategori bazlı harcama
- Tedarikçi dağılımı
- Fiyat trendleri
- Sezonsal analiz

### 8.3 Dashboard ve KPI'lar

#### 8.3.1 İhale Dashboard

**KPI'lar**:
- Aktif ihale sayısı
- Bekleyen onay sayısı
- Bu ay tamamlanan ihaleler
- Toplam tasarruf
- Ortalama ihale süresi

#### 8.3.2 Tedarikçi Dashboard

**KPI'lar**:
- Toplam tedarikçi sayısı
- Aktif tedarikçi sayısı
- Ortalama teklif sayısı
- En çok kazanan tedarikçiler
- Performans skoru dağılımı

---

## 9. Entegrasyonlar

###
 9.1 SAP/ERP Entegrasyonu

#### 9.1.1 Entegrasyon Mimarisi

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   SAP/ERP   │ ←────→  │  Middleware │ ←────→  │   İLKOis    │
└─────────────┘         └─────────────┘         └─────────────┘
      │                        │                        │
      │                        │                        │
   Master Data            Mapping &              Tender Data
   (Ürün, Tedarikçi)     Transformation         (İhale, Teklif)
```

#### 9.1.2 Veri Akışları

**ERP → İLKOis**:
- Ürün master verisi
- Tedarikçi bilgileri
- Satın alma talepleri
- Stok durumu
- Bütçe bilgileri

**İLKOis → ERP**:
- Onaylı siparişler
- Teslim bilgileri
- Fatura bilgileri
- Maliyet verileri

#### 9.1.3 Entegrasyon Yöntemleri

**1. REST API**:
```python
# Örnek API çağrısı
response = requests.post(
    'https://erp.company.com/api/purchase_orders',
    json={
        'tender_id': 'TND/2024/001',
        'vendor': 'Tedarikçi A',
        'items': [...]
    },
    headers={'Authorization': 'Bearer TOKEN'}
)
```

**2. File Transfer (SFTP)**:
- Günlük veri dosyaları
- Excel/CSV formatında
- Otomatik import/export

**3. Database Link**:
- Direkt veritabanı bağlantısı
- Real-time veri senkronizasyonu

### 9.2 E-posta Sistemi Entegrasyonu

#### 9.2.1 SMTP Yapılandırması

**Giden E-posta**:
```
SMTP Server: smtp.company.com
Port: 587 (TLS) / 465 (SSL)
Authentication: Yes
From: noreply@ilkois.com.tr
```

#### 9.2.2 IMAP Yapılandırması (SAT Import)

**Gelen E-posta**:
```
IMAP Server: mail.ilko.com.tr
Port: 993 (SSL)
Email: ilkoisdata@ilko.com.tr
Folder: INBOX
Check Interval: 1 hour
```

#### 9.2.3 E-posta Şablonları

**Şablon Tipleri**:
- İhale daveti
- Teklif onayı
- Kazanma bildirimi
- Sipariş onayı
- Hatırlatma e-postaları

### 9.3 Portal Entegrasyonu

#### 9.3.1 Tedarikçi Portal

**Özellikler**:
- Single Sign-On (SSO)
- Responsive tasarım
- Mobil uyumlu
- Çoklu dil desteği

**Erişim Seviyeleri**:
- Tedarikçi yöneticisi: Tam erişim
- Tedarikçi kullanıcısı: Teklif verme
- Tedarikçi görüntüleyici: Sadece okuma

### 9.4 Onay Sistemi Entegrasyonu

#### 9.4.1 Approvals Modülü

**Onay Akışları**:
```
Talep → Yönetici → Müdür → Genel Müdür
```

**Onay Kuralları**:
- Tutar bazlı
- Kategori bazlı
- Departman bazlı
- Özel koşullar

---

## 10. Sık Sorulan Sorular (SSS)

### 10.1 Genel Sorular

**S: İLKOis hangi sektörlerde kullanılabilir?**
C: İLKOis, satın alma ve ihale süreçleri olan her sektörde kullanılabilir: İmalat, perakende, hizmet, kamu, eğitim, sağlık, vb.

**S: Kaç kullanıcı desteklenir?**
C: Sistem, sınırsız kullanıcı destekler. Performans, sunucu kapasitesine bağlıdır. Standart kurulumda 100+ eşzamanlı kullanıcı desteklenir.

**S: Mobil uygulama var mı?**
C: Şu anda native mobil uygulama yok, ancak sistem responsive tasarıma sahip ve mobil tarayıcılardan kullanılabilir.

**S: Hangi dilleri destekliyor?**
C: Şu anda Türkçe ve İngilizce desteklenmektedir. Yeni diller kolayca eklenebilir.

### 10.2 Teknik Sorular

**S: Hangi veritabanlarını destekliyor?**
C: PostgreSQL 13+ desteklenmektedir. Odoo'nun resmi veritabanıdır.

**S: Cloud'da çalışır mı?**
C: Evet, AWS, Azure, Google Cloud gibi tüm cloud platformlarında çalışır.

**S: Yedekleme nasıl yapılır?**
C: Otomatik günlük yedekleme mevcuttur. Manuel yedekleme de yapılabilir. Yedekler şifreli olarak saklanır.

**S: API dokümantasyonu var mı?**
C: Evet, Swagger/OpenAPI formatında API dokümantasyonu mevcuttur.

### 10.3 İş Süreci Soruları

**S: İhale süreci ne kadar sürer?**
C: İhale tipine ve karmaşıklığına bağlı olarak 1-4 hafta arası sürebilir.

**S: Kaç tedarikçi eklenebilir?**
C: Sınırsız tedarikçi eklenebilir. Ancak ihale başına 20-30 tedarikçi önerilir.

**S: Hedef fiyat zorunlu mu?**
C: Hayır, hedef fiyat opsiyoneldir. Ancak 2 turlu ihaleler için önerilir.

**S: Alternatif ürün teklifi nasıl değerlendirilir?**
C: İhale yöneticisi, alternatif ürünleri teknik şartnameye uygunluk açısından değerlendirir ve onaylar.

### 10.4 Güvenlik Soruları

**S: Veriler güvende mi?**
C: Evet, SSL/TLS şifreleme, veritabanı şifreleme, rol tabanlı erişim kontrolü ve düzenli güvenlik güncellemeleri ile veriler korunur.

**S: KVKK uyumlu mu?**
C: Evet, sistem KVKK ve GDPR gerekliliklerine uygundur.

**S: Denetim izi tutuluyor mu?**
C: Evet, tüm işlemler loglanır ve 2 yıl saklanır.

### 10.5 Destek Soruları

**S: Teknik destek nasıl alınır?**
C: E-posta, telefon ve online ticket sistemi üzerinden 7/24 destek sağlanır.

**S: Eğitim veriliyor mu?**
C: Evet, kurulum sonrası kullanıcı eğitimleri verilir. Online eğitim materyalleri de mevcuttur.

**S: Güncelleme nasıl yapılır?**
C: Sistem güncellemeleri otomatik veya manuel olarak yapılabilir. Güncelleme öncesi yedekleme önerilir.

---

## 11. Ek Bilgiler

### 11.1 Sistem Gereksinimleri Özeti

#### Sunucu
- **OS**: Linux (Ubuntu 20.04+ / Debian 11+)
- **CPU**: 2+ cores
- **RAM**: 8GB+ (16GB önerilir)
- **Disk**: 50GB+ SSD
- **Network**: 100 Mbps+

#### İstemci
- **Tarayıcı**: Modern tarayıcılar (Chrome, Firefox, Safari, Edge)
- **Ekran**: 1366x768+ (1920x1080 önerilir)
- **İnternet**: 2 Mbps+

### 11.2 Lisanslama

**Odoo 18 CE**: LGPL-3 lisansı (Açık kaynak)
**İLKOis Modülü**: LGPL-3 lisansı
**Ticari Destek**: Kardan.Digital

### 11.3 Versiyon Geçmişi

| Versiyon | Tarih | Özellikler |
|----------|-------|------------|
| 0.1 | 2023-Q1 | İlk prototip |
| 0.2 | 2023-Q2 | İş akışı entegrasyonu |
| 0.3 | 2023-Q3 | Portal geliştirmeleri |
| 0.4 | 2023-Q4 | NPV hesaplamaları |
| 0.5 | 2024-Q1 | Multi-currency desteği |

### 11.4 Gelecek Özellikler (Roadmap)

#### Kısa Vadeli (3-6 ay)
- [ ] Mobil uygulama (iOS/Android)
- [ ] Gelişmiş raporlama (BI entegrasyonu)
- [ ] E-imza entegrasyonu
- [ ] Blockchain entegrasyonu (şeffaflık için)

#### Orta Vadeli (6-12 ay)
- [ ] AI destekli fiyat tahmini
- [ ] Otomatik tedarikçi önerisi
- [ ] Chatbot desteği
- [ ] Video konferans entegrasyonu

#### Uzun Vadeli (12+ ay)
- [ ] IoT entegrasyonu (stok takibi)
- [ ] Blockchain tabanlı akıllı sözleşmeler
- [ ] Predictive analytics
- [ ] Quantum-safe şifreleme

### 11.5 İletişim Bilgileri

**Geliştirici**: Kardan.Digital
**Web**: https://www.kardan.digital
**E-posta**: info@kardan.digital
**Destek**: support@kardan.digital
**Telefon**: +90 (XXX) XXX XX XX

### 11.6 Kaynaklar

**Dokümantasyon**:
- Kullanıcı Kılavuzu
- Yönetici Kılavuzu
- API Dokümantasyonu
- Geliştirici Kılavuzu

**Eğitim Materyalleri**:
- Video eğitimler
- Webinarlar
- Örnek senaryolar
- Best practices

**Topluluk**:
- Forum
- GitHub repository
- Stack Overflow
- LinkedIn grubu

---

## 12. Sonuç

İLKOis İhale Yönetim Sistemi, modern satın alma ve ihale süreçlerini dijitalleştiren, şeffaf ve verimli bir çözümdür. Odoo 18 CE platformu üzerinde geliştirilmiş olması, güçlü bir altyapı ve geniş entegrasyon imkanları sağlar.

### 12.1 Temel Avantajlar

✅ **Dijital Dönüşüm**: Kağıt bazlı süreçlerin tamamen dijitalleşmesi
✅ **Maliyet Tasarrufu**: Rekabetçi fiyatlandırma ve NPV analizleri ile %10-20 tasarruf
✅ **Zaman Tasarrufu**: Otomatik iş akışları ile %50 süre tasarrufu
✅ **Şeffaflık**: Tüm süreçlerin izlenebilir ve denetlenebilir olması
✅ **Esneklik**: Farklı ihale tiplerini destekleyen modüler yapı
✅ **Güvenlik**: Rol tabanlı erişim kontrolü ve veri şifreleme
✅ **Entegrasyon**: ERP, e-posta ve diğer sistemlerle sorunsuz entegrasyon

### 12.2 Başarı Metrikleri

- **İhale Süresi**: %50 azalma
- **Maliyet Tasarrufu**: %15 ortalama
- **Tedarikçi Katılımı**: %30 artış
- **Hata Oranı**: %80 azalma
- **Kullanıcı Memnuniyeti**: %90+

### 12.3 Sonraki Adımlar

1. **Demo Talebi**: Test ortamında sistem demosu
2. **İhtiyaç Analizi**: Kurumsal ihtiyaçların belirlenmesi
3. **Pilot Uygulama**: Seçili departmanda pilot çalışma
4. **Eğitim**: Kullanıcı ve yönetici eğitimleri
5. **Canlıya Geçiş**: Tam kapsamlı kullanıma başlama
6. **Sürekli İyileştirme**: Geri bildirimler ve güncellemeler

---

**Doküman Versiyonu**: 1.0
**Son Güncelleme**: 30 Ekim 2024
**Hazırlayan**: Kardan.Digital
**Durum**: Final

---

## Ekler

### Ek A: Ekran Görüntüleri
(Ekran görüntüleri ayrı dosyada)

### Ek B: Örnek Raporlar
(Örnek raporlar ayrı dosyada)

### Ek C: API Dokümantasyonu
(API dokümantasyonu ayrı dosyada)

### Ek D: Kurulum Kılavuzu
(Kurulum kılavuzu ayrı dosyada)

---

**© 2024 Kardan.Digital - Tüm hakları saklıdır.**