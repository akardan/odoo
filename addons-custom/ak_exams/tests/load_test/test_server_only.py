#!/usr/bin/env python3
"""
Pure HTTP Load Test - Browser Rendering Yok
Sadece Odoo server yükünü ölçer
"""

import requests
import time
import threading
import statistics
from datetime import datetime

BASE_URL = "https://digipharma.com.tr"
SURVEY_TOKEN = "16a184a0-d826-4451-bb61-ce4754b1526d"
USER_COUNT = 20
QUESTION_COUNT = 4

# Response time tracking
response_times = []
errors = []
lock = threading.Lock()

def simulate_user(user_id):
    """Bir kullanıcının sınavını simüle et - sadece HTTP requestleri"""
    try:
        session = requests.Session()
        user_start = time.time()
        
        # 1. Survey sayfasını aç (GET)
        start = time.time()
        response = session.get(f"{BASE_URL}/survey/start/{SURVEY_TOKEN}", allow_redirects=True)
        with lock:
            response_times.append(time.time() - start)
        
        if response.status_code != 200:
            with lock:
                errors.append(f"User {user_id}: Survey start failed - {response.status_code}")
            return
        
        # Access token'ı bul
        # Gerçek üretim ortamında bu sayfada olur, şimdilik mock edelim
        access_token = f"mock_token_{user_id}_{int(time.time())}"
        
        # 2. Her soru için submit (JSON POST)
        for q in range(1, QUESTION_COUNT + 1):
            start = time.time()
            payload = {
                "params": {
                    "survey_token": SURVEY_TOKEN,
                    "access_token": access_token,
                    f"question_id_{q}": f"answer_{q}"
                }
            }
            response = session.post(
                f"{BASE_URL}/survey/submit/{SURVEY_TOKEN}/{access_token}",
                json=payload
            )
            with lock:
                response_times.append(time.time() - start)
            
            if response.status_code != 200:
                with lock:
                    errors.append(f"User {user_id}: Question {q} submit failed - {response.status_code}")
            
            time.sleep(0.5)  # Soru arası bekleme
        
        user_elapsed = time.time() - user_start
        print(f"✅ Kullanıcı {user_id} tamamlandı - {user_elapsed:.2f} saniye")
        
    except Exception as e:
        with lock:
            errors.append(f"User {user_id}: Exception - {str(e)}")

def main():
    print("=" * 70)
    print("🔥 HTTP-ONLY YÜK TESTİ (Browser Rendering YOK)")
    print("=" * 70)
    print(f"📊 Toplam Kullanıcı: {USER_COUNT}")
    print(f"🔗 Survey Token: {SURVEY_TOKEN}")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📝 Soru Sayısı: {QUESTION_COUNT}")
    print("=" * 70)
    print()
    
    # CPU monitör uyarısı
    print("💡 BU TEST SIRASINDA:")
    print("   - CPU kullanımı çok düşük olmalı (%5-10)")
    print("   - Browser rendering YOK")
    print("   - Sadece HTTP request/response")
    print()
    print("🚀 Test başlıyor...")
    print()
    
    start_time = time.time()
    
    # Thread'leri başlat
    threads = []
    for i in range(1, USER_COUNT + 1):
        thread = threading.Thread(target=simulate_user, args=(i,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Kademeli başlatma
    
    # Tamamlanmasını bekle
    for thread in threads:
        thread.join()
    
    elapsed = time.time() - start_time
    
    # Sonuçları göster
    print()
    print("=" * 70)
    print("📊 HTTP-ONLY TEST SONUÇLARI")
    print("=" * 70)
    print(f"⏱️  Toplam Süre: {elapsed:.2f} saniye")
    print(f"👥 Kullanıcı: {USER_COUNT}")
    print(f"❌ Hata: {len(errors)}")
    print(f"📡 Toplam Request: {len(response_times)}")
    print()
    
    if response_times:
        print("📈 RESPONSE TIME İSTATİSTİKLERİ:")
        print(f"   ⚡ Min: {min(response_times)*1000:.0f} ms")
        print(f"   📊 Ortalama: {statistics.mean(response_times)*1000:.0f} ms")
        print(f"   📈 Median: {statistics.median(response_times)*1000:.0f} ms")
        print(f"   🔥 Max: {max(response_times)*1000:.0f} ms")
        print(f"   📉 StdDev: {statistics.stdev(response_times)*1000:.0f} ms" if len(response_times) > 1 else "")
    
    if errors:
        print()
        print("❌ HATALAR:")
        for error in errors[:10]:  # İlk 10 hatayı göster
            print(f"   {error}")
    
    print("=" * 70)
    print()
    print("💡 KARŞILAŞTIRMA:")
    print(f"   🖥️  Playwright Test (Browser rendering var): ~165 saniye, CPU %100")
    print(f"   📡 HTTP-Only Test (Browser rendering YOK): ~{elapsed:.0f} saniye, CPU %??")
    print()
    print("👉 Şimdi CPU kullanımını kontrol edin!")
    print("   Playwright test: %100 → Browser rendering")
    print("   HTTP-only test: %5-10 → Gerçek Odoo server yükü")

if __name__ == "__main__":
    main()
