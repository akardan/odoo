#!/bin/bash
# Playwright Exam Load Test - Quick Run Script
# ==============================================
# Bu script, testi hızlıca çalıştırmanızı sağlar.

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🎭 Playwright Exam Load Test${NC}"
echo -e "${BLUE}======================================${NC}\n"

# .env dosyası kontrolü
if [ ! -f .env ]; then
    echo -e "${RED}❌ Hata: .env dosyası bulunamadı!${NC}\n"
    echo -e "${YELLOW}Lütfen .env.example dosyasını .env olarak kopyalayın:${NC}"
    echo -e "  cp .env.example .env"
    echo -e "\nVe SURVEY_TOKEN değerini doldurun.\n"
    exit 1
fi

# .env dosyasını yükle
source .env

# SURVEY_TOKEN kontrolü
if [ -z "$SURVEY_TOKEN" ]; then
    echo -e "${RED}❌ Hata: SURVEY_TOKEN tanımlanmamış!${NC}\n"
    echo -e "${YELLOW}.env dosyasında SURVEY_TOKEN değerini doldurun.${NC}\n"
    exit 1
fi

# Parametreleri göster
echo -e "${GREEN}✅ Konfigürasyon:${NC}"
echo -e "  Survey Token: ${SURVEY_TOKEN:0:8}...${SURVEY_TOKEN: -8}"
echo -e "  Base URL: ${BASE_URL:-https://digipharma.com.tr}"
echo -e "  User Count: ${USER_COUNT:-50}"
echo -e "  Parallel: ${PARALLEL:-10}\n"

# Çalıştırma modu seç
echo -e "${YELLOW}Çalıştırma modunu seçin:${NC}"
echo "1) Docker Compose (önerilen)"
echo "2) Docker Run"
echo "3) Python Standalone"
read -p "Seçim (1-3): " choice

case $choice in
    1)
        echo -e "\n${BLUE}🐳 Docker Compose ile başlatılıyor...${NC}\n"
        docker-compose up --build
        ;;
    2)
        echo -e "\n${BLUE}🐳 Docker ile başlatılıyor...${NC}\n"
        docker build -t playwright-exam-test .
        docker run --rm \
            -e SURVEY_TOKEN="$SURVEY_TOKEN" \
            -e BASE_URL="${BASE_URL:-https://digipharma.com.tr}" \
            -e USER_COUNT="${USER_COUNT:-50}" \
            -e PARALLEL="${PARALLEL:-50}" \
            -v "$(pwd)/reports:/app/reports" \
            -v /tmp:/tmp \
            playwright-exam-test
        ;;
    3)
        echo -e "\n${BLUE}🐍 Python ile başlatılıyor...${NC}\n"
        
        # Virtual environment kontrolü
        if [ ! -d "venv" ]; then
            echo -e "${YELLOW}Python virtual environment oluşturuluyor...${NC}"
            python3 -m venv venv
        fi
        
        # Activate venv
        source venv/bin/activate
        
        # Bağımlılıkları yükle
        echo -e "${YELLOW}Bağımlılıklar yükleniyor...${NC}"
        pip install -q -r requirements.txt
        
        # Playwright tarayıcıları kontrol et
        if ! command -v playwright &> /dev/null; then
            echo -e "${YELLOW}Playwright tarayıcıları yükleniyor...${NC}"
            playwright install chromium
            playwright install-deps chromium
        fi
        
        # Testi çalıştır
        echo -e "${GREEN}Test başlatılıyor...${NC}\n"
        export SURVEY_TOKEN BASE_URL USER_COUNT PARALLEL
        python test_exam_playwright.py
        ;;
    *)
        echo -e "${RED}Geçersiz seçim!${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✅ Test tamamlandı!${NC}"
echo -e "${BLUE}Raporlar: ${NC}playwright_report_*.json"
