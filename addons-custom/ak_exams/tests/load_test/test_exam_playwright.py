#!/usr/bin/env python3
"""
Playwright ile Gerçek UI Yük Testi (Optimize Edilmiş + Hata Dayanıklı)
=====================================================================
Kullanım:
    SURVEY_TOKEN=your_token python test_exam_playwright.py

Parametreler:
    SURVEY_TOKEN : Sınav token'ı (zorunlu)
    USER_COUNT   : Toplam kullanıcı sayısı (default: 50)
    PARALLEL     : Paralel kullanıcı sayısı (default: 10)
    BASE_URL     : Sunucu adresi (default: https://digipharma.com.tr)
    HEADLESS     : Gizli mod (default: true)

Kapsanan hata senaryoları:
  - Sunucu hata sayfası / erişim reddedildi / sınav kapalı
  - Validation hatası → stuck state (submit tıklandı ama sayfa değişmedi)
  - SweetAlert / Bootstrap modal popup'ları bloklama
  - Sunucu tarafından oturum sonlandırma (güvenlik ihlali limiti)
  - Ağ hatası / timeout ortasında recovery
  - Güvenlik overlay sürekli çıkıp tıklamayı engellemesi
  - Yanlış cevap gönderilmeden submit — validation döngüsü
  - Sınav süresi dolmuş ya da henüz başlamamış
  - Aynı soru ikinci kez gelme (stuck-question dedektörü)
"""

import os, sys, json, time, random, logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Kullanıcı %(user)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ---------------------------------------------------------------------------
# Hata türleri — test raporunda nedenini görmek için
# ---------------------------------------------------------------------------
STATUS_SUCCESS        = 'SUCCESS'
STATUS_CRITICAL       = 'CRITICAL_ERROR'
STATUS_SURVEY_CLOSED  = 'SURVEY_CLOSED'       # Sınav kapalı / süresi dolmuş
STATUS_TERMINATED     = 'SESSION_TERMINATED'  # Sunucu oturumu kapattı
STATUS_STUCK          = 'STUCK_LOOP'          # Sayfa değişmeden döngüde kaldı

IPAD_DEVICES = [
    {
        'viewport': {'width': 1024, 'height': 1366},
        'user_agent': 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'device_scale_factor': 2, 'is_mobile': True, 'has_touch': True,
    },
    {
        'viewport': {'width': 820, 'height': 1180},
        'user_agent': 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'device_scale_factor': 2, 'is_mobile': True, 'has_touch': True,
    },
    {
        'viewport': {'width': 768, 'height': 1024},
        'user_agent': 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'device_scale_factor': 2, 'is_mobile': True, 'has_touch': True,
    },
]

# URL / içerik bazlı hata belirteçleri
ERROR_KEYWORDS = [
    # Türkçe
    'bu sınav henüz başlamamıştır',
    'bu sınav sona ermiştir',
    'erişim reddedildi',
    'sayfa bulunamadı',
    'bir hata oluştu',
    'yetkiniz yok',
    # İngilizce
    'access denied',
    'forbidden',
    'page not found',
    'error occurred',
    '404',
    '500',
    'internal server error',
]

# Sunucu tarafından oturum kapatılma belirteçleri
TERMINATED_KEYWORDS = [
    'güvenlik ihlali',
    'sınavınız sonlandırıldı',
    'oturumunuz kapatıldı',
    'terminated due to security',
    'security violations',
    'exam has been terminated',
    'is_terminated',
]

# Tamamlanma belirteçleri
COMPLETED_KEYWORDS = [
    'sınav tamamlanmıştır',
    'katılımınız için teşekkürler',
    'sayfayı kapatabilirsiniz',
    'thank you for participating',
    'survey has been submitted',
    'cevaplarınız kaydedildi',
    'you scored',
    'anketiniz gönderildi',
    'tebrikler',
    'congratulations',
]


class ExamTester:
    def __init__(self, survey_token, base_url="https://digipharma.com.tr"):
        self.survey_token = survey_token
        self.base_url = base_url
        self.results = []
        self.start_time = None
        self.end_time = None

    # ------------------------------------------------------------------
    # Yardımcı: Sayfanın içeriğini güvenli al
    # ------------------------------------------------------------------
    def _get_content_lower(self, page):
        try:
            return page.content().lower()
        except Exception:
            return ''

    # ------------------------------------------------------------------
    # Hata/durum kontrolü
    # ------------------------------------------------------------------
    def _check_page_state(self, page):
        """
        Sayfanın mevcut durumunu döndürür:
          'completed'  — Sınav başarıyla tamamlandı
          'terminated' — Sunucu oturumu kapattı (güvenlik ihlali vb.)
          'error'      — Hata sayfası (kapalı sınav, 404, erişim yok)
          'active'     — Normal sınav sayfası devam ediyor
        """
        url = page.url
        if any(x in url for x in ('/print', '/results', '/done')):
            return 'completed'

        content = self._get_content_lower(page)

        if any(k in content for k in COMPLETED_KEYWORDS):
            return 'completed'

        if any(k in content for k in TERMINATED_KEYWORDS):
            return 'terminated'

        if any(k in content for k in ERROR_KEYWORDS):
            return 'error'

        return 'active'

    # ------------------------------------------------------------------
    # Modal / Popup kapatma
    # ------------------------------------------------------------------
    def _dismiss_modals(self, page, logger):
        """
        SweetAlert2, Bootstrap modal, ya da özel güvenlik overlay gibi
        popup'ları kapatmaya çalışır.
        """
        # Güvenlik overlay (ak_exams fullscreen uyarısı)
        try:
            page.evaluate('document.getElementById("ak-fullscreen-overlay")?.remove()')
        except Exception:
            pass

        # SweetAlert / özel popup onay butonları
        confirm_selectors = [
            '.swal2-confirm',
            '.swal2-close',
            'button.swal2-confirm',
            'button:has-text("Tamam")',
            'button:has-text("OK")',
            'button:has-text("Re-enter")',
            'button:has-text("Tam Ekran")',
            '.modal-footer .btn-primary',
            '.modal .btn:has-text("Kapat")',
            '.modal .close',
            '[data-dismiss="modal"]',
        ]
        for sel in confirm_selectors:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    btn.click(force=True)
                    page.wait_for_timeout(300)
                    logger.debug(f"Modal kapatıldı: {sel}")
                    break
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Validation hatası tespiti
    # ------------------------------------------------------------------
    def _has_validation_error(self, page):
        """
        Submit sonrası validation hatası var mı?
        (Soru cevapsız bırakıldıysa Odoo inline hata gösterir.)
        """
        try:
            content = self._get_content_lower(page)
            # Odoo survey validation mesajları
            validation_markers = [
                'this question requires an answer',
                'bu soru zorunludur',
                'o_survey_question_error',
                'is-invalid',
            ]
            return any(m in content for m in validation_markers)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Cevap seçimi — validation hatası döngüsüne karşı korumalı
    # ------------------------------------------------------------------
    def _answer_question(self, page, question_number, logger):
        """
        Sayfadaki soruyu cevapla. Radio → Checkbox → Text sırasıyla dener.
        wait_for_selector ile sayfanın render tamamlanmasını bekler.
        Maksimum MAX_ANSWER_RETRIES deneme yapar.
        """
        MAX_ANSWER_RETRIES = 2

        for attempt in range(1, MAX_ANSWER_RETRIES + 1):
            # Önce modal/popup varsa kapat
            self._dismiss_modals(page, logger)

            # Sayfanın render tamamlanmasını bekle
            try:
                page.wait_for_selector(
                    'label.o_survey_choice_btn, input[type="checkbox"], input[type="text"], textarea',
                    timeout=6000,
                    state='visible',
                )
            except PlaywrightTimeout:
                pass

            # 1. Radio (Simple Choice)
            try:
                labels = page.query_selector_all('label.o_survey_choice_btn')
                if labels:
                    labels[0].click(force=True)
                    page.wait_for_timeout(300)
                    logger.info(f"Soru {question_number}: ✅ Radio seçildi ({len(labels)} şık)")
                    return True
            except Exception as e:
                logger.debug(f"Soru {question_number}: Radio hatası - {e}")

            # 2. Checkbox (Multiple Choice)
            try:
                boxes = [cb for cb in page.query_selector_all('input[type="checkbox"]') if cb.is_visible()]
                if boxes:
                    page.evaluate(
                        '(el) => { el.checked = true; el.dispatchEvent(new Event("change", {bubbles:true})); }',
                        boxes[0],
                    )
                    page.wait_for_timeout(300)
                    logger.info(f"Soru {question_number}: ✅ Checkbox seçildi")
                    return True
            except Exception as e:
                logger.debug(f"Soru {question_number}: Checkbox hatası - {e}")

            # 3. Text Input
            try:
                inputs = [i for i in page.query_selector_all('input[type="text"], textarea') if i.is_visible()]
                if inputs:
                    inputs[0].fill("Test cevabı")
                    page.wait_for_timeout(200)
                    logger.info(f"Soru {question_number}: ✅ Text dolduruldu")
                    return True
            except Exception as e:
                logger.debug(f"Soru {question_number}: Text hatası - {e}")

            if attempt < MAX_ANSWER_RETRIES:
                logger.warning(f"Soru {question_number}: Cevap denenemedi, {attempt}. deneme başarısız — 1s bekleyip retry...")
                page.wait_for_timeout(1000)

        logger.error(f"Soru {question_number}: ❌ HİÇBİR CEVAP VERİLEMEDİ! (Tüm denemeler bitti)")
        return False

    # ------------------------------------------------------------------
    # Submit — retry + stuck-state dedektörü
    # ------------------------------------------------------------------
    def _click_submit(self, page, question_number, logger, max_retries=2):
        """
        Submit / İleri butonunu bul ve tıkla.
        Submit sonrası URL / içerik değişmezse (stuck) tekrar dener.
        """
        selectors = [
            'button[type="submit"].btn-primary',
            'button.btn-primary[type="submit"]',
            'button[type="submit"]',
            'a.btn-primary[role="button"]',
            'button.o_survey_submit',
            'button.o_survey_navigation_submit',
            'button:has-text("Gönder")',
            'button:has-text("İleri")',
            'button:has-text("Next")',
            'button:has-text("Submit")',
            'button:has-text("Finish")',
            'button:has-text("Tamamla")',
        ]

        url_before = page.url

        for attempt in range(1, max_retries + 1):
            # Modal varsa kapat
            self._dismiss_modals(page, logger)

            clicked = False
            for sel in selectors:
                try:
                    btn = page.query_selector(sel)
                    if btn and btn.is_visible():
                        btn.click(force=True)
                        logger.info(f"Soru {question_number}: Submit → {sel} (deneme {attempt})")
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                # Form submit fallback
                try:
                    page.evaluate("document.querySelector('form')?.submit()")
                    logger.warning(f"Soru {question_number}: Form fallback submit denendi")
                    clicked = True
                except Exception:
                    pass

            if not clicked:
                logger.warning(f"Soru {question_number}: Submit butonu hiç bulunamadı (deneme {attempt})")
                return False

            # Sayfa değişimini bekle
            try:
                page.wait_for_load_state('load', timeout=8000)
            except PlaywrightTimeout:
                page.wait_for_timeout(2000)

            # Validation hatası varsa tekrar cevaplamayı dene
            if self._has_validation_error(page):
                logger.warning(f"Soru {question_number}: Validation hatası — cevap tekrar deneniyor...")
                self._answer_question(page, question_number, logger)
                continue  # Tekrar submit dene

            # URL değiştiyse veya tamamlandıysa başarılı
            if page.url != url_before or self._check_page_state(page) in ('completed', 'terminated'):
                return True

            # URL değişmedi — stuck olabilir
            if attempt < max_retries:
                logger.warning(f"Soru {question_number}: Sayfa değişmedi (stuck?), {attempt}. deneme — 1s bekleyip retry...")
                page.wait_for_timeout(1000)

        # Hâlâ değişmediyse, stuck sayılır ama devam et
        logger.warning(f"Soru {question_number}: Tüm submit denemeleri bitti, devam ediliyor...")
        return True

    # ------------------------------------------------------------------
    # İhlal simülasyonu (submit SONRASI)
    # ------------------------------------------------------------------
    def _simulate_violation(self, page, question_number, logger):
        """Hafif ihlal simülasyonu — cevap+submit'ten SONRA çalışır."""
        vtype = random.choice(['tab_switch', 'fullscreen', 'devtools', 'print_screen'])
        logger.info(f"Soru {question_number}: 🚨 İhlal simülasyonu - {vtype}")

        try:
            if vtype == 'tab_switch':
                page.evaluate("""
                    window.dispatchEvent(new Event('blur'));
                    document.dispatchEvent(new Event('visibilitychange'));
                """)
                page.wait_for_timeout(150)
                page.evaluate("""
                    window.dispatchEvent(new Event('focus'));
                    document.dispatchEvent(new Event('visibilitychange'));
                """)
            elif vtype == 'fullscreen':
                page.evaluate("document.exitFullscreen().catch(() => {})")
                page.wait_for_timeout(300)
                # Oluşabilecek popup'ı kapat
                self._dismiss_modals(page, logger)
            elif vtype == 'devtools':
                page.evaluate("window.dispatchEvent(new Event('resize'))")
            elif vtype == 'print_screen':
                page.keyboard.press('PrintScreen')
        except Exception:
            pass

        page.wait_for_timeout(200)
        # İhlal sonrası çıkabilecek modal'ları kapat
        self._dismiss_modals(page, logger)

    # ------------------------------------------------------------------
    # Sınav başlatma — hata sayfası kontrolü ile
    # ------------------------------------------------------------------
    def _start_exam(self, page, logger):
        """
        Sınav sayfasını aç ve Start butonuna tıkla.
        Dönüş değerleri:
          'started'  — Sınav başarıyla başladı
          'closed'   — Sınav kapalı / henüz başlamamış / erişim yok
          'error'    — Beklenmeyen hata
        """
        url = f"{self.base_url}/survey/start/{self.survey_token}"
        logger.info("Sınav sayfası açılıyor...")

        # CI ortamında timeout daha uzun tutulur
        _is_ci = os.environ.get('CI', 'false').lower() == 'true'
        _goto_timeout = 90000 if _is_ci else 60000

        # 2 kez dene (ağ hatası olursa)
        for attempt in range(1, 3):
            try:
                page.goto(url, wait_until='load', timeout=_goto_timeout)
                break
            except PlaywrightTimeout:
                if attempt == 2:
                    logger.error("Sınav sayfası yüklenemedi (timeout)")
                    return 'error'
                logger.warning(f"Sayfa yükleme timeout (deneme {attempt}), tekrar deneniyor...")
                page.wait_for_timeout(3000)
            except Exception as e:
                logger.error(f"Sınav sayfası açma hatası: {e}")
                return 'error'

        # Hata / kapalı sınav kontrolü
        state = self._check_page_state(page)
        if state == 'error':
            content_snippet = self._get_content_lower(page)[:200]
            logger.warning(f"Sınav erişilemez durumda: {content_snippet}")
            return 'closed'

        if state == 'completed':
            logger.info("Sayfa zaten tamamlanmış durumda gösteriyor.")
            return 'started'

        # Start butonu
        try:
            btn = page.wait_for_selector(
                'button[value="start"], button:has-text("Başla"), button:has-text("Start")',
                timeout=8000, state='visible',
            )
            if btn:
                btn.click()
                page.wait_for_load_state('load', timeout=10000)
                logger.info("Sınav başlatıldı.")
        except PlaywrightTimeout:
            logger.warning("Start butonu bulunamadı — sınav zaten açık olabilir.")

        # Başlatma sonrası hata kontrolü
        state = self._check_page_state(page)
        if state == 'error':
            return 'closed'

        return 'started'

    # ------------------------------------------------------------------
    # Tek kullanıcı testi
    # ------------------------------------------------------------------
    def test_single_user(self, user_id):
        logger = logging.LoggerAdapter(logging.getLogger(), {'user': user_id})
        result = {
            'user_id': user_id,
            'status': 'UNKNOWN',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'questions_answered': 0,
            'errors': [],
            'warnings': [],
        }

        browser = context = pw = None
        try:
            pw = sync_playwright().start()
            headless = os.environ.get('HEADLESS', 'true').lower() == 'true'
            browser = pw.chromium.launch(
                headless=headless,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--disable-background-networking',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                    '--js-flags=--max-old-space-size=256',
                ],
            )
            device = random.choice(IPAD_DEVICES)
            context = browser.new_context(**device)
            page = context.new_page()

            # Console hataları (sadece kritikler)
            console_errors = []
            page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)

            # Native dialog'ları otomatik kabul et (alert, confirm, prompt)
            page.on('dialog', lambda d: d.accept())

            # --- Sınavı başlat ---
            start_result = self._start_exam(page, logger)
            if start_result == 'closed':
                result['status'] = STATUS_SURVEY_CLOSED
                result['errors'].append("Sınav kapalı, henüz başlamamış veya erişim reddedildi")
                return result
            if start_result == 'error':
                result['status'] = STATUS_CRITICAL
                result['errors'].append("Sınav sayfası açılamadı")
                return result

            # --- Soru döngüsü ---
            max_questions = 50          # 25 sorulu sınavda güvenli üst sınır
            violation_interval = random.randint(8, 12)
            stuck_count = 0             # Aynı URL üst üste gelme sayacı
            MAX_STUCK = 3               # Bu kadar üst üste aynı URL → döngüden çık
            last_url = ''

            for q_num in range(1, max_questions + 1):

                # --- Tamamlanma / sonlandırma / hata kontrolü (her soru başında) ---
                state = self._check_page_state(page)

                if state == 'completed':
                    logger.info(f"✅ Sınav tamamlandı! ({q_num - 1} soru cevaplandı)")
                    result['status'] = STATUS_SUCCESS
                    result['questions_answered'] = q_num - 1
                    break

                if state == 'terminated':
                    logger.warning(f"⚠️ Oturum sunucu tarafından sonlandırıldı (soru {q_num})")
                    result['status'] = STATUS_TERMINATED
                    result['questions_answered'] = q_num - 1
                    result['warnings'].append(f"Oturum soru {q_num}'de sonlandırıldı")
                    break

                if state == 'error':
                    logger.warning(f"⚠️ Hata sayfası tespit edildi (soru {q_num})")
                    result['status'] = STATUS_SURVEY_CLOSED
                    result['errors'].append(f"Soru {q_num}'de hata sayfası görüntülendi")
                    result['questions_answered'] = q_num - 1
                    break

                # --- Stuck-state dedektörü ---
                current_url = page.url
                if current_url == last_url:
                    stuck_count += 1
                    if stuck_count >= MAX_STUCK:
                        logger.error(
                            f"❌ STUCK: URL {MAX_STUCK} kez değişmedi "
                            f"(soru {q_num}, url={current_url})"
                        )
                        result['status'] = STATUS_STUCK
                        result['errors'].append(f"Stuck loop soru {q_num}'de: {current_url}")
                        result['questions_answered'] = q_num - 1
                        break
                else:
                    stuck_count = 0
                    last_url = current_url

                logger.info(f"Soru {q_num} cevaplandırılıyor...")

                # --- Cevap ver ---
                answered = self._answer_question(page, q_num, logger)
                if not answered:
                    result['warnings'].append(f"Soru {q_num}: cevap verilemedi")

                # --- Submit ---
                self._click_submit(page, q_num, logger)

                result['questions_answered'] = q_num

                # --- Submit sonrası durum kontrolü ---
                state = self._check_page_state(page)

                if state == 'completed':
                    logger.info(f"✅ Sınav tamamlandı! ({q_num} soru)")
                    result['status'] = STATUS_SUCCESS
                    break

                if state == 'terminated':
                    logger.warning(f"⚠️ Oturum submit sonrası sonlandırıldı (soru {q_num})")
                    result['status'] = STATUS_TERMINATED
                    result['warnings'].append(f"Oturum soru {q_num} submit sonrası sonlandırıldı")
                    break

                if state == 'error':
                    logger.warning(f"⚠️ Submit sonrası hata sayfası (soru {q_num})")
                    result['status'] = STATUS_SURVEY_CLOSED
                    result['errors'].append(f"Submit sonrası soru {q_num}'de hata sayfası")
                    break

                # --- İhlal simülasyonu (belirli aralıklarla, submit SONRASI) ---
                if q_num % violation_interval == 0:
                    self._simulate_violation(page, q_num, logger)
                    violation_interval = random.randint(8, 12)

            else:
                # max_questions'a ulaşıldı — başarı sayılır
                logger.info(f"✅ Tüm sorular tamamlandı ({max_questions})")
                result['status'] = STATUS_SUCCESS

            if result['status'] == 'UNKNOWN':
                result['status'] = STATUS_SUCCESS

            # Konsol hatalarını kaydet
            critical = [e for e in console_errors if 'ERR_UNKNOWN_URL_SCHEME' not in e and 'Save All' not in e]
            if critical:
                result['errors'].extend([f"Console: {e}" for e in critical[:5]])

        except PlaywrightTimeout as e:
            logger.error(f"❌ Timeout: {e}")
            result['status'] = STATUS_CRITICAL
            result['errors'].append(f"Critical timeout: {str(e)[:200]}")
        except Exception as e:
            logger.error(f"❌ Kritik hata: {e}")
            result['status'] = STATUS_CRITICAL
            result['errors'].append(f"Critical: {str(e)[:200]}")
        finally:
            for obj in (context, browser, pw):
                try:
                    if obj:
                        obj.close() if hasattr(obj, 'close') else obj.stop()
                except Exception:
                    pass

        result['completed_at'] = datetime.now().isoformat()
        icon = '✅' if result['status'] == STATUS_SUCCESS else ('⚠️' if result['status'] == STATUS_TERMINATED else '❌')
        logger.info(f"{icon} {result['status']} — {result['questions_answered']} soru")
        return result

    # ------------------------------------------------------------------
    # Yük testi
    # ------------------------------------------------------------------
    def run_load_test(self, user_count=50, parallel_count=10):
        print("\n" + "=" * 65)
        print("🚀 PLAYWRIGHT UI YÜK TESTİ")
        print("=" * 65)
        print(f"👥 Kullanıcı: {user_count}  |  ⚡ Paralel: {parallel_count}")
        print(f"🌐 URL: {self.base_url}")
        print(f"🔑 Token: {self.survey_token}")
        print("=" * 65 + "\n")

        self.start_time = time.time()

        # CI ortamında tarayıcı başlatmaları arasında stagger uygula
        _is_ci = os.environ.get('CI', 'false').lower() == 'true'
        _stagger_sec = 1.0 if _is_ci else 0.2   # CI: 1s, lokal: 0.2s

        with ThreadPoolExecutor(max_workers=parallel_count) as executor:
            futures = {}
            for uid in range(1, user_count + 1):
                futures[executor.submit(self.test_single_user, uid)] = uid
                time.sleep(_stagger_sec)          # Her kullanıcı başlatması arasında bekle

            completed = 0
            for future in as_completed(futures):
                try:
                    res = future.result(timeout=300)
                    self.results.append(res)
                except Exception as e:
                    uid = futures[future]
                    self.results.append({
                        'user_id': uid, 'status': STATUS_CRITICAL,
                        'questions_answered': 0,
                        'errors': [f"Executor error: {str(e)[:200]}"],
                        'warnings': [],
                        'started_at': datetime.now().isoformat(),
                        'completed_at': datetime.now().isoformat(),
                    })
                completed += 1
                r = self.results[-1]
                icon = '✅' if r['status'] == STATUS_SUCCESS else ('⚠️' if r['status'] == STATUS_TERMINATED else '❌')
                print(
                    f"[{completed:3}/{user_count}] Kullanıcı {r['user_id']:3} "
                    f"{icon} {r['status']:<20} — {r['questions_answered']} soru"
                )

        self.end_time = time.time()
        self._print_summary()
        self._save_report()

    def _print_summary(self):
        dur = self.end_time - self.start_time
        success    = [r for r in self.results if r['status'] == STATUS_SUCCESS]
        terminated = [r for r in self.results if r['status'] == STATUS_TERMINATED]
        closed     = [r for r in self.results if r['status'] == STATUS_SURVEY_CLOSED]
        stuck      = [r for r in self.results if r['status'] == STATUS_STUCK]
        critical   = [r for r in self.results if r['status'] == STATUS_CRITICAL]
        total_q    = sum(r['questions_answered'] for r in self.results)
        n          = len(self.results)

        print("\n" + "=" * 65)
        print("📊 SONUÇLAR")
        print("=" * 65)
        print(f"⏱  Süre       : {dur:.1f}s ({dur/60:.1f} dk)")
        print(f"✅ Başarı     : {len(success)}/{n} (%{len(success)/n*100:.1f})")
        if terminated:
            print(f"⚠️  Sonlandırıldı: {len(terminated)}/{n} (%{len(terminated)/n*100:.1f})")
        if closed:
            print(f"🔒 Sınav Kapalı: {len(closed)}/{n} (%{len(closed)/n*100:.1f})")
        if stuck:
            print(f"🔄 Stuck Döngü : {len(stuck)}/{n} (%{len(stuck)/n*100:.1f})")
        if critical:
            print(f"❌ Kritik Hata : {len(critical)}/{n} (%{len(critical)/n*100:.1f})")
        print(f"📝 Toplam cevap: {total_q}  |  Ort: {total_q/n:.1f} soru/kullanıcı")

        # Başarısızları listele
        failed_all = [r for r in self.results if r['status'] != STATUS_SUCCESS]
        if failed_all:
            print("\n🔍 Başarısız / Uyarılı kullanıcılar:")
            for r in failed_all:
                print(f"  Kullanıcı {r['user_id']}: {r['status']} — {r['questions_answered']} soru")
                for e in (r.get('errors', []) + r.get('warnings', []))[:3]:
                    print(f"    → {e[:120]}")

        print("=" * 65)

    def _save_report(self):
        success_count = len([r for r in self.results if r['status'] == STATUS_SUCCESS])
        report = {
            'test_info': {
                'survey_token': self.survey_token,
                'base_url': self.base_url,
                'user_count': len(self.results),
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
                'duration_seconds': self.end_time - self.start_time,
            },
            'summary': {
                'success':    success_count,
                'terminated': len([r for r in self.results if r['status'] == STATUS_TERMINATED]),
                'closed':     len([r for r in self.results if r['status'] == STATUS_SURVEY_CLOSED]),
                'stuck':      len([r for r in self.results if r['status'] == STATUS_STUCK]),
                'critical':   len([r for r in self.results if r['status'] == STATUS_CRITICAL]),
                'total_questions_answered': sum(r['questions_answered'] for r in self.results),
            },
            'results': self.results,
        }
        fname = f"playwright_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fpath = os.path.join(script_dir, fname)
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Rapor: {fpath}")


def main():
    token = os.environ.get('SURVEY_TOKEN')
    if not token:
        print("❌ SURVEY_TOKEN tanımlanmamış!")
        print("Kullanım: SURVEY_TOKEN=xxx python test_exam_playwright.py")
        sys.exit(1)

    user_count     = int(os.environ.get('USER_COUNT', 50))
    parallel_count = int(os.environ.get('PARALLEL', 10))
    base_url       = os.environ.get('BASE_URL', 'https://digipharma.com.tr')

    ExamTester(token, base_url).run_load_test(user_count, parallel_count)


if __name__ == '__main__':
    main()
