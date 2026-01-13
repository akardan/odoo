#!/usr/bin/env python3
"""Survey bilgilerini kontrol et"""

import requests

SURVEY_TOKEN = "16a184a0-d826-4451-bb61-ce4754b1526d"
BASE_URL = "https://digipharma.com.tr"

# Survey sayfasını al
url = f"{BASE_URL}/survey/start/{SURVEY_TOKEN}"
response = requests.get(url, allow_redirects=True)

print(f"URL: {url}")
print(f"Final URL: {response.url}")
print(f"Status: {response.status_code}")
print("\n" + "="*70)

# HTML'de "question" kelimesini say
question_count = response.text.count('o_survey_question')
print(f"Sayfada 'o_survey_question' sayısı: {question_count}")

# Pagination var mı?
has_next = 'Next' in response.text or 'İleri' in response.text
has_submit = 'Submit' in response.text or 'Gönder' in response.text
has_save_all = 'Save All' in response.text or 'Tümünü Kaydet' in response.text

print(f"'Next' butonu var mı? {has_next}")
print(f"'Submit' butonu var mı? {has_submit}")
print(f"'Save All' butonu var mı? {has_save_all}")

# Sınav tipini anla
if 'one page' in response.text.lower() or 'tek sayfa' in response.text.lower():
    print("\n📄 Sınav Tipi: ONE PAGE (Tüm sorular tek sayfada)")
elif 'page per section' in response.text.lower():
    print("\n📄 Sınav Tipi: PAGE PER SECTION (Bölüm başına sayfa)")
elif 'page per question' in response.text.lower() or has_next:
    print("\n📄 Sınav Tipi: PAGE PER QUESTION (Soru başına sayfa)")
else:
    print("\n📄 Sınav Tipi: BELİRSİZ")

print("="*70)
