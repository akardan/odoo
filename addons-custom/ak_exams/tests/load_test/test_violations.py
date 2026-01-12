#!/usr/bin/env python3
"""
İhlal simülasyonunu direkt test eden script
Her kullanıcı için random ihlaller oluşturur
"""
import requests
import random
import urllib3
from datetime import datetime

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
BASE_URL = "https://digipharma.com.tr"
SURVEY_TOKEN = "16a184a0-d826-4451-bb61-ce4754b1526d"
USER_COUNT = 10  # Kaç kullanıcı simüle edilecek
QUESTIONS_PER_USER = 20  # Her kullanıcı kaç soru cevaplasın

def simulate_violations_for_user_input(user_input_id, question_count=20):
    """Bir user_input için random ihlaller oluştur"""
    total_violations = 0
    
    for question_num in range(1, question_count + 1):
        # Her ihlal tipi için random 1-3 arası sayı
        fullscreen_count = random.randint(1, 3)
        tab_switch_count = random.randint(1, 3)
        devtools_count = random.randint(1, 3)
        print_screen_count = random.randint(1, 3)
        
        print(f"  Soru {question_num}: Fullscreen={fullscreen_count}, Tab={tab_switch_count}, DevTools={devtools_count}, PrintScreen={print_screen_count}")
        
        # Fullscreen ihlalleri
        for i in range(fullscreen_count):
            response = requests.post(
                f"{BASE_URL}/survey/log_violation/{SURVEY_TOKEN}",
                json={
                    'user_input_id': user_input_id,
                    'violation_type': 'fullscreen_exit',
                    'question_number': question_num,
                    'timestamp': i
                },
                verify=False
            )
            if response.status_code == 200:
                total_violations += 1
        
        # Tab switch ihlalleri
        for i in range(tab_switch_count):
            response = requests.post(
                f"{BASE_URL}/survey/log_violation/{SURVEY_TOKEN}",
                json={
                    'user_input_id': user_input_id,
                    'violation_type': 'tab_switch',
                    'question_number': question_num,
                    'timestamp': i
                },
                verify=False
            )
            if response.status_code == 200:
                total_violations += 1
        
        # DevTools ihlalleri
        for i in range(devtools_count):
            response = requests.post(
                f"{BASE_URL}/survey/log_violation/{SURVEY_TOKEN}",
                json={
                    'user_input_id': user_input_id,
                    'violation_type': 'devtools_open',
                    'question_number': question_num,
                    'timestamp': i
                },
                verify=False
            )
            if response.status_code == 200:
                total_violations += 1
        
        # Print screen ihlalleri
        for i in range(print_screen_count):
            response = requests.post(
                f"{BASE_URL}/survey/log_violation/{SURVEY_TOKEN}",
                json={
                    'user_input_id': user_input_id,
                    'violation_type': 'print_screen',
                    'question_number': question_num,
                    'timestamp': i
                },
                verify=False
            )
            if response.status_code == 200:
                total_violations += 1
    
    return total_violations

def main():
    print(f"=== İhlal Simülasyonu Başlıyor ===")
    print(f"Kullanıcı sayısı: {USER_COUNT}")
    print(f"Soru sayısı: {QUESTIONS_PER_USER}")
    print(f"Başlangıç: {datetime.now()}\n")
    
    # Mevcut survey_user_input kayıtlarını kullan (son 10)
    # Normalde burada gerçek user_input_id'leri PostgreSQL'den alırdık
    # Ama test için manuel ID'ler verebiliriz
    
    # Ya da yeni session başlat
    for user_num in range(1, USER_COUNT + 1):
        print(f"\n--- Kullanıcı {user_num} ---")
        
        # Sınav session başlat
        response = requests.get(
            f"{BASE_URL}/survey/start/{SURVEY_TOKEN}",
            verify=False
        )
        
        if response.status_code != 200:
            print(f"  ❌ Session başlatılamadı: {response.status_code}")
            continue
        
        # Session cookie'den user_input_id'yi al (gerçek implementasyonda)
        # Şimdilik simüle edelim - son kayıtlardaki ID'leri kullanabiliriz
        # Örnek: 53346 + user_num gibi
        user_input_id = 53345 + user_num  # Son test kayıtlarından
        
        print(f"  User Input ID: {user_input_id}")
        total = simulate_violations_for_user_input(user_input_id, QUESTIONS_PER_USER)
        print(f"  ✅ Toplam {total} ihlal kaydı oluşturuldu")
    
    print(f"\n=== Tamamlandı ===")
    print(f"Bitiş: {datetime.now()}")

if __name__ == "__main__":
    main()
