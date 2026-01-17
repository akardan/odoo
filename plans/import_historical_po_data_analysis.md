og# Geçmiş Dönem PO Import - Veri Analizi

## Verilen Excel Verisinin Analizi

### 1. Kolon Yapısı Kontrolü

#### Beklenen Zorunlu Kolonlar (Wizard'dan)
1. ✓ **SIPARIS_NO** - SAP Sipariş Numarası
2. ✓ **SIPARIS_TARIHI** - Sipariş Tarihi  
3. ✓ **TEDARIKCI_KODU** - Tedarikçi SAP Kodu
4. ✓ **TEDARIKCI_ADI** - Tedarikçi Ünvanı
5. ✓ **MALZEME_KODU** - Malzeme SAP Kodu (Opsiyonel ancak verinizdeki mevcut)
6. ✓ **MALZEME_ADI** - Malzeme Açıklaması
7. ? **MALZEME_GRUBU** - SAP Malzeme Grubu (Kontrol edilmeli)
8. ✓ **MIKTAR** - Sipariş Miktarı
9. ✓ **BIRIM** - Ölçü Birimi
10. ✓ **BIRIM_FIYAT** - Birim Fiyat
11. ✓ **PARA_BIRIMI** - Para Birimi
12. ✓ **TOPLAM_TUTAR** - Toplam Tutar
13. ✓ **VADE** - Ödeme Vadesi
14. ? **IHALE_TIPI** - İhale Tipi (Kontrol edilmeli)
15. ✓ **SIRKET_KODU** - SAP Şirket Kodu
16. ? **TESIS** - Tesis/Depo Adı (Opsiyonel olabilir)
17. ? **SATIN_ALMACI** - Satınalmacı Adı (Opsiyonel olabilir)
18. ✓ **MALZEME_GRUBU_TANIMI** - Malzeme Grubu Tanımı (Ekstra, sorun değil)
19. ✓ **TESLIMAT_TARIHI** - Teslimat Tarihi
20. ✓ **NOTLAR** - Notlar

### 2. TESPİT EDİLEN SORUNLAR

#### 🔴 KRİTİK SORUNLAR

**A. Kolon İsimlendirme Problemleri**

Verinizdeki kolonlarda **Türkçe karakterler ve boşluklar** var. Örneğin:
- `Tip` yerine `IHALE_TIPI` olmalı
- `Birim` yerine `BIRIM` olmalı  
- `vADE` gibi küçük/büyük harf karışımları olabilir

**Excel'deki kolon başlıkları TAM OLARAK şu şekilde olmalı:**
```
SIPARIS_NO
KALEM_NO
SIPARIS_TARIHI
TEDARIKCI_KODU
TEDARIKCI_ADI
MALZEME_KODU
MALZEME_ADI
MALZEME_GRUBU
MIKTAR
BIRIM
BIRIM_FIYAT
PARA_BIRIMI
TOPLAM_TUTAR
VADE
IHALE_TIPI
SIRKET_KODU
TESIS
SATIN_ALMACI
TESLIMAT_TARIHI
NOTLAR
```

#### 🟡 FORMAT SORUNLARI

**B. Tarih Formatı (Görünen Satırlardan)**
- ✓ `1.01.2025` formatı görünüyor
- ⚠️ **GEREKLI FORMAT:** `YYYY-MM-DD` (örn: `2025-01-01`)
- Wizard tarihleri `%Y-%m-%d` formatında bekliyor (satır 470)

**C. Sayısal Değerler**
Görünen satırlarda:
- Miktar değerleri (1, 0, 5860) - ✓ OK
- Birim fiyat (541.000 ADT gibi) - ⚠️ **SORUN:** Sayı değil, metin olarak görünüyor
- TOPLAM_TUTAR değerleri kontrol edilmeli

**D. Para Birimi**
- Görünen satırlarda boş alan var gibi
- Varsayılan olarak TRY kullanılacak

**E. Birim (UoM) Değerleri**
Görünen değerler:
- `KG`, `AD`, `LT`, `METRE`, `ADET` vs. 
- Wizard'ın mapping'i var (satır 444-452), ancak bazı birimler eşleşmeyebilir

#### 🟢 DOĞRU GÖRÜNEN ALANLAR
- SIPARIS_NO formatı (4000xxx) ✓
- KALEM_NO (10, 20, 30 vs.) ✓
- TEDARIKCI_KODU sayısal değerler ✓
- TEDARIKCI_ADI tam firma isimleri ✓

### 3. ÖNERİLER VE ÇÖZÜMLER

#### Adım 1: Excel Kolon Başlıklarını Düzelt
Excel'in ilk satırındaki kolon başlıklarını tam olarak şu formatta düzenleyin:
- Tüm harfler BÜYÜK HARF olmalı
- Türkçe karakter kullanmayın (ş→S, ı→I, ğ→G, ü→U, ö→O, ç→C)
- Alt çizgi (_) kullanın, boşluk kullanmayın
- Kelimeler arasında tek bir alt çizgi

#### Adım 2: Tarih Formatını Düzelt
Excel'de tarih kolonlarını (SIPARIS_TARIHI, TESLIMAT_TARIHI) düzenleyin:
```
Mevcut: 1.01.2025, 1.12.2024
Olması Gereken: 2025-01-01, 2024-12-01
```

Excel'de tarihleri düzeltmek için:
1. Tarih kolonunu seç
2. Format → Cells → Custom
3. Format kodu: `yyyy-mm-dd`

#### Adım 3: Sayısal Değerleri Kontrol Et
- **MIKTAR** kolonunda sadece sayı olmalı (1, 234.56 gibi)
- **BIRIM_FIYAT** kolonunda sadece sayı olmalı 
- **TOPLAM_TUTAR** kolonunda sadece sayı olmalı
- Metin (örn: "ADT", "TRY") ayrı kolonlarda olmalı

#### Adım 4: Zorunlu Alan Kontrolü
Wizard aşağıdaki alanların BOŞ olmamasını kontrol eder (satır 211-220):
```
SIPARIS_NO ✓
SIPARIS_TARIHI ✓
TEDARIKCI_KODU ✓
TEDARIKCI_ADI ✓
MALZEME_ADI ✓
MALZEME_GRUBU ⚠️ (Kontrol edin)
MIKTAR ✓
BIRIM ✓
BIRIM_FIYAT ⚠️ (Format düzelt)
PARA_BIRIMI ⚠️ (Boş satırlar var gibi)
VADE ✓
SIRKET_KODU ✓
```

#### Adım 5: Sheet İsmi Kontrolü
Excel dosyasında sheet (sayfa) isminin **tam olarak** `Geçmiş_PO` olması gerekiyor (satır 192).

### 4. DÜZELTME ŞABLONu

Template dosyasını wizard'dan indirip inceleyebilirsiniz:
- Wizard'da "Template İndir" butonunu kullanın
- İndirilen şablon dosyasını esas alın
- Verilerinizi bu şablona uyarlayın

### 5. TEST SÜRECİ

1. **Küçük Bir Test Yapın**
   - İlk 10 satırı ayrı bir Excel'e kopyalayın
   - Yukarıdaki düzeltmeleri yapın
   - Import işlemini test edin

2. **Hata Mesajlarını İzleyin**
   - Wizard hangi kolon eksik diyor?
   - Hangi satırlarda boş değer var?
   - Tarih parse edilemiyor mu?

3. **Toplu Import**
   - Test başarılı olduktan sonra tüm veriyi import edin

### 6. WIZARD AYARLARI ÖNERİSİ

Import sırasında şu ayarları kullanın:
- ✓ **Yeni Tedarikçi Oluştur:** AÇIK (Eğer sistemde yoksa)
- ✗ **Yeni Ürün Oluştur:** KAPALI (Önce ürünler sisteme girilmeli)
- ✓ **Duplikaları Atla:** AÇIK (Aynı sipariş 2 kez import edilmesin)
- ✗ **Siparişleri Onayla:** KAPALI (İlk Import'ta draft olarak kalsın, kontrol edelim)

## ÖZET: YAPILACAKLAR

### Hemen Düzeltilmesi Gerekenler
1. ❌ Kolon başlıklarını BÜYÜK HARF + ALT ÇİZGİ formatına çevir
2. ❌ Tarih formatını `YYYY-MM-DD` yap
3. ❌ Sayısal kolonlarda metin olmamasını sağla
4. ❌ Sheet ismini `Geçmiş_PO` yap
5. ❌ PARA_BIRIMI kolonunda boş satırları TRY ile doldur
6. ❌ Tüm zorunlu alanlarda değer olduğunu kontrol et

### İsteğe Bağlı Düzeltmeler
- MALZEME_KODU boş olabilir (ama olması daha iyi)
- KALEM_NO boş olabilir
- IHALE_TIPI boş olabilir (default direct kullanılır)
- TESIS boş olabilir (opsiyonel)
- SATIN_ALMACI boş olabilir (opsiyonel)
- NOTLAR boş olabilir

---

**Sonuç:** Verileriniz import için uygun görünüyor ancak bazı format düzeltmeleri gerekiyor. Yukarıdaki adımları izlerseniz başarıyla import edebilirsiniz.
