# Playwright ile Gerçek UI Yük Testi

Bu dosya, **Playwright** kullanarak **gerçek tarayıcı** ile sınav sistemini test etmenizi sağlar. Locust'tan farkı, gerçek bir Chrome tarayıcısı açıp JavaScript, rendering ve kullanıcı etkileşimlerini tam olarak simüle etmesidir.

## 🎯 Neden Playwright?

✅ **Gerçek tarayıcı** - JavaScript hatalarını yakalar  
✅ **Screenshot** - Hata anında ekran görüntüsü alır  
✅ **Console logları** - Frontend hatalarını gösterir  
✅ **Paralel çalıştırma** - 50 kullanıcıyı aynı anda test eder  
✅ **Headless mode** - Sunucuda GUI olmadan çalışır  

## 📦 Kurulum

### 1. Playwright'ı Yükleyin

```bash
pip install playwright beautifulsoup4
```

### 2. Tarayıcıları İndirin

```bash
playwright install chromium
```

### 3. Sistem Bağımlılıkları (Ubuntu/Debian)

```bash
playwright install-deps
```

## 🚀 Kullanım

### Temel Kullanım (50 Kullanıcı)

```bash
cd /opt/odoo18/addons-custom/ak_exams/tests/load_test

SURVEY_TOKEN=49660127-9ee1-4377-ad89-4771401ae43b \
python test_exam_playwright.py
```

### Özelleştirilmiş Test

```bash
# 100 kullanıcı, 20 paralel
SURVEY_TOKEN=your_token \
USER_COUNT=100 \
PARALLEL=20 \
python test_exam_playwright.py
```

### Görünür Modda Test (Debug için)

```bash
# Tarayıcıyı görmek için (local bilgisayarda)
SURVEY_TOKEN=your_token \
HEADLESS=false \
USER_COUNT=2 \
PARALLEL=1 \
python test_exam_playwright.py
```

### Farklı Sunucuda Test

```bash
SURVEY_TOKEN=your_token \
BASE_URL=https://test.digipharma.com.tr \
python test_exam_playwright.py
```

## 🔧 Parametreler

| Parametre | Varsayılan | Açıklama |
|-----------|-----------|----------|
| `SURVEY_TOKEN` | - | **ZORUNLU** - Sınav token'ı |
| `USER_COUNT` | 50 | Toplam kullanıcı sayısı |
| `PARALLEL` | 10 | Aynı anda çalışacak kullanıcı |
| `HEADLESS` | true | Tarayıcıyı gizli modda çalıştır |
| `BASE_URL` | https://digipharma.com.tr | Test sunucusu |

## 📊 Test Çıktıları

Test çalıştığında:

1. **Console'da canlı log** - Her kullanıcının ilerlemesi
2. **JSON rapor** - `playwright_report_YYYYMMDD_HHMMSS.json`
3. **Screenshot'lar** - `/tmp/user_X_*.png` (hata durumunda)

### Örnek Çıktı

```
🚀 PLAYWRIGHT UI YÜK TESTİ BAŞLIYOR
======================================================================
📊 Toplam Kullanıcı: 50
⚡ Paralel Kullanıcı: 10
🔗 Survey Token: 49660127-9ee1-4377-ad89-4771401ae43b
🌐 Base URL: https://digipharma.com.tr
👁️  Headless Mode: true
======================================================================

[1/50] Kullanıcı 1 tamamlandı - Durum: SUCCESS
[2/50] Kullanıcı 2 tamamlandı - Durum: SUCCESS
...

📊 TEST SONUÇLARI
======================================================================
⏱️  Toplam Süre: 245.32 saniye (4.09 dakika)
👥 Toplam Kullanıcı: 50
✅ Başarılı: 48 (96.0%)
❌ Başarısız: 2 (4.0%)
🔥 Kritik Hata: 0 (0.0%)
📝 Toplam Cevaplanan Soru: 980
📈 Ortalama Soru/Kullanıcı: 19.6
======================================================================
```

## 🔍 Hata Ayıklama

### Hata: "playwright: command not found"

```bash
pip install playwright
playwright install chromium
```

### Hata: "Browser closed"

Sistem kaynakları yetersiz olabilir. Paralel sayısını azaltın:

```bash
PARALLEL=5 python test_exam_playwright.py
```

### Hata: "Timeout waiting for selector"

Sınav token'ı geçersiz veya sınav aktif değil. Kontrol edin:

```bash
curl -I https://digipharma.com.tr/survey/start/YOUR_TOKEN
```

## 📸 Screenshot'ları İnceleme

Test sırasında hatalar için otomatik screenshot alınır:

```bash
# Screenshot'ları listele
ls -lh /tmp/user_*_*.png

# Screenshot'ları bilgisayara indir (SCP)
scp root@sunucu:/tmp/user_*_error*.png ./screenshots/
```

## 🎬 Gerçek Sınav Öncesi Test Senaryosu

Gerçek sınavdan **1 gün önce** şunu yapın:

```bash
# 1. Küçük test (5 kullanıcı)
SURVEY_TOKEN=your_token USER_COUNT=5 PARALLEL=2 python test_exam_playwright.py

# 2. Orta test (25 kullanıcı)
SURVEY_TOKEN=your_token USER_COUNT=25 PARALLEL=10 python test_exam_playwright.py

# 3. Gerçek yük testi (50 kullanıcı)
SURVEY_TOKEN=your_token USER_COUNT=50 PARALLEL=10 python test_exam_playwright.py

# 4. Aşırı yük testi (100 kullanıcı) - Limitleri test edin
SURVEY_TOKEN=your_token USER_COUNT=100 PARALLEL=20 python test_exam_playwright.py
```

Her testten sonra:
- ✅ Raporu inceleyin
- ✅ Sunucu resource'larını kontrol edin (CPU, RAM, Disk)
- ✅ Odoo log'larını kontrol edin
- ✅ PostgreSQL yükünü kontrol edin

## ⚠️ Dikkat Edilecekler

1. **Veritabanı kirlenebilir** - Test sonrası `survey.user_input` tablosunda çok sayıda kayıt oluşacak
2. **Email gönderimi** - Sınav ayarlarında email bildirimlerini kapatın
3. **Webhook'lar** - Varsa test sırasında devre dışı bırakın
4. **Resource kullanımı** - Sunucunun yeterli RAM'i olduğundan emin olun (50 kullanıcı için en az 8GB önerilir)

## 🆚 Locust vs Playwright

| Özellik | Locust | Playwright |
|---------|--------|------------|
| **Hız** | Çok hızlı | Orta |
| **Kaynak** | Minimal | Yüksek |
| **JavaScript** | ❌ Görmez | ✅ Çalıştırır |
| **Screenshot** | ❌ | ✅ |
| **Console Error** | ❌ | ✅ |
| **Gerçekçilik** | %70 | %100 |
| **Kullanım** | Yük testi | UI + Yük |

**Öneri:** 
- İlk testi **Playwright** ile yapın (gerçek hatalar için)
- Ardından **Locust** ile yük testi yapın (daha fazla kullanıcı için)

## 📞 Destek

Sorun yaşarsanız:

1. Log dosyalarını kontrol edin
2. Screenshot'ları inceleyin
3. JSON raporunda hata detaylarını arayın
4. Odoo log'larını kontrol edin: `tail -f /var/log/odoo/odoo-server.log`
