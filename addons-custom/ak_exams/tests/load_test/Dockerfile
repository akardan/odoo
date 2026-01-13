# Playwright Exam Load Test - Docker Image
# ==========================================
# Bu Dockerfile, Playwright testini izole Docker container içinde çalıştırır.
#
# Kullanım:
#   docker build -t playwright-exam-test .
#   docker run --rm -e SURVEY_TOKEN=your-token playwright-exam-test

FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Metadata
LABEL maintainer="AK Exams"
LABEL description="Playwright-based exam load testing tool"
LABEL version="1.0"

# Çalışma dizini
WORKDIR /app

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Test scriptini kopyala
COPY test_exam_playwright.py .

# Playwright tarayıcıları zaten base image'de yüklü
# Chromium kullanacağız (headless mode)

# Environment variables için varsayılan değerler
ENV HEADLESS=true \
    USER_COUNT=50 \
    PARALLEL=10 \
    BASE_URL=https://digipharma.com.tr

# Raporların kaydedileceği dizin
RUN mkdir -p /app/reports

# Volume için mount point
VOLUME ["/app/reports"]

# Healthcheck (opsiyonel)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python --version || exit 1

# Script'i çalıştır
# Not: SURVEY_TOKEN environment variable olarak geçilmelidir
ENTRYPOINT ["python", "test_exam_playwright.py"]
