# GitHub Actions Workflows

## Playwright Exam Load Test

Bu workflow, Odoo sınav sistemini 50 eş zamanlı kullanıcı ile test etmek için tasarlanmış Playwright tabanlı UI yük testidir.

### 📋 Özellikler

- **50 Eş Zamanlı Kullanıcı**: Gerçek tarayıcı (Chromium) ile paralel test
- **Gerçek UI Testi**: Playwright kullanarak gerçek kullanıcı simülasyonu
- **İhlal Simülasyonu**: Fullscreen çıkış, tab değiştirme, DevTools, PrintScreen gibi ihlalleri test eder
- **Otomatik Raporlama**: JSON formatında detaylı test raporları
- **Screenshot Desteği**: Hata durumlarında ekran görüntüleri
- **Artifact Yönetimi**: Test sonuçları ve screenshot'ları otomatik yükleme

### 🚀 Kullanım

#### Manuel Tetikleme (Önerilen)

1. GitHub reposuna gidin
2. **Actions** sekmesine tıklayın
3. Sol taraftan **"Playwright Exam Load Test"** workflow'unu seçin
4. **"Run workflow"** butonuna tıklayın
5. Parametreleri girin:
   - **Survey Token**: Sınav URL'sinin sonundaki token (zorunlu)
   - **Base URL**: Sınav sitesinin URL'si (varsayılan: https://digipharma.com.tr)
   - **User Count**: Toplam kullanıcı sayısı (varsayılan: 50)
   - **Parallel Count**: Eş zamanlı kullanıcı sayısı (varsayılan: 50)

#### Örnek Parametre Değerleri

```yaml
survey_token: 16a184a0-d826-4451-bb61-ce4754b1526d 
base_url: https://digipharma.com.tr
user_count: 50
parallel_count: 50
```

#### Secret ile Kullanım

Eğer survey token'ı her seferinde girmek istemiyorsanız, GitHub Secret olarak ekleyebilirsiniz:

1. Repository **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** butonuna tıklayın
3. Name: `SURVEY_TOKEN`
4. Value: token değeriniz
5. Workflow'u çalıştırırken survey_token parametresini boş bırakın

### 📊 Test Çıktıları

#### Test Raporları

Test sonunda otomatik olarak oluşturulan raporlar:
- `playwright_report_YYYYMMDD_HHMMSS.json`: Detaylı test sonuçları

#### Rapor İçeriği

```json
{
  "test_info": {
    "survey_token": "xxx",
    "base_url": "https://digipharma.com.tr",
    "user_count": 50,
    "start_time": "2024-01-13T18:00:00",
    "end_time": "2024-01-13T18:15:00",
    "duration_seconds": 900
  },
  "summary": {
    "success": 48,
    "failed": 2,
    "critical": 0,
    "total_questions_answered": 1200
  },
  "results": [...]
}
```

#### Artifacts

Test tamamlandığında aşağıdaki artifacts oluşturulur:
- **playwright-test-results**: JSON raporlar ve screenshot'lar (30 gün saklanır)
- **playwright-screenshots**: Hata durumlarında screenshot'lar (7 gün saklanır)

### ⚙️ Workflow Yapılandırması

#### Önemli Ayarlar

- **Timeout**: 120 dakika (2 saat) - Uzun süreli testler için
- **Python Version**: 3.11
- **Browser**: Chromium (Headless mode)
- **Runner**: ubuntu-latest

#### Environment Variables

Workflow içinde kullanılan environment variable'lar:
```yaml
SURVEY_TOKEN: ${{ github.event.inputs.survey_token || secrets.SURVEY_TOKEN }}
BASE_URL: ${{ github.event.inputs.base_url || 'https://digipharma.com.tr' }}
USER_COUNT: ${{ github.event.inputs.user_count || '50' }}
PARALLEL: ${{ github.event.inputs.parallel_count || '50' }}
HEADLESS: 'true'
```

### 🔧 Özelleştirme

#### Zamanlanmış Çalıştırma

Workflow'u otomatik olarak çalıştırmak için schedule açınız:

```yaml
on:
  workflow_dispatch:
    # ...
  schedule:
    - cron: '0 2 * * *'  # Her gün saat 02:00'de çalış
```

#### Paralel Kullanıcı Sayısını Ayarlama

50 eş zamanlı kullanıcı varsayılan olarak ayarlanmıştır. Bunu değiştirmek için:

1. Workflow dosyasını düzenleyin (`.github/workflows/playwright-exam-test.yml`)
2. `parallel_count` default değerini değiştirin:

```yaml
parallel_count:
  description: 'Paralel çalışacak kullanıcı sayısı'
  required: false
  default: '50'  # İstediğiniz sayıyı girin
  type: string
```

### 📈 Performans Notları

#### 50 Eş Zamanlı Kullanıcı

- **Tahmini Süre**: 10-20 dakika (sınav uzunluğuna bağlı)
- **Memory Kullanımı**: ~8-12 GB (GitHub Actions runner'da yeterli)
- **CPU Kullanımı**: Yüksek (paralel browser instance'ları nedeniyle)

#### Sistem Gereksinimleri

GitHub Actions ubuntu-latest runner özellikleri:
- **CPU**: 2-core
- **RAM**: 7 GB
- **Disk**: 14 GB SSD

50 paralel kullanıcı bu kaynaklar için optimize edilmiştir.

### 🐛 Hata Ayıklama

#### Common Issues

**1. Timeout Hatası**
```
Solution: timeout-minutes değerini artırın (120 → 180)
```

**2. Browser Launch Hatası**
```
Solution: playwright install-deps chromium komutu çalıştığından emin olun
```

**3. Memory Hatası**
```
Solution: parallel_count değerini düşürün (50 → 25)
```

#### Log'ları İnceleme

1. Actions sekmesinden workflow run'ı seçin
2. "Run Playwright Load Test" step'ini açın
3. Detaylı log'ları inceleyin

### 📝 Örnek Kullanım Senaryoları

#### Senaryo 1: Hızlı Test (10 Kullanıcı)

```yaml
user_count: 10
parallel_count: 10
```

#### Senaryo 2: Orta Seviye Test (25 Kullanıcı)

```yaml
user_count: 25
parallel_count: 25
```

#### Senaryo 3: Tam Yük Testi (50 Kullanıcı) - Varsayılan

```yaml
user_count: 50
parallel_count: 50
```

#### Senaryo 4: Yüksek Yük Testi (100 Kullanıcı)

```yaml
user_count: 100
parallel_count: 50  # Aynı anda 50, toplamda 100
```

### 🔒 Güvenlik

- Survey token'ları GitHub Secrets'ta saklanmalıdır
- Test sonuçlarında hassas bilgiler varsa artifact retention'ı kısaltın
- Public repository'lerde workflow log'larını dikkatlice inceleyin

### 📚 İlgili Dosyalar

- **Workflow**: `.github/workflows/playwright-exam-test.yml`
- **Test Script**: `addons-custom/ak_exams/tests/load_test/test_exam_playwright.py`
- **Requirements**: `addons-custom/ak_exams/tests/load_test/requirements.txt`
- **README**: `addons-custom/ak_exams/tests/load_test/README.md`

### 🆘 Destek

Sorun yaşarsanız:
1. Workflow log'larını kontrol edin
2. Test raporu JSON dosyasını indirin
3. Screenshot'ları inceleyin
4. Issue açın veya proje yöneticisiyle iletişime geçin

---

**Son Güncelleme**: 2026-01-13
**Workflow Version**: 1.0
**Test Script Version**: 1.0
