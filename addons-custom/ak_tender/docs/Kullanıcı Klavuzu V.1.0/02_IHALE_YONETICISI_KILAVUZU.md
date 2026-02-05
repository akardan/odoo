# İhale Yöneticisi Kullanıcı Kılavuzu

**Versiyon:** 1.0
**Tarih:** 3 Şubat 2026
**Hedef Kullanıcı:** İhale Yöneticileri, Satın Alma Uzmanları

---

## 📋 İçindekiler

1. [Giriş](#1-giriş)
2. [İhale Oluşturma](#2-ihale-oluşturma)
3. [Tedarikçi Yönetimi](#3-tedarikçi-yönetimi)
4. [Teklif Toplama ve Takibi](#4-teklif-toplama-ve-takibi)
5. [Hedef Fiyat Belirleme](#5-hedef-fiyat-belirleme)
6. [Değerlendirme ve Karar](#6-değerlendirme-ve-karar)
7. [Onay Süreçleri](#7-onay-süreçleri)
8. [Sipariş Onaylama ve Tamamlama](#8-sipariş-onaylama-ve-tamamlama)
9. [Raporlama](#9-raporlama)
10. [İpuçları ve En İyi Uygulamalar](#10-ipuçları-ve-en-iyi-uygulamalar)
11. [Sık Sorulan Sorular](#11-sık-sorulan-sorular)

---

## 1. Giriş

### 1.1 Kılavuz Hakkında

Bu kılavuz, İLKOis İhale Yönetim Sistemi'nde ihale yöneticisi rolündeki kullanıcılar için hazırlanmıştır. İhale oluşturma, teklif değerlendirme, onay süreçleri ve sipariş oluşturma gibi tüm işlemleri adım adım açıklar.

### 1.2 Hedef Kullanıcılar

- İhale Yöneticileri
- Satın Alma Uzmanları
- Satın Alma Müdürleri
- Satın Alma Direktörleri

### 1.3 Ön Koşullar

- ✅ Odoo sistemi kullanıcı hesabı
- ✅ "Tender Manager" veya "Tender User" yetkisi
- ✅ Temel Odoo bilgisi
- ✅ İhale süreçleri hakkında bilgi

---

## 2. İhale Oluşturma

### 2.1 SAT'lardan İhale Oluşturma

#### Adım 1: SAT Havuzuna Erişim

1. Ana menüden **İhale → Talepler → SAT Kalemleri** seçin
2. İşlenmemiş SAT kalemlerini görüntüleyin
3. Filtreleme seçeneklerini kullanın:
   - Malzeme Grubu
   - Satınalma Grubu
   - Üretim Yeri
   - İhale Tipi

#### Adım 2: SAT Kalemlerini Seçme

1. İhaleye dahil etmek istediğiniz kalemleri seçin
2. Toplu seçim için:
   - Filtre uygula
   - "Tümünü Seç" kutucuğunu işaretle
3. Seçili kalemleri kontrol edin

#### Adım 3: İhale Oluşturma

1. **Eylem** menüsünden **"İhale Oluştur"** seçin
2. İhale Oluşturma Sihirbazı açılır
3. Gerekli bilgileri girin:

| Alan | Açıklama | Zorunlu |
|------|----------|---------|
| İhale Adı | Açıklayıcı başlık | ✅ |
| İhale Tipi | direct/indirect/mice/promotion | ✅ |
| Para Birimi | TRY/USD/EUR | ✅ |
| Başlangıç Tarihi | İhale başlangıç tarihi | ✅ |
| Bitiş Tarihi | İhale bitiş tarihi | ✅ |
| Teslim Tarihi | Gerekli teslim tarihi | ✅ |

4. **"İhale Oluştur"** butonuna tıklayın
5. İhale otomatik olarak oluşturulur ve TASLAK durumunda açılır

### 2.2 Manuel İhale Oluşturma

#### Adım 1: Yeni İhale Formu

1. **İhale → İhaleler → Tüm İhaleler** menüsüne gidin
2. **Oluştur** butonuna tıklayın
3. Yeni ihale formu açılır

#### Adım 2: Temel Bilgileri Girme

**Üst Bilgi Bölümü**:
```
İhale Adı: 2024 Q1 Ofis Malzemeleri İhalesi
İhale Tipi: Indirect
Para Birimi: TRY
Başlangıç Tarihi: 01.03.2024
Bitiş Tarihi: 15.03.2024
Teslim Tarihi: 30.03.2024
```

#### Adım 3: İhale Kalemlerini Ekleme

1. **İhale Kalemleri** sekmesine gidin
2. **Satır Ekle** butonuna tıklayın
3. Her kalem için:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| Ürün | Ürün seçimi | Yazıcı Kartuşu HP 305A |
| Miktar | İstenen miktar | 100 |
| Birim | Ölçü birimi | Adet |
| Hedef Fiyat | Beklenen fiyat (opsiyonel) | 150.00 |
| Teslim Tarihi | Kalem teslim tarihi | 30.03.2026 |

4. Gerektiği kadar kalem ekleyin
5. **Kaydet** butonuna tıklayın

### 2.3 İhale Şablonu Kullanma

#### Şablon Seçimi

1. İhale formunda **Eylem → Şablon Uygula** seçin
2. Mevcut şablonlardan birini seçin:
   - Ofis Malzemeleri Şablonu
   - Laboratuvar Malzemeleri Şablonu
   - MICE Organizasyon Şablonu
3. Şablon otomatik olarak uygulanır
4. Gerekirse özelleştirin

#### Yeni Şablon Oluşturma

1. Mevcut bir ihaleyi açın
2. **Eylem → Şablon Olarak Kaydet** seçin
3. Şablon adı girin
4. Şablon kaydedilir ve gelecekte kullanılabilir

---

## 3. Tedarikçi Yönetimi

### 3.1 Tedarikçi Ekleme

#### Manuel Tedarikçi Ekleme

1. İhale formunda **Tedarikçiler** sekmesine gidin
2. **Satır Ekle** butonuna tıklayın
3. Tedarikçi listesinden seçim yapın
4. Birden fazla tedarikçi ekleyebilirsiniz

#### Toplu Tedarikçi Ekleme

1. **Eylem → Toplu Tedarikçi Ekle** seçin
2. Excel dosyası yükleyin (şablon indirebilirsiniz)
3. Tedarikçiler otomatik olarak eklenir

#### Coğrafi Filtreleme (MICE İhaleleri)

1. **Tedarikçiler** sekmesinde **Filtrele** butonuna tıklayın
2. Filtreleme kriterleri:
   - Ülke
   - İl
   - Şehir/İlçe
3. Uygun tedarikçiler listelenir
4. Seçim yapın ve ekleyin

### 3.2 Tedarikçi Daveti

#### E-posta Şablonu Hazırlama

1. **Tedarikçiler** sekmesinde tedarikçileri seçin
2. **Toplu E-posta Gönder** butonuna tıklayın
3. E-posta şablonu otomatik yüklenir:
   - İhale detayları
   - Portal erişim linki
   - Teklif verme talimatları
   - Son tarih bilgisi
4. Gerekirse şablonu özelleştirin
5. **Gönder** butonuna tıklayın

#### E-posta Gönderim Kontrolü

- Gönderilen e-postalar **Chatter** bölümünde görünür
- Her tedarikçi için gönderim durumu kontrol edilebilir
- Hata durumunda tekrar gönderim yapılabilir

### 3.3 Dinamik Tedarikçi Ekleme

İhale başladıktan sonra bile yeni tedarikçi ekleyebilirsiniz:

1. **Tedarikçiler** sekmesinde **Satır Ekle**
2. Yeni tedarikçi seçin
3. **Davet E-postası Gönder** işaretini koyun
4. Kaydet
5. Tedarikçiye otomatik davet gönderilir

---

## 4. Teklif Toplama ve Takibi

### 4.1 İhaleyi Başlatma

#### İş Akışı Geçişi

1. İhale formunda **İhaleyi Başlat** butonuna tıklayın
2. Onay mesajı görüntülenir
3. İhale durumu **"1. Teklif Toplama"** olur
4. Tedarikçilere otomatik davet e-postaları gönderilir
5. Portal'da ihale görünür hale gelir

### 4.2 Teklif Takibi

#### Teklif Tamamlanma Göstergesi

İhale formunda:
- **Teklif Sayısı**: Alınan teklif sayısı
- **Davet Edilen**: Toplam davet edilen tedarikçi
- **Tamamlanma Oranı**: Yüzde olarak gösterilir
- **Durum Rengi**: 
  - 🔴 Kırmızı: Teklif yok
  - 🟡 Sarı: Devam ediyor
  - 🟢 Yeşil: Tamamlandı

#### Teklifleri Görüntüleme

1. **Teklifler (SAT)** sekmesine gidin
2. Tüm teklifler listelenir:
   - Tedarikçi adı
   - Teklif durumu
   - Toplam tutar
   - Teklif tarihi
3. Detay görmek için teklif satırına tıklayın

### 4.3 Teklif Karşılaştırma

#### Karşılaştırma Raporu Oluşturma

1. İhale formunda **Teklifleri Karşılaştır** seçin
2. Rapor otomatik oluşturulur
3. Rapor içeriği:
   - Kalem bazında fiyat karşılaştırması
   - En düşük fiyat vurgulama (yeşil)
   - NPV hesaplamaları
   - Sistem seçimi (mavi, otomatik)
   - Teslimat tarihi karşılaştırması
   - Garanti süresi karşılaştırması
   - Toplam maliyet analizi

#### NPV (Net Bugünkü Değer) Hesaplaması

Sistem otomatik olarak NPV hesaplar:

```
NPV = Ödeme Tutarı / (1 + NPV Oranı)^(Gün Sayısı/365)

Örnek:
Fiyat: 10.000 TL
Vade: 90 gün
NPV Oranı: %15
NPV = 10.000 / (1 + 0.15)^(90/365) = 9.650 TL
```

---

## 5. Hedef Fiyat Belirleme

### 5.1 Hedef Fiyat Belirleme Yöntemleri

İhale sisteminde hedef fiyat belirleme iki şekilde yapılabilir:

#### Yöntem 1: Manuel Hedef Fiyat Belirleme (Eylem Menüsü)

1. İhale formunda **Eylem → Hedef Fiyat Belirle** seçin
4. Her kalem için hedef fiyat belirlenir

#### Yöntem 2: Otomatik Hedef Fiyat Belirleme (Workflow)

İş akışı geçişi sırasında otomatik olarak:
1. İhale durumu **"1. Teklif Toplama"** → **"Hedef Fiyat Belirlendi"** geçişinde
2. Sistem otomatik olarak hedef fiyat belirleme işlemini tetikler
3. En düşük teklifler baz alınarak hedef fiyatlar otomatik belirlenir
4. Gerekirse manuel olarak düzenleyebilirsiniz

### 5.2 Hedef Fiyat Sihirbazı

#### Hedef Fiyat Belirleme Stratejileri

**1. En Düşük Teklifi Baz Al (Otomatik)**:
```
Sistem otomatik olarak en düşük teklifi hedef fiyat olarak belirler
Bu yöntem workflow geçişinde varsayılan olarak kullanılır
```

**2. Manuel Fiyat Gir**:
```
Her kalem için özel fiyat girebilirsiniz
Bütçe kısıtları veya özel durumlar için kullanılır
```

**3. Yüzde İndirim Uygula**:
```
En düşük teklife %X indirim uygulayarak hedef belirleyin
Örnek: En düşük 100 TL, %10 indirim = 90 TL hedef
2. tur için daha agresif fiyat hedefi belirleme
```

**4. Piyasa Fiyatı**:
```
Piyasa araştırması sonucu belirlenen fiyat
Referans fiyat olarak kullanılır
```

### 5.3 Hedef Fiyatları Kaydetme

1. Tüm kalemlerin hedef fiyatlarını belirleyin (manuel veya otomatik)
2. Toplam bütçeyi kontrol edin
3. Yeni tur için hazır hale gelir

**Not:** Workflow geçişi ile otomatik belirlenen hedef fiyatlar, eylem menüsünden tekrar hesaplanabilir yada ihale kalemlerinde manuel düzenlenebilir.

### 5.4 Yeni Tur Başlatma

1. İhale formunda **Yeni Teklif Turu Başlat** butonuna tıklayın
2. Teklif Turu artırılır, Teklif Talepleri oluşturulur ve Tedarikçilere bildirim e-postaları gönderilir
3. E-postada:
   - Hedef fiyatlar 
   - Yeni teklif istenir
   - Son tarih belirtilir
4. İhale durumu **"Yeni Teklif Turu"** olur

---

## 6. Onay Süreçleri

### 7.1 Onay Hiyerarşisi

**Seviye Bazlı Onay Sistemi**:

| Seviye | Onaylayıcı | Koşul |
|--------|-----------|-------|
| 1 | Satınalma Direktörü | Tüm tutarlar (Zorunlu) |
| 2 | YK Üyesi (Alperen Bey) | 1. Seviye + koşul |
| 3 | YK Üyesi (İsmail Bey) | 2. Seviye + koşul |

### 7.2 Onay Durumu Takibi

**Chatter** bölümünde:
- Onay talepleri
- Onaylayan kişiler
- Onay tarihleri
- Red durumları ve gerekçeleri

### 7.3 "Son Onay?" Mekanizması

Satınalma Direktörü onayında:
- ✅ **"Son Onay?" işaretli**: Süreç tamamlanır, sipariş oluşturulabilir
- ❌ **"Son Onay?" işaretsiz**: Onay akışı devam eder (YK onayına gider)

---

## 8. Sipariş Onaylama ve Tamamlama

### 8.1 Onay Sonrası İşlemler

#### Siparişleri Onaylama

1. İhale onaylandıktan sonra
2. Değerlendirme aşamasında oluşturulan siparişler **Taslak** durumundan çıkar
3. Her siparişi tek tek onaylayın veya toplu onay yapın

#### Sipariş Onaylama Adımları

1. **Teklifler (SAT)** sekmesinden siparişleri görüntüleyin
2. Her siparişi açın ve kontrol edin
3. **Onayla** butonuna tıklayın
4. Sipariş durumu **"Satın Alma Siparişi"** olur

### 8.2 Tedarikçiye Bildirim

Sipariş onaylandığında:
- Tedarikçiye otomatik e-posta gönderilir
- E-postada:
  - Sipariş detayları
  - Sipariş PDF'i ekte
  - Teslimat talimatları
  - İletişim bilgileri

### 8.3 İhaleyi Tamamlama

1. Tüm siparişler onaylandıktan sonra
2. İhale durumu otomatik olarak **"Tamamlandı"** olur
3. İhale kapatılır
4. Süreç tamamlanmış olur

**Tamamlanan İhalede:**
- Yeni teklif alınamaz
- Siparişler takip edilir
- Raporlar oluşturulabilir
- Arşivlenir