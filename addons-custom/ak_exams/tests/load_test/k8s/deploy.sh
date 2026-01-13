#!/bin/bash
# Kubernetes Load Test Deployment Script

set -e

echo "=============================================="
echo "🚀 EXAM LOAD TEST - K8S DEPLOYMENT"
echo "=============================================="

# Konfigürasyon
ECR_REPO="<YOUR_AWS_ACCOUNT>.dkr.ecr.eu-central-1.amazonaws.com"
IMAGE_NAME="exam-load-test"
TAG="latest"
AWS_REGION="eu-central-1"

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "${YELLOW}📋 Konfigürasyon:${NC}"
echo "   ECR Repo: ${ECR_REPO}/${IMAGE_NAME}:${TAG}"
echo "   AWS Region: ${AWS_REGION}"
echo "   Pods: 5 x 20 kullanıcı = 100 kullanıcı"
echo ""

# 1. Test script'ini kopyala
echo "${YELLOW}📦 1. Test script kopyalanıyor...${NC}"
cp ../test_exam_playwright.py .
echo "${GREEN}   ✅ test_exam_playwright.py kopyalandı${NC}"

# 2. Docker build
echo ""
echo "${YELLOW}🐳 2. Docker image build ediliyor...${NC}"
docker build -t ${IMAGE_NAME}:${TAG} .

if [ $? -eq 0 ]; then
    echo "${GREEN}   ✅ Docker build başarılı${NC}"
else
    echo "${RED}   ❌ Docker build başarısız${NC}"
    exit 1
fi

# 3. ECR login
echo ""
echo "${YELLOW}🔐 3. AWS ECR login...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

if [ $? -eq 0 ]; then
    echo "${GREEN}   ✅ ECR login başarılı${NC}"
else
    echo "${RED}   ❌ ECR login başarısız${NC}"
    exit 1
fi

# 4. Docker tag
echo ""
echo "${YELLOW}🏷️  4. Docker image tag ediliyor...${NC}"
docker tag ${IMAGE_NAME}:${TAG} ${ECR_REPO}/${IMAGE_NAME}:${TAG}
echo "${GREEN}   ✅ Tag oluşturuldu${NC}"

# 5. Docker push
echo ""
echo "${YELLOW}📤 5. ECR'ye push ediliyor...${NC}"
docker push ${ECR_REPO}/${IMAGE_NAME}:${TAG}

if [ $? -eq 0 ]; then
    echo "${GREEN}   ✅ Push başarılı${NC}"
else
    echo "${RED}   ❌ Push başarısız${NC}"
    exit 1
fi

# 6. Job YAML'i güncelle
echo ""
echo "${YELLOW}📝 6. Job YAML güncelleniyor...${NC}"
sed -i "s|<YOUR_ECR_REPO>|${ECR_REPO}|g" job.yaml
echo "${GREEN}   ✅ job.yaml güncellendi${NC}"

# 7. Kubernetes'e deploy
echo ""
echo "${YELLOW}☸️  7. Kubernetes Job deploy ediliyor...${NC}"
kubectl apply -f job.yaml

if [ $? -eq 0 ]; then
    echo "${GREEN}   ✅ Job deploy edildi${NC}"
else
    echo "${RED}   ❌ Job deploy başarısız${NC}"
    exit 1
fi

# 8. İzleme talimatları
echo ""
echo "=============================================="
echo "${GREEN}✅ DEPLOYMENT TAMAMLANDI!${NC}"
echo "=============================================="
echo ""
echo "${YELLOW}📊 İzleme Komutları:${NC}"
echo ""
echo "1️⃣  Job durumunu izle:"
echo "   ${GREEN}kubectl get jobs exam-load-test -w${NC}"
echo ""
echo "2️⃣  Pod'ları izle:"
echo "   ${GREEN}kubectl get pods -l app=exam-load-test -w${NC}"
echo ""
echo "3️⃣  Tüm pod log'larını izle:"
echo "   ${GREEN}kubectl logs -f -l app=exam-load-test --max-log-requests=10${NC}"
echo ""
echo "4️⃣  Resource kullanımını izle:"
echo "   ${GREEN}kubectl top pods -l app=exam-load-test${NC}"
echo ""
echo "5️⃣  Temizlik:"
echo "   ${GREEN}kubectl delete job exam-load-test${NC}"
echo ""
echo "${YELLOW}⏱️  Beklenen süre: 5-10 dakika${NC}"
echo ""
