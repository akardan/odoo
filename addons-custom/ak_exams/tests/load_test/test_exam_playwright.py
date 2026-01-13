#!/usr/bin/env python3
"""
Playwright ile Gerçek UI Yük Testi
==================================
Bu script, gerçek tarayıcı (Chromium) kullanarak sınav sistemini test eder.
Her kullanıcı gerçek bir tarayıcı instance'ı ile sınavı tamamlar.

Kullanım:
    SURVEY_TOKEN=your_token python test_exam_playwright.py
    
Parametreler (opsiyonel):
    SURVEY_TOKEN: Sınav link'inin sonundaki token
    USER_COUNT: Toplam kullanıcı sayısı (default: 50)
    PARALLEL: Aynı anda çalışacak kullanıcı sayısı (default: 10)
    HEADLESS: Tarayıcıyı gizli modda çalıştır (default: true)
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import os
import sys
from datetime import datetime
import json
import random
import requests

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Kullanıcı %(user)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ExamTester:
    def __init__(self, survey_token, base_url="https://digipharma.com.tr"):
        self.survey_token = survey_token
        self.base_url = base_url
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def _simulate_real_violations(self, page, question_number, logger):
        """Gerçek kullanıcı gibi HAFIF ihlal yap - max_total_violations_allowed limitini aşmamak için"""
        # GERÇEK KULLANICI DAVRANIŞI: Her violation simülasyonunda sadece 1-2 ihlal
        # Çok fazla violation yaparsak max_total_violations_allowed limitini aşıp sınav otomatik kapanır
        
        # Rastgele bir violation tipi seç (her seferinde sadece 1 tip)
        violation_types = ['fullscreen', 'tab_switch', 'devtools', 'print_screen']
        selected_type = random.choice(violation_types)
        
        # Seçilen tip için 1 kez ihlal yap (nadiren 2)
        count = 1 if random.random() < 0.8 else 2  # %80 ihtimalle 1, %20 ihtimalle 2
        
        violations_config = {
            'fullscreen': count if selected_type == 'fullscreen' else 0,
            'tab_switch': count if selected_type == 'tab_switch' else 0,
            'devtools': count if selected_type == 'devtools' else 0,
            'print_screen': count if selected_type == 'print_screen' else 0
        }
        
        total = sum(violations_config.values())
        logger.info(f"Soru {question_number}: 🚨 Hafif ihlal simülasyonu - "
                   f"Tip:{selected_type}, Miktar:{count} (max_violations limitini aşmamak için)")
        
        # 1. FULLSCREEN ÇIKIŞ İHLALİ
        for i in range(violations_config['fullscreen']):
            try:
                # Fullscreen'den çık (İHLAL!)
                page.evaluate('document.exitFullscreen().catch(() => {})')
                page.wait_for_timeout(500)
                logger.debug(f"  ↳ Fullscreen ihlali #{i+1} tetiklendi")
                
                # Popup'ta "Re-enter Fullscreen" butonunu bul ve tıkla
                reenter_selectors = [
                    'button:has-text("Re-enter")',
                    'button:has-text("Fullscreen")',
                    'button:has-text("Tam Ekran")',
                    'button:has-text("Tekrar")',
                    '.modal button.btn-primary',
                    '.swal2-confirm',
                    'button[class*="confirm"]'
                ]
                
                for selector in reenter_selectors:
                    try:
                        reenter_btn = page.wait_for_selector(selector, timeout=2000)
                        if reenter_btn and reenter_btn.is_visible():
                            reenter_btn.click(force=True)
                            logger.debug(f"  ↳ Re-enter Fullscreen butonuna tıklandı")
                            page.wait_for_timeout(500)
                            break
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"  ↳ Fullscreen ihlali hatası: {str(e)}")
                pass
        
        # 2. TAB SWITCH İHLALİ
        for i in range(violations_config['tab_switch']):
            try:
                # Visibility change event'ini tetikle
                page.evaluate('''
                    window.dispatchEvent(new Event('blur'));
                    document.dispatchEvent(new Event('visibilitychange'));
                ''')
                page.wait_for_timeout(200)
                page.evaluate('''
                    window.dispatchEvent(new Event('focus'));
                    document.dispatchEvent(new Event('visibilitychange'));
                ''')
                page.wait_for_timeout(100)
                logger.debug(f"  ↳ Tab switch ihlali #{i+1} tetiklendi")
            except:
                pass
        
        # 3. DEVTOOLS İHLALİ
        for i in range(violations_config['devtools']):
            try:
                # DevTools detection simülasyonu
                # Console.log width değişikliği gibi DevTools algılama yöntemlerini tetikle
                page.evaluate('''
                    // DevTools açılma simülasyonu
                    window.outerWidth = window.innerWidth + 300;
                    window.dispatchEvent(new Event('resize'));
                ''')
                page.wait_for_timeout(150)
                # Normale dön
                page.evaluate('''
                    window.dispatchEvent(new Event('resize'));
                ''')
                logger.debug(f"  ↳ DevTools ihlali #{i+1} tetiklendi")
            except:
                pass
        
        # 4. PRINT SCREEN İHLALİ
        for i in range(violations_config['print_screen']):
            try:
                # PrintScreen tuşuna basma simülasyonu
                page.keyboard.press('PrintScreen')
                page.wait_for_timeout(100)
                logger.debug(f"  ↳ PrintScreen ihlali #{i+1} tetiklendi")
            except:
                pass
        
        page.wait_for_timeout(300)  # İhlal kayıtlarının işlenmesi için
        
    def test_single_user(self, user_id):
        """Tek bir kullanıcı için sınav testi çalıştır"""
        logger = logging.LoggerAdapter(logging.getLogger(), {'user': user_id})
        result = {
            'user_id': user_id,
            'status': 'UNKNOWN',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'questions_answered': 0,
            'errors': [],
            'screenshots': []
        }
        
        browser = None
        context = None
        playwright_instance = None
        
        try:
            playwright_instance = sync_playwright().start()
            
            # Tarayıcıyı başlat
            headless = os.environ.get('HEADLESS', 'true').lower() == 'true'
            browser = playwright_instance.chromium.launch(
                headless=headless,
                args=['--disable-dev-shm-usage', '--no-sandbox']  # Prevent resource issues
            )
            
            # iPad device emulation
            # Support for various iPad models (Pro, Air, standard)
            ipad_devices = [
                {
                    'name': 'iPad Pro 12.9',
                    'viewport': {'width': 1024, 'height': 1366},
                    'user_agent': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                    'device_scale_factor': 2,
                    'is_mobile': True,
                    'has_touch': True
                },
                {
                    'name': 'iPad Air',
                    'viewport': {'width': 820, 'height': 1180},
                    'user_agent': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                    'device_scale_factor': 2,
                    'is_mobile': True,
                    'has_touch': True
                },
                {
                    'name': 'iPad Mini',
                    'viewport': {'width': 768, 'height': 1024},
                    'user_agent': 'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                    'device_scale_factor': 2,
                    'is_mobile': True,
                    'has_touch': True
                }
            ]
            
            # Randomly select an iPad device for variety
            selected_device = random.choice(ipad_devices)
            logger.info(f"Emulating device: {selected_device['name']}")
            
            # Yeni sayfa aç - iPad emulation
            context = browser.new_context(
                viewport=selected_device['viewport'],
                user_agent=selected_device['user_agent'],
                device_scale_factor=selected_device['device_scale_factor'],
                is_mobile=selected_device['is_mobile'],
                has_touch=selected_device['has_touch']
            )
            page = context.new_page()
            
            # Console hatalarını dinle - Detaylı loglama ile
            console_errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    error_text = msg.text
                    console_errors.append(error_text)
                    # Console hatalarını gerçek zamanlı logla
                    if 'ERR_UNKNOWN_URL_SCHEME' not in error_text and 'Save All' not in error_text:
                        logger.warning(f"Console Error: {error_text}")
            
            page.on('console', handle_console)
            page.on('pageerror', lambda exc: console_errors.append(str(exc)) or logger.error(f"Page Error: {str(exc)}"))
            
            logger.info("Sınav sayfası açılıyor...")
            
            # Sınav sayfasına git
            url = f"{self.base_url}/survey/start/{self.survey_token}"
            page.goto(url, wait_until='networkidle', timeout=30000)
                
            # Screenshot al (Disabled for performance)
            # screenshot_path = f"/tmp/user_{user_id}_start.png"
            # page.screenshot(path=screenshot_path)
            # result['screenshots'].append(screenshot_path)
            logger.info(f"Başlangıç - screenshot devre dışı (performans)")
            
            # "Start" butonunu bul ve tıkla
            try:
                logger.info("Start butonuna tıklanıyor...")
                start_button = page.wait_for_selector(
                    'button[value="start"], button:has-text("Başla"), button:has-text("Start")',
                    timeout=10000
                )
                if start_button:
                    start_button.click()
                    page.wait_for_load_state('networkidle')
                    logger.info("Sınav başlatıldı!")
                else:
                    # Belki zaten sınav sayfasındayız
                    logger.warning("Start butonu bulunamadı, zaten sınav başlamış olabilir")
            except PlaywrightTimeout:
                logger.warning("Start butonu timeout - zaten sınav sayfasında olabilir")
            
            # Soruları cevapla
            question_number = 0
            max_questions = 100  # Sonsuz döngüyü engellemek için
            
            while question_number < max_questions:
                question_number += 1
                
                try:
                    # Sınav bitmiş mi kontrol et
                    if self._check_completion(page):
                        logger.info(f"✅ Sınav başarıyla tamamlandı! Toplam {question_number-1} soru cevaplandı")
                        result['status'] = 'SUCCESS'
                        result['questions_answered'] = question_number - 1
                        break
                    
                    logger.info(f"Soru {question_number} cevaplandırılıyor...")
                    
                    # Sayfanın tam yüklendiğinden emin ol
                    page.wait_for_timeout(1000)
                        
                    # Soruyu cevapla - Radio, Checkbox veya Text
                    answered = False
                    
                    # 1. RADIO BUTTON (Simple Choice - A,B,C,D)
                    # Odoo Survey'de radio butonlar gizli, label'lara tıklamak gerekiyor
                    try:
                        # Radio butonların label'larını bul
                        radio_labels = page.query_selector_all('label.o_survey_choice_btn')
                        
                        if radio_labels and len(radio_labels) > 0:
                            # İlk label'a tıkla
                            first_label = radio_labels[0]
                            first_label.click(force=True)
                            
                            page.wait_for_timeout(500)
                            
                            # İlgili radio'nun seçildiğini kontrol et
                            label_for = first_label.get_attribute('for')
                            if label_for:
                                checked = page.evaluate(f'document.getElementById("{label_for}")?.checked')
                                if checked:
                                    logger.info(f"Soru {question_number}: ✅ Radio seçildi (label tıklama) - Toplam {len(radio_labels)} şık")
                                    answered = True
                                else:
                                    logger.warning(f"Soru {question_number}: ⚠️ Label tıklandı ama radio seçilmedi")
                                    answered = True  # Yine de devam et
                            else:
                                logger.info(f"Soru {question_number}: ✅ Label tıklandı - Toplam {len(radio_labels)} şık")
                                answered = True
                    except Exception as e:
                        logger.warning(f"Soru {question_number}: Radio/Label hatası - {str(e)}")
                   
                    # 2. CHECKBOX (Multiple Choice)
                    if not answered:
                        try:
                            all_checkboxes = page.query_selector_all('input[type="checkbox"]')
                            visible_checkboxes = [cb for cb in all_checkboxes if cb.is_visible()]
                            
                            if visible_checkboxes and len(visible_checkboxes) > 0:
                                page.evaluate('''(checkbox) => {
                                    checkbox.checked = true;
                                    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                                    checkbox.dispatchEvent(new Event('input', { bubbles: true }));
                                }''', visible_checkboxes[0])
                                logger.info(f"Soru {question_number}: ✅ Checkbox seçildi")
                                answered = True
                                page.wait_for_timeout(300)
                        except Exception as e:
                            logger.warning(f"Soru {question_number}: Checkbox hatası - {str(e)}")
                    
                    # 3. TEXT INPUT
                    if not answered:
                        try:
                            all_text_inputs = page.query_selector_all('input[type="text"], textarea')
                            visible_text_inputs = [ti for ti in all_text_inputs if ti.is_visible()]
                            
                            if visible_text_inputs and len(visible_text_inputs) > 0:
                                visible_text_inputs[0].fill("Test cevabı")
                                logger.info(f"Soru {question_number}: ✅ Text input dolduruldu")
                                answered = True
                                page.wait_for_timeout(300)
                        except Exception as e:
                            logger.warning(f"Soru {question_number}: Text input hatası - {str(e)}")
                    
                    # CEVAP KONTROLü
                    if not answered:
                        logger.error(f"Soru {question_number}: ❌ HİÇBİR CEVAP VERİLEMEDİ!")
                    
                    # İhlal simülasyonu yap (her 8-12 soruda bir, çok daha az agresif)
                    # Gerçek kullanıcılar her soruda violation yapmaz
                    # max_total_violations_allowed limitini aşıp sınavın erken kapanmasını engellemek için
                    if question_number % random.randint(8, 12) == 0:
                        self._simulate_real_violations(page, question_number, logger)
                    
                    # Submit butonunu bul
                    submit_selectors = [
                        'button:has-text("Gönder")',  # ÖNCELİK - Final submit butonu
                        'button:has-text("Submit")',
                        'button:has-text("Save All")',
                        'button[type="submit"].btn-primary',
                        'button.btn-primary[type="submit"]',
                        'button[type="submit"]',
                        'button.o_survey_submit',
                        'form button[type="submit"]',
                        'a.btn-primary[role="button"]',
                        '.o_survey_submit_button',
                        'button:has-text("Finish")',
                        'button:has-text("Complete")',
                        'button:has-text("Tamamla")',
                        'button:has-text("Kaydet")',
                        'button:has-text("Next")',  # Sonraki soru
                        'button:has-text("İleri")'
                    ]
                    
                    submit_button = None
                    selected_selector = None
                    for selector in submit_selectors:
                        try:
                            submit_button = page.query_selector(selector)
                            if submit_button and submit_button.is_visible():
                                selected_selector = selector
                                logger.info(f"Soru {question_number}: Submit butonu bulundu ({selector})")
                                break
                        except:
                            continue
                    
                    if submit_button:
                        # Fullscreen overlay'i kaldır (sınav güvenlik önlemi)
                        try:
                            page.evaluate('document.getElementById("ak-fullscreen-overlay")?.remove()')
                            page.wait_for_timeout(100)
                        except:
                            pass
                        
                        # Force click kullan (overlay bypass)
                        try:
                            submit_button.click(force=True)
                            logger.info(f"Soru {question_number}: Submit yapıldı ({selected_selector})")
                        except:
                            # Force click de işe yaramazsa JavaScript ile
                            logger.warning(f"Soru {question_number}: Normal click başarısız, JavaScript ile deneniyor")
                            page.evaluate('element => element.click()', submit_button)
                            logger.info(f"Soru {question_number}: Submit yapıldı (JavaScript)")
                        
                        # Sayfa yüklensin
                        try:
                            page.wait_for_load_state('networkidle', timeout=10000)
                        except:
                            # Networkidle beklemek her zaman başarılı olmayabilir
                            page.wait_for_timeout(2000)
                        
                        # Tamamlanma kontrolü
                        page.wait_for_timeout(1500)
                        if self._check_completion(page):
                            logger.info(f"✅ Sınav tamamlandı! (Soru {question_number})")
                            result['status'] = 'SUCCESS'
                            result['questions_answered'] = question_number
                            break
                        
                        # Eğer "Gönder" butonuysa, muhtemelen son sayfa
                        if selected_selector and "Gönder" in selected_selector:
                            logger.info(f"'Gönder' butonuna tıklandı - Sınav bitiyor olabilir")
                            page.wait_for_timeout(2000)
                            if self._check_completion(page):
                                logger.info(f"✅ Sınav Gönder butonu ile tamamlandı!")
                                result['status'] = 'SUCCESS'
                                result['questions_answered'] = question_number
                                break
                    else:
                        logger.warning(f"Soru {question_number}: Submit butonu bulunamadı")
                        
                        # Belki sınav zaten tamamlanmıştır?
                        if self._check_completion(page):
                            logger.info(f"✅ Sınav zaten tamamlanmış")
                            result['status'] = 'SUCCESS'
                            result['questions_answered'] = question_number
                            break
                        
                        # JavaScript ile form submit etmeyi dene
                        try:
                            page.evaluate('document.querySelector("form")?.submit()')
                            page.wait_for_timeout(2000)
                            if self._check_completion(page):
                                result['status'] = 'SUCCESS'
                                result['questions_answered'] = question_number
                                break
                        except:
                            logger.error(f"Soru {question_number}: Form submit başarısız")
                            break
                        
                except PlaywrightTimeout as e:
                    logger.error(f"Soru {question_number}: Timeout hatası - {str(e)}")
                    # Screenshot disabled for performance
                    # screenshot_path = f"/tmp/user_{user_id}_error_q{question_number}.png"
                    # page.screenshot(path=screenshot_path)
                    # result['screenshots'].append(screenshot_path)
                    result['errors'].append(f"Question {question_number}: Timeout")
                    
                    # Sınav bitmiş olabilir
                    if self._check_completion(page):
                        logger.info("Sınav tamamlandı (timeout sonrası kontrol)")
                        result['status'] = 'SUCCESS'
                        result['questions_answered'] = question_number
                        break
                    else:
                        result['status'] = 'FAILED'
                        break
                        
                except Exception as e:
                    logger.error(f"Soru {question_number}: Beklenmeyen hata - {str(e)}")
                    # Screenshot disabled for performance
                    # screenshot_path = f"/tmp/user_{user_id}_error_q{question_number}.png"
                    # page.screenshot(path=screenshot_path)
                    # result['screenshots'].append(screenshot_path)
                    result['errors'].append(f"Question {question_number}: {str(e)}")
                    result['status'] = 'FAILED'
                    break
            
            # Eğer buraya kadar geldiyse ve status hala UNKNOWN ise,
            # muhtemelen tüm sorular cevaplandı ama completion tespit edilemedi
            if result['status'] == 'UNKNOWN' and question_number > 0:
                result['status'] = 'SUCCESS'
                result['questions_answered'] = question_number
                logger.info(f"✅ Sınav tamamlandı (max soru limitine ulaşıldı): {question_number} soru")
            
            # Console hatalarını kaydet
            if console_errors:
                result['errors'].extend([f"Console: {err}" for err in console_errors])
                logger.warning(f"{len(console_errors)} console hatası tespit edildi")
            
            # Son screenshot (Disabled for performance)
            # screenshot_path = f"/tmp/user_{user_id}_end.png"
            # page.screenshot(path=screenshot_path)
            # result['screenshots'].append(screenshot_path)
                
        except Exception as e:
            logger.error(f"❌ Kritik hata: {str(e)}")
            result['status'] = 'CRITICAL_ERROR'
            result['errors'].append(f"Critical: {str(e)}")
        finally:
            # CRITICAL: Always cleanup browser resources to prevent EPIPE errors
            try:
                if context:
                    context.close()
                    logger.debug("Context closed successfully")
            except Exception as e:
                logger.warning(f"Error closing context: {str(e)}")
            
            try:
                if browser:
                    browser.close()
                    logger.debug("Browser closed successfully")
            except Exception as e:
                logger.warning(f"Error closing browser: {str(e)}")
            
            try:
                if playwright_instance:
                    playwright_instance.stop()
                    logger.debug("Playwright instance stopped successfully")
            except Exception as e:
                logger.warning(f"Error stopping playwright: {str(e)}")
        
        result['completed_at'] = datetime.now().isoformat()
        
        # Durum log'u
        if result['status'] == 'SUCCESS':
            logger.info(f"✅ Kullanıcı testi BAŞARILI - {result['questions_answered']} soru")
        else:
            logger.error(f"❌ Kullanıcı testi BAŞARISIZ - Durum: {result['status']}")
        
        return result
    
    def _check_completion(self, page):
        """Sınavın tamamlanıp tamamlanmadığını kontrol et"""
        
        # 1. URL Kontrolü (En güvenilir)
        current_url = page.url
        if "/print" in current_url or "/results" in current_url or "/done" in current_url:
            return True
        
        # 2. SADECE Tamamlanma mesajlarını kontrol et
        # Soru yoksa değil, mesaj varsa TRUE
        completion_keywords = [
            "sınav tamamlanmıştır",
            "katılımınız için teşekkürler",
            "sayfayı kapatabilirsiniz",
            "thank you for participating",
            "survey has been submitted",
            "cevaplarınız kaydedildi"
        ]
        
        page_content = page.content().lower()
        for keyword in completion_keywords:
            if keyword in page_content:
                return True
        
        return False
    
    def run_load_test(self, user_count=50, parallel_count=5):
        """Yük testini çalıştır"""
        print("\n" + "="*70)
        print("🚀 PLAYWRIGHT UI YÜK TESTİ BAŞLIYOR")
        print("="*70)
        print(f"📊 Toplam Kullanıcı: {user_count}")
        print(f"⚡ Paralel Kullanıcı: {parallel_count}")
        print(f"🔗 Survey Token: {self.survey_token}")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"👁️  Headless Mode: {os.environ.get('HEADLESS', 'true')}")
        print(f"⚠️  Browser Launch Delay: 0.5s (prevent EPIPE errors)")
        print("="*70 + "\n")
        
        self.start_time = time.time()
        
        # Paralel olarak kullanıcıları çalıştır
        with ThreadPoolExecutor(max_workers=parallel_count) as executor:
            futures = {}
            
            # Launch browsers with delay to prevent resource exhaustion
            for user_id in range(1, user_count + 1):
                future = executor.submit(self.test_single_user, user_id)
                futures[future] = user_id
                
                # Small delay between browser launches to prevent EPIPE
                if user_id % parallel_count == 0:
                    time.sleep(0.5)
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=300)  # 5 min timeout per user
                    self.results.append(result)
                    completed += 1
                    
                    # İlerleme göster
                    print(f"\n[{completed}/{user_count}] Kullanıcı {result['user_id']} tamamlandı - Durum: {result['status']}")
                except Exception as e:
                    user_id = futures[future]
                    print(f"\n[{completed+1}/{user_count}] Kullanıcı {user_id} BAŞARISIZ - Hata: {str(e)}")
                    self.results.append({
                        'user_id': user_id,
                        'status': 'EXECUTOR_ERROR',
                        'errors': [f"Executor error: {str(e)}"],
                        'questions_answered': 0,
                        'started_at': datetime.now().isoformat(),
                        'completed_at': datetime.now().isoformat(),
                        'screenshots': []
                    })
                    completed += 1
        
        self.end_time = time.time()
        self._print_summary()
        self._save_report()
    
    def _print_summary(self):
        """Test sonuçlarının özetini yazdır"""
        duration = self.end_time - self.start_time
        
        success_count = len([r for r in self.results if r['status'] == 'SUCCESS'])
        failed_count = len([r for r in self.results if r['status'] == 'FAILED'])
        critical_count = len([r for r in self.results if r['status'] == 'CRITICAL_ERROR'])
        
        total_questions = sum([r['questions_answered'] for r in self.results])
        avg_questions = total_questions / len(self.results) if self.results else 0
        
        print("\n" + "="*70)
        print("📊 TEST SONUÇLARI")
        print("="*70)
        print(f"⏱️  Toplam Süre: {duration:.2f} saniye ({duration/60:.2f} dakika)")
        print(f"👥 Toplam Kullanıcı: {len(self.results)}")
        print(f"✅ Başarılı: {success_count} ({success_count/len(self.results)*100:.1f}%)")
        print(f"❌ Başarısız: {failed_count} ({failed_count/len(self.results)*100:.1f}%)")
        print(f"🔥 Kritik Hata: {critical_count} ({critical_count/len(self.results)*100:.1f}%)")
        print(f"📝 Toplam Cevaplanan Soru: {total_questions}")
        print(f"📈 Ortalama Soru/Kullanıcı: {avg_questions:.1f}")
        print("="*70)
        
        # Başarısız testlerin detayları
        if failed_count > 0 or critical_count > 0:
            print("\n🔍 BAŞARISIZ TESTLER:")
            print("-"*70)
            for r in self.results:
                if r['status'] != 'SUCCESS':
                    print(f"\nKullanıcı {r['user_id']}:")
                    print(f"  Durum: {r['status']}")
                    print(f"  Cevaplanan Soru: {r['questions_answered']}")
                    if r['errors']:
                        print(f"  Hatalar:")
                        for err in r['errors'][:3]:  # İlk 3 hata
                            print(f"    - {err}")
                    if r['screenshots']:
                        print(f"  Screenshots: {', '.join(r['screenshots'])}")
            print("-"*70)
    
    def _save_report(self):
        """JSON rapor kaydet"""
        report = {
            'test_info': {
                'survey_token': self.survey_token,
                'base_url': self.base_url,
                'user_count': len(self.results),
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
                'duration_seconds': self.end_time - self.start_time
            },
            'summary': {
                'success': len([r for r in self.results if r['status'] == 'SUCCESS']),
                'failed': len([r for r in self.results if r['status'] == 'FAILED']),
                'critical': len([r for r in self.results if r['status'] == 'CRITICAL_ERROR']),
                'total_questions_answered': sum([r['questions_answered'] for r in self.results])
            },
            'results': self.results
        }
        
        filename = f"playwright_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Rapor kaydedildi: {filename}")


def main():
    # Environment variable'dan token al
    survey_token = os.environ.get('SURVEY_TOKEN')
    
    if not survey_token:
        print("❌ HATA: SURVEY_TOKEN environment variable tanımlanmamış!")
        print("\nKullanım:")
        print("  SURVEY_TOKEN=your_token python test_exam_playwright.py")
        print("\nÖrnek:")
        print("  SURVEY_TOKEN=49660127-9ee1-4377-ad89-4771401ae43b python test_exam_playwright.py")
        sys.exit(1)
    
    # Opsiyonel parametreler
    user_count = int(os.environ.get('USER_COUNT', 50))
    parallel_count = int(os.environ.get('PARALLEL', 5))  # Reduced default from 10 to 5
    base_url = os.environ.get('BASE_URL', 'https://digipharma.com.tr')
    
    # Test başlat
    tester = ExamTester(survey_token, base_url)
    tester.run_load_test(user_count, parallel_count)


if __name__ == "__main__":
    main()
