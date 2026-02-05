# Tedarikçi Portal Kullanıcı Kılavuzu

**Versiyon:** 1.0  
**Tarih:** 3 Şubat 2026  
**Hedef Kullanıcı:** Tedarikçiler

---

## 📋 İçindekiler

1. [Portal Erişimi](#1-portal-erişimi)
2. [Dashboard ve Ana Sayfa](#2-dashboard-ve-ana-sayfa)
3. [İhale Görüntüleme](#3-ihale-görüntüleme)
4. [Teklif Verme](#4-teklif-verme)
5. [Sipariş Takibi](#5-sipariş-takibi)
6. [Belge Yönetimi](#6-belge-yönetimi)
7. [Profil Ayarları](#7-profil-ayarları)
8. [Sık Sorulan Sorular](#8-sık-sorulan-sorular)

---

## 1. Portal Erişimi

### 1.1 İlk Giriş

#### Davet E-postası

Başvurunuz onaylandığında size bir e-posta gelir:

```
Konu: Portal Erişiminiz Hazır

Başvurunuz onaylandı! 🎉

Portal: https://ilkois.ilko.com.tr
Kullanıcı Adı: tedarikci@firma.com

Şifrenizi oluşturmak için aşağıdaki linke tıklayın:
[Şifre Oluştur]
```

#### Şifre Oluşturma

1. E-postadaki "Şifre Oluştur" linkine tıklayın
2. Yeni şifre oluşturma sayfası açılır
3. Güçlü bir şifre belirleyin:
   - Minimum 8 karakter
   - En az 1 büyük harf
   - En az 1 küçük harf
   - En az 1 rakam
4. Şifreyi onaylayın
5. **"Şifreyi Kaydet"** butonuna tıklayın

### 1.2 Portal'a Giriş

1. Tarayıcınızda `https://ilkois.ilko.com.tr` adresini açın
2. Giriş sayfasında:
   - **E-posta**: tedarikci@firma.com
   - **Şifre**: Oluşturduğunuz şifre
3. **"Giriş Yap"** butonuna tıklayın
4. Portal ana sayfası açılır

### 1.3 Şifremi Unuttum

1. Giriş sayfasında **"Şifremi Unuttum"** linkine tıklayın
2. E-posta adresinizi girin
3. **"Şifre Sıfırlama Linki Gönder"** butonuna tıklayın
4. E-postanıza gelen linke tıklayın
5. Yeni şifre oluşturun

---

## 2. Dashboard ve Ana Sayfa

### 2.1 Dashboard Özellikleri

Portal ana sayfasında görebileceğiniz bilgiler:

#### İstatistikler

| Kart | Açıklama |
|------|----------|
| **Bekleyen İhaleler** | Teklif vermeniz gereken aktif ihaleler |
| **Teklif Verilen** | Teklif verdiğiniz ihaleler |
| **Kazanılan İhaleler** | Kazandığınız ihaleler |
| **Aktif Siparişler** | Devam eden siparişleriniz |

#### Son Aktiviteler

- Yeni ihale bildirimleri
- Teklif durumu güncellemeleri
- Sipariş bildirimleri
- Sistem mesajları

### 2.2 Hızlı Erişim Menüsü

```
Portal Ana Menü
├── İhaleler
│   ├── Aktif İhaleler
│   ├── Teklif Verilenler
│   └── Tamamlanan İhaleler
├── Siparişler
│   ├── Bekleyen Siparişler
│   └── Tamamlanan Siparişler
├── Belgeler
│   ├── Sözleşmeler
│   └── Faturalar
└── Profil
    ├── Firma Bilgileri
    └── Şifre Değiştir
```

---

## 3. İhale Görüntüleme

### 3.1 İhale Listesi

#### Aktif İhaleler

1. Ana menüden **İhaleler → Aktif İhaleler** seçin
2. Teklif vermeniz gereken ihaleler listelenir
3. Her ihale için:
   - İhale adı
   - İhale numarası
   - Son teklif tarihi
   - Kalan süre
   - Durum

#### Filtreleme

- **Duruma Göre**: Aktif, Bekleyen, Tamamlanan
- **Tarihe Göre**: Son 7 gün, Son 30 gün, Özel tarih aralığı
- **Arama**: İhale adı veya numarasına göre

### 3.2 İhale Detayları

#### İhale Bilgilerini Görüntüleme

1. İhale listesinden bir ihaleye tıklayın
2. İhale detay sayfası açılır
3. Görüntüleyebileceğiniz bilgiler:

**Genel Bilgiler**:
- İhale adı ve numarası
- İhale tipi
- Başlangıç ve bitiş tarihleri
- Teslim tarihi
- Para birimi

**İhale Kalemleri**:
- Ürün/Hizmet adı
- Miktar ve birim
- Teknik şartname
- Özel notlar
- Ekler (PDF, resim)

**Özel Şartlar**:
- Ödeme koşulları
- Teslimat koşulları
- Garanti şartları
- Diğer özel koşullar

#### Belgeleri İndirme

1. İhale detay sayfasında **Belgeler** bölümüne gidin
2. İndirmek istediğiniz belgeye tıklayın:
   - Teknik şartname
   - Ürün resimleri
   - Özel talimatlar
3. Belge otomatik indirilir

---

## 4. Teklif Verme

### 4.1 Teklif Formu

#### Teklif Verme Adımları

1. İhale detay sayfasında **"Teklif Ver"** butonuna tıklayın
2. Teklif formu açılır
3. Her kalem için bilgileri girin

#### Kalem Bazında Teklif

| Alan | Açıklama | Zorunlu | Örnek |
|------|----------|---------|-------|
| **Birim Fiyat** | Teklif ettiğiniz fiyat | ✅ | 150.00 |
| **Teslimat Tarihi** | Teslim edebileceğiniz tarih | ✅ | 30.03.2024 |
| **Garanti Süresi** | Garanti süresi | ✅ | 12 ay |
| **İndirim Oranı** | Yüzde cinsinden | ❌ | %5 |
| **Alternatif Ürün** | Muadil ürün önerisi | ❌ | Marka B Model Y |
| **Vergi** | KDV oranı | ✅ | %20 |
| **Not** | Özel notlar | ❌ | Toplu alımda indirim |

### 4.2 Alternatif Ürün Teklifi

#### Muadil Ürün Önerme

1. Kalem satırında **"Alternatif Ürün"** alanını doldurun
2. Alternatif ürün bilgileri:
   - Marka ve model
   - Teknik özellikler
   - Fiyat avantajı
   - Gerekçe
3. Gerekirse teknik doküman ekleyin

**Örnek**:
```
Talep Edilen: Marka A - Model X
Alternatif: Marka B - Model Y
Gerekçe: Aynı teknik özellikler, %20 daha ucuz, 2 yıl garanti
```

### 4.3 Toplu Kaydetme

#### Ara Kayıt

- Teklif verme sırasında istediğiniz zaman **"Kaydet"** butonuna tıklayın
- Teklifleriniz kaydedilir
- Daha sonra devam edebilirsiniz
- Son tarihten önce istediğiniz kadar değişiklik yapabilirsiniz

#### Teklifi Gönderme

1. Tüm alanları doldurduktan sonra
2. Teklifinizi son kez kontrol edin
3. **"Teklifi Gönder"** butonuna tıklayın
4. Onay mesajı:
   ```
   ✅ Teklifiniz Başarıyla Gönderildi!
   
   İhale No: TND/2024/001
   Teklif Tarihi: 15.03.2024 14:30
   
   Teklif özeti e-postanıza gönderildi.
   ```

### 4.4 Teklif Sonrası

#### E-posta Onayı

Teklif gönderdikten sonra size bir e-posta gelir:

```
Konu: Teklifiniz Alındı

Sayın Tedarikçi,

TND/2024/001 numaralı ihale için teklifiniz alınmıştır.

Teklif Özeti:
- Toplam Kalem: 10
- Toplam Tutar: 15.000,00 TL
- Teklif Tarihi: 15.03.2024 14:30

Değerlendirme sonuçları size bildirilecektir.
```

#### Teklif Güncelleme

İhale süresi dolmadan:
1. İhale detay sayfasına gidin
2. **"Teklifi Güncelle"** butonuna tıklayın
3. Değişiklik yapın
4. **"Teklifi Gönder"** butonuna tıklayın
5. Eski teklif güncellenir

---

## 5. Sipariş Takibi

### 5.1 Sipariş Listesi

#### Siparişleri Görüntüleme

1. Ana menüden **Siparişler** seçin
2. Tüm siparişleriniz listelenir:
   - Sipariş numarası
   - İhale referansı
   - Sipariş tarihi
   - Toplam tutar
   - Durum

#### Sipariş Durumları

| Durum | Açıklama | Yapılacak |
|-------|----------|-----------|
| **Taslak** | Sipariş oluşturuldu | Bekleyin |
| **Onaylandı** | Sipariş onaylandı | Hazırlık yapın |
| **Gönderildi** | Ürün gönderildi | Teslimat takibi |
| **Teslim Edildi** | Teslim tamamlandı | Fatura gönderin |
| **İptal** | Sipariş iptal edildi | - |

### 5.2 Sipariş Detayları

#### Detaylı Bilgiler

1. Sipariş listesinden bir siparişe tıklayın
2. Sipariş detay sayfası açılır
3. Görüntüleyebileceğiniz bilgiler:

**Sipariş Bilgileri**:
- Sipariş numarası ve tarihi
- İhale referansı
- Teslimat adresi
- Teslimat tarihi
- Ödeme koşulları

**Sipariş Kalemleri**:
- Ürün adı
- Miktar
- Birim fiyat
- Toplam tutar

**Teslimat Bilgileri**:
- Teslimat adresi
- İletişim kişisi
- Telefon
- Özel talimatlar

### 5.3 Sipariş Belgeleri

#### Sipariş PDF'i İndirme

1. Sipariş detay sayfasında **"Yazdır"** butonuna tıklayın
2. Sipariş PDF'i oluşturulur
3. PDF indirilir veya yazdırılabilir

#### Fatura Yükleme (Gelecek Özellik)

1. Sipariş detay sayfasında **"Fatura Yükle"** butonuna tıklayın
2. Fatura dosyasını seçin (PDF)
3. **"Yükle"** butonuna tıklayın
4. Fatura sisteme kaydedilir

---

## 6. Belge Yönetimi

### 6.1 Belge Türleri

Portal'da yönetebileceğiniz belgeler:

| Belge Türü | Açıklama | Format |
|------------|----------|--------|
| **Sözleşmeler** | İmzalanan sözleşmeler | PDF |
| **Siparişler** | Sipariş belgeleri | PDF |
| **Faturalar** | Gönderilen faturalar | PDF |
| **Teknik Dokümanlar** | Ürün katalogları | PDF, JPG |

### 6.2 Belge İndirme

1. **Belgeler** menüsüne gidin
2. Belge türünü seçin
3. İndirmek istediğiniz belgeye tıklayın
4. Belge otomatik indirilir

### 6.3 Belge Yükleme

1. İlgili bölümde **"Belge Yükle"** butonuna tıklayın
2. Dosya seçin (maksimum 10MB)
3. Belge açıklaması girin
4. **"Yükle"** butonuna tıklayın

---

## 7. Profil Ayarları

### 7.1 Firma Bilgileri

#### Bilgileri Görüntüleme

1. Sağ üst köşeden profil ikonuna tıklayın
2. **"Profil"** seçin
3. Firma bilgileriniz görüntülenir:
   - Firma ünvanı
   - Vergi numarası
   - Adres
   - Telefon
   - E-posta

#### Bilgileri Güncelleme

1. **"Düzenle"** butonuna tıklayın
2. Güncellemek istediğiniz alanları değiştirin
3. **"Kaydet"** butonuna tıklayın
4. Değişiklikler kaydedilir

### 7.2 Şifre Değiştirme

1. Profil sayfasında **"Şifre Değiştir"** seçin
2. Gerekli bilgileri girin:
   - Mevcut şifre
   - Yeni şifre
   - Yeni şifre (tekrar)
3. **"Şifreyi Güncelle"** butonuna tıklayın

### 7.3 Bildirim Ayarları

#### E-posta Bildirimleri

1. Profil sayfasında **"Bildirimler"** sekmesine gidin
2. Almak istediğiniz bildirimleri seçin:
   - ✅ Yeni ihale bildirimleri
   - ✅ Teklif durumu güncellemeleri
   - ✅ Sipariş bildirimleri
   - ❌ Pazarlama e-postaları
3. **"Kaydet"** butonuna tıklayın

---

## 8. Sık Sorulan Sorular

### 8.1 Genel Sorular

**S: Portal'a erişemiyorum, ne yapmalıyım?**
C: Şifrenizi sıfırlayın veya destek ekibiyle iletişime geçin: support@ilko.com.tr

**S: Teklif verdikten sonra değişiklik yapabilir miyim?**
C: Evet, ihale süresi dolmadan istediğiniz kadar güncelleme yapabilirsiniz.

**S: Teklifim neden reddedildi?**
C: Red gerekçesi size e-posta ile bildirilir. Detaylar için ihale yöneticisiyle iletişime geçin.

**S: Birden fazla ihaleye aynı anda teklif verebilir miyim?**
C: Evet, istediğiniz kadar ihaleye teklif verebilirsiniz.

### 8.2 Teknik Sorular

**S: Hangi tarayıcıları kullanabilirim?**
C: Chrome, Firefox, Safari, Edge (güncel versiyonlar)

**S: Mobil cihazdan erişebilir miyim?**
C: Evet, portal mobil uyumludur.

**S: Dosya yükleme limiti nedir?**
C: Maksimum 10MB per dosya.

**S: Hangi dosya formatlarını yükleyebilirim?**
C: PDF, JPG, PNG formatları desteklenir.

### 8.3 İletişim

**Teknik Destek**:
- Email: support@ilko.com.tr
- Çalışma Saatleri: Pazartesi-Cuma 09:00-18:00

**Satın Alma Departmanı**:
- Email: satin.alma@ilko.com.tr

---

**Son Güncelleme**: 3 Şubat 2026  
**Versiyon**: 1.0  
**Hazırlayan**: Kardan.Digital

---

**© 2023-2026 Kardan.Digital - Tüm hakları saklıdır.**
