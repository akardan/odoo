# Kubernetes ile 100 Kullanıcı Load Test

## Mimari

```
┌─────────────────────────────────────────────┐
│  AWS EKS Cluster                            │
│                                             │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐│
│  │  Pod 1    │  │  Pod 2    │  │  Pod 5   ││
│  │ 20 user   │  │ 20 user   │  │ 20 user  ││
│  │ 20 browser│  │ 20 browser│  │ 20 browser│
│  └─────┬─────┘  └─────┬─────┘  └─────┬────┘│
│        │              │              │      │
│        └──────────────┼──────────────┘      │
│                       │                     │
└───────────────────────┼─────────────────────┘
                        │
                        │ HTTPS
                        ▼
            ┌───────────────────────┐
            │  Odoo Server          │
            │  digipharma.com.tr    │
            └───────────────────────┘
```

**Toplam:** 5 pod x 20 kullanıcı = **100 kullanıcı** aynı anda

## Kurulum Adımları

### 1. Docker Image Build

```bash
cd /opt/odoo18/addons-custom/ak_exams/tests/load_test/k8s

# Test script'ini kopyala
cp ../test_exam_playwright.py .

# Docker build
docker build -t exam-load-test:latest .

# AWS ECR'ye push
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT>.dkr.ecr.eu-central-1.amazonaws.com

docker tag exam-load-test:latest <YOUR_AWS_ACCOUNT>.dkr.ecr.eu-central-1.amazonaws.com/exam-load-test:latest

docker push <YOUR_AWS_ACCOUNT>.dkr.ecr.eu-central-1.amazonaws.com/exam-load-test:latest
```

### 2. Kubernetes Job Deploy

```bash
# job.yaml dosyasını düzenle - ECR repo URL'ini güncelle

# Job'ı deploy et
kubectl apply -f job.yaml

# İlerlemeyi izle
kubectl get jobs exam-load-test -w

# Pod'ları izle
kubectl get pods -l app=exam-load-test -w

# Log'ları izle
kubectl logs -f -l app=exam-load-test --max-log-requests=10
```

### 3. Sonuçları Topla

```bash
# Tüm pod'ların log'larını al
for pod in $(kubectl get pods -l app=exam-load-test -o name); do
    echo "=== $pod ==="
    kubectl logs $pod
    echo ""
done > load_test_results.txt

# Başarılı pod sayısı
kubectl get pods -l app=exam-load-test --field-selector=status.phase=Succeeded | wc -l

# Başarısız pod sayısı
kubectl get pods -l app=exam-load-test --field-selector=status.phase=Failed | wc -l
```

### 4. Cleanup

```bash
# Job'ı sil (pod'lar otomatik silinir)
kubectl delete job exam-load-test
```

## Beklenen Sonuçlar

- ⏱️  **Süre:** 3-5 dakika (5 pod paralel çalışacak)
- ✅ **Başarı:** %95+ (network timeout'ları olabilir)
- 📝 **Toplam Soru:** 2500 (100 user x 25 soru)
- 💻 **CPU (Odoo server):** %10-20 (browserlar pod'larda!)

## Alternatif: kubectl run (Hızlı Test)

Kubernetes Job yerine direkt pod başlat:

```bash
# Tek pod test
kubectl run exam-test-1 \
  --image=<YOUR_ECR_REPO>/exam-load-test:latest \
  --restart=Never \
  --env="SURVEY_TOKEN=16a184a0-d826-4451-bb61-ce4754b1526d" \
  --env="USER_COUNT=20" \
  --env="PARALLEL=20"

# Log izle
kubectl logs -f exam-test-1

# Temizle
kubectl delete pod exam-test-1
```

## Monitoring

### Odoo Server CPU İzleme

Odoo server'da (digipharma):

```bash
watch -n 2 "echo '=== CPU ===' && mpstat 1 1 | tail -1"
```

### Kubernetes Resource Monitoring

```bash
# Pod resource kullanımı
kubectl top pods -l app=exam-load-test

# Node resource kullanımı
kubectl top nodes
```

## Önemli Notlar

⚠️ **Her pod için:**
- 20 browser = ~4GB RAM
- 20 browser = ~2-4 CPU core
- Toplam 5 pod = 20GB RAM, 10-20 CPU

⚠️ **Cluster Kapasitesi:**
- Node'ların yeterli resource'u olduğundan emin olun
- Auto-scaling aktif olmalı

✅ **Avantajlar:**
- Gerçek production senaryosu
- Dağıtık yük
- Odoo server gerçek performansını görebilirsiniz
