#!/usr/bin/env python3
"""Survey HTML yapısını debug et"""

from playwright.sync_api import sync_playwright
import sys

SURVEY_TOKEN = "16a184a0-d826-4451-bb61-ce4754b1526d"
BASE_URL = "https://digipharma.com.tr"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("🔍 Survey sayfası açılıyor...")
    url = f"{BASE_URL}/survey/start/{SURVEY_TOKEN}"
    page.goto(url, wait_until='networkidle')
    
    # Start butonuna tıkla
    try:
        start_btn = page.wait_for_selector('button[value="start"], button:has-text("Başla")', timeout=5000)
        if start_btn:
            start_btn.click()
            page.wait_for_load_state('networkidle')
            print("✅ Start butonuna tıklandı\n")
    except:
        print("⚠️ Start butonu bulunamadı, zaten sınav sayfasındayız\n")
    
    page.wait_for_timeout(2000)
    
    # Radio butonları ara
    print("=" * 70)
    print("RADIO BUTONLARI")
    print("=" * 70)
    
    all_radios = page.query_selector_all('input[type="radio"]')
    print(f"📊 Toplam radio sayısı: {len(all_radios)}")
    
    for i, radio in enumerate(all_radios[:10]):  # İlk 10 tanesine bak
        is_visible = radio.is_visible()
        is_enabled = radio.is_enabled()
        name = radio.get_attribute('name')
        value = radio.get_attribute('value')
        parent_html = page.evaluate('el => el.parentElement.outerHTML', radio)[:200]
        
        print(f"\n Radio #{i+1}:")
        print(f"  - Visible: {is_visible}")
        print(f"  - Enabled: {is_enabled}")
        print(f"  - Name: {name}")
        print(f"  - Value: {value}")
        print(f"  - Parent HTML: {parent_html}...")
    
    # Tüm input elementlerini listele
    print("\n" + "=" * 70)
    print("TÜM INPUT ELEMENTLERİ")
    print("=" * 70)
    
    all_inputs = page.query_selector_all('input')
    print(f"📊 Toplam input sayısı: {len(all_inputs)}")
    
    input_types = {}
    for inp in all_inputs:
        inp_type = inp.get_attribute('type') or 'text'
        input_types[inp_type] = input_types.get(inp_type, 0) + 1
    
    for inp_type, count in input_types.items():
        print(f"  - type='{inp_type}': {count} adet")
    
    # Screenshot al
    page.screenshot(path='/tmp/debug_survey.png')
    print("\n📸 Screenshot kaydedildi: /tmp/debug_survey.png")
    
    # HTML içeriğini kaydet
    html_content = page.content()
    with open('/tmp/debug_survey.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("📄 HTML kaydedildi: /tmp/debug_survey.html")
    
    browser.close()
    print("\n✅ Debug tamamlandı!")
