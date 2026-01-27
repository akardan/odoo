# Ekonomik Veri Yönetimi - Finans Bölümü İşbirliği

## Konu: İhale Sistemi Ekonomik Veri Yönetimi ve NPV Hesaplamaları İçin İşbirliği Talebi

---

**Sayın Finans Bölümü Yöneticisi,**

İhale yönetim sistemimizde (Odoo ak_tender modülü) tedarikçi tekliflerinin değerlendirilmesinde kullanılan **Net Bugünkü Değer (NPV)** hesaplamaları ve **döviz kuru** bilgilerinin güncel ve doğru tutulması kritik önem taşımaktadır.

### 📊 Mevcut Durum

Sistemimizde şu anda aşağıdaki ekonomik veriler kullanılmaktadır:

1. **NPV Oranı** - Tedarikçi tekliflerinin zaman değerini hesaplamak için kullanılan ana oran
2. **Enflasyon Oranı** - NPV oranı tespitinde referans ve teyit amaçlı
3. **Faiz Oranı** - NPV oranı tespitinde referans ve teyit amaçlı
4. **Döviz Kurları** - Farklı para birimlerindeki tekliflerin karşılaştırılması için (otomatik hesaplanır)

### 🎯 İhtiyaç Tespiti

İhale süreçlerinin sağlıklı yürütülmesi için aşağıdaki konularda desteğinize ihtiyacımız bulunmaktadır:

#### 1. Güncel Kur Bilgileri
- **Durum:** Sistemde otomatik kur hesaplama aktif edilmiştir
- **Özellik:** Her para birimi için şirket para birimine göre güncel kur otomatik gösterilmektedir
- **Format:** Örnek: "USD (1.0 = 34.567890 TRY)"
- **Beklenti:** Kritik ihaleler öncesi kur bilgilerinin doğruluğunun teyit edilmesi

#### 2. NPV Oranlarının Belirlenmesi
- **Sorun:** Her para birimi için uygun NPV oranının belirlenmesi gerekmektedir
- **Mevcut Yaklaşım:** 
  - Enflasyon ve faiz oranları referans olarak sisteme girilmektedir
  - Finans bölümü bu referans değerleri ve kendi değerlendirmelerini kullanarak NPV oranını belirlemektedir
  - NPV oranı, şirket politikaları ve risk değerlendirmeleri doğrultusunda özelleştirilebilmektedir
- **Beklenti:** 
  - Aylık veya üç aylık periyotlarda referans oranların (enflasyon, faiz) güncellenmesi
  - Bu referanslar ışığında NPV oranının Finans bölümü tarafından belirlenmesi

#### 3. Referans Ekonomik Göstergeler
- **Amaç:** NPV oranı tespitinde kullanılmak üzere güncel piyasa verilerinin tutulması
- **Kaynaklar:** TCMB (faiz oranları), TÜİK (enflasyon verileri)
- **Kullanım:** 
  - Bu oranlar doğrudan NPV hesaplamasında kullanılmaz
  - Finans bölümünün NPV oranı belirlerken referans alacağı göstergelerdir
  - Şirket politikaları, risk primleri ve diğer faktörler de değerlendirilerek nihai NPV oranı belirlenir

### 💡 Önerilen İşbirliği Modeli

#### A. Rutin Güncellemeler
- **Periyot:** Ayda bir (her ayın ilk iş günü)
- **Kapsam:** 
  - **Referans Göstergelerin Güncellenmesi:**
    - TCMB politika faizi
    - TÜİK enflasyon oranı
    - Diğer ilgili piyasa göstergeleri
  - **NPV Oranının Belirlenmesi:**
    - Referans göstergeler değerlendirilerek
    - Şirket risk politikaları göz önünde bulundurularak
    - Para birimi bazında uygun NPV oranının tespiti

#### B. Kritik İhale Öncesi Kontroller
- **Tetikleyici:** 1 milyon TL üzeri ihaleler
- **Süreç:**
  1. İhale başlamadan 2 iş günü önce bildirim
  2. Finans bölümü tarafından:
     - Güncel kur bilgilerinin doğrulanması
     - Mevcut NPV oranının uygunluğunun değerlendirilmesi
     - Gerekirse özel NPV oranı belirlenmesi

#### C. Veri Kaynakları ve Kullanım Şekli

**Otomatik Veriler:**
- **Döviz Kurları:** Sistem tarafından otomatik hesaplanır ve gösterilir
- **Kaynak:** Odoo'nun kur veritabanı (günlük güncellenir)

**Manuel Veriler (Finans Bölümü Tarafından):**
- **Enflasyon Oranı:** TCMB/TÜİK verilerinden alınır → NPV tespitinde referans
- **Faiz Oranı:** TCMB politika faizinden alınır → NPV tespitinde referans
- **NPV Oranı:** Yukarıdaki referanslar + şirket politikaları → İhalede kullanılır

### 🔧 Teknik Detaylar

**Ekonomik Veri Modülü Özellikleri:**
- Para birimi bazında ayrı kayıtlar
- Geçerlilik tarihi aralıkları
- Otomatik kur hesaplama ve gösterimi
- Manuel veri girişi imkanı
- Veri kaynağı takibi (TCMB/TÜİK/Manuel)

**Erişim Bilgileri:**
- Menü: İhale > Konfigürasyon > Ekonomik Veriler
- Gerekli Yetki: Finans Yöneticisi veya İhale Yöneticisi

**Sistemde Tutulan Ekonomik Veri Alanları:**

| Alan | Nasıl Belirlenir | Kullanım Amacı |
|------|------------------|----------------|
| **Para Birimi** | Manuel seçilir | Hangi para birimi için veri tutulduğu |
| **Güncel Kur** | Otomatik hesaplanır | Bilgilendirme ve doğrulama |
| **Enflasyon Oranı** | Manuel girilir (TCMB/TÜİK) | NPV oranı tespitinde referans |
| **Faiz Oranı** | Manuel girilir (TCMB) | NPV oranı tespitinde referans |
| **NPV Oranı** | Finans bölümü belirler | İhale NPV hesaplamasında kullanılır |
| **Veri Kaynağı** | Manuel seçilir | Takip ve denetim |
| **Geçerlilik Tarihleri** | Manuel girilir | Hangi dönem için geçerli |

### 📋 Aksiyon Planı

#### Kısa Vadeli (1 Hafta)
1. ✅ Sistemde güncel kur gösterimi eklendi
2. ⏳ Mevcut NPV oranlarının Finans bölümü tarafından gözden geçirilmesi
3. ⏳ Kullanılan para birimleri listesinin belirlenmesi (USD, EUR, GBP, vb.)
4. ⏳ Her para birimi için referans göstergelerin (enflasyon, faiz) güncellenmesi

#### Orta Vadeli (1 Ay)
1. ⏳ Aylık güncelleme takviminin oluşturulması
2. ⏳ Sorumlu kişilerin belirlenmesi
3. ⏳ NPV oranı belirleme prosedürünün dokümante edilmesi
4. ⏳ Referans gösterge güncelleme prosedürünün oluşturulması

#### Uzun Vadeli (3 Ay)
1. ⏳ Otomatik veri çekme entegrasyonlarının değerlendirilmesi (TCMB API)
2. ⏳ Uyarı ve bildirim mekanizmalarının kurulması
3. ⏳ NPV oranı belirleme kriterlerinin standardizasyonu
4. ⏳ Performans metriklerinin oluşturulması

### 🤝 İşbirliği Talebi

Bu konuda sizlerle bir toplantı organize ederek:
- Mevcut durumu detaylı paylaşmak
- NPV oranı belirleme sürecinizi anlamak
- Referans gösterge ihtiyaçlarınızı netleştirmek
- Sorumlulukları belirlemek
- Güncelleme süreçlerini tanımlamak

isteriz.

**Önerilen Toplantı Gündemi:**
1. Sistem tanıtımı ve mevcut durum (15 dk)
   - Otomatik kur gösterimi
   - Ekonomik veri yönetimi
2. NPV oranı belirleme süreci (20 dk)
   - Mevcut yaklaşımınız
   - Kullandığınız kriterler
   - Referans gösterge ihtiyaçları
3. Süreç tasarımı ve sorumluluklar (20 dk)
   - Güncelleme periyotları
   - Veri kaynakları
   - Onay mekanizmaları
4. Aksiyon planı ve takvim (15 dk)

### 📞 İletişim

Bu konuda görüşlerinizi almak ve uygun bir toplantı tarihi belirlemek için tarafınızla iletişime geçmek isteriz.

**İhale Yönetimi Ekibi**
- Sistem Sorumlusu: [İsim]
- İhale Müdürü: [İsim]
- İletişim: [Email/Telefon]

---

### 📚 Ek Bilgiler

**NPV Hesaplama Formülü:**
```
NPV = Σ (Ödeme Tutarı / (1 + NPV Oranı)^Gün Sayısı)
```

**NPV Oranı Belirleme Örneği:**
```
Referans Göstergeler:
- TCMB Politika Faizi: %50
- TÜİK Yıllık Enflasyon: %65
- Şirket Risk Primi: %5

Finans Bölümü Değerlendirmesi:
→ NPV Oranı: %60 (Enflasyon + Risk Primi - Diğer Faktörler)
```

Bu formül ile tedarikçi tekliflerinin bugünkü değeri hesaplanarak en avantajlı teklif belirlenmektedir.

**Örnek Senaryo:**
- Teklif Tutarı: 100.000 USD
- Ödeme Vadesi: 90 gün
- NPV Oranı: %10 (yıllık)
- Günlük Oran: 0.10/365 = 0.000274
- NPV = 100.000 / (1 + 0.000274)^90 = 97.561 USD

---

Saygılarımızla,

**İhale Yönetimi Ekibi**

*Not: Bu email, ihale süreçlerinin etkinliğini artırmak ve şirketimizin finansal çıkarlarını korumak amacıyla hazırlanmıştır. Ekonomik verilerin doğru yönetimi, en avantajlı tedarikçi seçimini sağlayacaktır.*