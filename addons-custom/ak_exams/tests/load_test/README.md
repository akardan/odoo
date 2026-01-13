# 🎭 Playwright Exam Load Test - Dışarıdan Çalıştırma Kılavuzu

Bu test scripti, Odoo sınav sistemini gerçek tarayıcılar (Chromium) kullanarak yük testine tabi tutar. **Dışarıdan** (GitHub Actions, farklı sunucu, Docker) çalıştırılabilir.

---

## 📋 İçindekiler

1. [GitHub Actions ile Çalıştırma](#1-github-actions-ile-çalıştırma-önerilen)
2. [Standalone Çalıştırma](#2-standalone-çalıştırma-farklı-bilgisayardan)
3. [Docker ile Çalıştırma](#3-docker-ile-çalıştırma)
4. [Parametreler](#4-parametreler)
5. [Çıktılar ve Raporlar](#5-çıktılar-ve-raporlar)

---

## 1. GitHub Actions ile Çalıştırma (ÖNERİLEN) ✅

### Adım 1: GitHub'a Push Edin

Projenizi GitHub'a push edin (`.github/workflows/playwright-exam-test.yml` dosyası dahil).

```bash
git add .
git commit -m "Add Playwright load test with GitHub Actions"
git push origin main
```

### Adım 2: GitHub'da Workflow'u Çalıştırın

1. GitHub repository'nizde **Actions** sekmesine gidin
2. Sol tarafta **"Playwright Exam Load Test"** workflow'unu seçin
3. Sağ tarafta **"Run workflow"** butonuna tıklayın
4. Parametreleri girin:
   - **survey_token**: Sınav URL'indeki token (örn: `49660127-9ee1-4377-ad89-4771401ae43b`)
   - **base_url**: Odoo sunucu URL'i (örn: `https://digipharma.com.tr`)
   - **user_count**: Toplam kullanıcı sayısı (örn: `50`)
   - **parallel_count**: Aynı anda çalışacak kullanıcı sayısı (örn: `10`)
5. **"Run workflow"** butonuna tıklayın

### Adım 3: Sonuçları İnceleyin

- Test çalışırken **Actions** sekmesinde ilerlemeyi takip edebilirsiniz
- Test bittiğinde **Artifacts** bölümünden:
  - `playwright-test-results`: JSON raporlar ve screenshot'lar
  - `playwright-screenshots`: Hata durumunda screenshot'lar

### Alternatif: GitHub Secrets Kullanarak

Token'ı her seferinde girmek istemiyorsanız:

1. Repository **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** → `SURVEY_TOKEN` ekleyin
3. Workflow'u çalıştırırken token parametresini boş bırakın (secret kullanılır)

---

## 2. Standalone Çalıştırma (Farklı Bilgisayardan) 💻

### Gereksinimler

- Python 3.11+
- İnternet bağlantısı

### Kurulum

```bash
# 1. Repository'yi klonlayın veya sadece test klasörünü kopyalayın
cd /herhangi/bir/dizin

# 2. Gerekli dosyaları kopyalayın
# - test_exam_playwright.py
# - requirements.txt

# 3. Python sanal ortamı oluşturun (opsiyonel ama önerilen)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 4. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 5. Playwright tarayıcılarını yükleyin
playwright install chromium
playwright install-deps chromium  # Linux'ta sistem bağımlılıkları için
```

### Çalıştırma

```bash
# Temel kullanım
SURVEY_TOKEN=your-token-here python test_exam_playwright.py

# Tüm parametrelerle
SURVEY_TOKEN=49660127-9ee1-4377-ad89-4771401ae43b \
BASE_URL=https://digipharma.com.tr \
USER_COUNT=50 \
PARALLEL=10 \
HEADLESS=true \
python test_exam_playwright.py

# Görsel mod (tarayıcıları görmek için)
SURVEY_TOKEN=your-token HEADLESS=false python test_exam_playwright.py
```

### Windows'ta Çalıştırma

```powershell
# PowerShell
$env:SURVEY_TOKEN="your-token-here"
$env:BASE_URL="https://digipharma.com.tr"
$env:USER_COUNT="50"
$env:PARALLEL="10"
python test_exam_playwright.py

# Veya CMD
set SURVEY_TOKEN=your-token-here
set BASE_URL=https://digipharma.com.tr
python test_exam_playwright.py
```

---

## 3. Docker ile Çalıştırma 🐳

### Dockerfile Oluşturun

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Test scriptini kopyala
COPY test_exam_playwright.py .

# Playwright tarayıcıları zaten base image'de var
# Chromium kullanacağız

# Environment variables için varsayılanlar
ENV HEADLESS=true
ENV USER_COUNT=50
ENV PARALLEL=10

ENTRYPOINT ["python", "test_exam_playwright.py"]
```

### Docker Image Build ve Çalıştırma

```bash
# 1. Image'ı build edin
docker build -t playwright-exam-test .

# 2. Container'ı çalıştırın
docker run --rm \
  -e SURVEY_TOKEN=your-token-here \
  -e BASE_URL=https://digipharma.com.tr \
  -e USER_COUNT=50 \
  -e PARALLEL=10 \
  -v $(pwd)/reports:/app \
  playwright-exam-test

# 3. Raporlar mevcut dizinde oluşturulur
```

### Docker Compose Kullanımı

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  playwright-test:
    build: .
    environment:
      - SURVEY_TOKEN=${SURVEY_TOKEN}
      - BASE_URL=${BASE_URL:-https://digipharma.com.tr}
      - USER_COUNT=${USER_COUNT:-50}
      - PARALLEL=${PARALLEL:-10}
      - HEADLESS=true
    volumes:
      - ./reports:/app
```

`.env` dosyası:

```bash
SURVEY_TOKEN=your-token-here
BASE_URL=https://digipharma.com.tr
USER_COUNT=50
PARALLEL=10
```

Çalıştırma:

```bash
docker-compose up
```

---

## 4. Parametreler ⚙️

| Parametre | Açıklama | Varsayılan | Örnek |
|-----------|----------|-----------|-------|
| `SURVEY_TOKEN` | **Zorunlu**. Sınav URL'sindeki token | - | `49660127-9ee1-4377-ad89-4771401ae43b` |
| `BASE_URL` | Odoo sunucu URL'i | `https://digipharma.com.tr` | `https://myodoo.com` |
| `USER_COUNT` | Toplam simulasyon yapılacak kullanıcı sayısı | `50` | `100` |
| `PARALLEL` | Aynı anda çalışacak kullanıcı sayısı | `10` | `20` |
| `HEADLESS` | Tarayıcıyı gizli modda çalıştır | `true` | `false` (görmek için) |

### Survey Token Nasıl Bulunur?

Sınav linkinden alın:
```
https://digipharma.com.tr/survey/start/49660127-9ee1-4377-ad89-4771401ae43b
                                     └─────────────────┬──────────────────┘
                                                  Bu kısım TOKEN
```

---

## 5. Çıktılar ve Raporlar 📊

### Console Çıktısı

Test çalışırken gerçek zamanlı log gösterir:

```
======================================================================
🚀 PLAYWRIGHT UI YÜK TESTİ BAŞLIYOR
======================================================================
📊 Toplam Kullanıcı: 50
⚡ Paralel Kullanıcı: 10
...
======================================================================

[1/50] Kullanıcı 1 tamamlandı - Durum: SUCCESS
[2/50] Kullanıcı 2 tamamlandı - Durum: SUCCESS
...

======================================================================
📊 TEST SONUÇLARI
======================================================================
⏱️  Toplam Süre: 127.45 saniye (2.12 dakika)
👥 Toplam Kullanıcı: 50
✅ Başarılı: 48 (96.0%)
❌ Başarısız: 2 (4.0%)
🔥 Kritik Hata: 0 (0.0%)
📝 Toplam Cevaplanan Soru: 240
📈 Ortalama Soru/Kullanıcı: 4.8
======================================================================
```

### JSON Rapor

Otomatik oluşturulur: `playwright_report_20260113_180000.json`

```json
{
  "test_info": {
    "survey_token": "49660127-9ee1-4377-ad89-4771401ae43b",
    "base_url": "https://digipharma.com.tr",
    "user_count": 50,
    "start_time": "2026-01-13T18:00:00",
    "end_time": "2026-01-13T18:02:07",
    "duration_seconds": 127.45
  },
  "summary": {
    "success": 48,
    "failed": 2,
    "critical": 0,
    "total_questions_answered": 240
  },
  "results": [
    {
      "user_id": 1,
      "status": "SUCCESS",
      "started_at": "2026-01-13T18:00:01",
      "completed_at": "2026-01-13T18:01:45",
      "questions_answered": 5,
      "errors": [],
      "screenshots": ["/tmp/user_1_start.png", "/tmp/user_1_end.png"]
    }
  ]
}
```

### Screenshot'lar

- `/tmp/user_{id}_start.png` - Başlangıç ekranı
- `/tmp/user_{id}_end.png` - Bitiş ekranı
- `/tmp/user_{id}_error_q{n}.png` - Hata durumunda

---

## 6. Sorun Giderme 🔧

### "SURVEY_TOKEN environment variable tanımlanmamış"

```bash
# Token'ı export edin
export SURVEY_TOKEN=your-token-here
python test_exam_playwright.py
```

### Playwright tarayıcı bulunamıyor

```bash
# Tarayıcıları tekrar yükleyin
playwright install chromium
playwright install-deps  # Linux için sistem bağımlılıkları
```

### GitHub Actions'ta timeout

`playwright-exam-test.yml` dosyasında timeout süresini artırın:

```yaml
timeout-minutes: 240  # 4 saat
```

### Çok fazla başarısızlık

- `PARALLEL` sayısını azaltın (sunucu yükü için)
- `USER_COUNT` sayısını azaltın
- Sınav tokenının geçerli olduğundan emin olun
- Sunucunun erişilebilir olduğunu kontrol edin

---

## 7. Gelişmiş Kullanım 🚀

### Scheduled Test (Zamanlanmış Çalıştırma)

`.github/workflows/playwright-exam-test.yml` içinde uncomment edin:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Her gün saat 02:00'de çalış
```

### Multiple Environments Test

Farklı ortamlar için workflow'ları çoğaltın:

```yaml
# .github/workflows/test-production.yml
env:
  BASE_URL: https://production.example.com

# .github/workflows/test-staging.yml
env:
  BASE_URL: https://staging.example.com
```

### CI/CD Integration

Pull Request'lerde otomatik test:

```yaml
on:
  pull_request:
    branches: [ main ]
```

---

## 8. Güvenlik Notları 🔒

- **Survey Token'ı asla repository'ye commit etmeyin!**
- GitHub Secrets kullanın veya environment variables ile geçirin
- `.gitignore` dosyasına `.env` ekleyin
- Production testleri için özel test hesapları kullanın

---

## 9. Performans İpuçları ⚡

| Senaryo | Önerilen Ayar | Açıklama |
|---------|---------------|----------|
| Düşük yük testi | `USER_COUNT=10`, `PARALLEL=2` | Hızlı test |
| Orta yük testi | `USER_COUNT=50`, `PARALLEL=10` | Dengeli |
| Yüksek yük testi | `USER_COUNT=200`, `PARALLEL=20` | Sunucu limitlerine dikkat |
| Stress test | `USER_COUNT=500`, `PARALLEL=50` | Sadece production-like ortamda |

---

## 10. Destek ve Katkı 🤝

Sorunlar için GitHub Issues kullanın veya projeye katkıda bulunun.

### Geliştirme Yapılacaklar

- [ ] Daha detaylı metrikler (response time, page load time)
- [ ] Grafana/Prometheus entegrasyonu
- [ ] Slack/Discord bildirimler
- [ ] Multi-browser test (Firefox, WebKit)
- [ ] Video kaydı (başarısızlıklar için)

---

## Lisans

Bu test scripti [Ana Proje Lisansı](../../../../LICENSE) altında lisanslanmıştır.
