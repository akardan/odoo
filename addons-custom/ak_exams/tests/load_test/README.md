# Sınav Yük Testi (Load Testing)

Bu klasör, Odoo sınav modülü (`ak_exams`) için yük testi yapmak amacıyla hazırlanmış dosyaları içerir. Test için **Locust** aracı kullanılmaktadır.

## Gereksinimler

Testi çalıştırmak için Python ve Locust kütüphanesine ihtiyacınız vardır.

1.  Python 3'ün yüklü olduğundan emin olun.
2.  Locust ve BeautifulSoup4 kütüphanelerini yükleyin:

```bash
pip install locust beautifulsoup4
```

## SURVEY_TOKEN Nereden Bulunur?

Testi çalıştırmak için geçerli bir sınav token'ına ihtiyacınız vardır. Token'ı bulmak için:

1.  Odoo'ya yönetici olarak giriş yapın.
2.  **Anketler (Surveys)** uygulamasına gidin.
3.  Test etmek istediğiniz sınavı açın.
4.  Üstteki **"Paylaş" (Share)** butonuna tıklayın.
5.  Açılan pencerede **"Genel Bağlantı" (Public Link)** kısmındaki URL'yi kopyalayın.
    *   Örnek Link: `https://digipharma.com.tr/survey/start/49660127-9ee1-4377-ad89-4771401ae43b`
6.  Linkin sonundaki kod sizin **SURVEY_TOKEN**'ınızdır.
    *   Örnek Token: `49660127-9ee1-4377-ad89-4771401ae43b`

**Önemli:** Sınavın "Seçenekler" sekmesinde **Erişim Modu**'nun "Bağlantıya sahip herkes" (Anyone with the link) olduğundan emin olun.

## Ön Kontrol (Curl ile Doğrulama)

Testi başlatmadan önce, sınavın erişilebilir olduğunu `curl` komutu ile doğrulamanız önerilir.

```bash
curl -I https://digipharma.com.tr/survey/start/SİZİN_TOKENINIZ
```

Eğer yanıt `HTTP/2 200` ise sınav erişilebilirdir. Eğer `303` veya `302` yönlendirmesi alıyorsanız (örneğin ana sayfaya), sınav aktif olmayabilir veya token geçersiz olabilir.

## Testi Çalıştırma (ÖNERİLEN YÖNTEM: Arayüzsüz Mod)

Sunucu üzerinde çalıştığınız için tarayıcı arayüzüne erişmekte sorun yaşayabilirsiniz. Bu nedenle testi **Headless (Arayüzsüz)** modda çalıştırmanız en garantili yöntemdir.

Aşağıdaki komutu terminale yapıştırın ve çalıştırın:

```bash
SURVEY_TOKEN=SİZİN_TOKENINIZ locust --headless -u 50 -r 5 --run-time 5m --host https://digipharma.com.tr --html report.html
```

**Bu komut ne yapar?**
*   `--headless`: Arayüzü açmaz, testi arka planda yapar.
*   `-u 50`: **50 kullanıcı** simüle eder.
*   `-r 5`: Saniyede **5 kullanıcı** ekler.
*   `--run-time 5m`: Testi **5 dakika** boyunca sürdürür.
*   `--host ...`: Test edilecek site adresidir.
*   `--html report.html`: Sonuçları **report.html** dosyasına kaydeder.

Test bittikten sonra oluşan `report.html` dosyasını bilgisayarınıza indirip açarak grafikleri ve sonuçları inceleyebilirsiniz.

---

### Alternatif: Arayüzlü Mod (Sadece Local Bilgisayarda)

Eğer bu testi kendi kişisel bilgisayarınızda (Sunucuda değil) yapıyorsanız:

1.  `SURVEY_TOKEN=... locust` komutunu çalıştırın.
2.  Tarayıcınızda `http://localhost:8089` adresine gidin.
3.  Host kısmına `https://digipharma.com.tr` yazın.

## Test Senaryosu

Bu test senaryosu (`locustfile.py`) şunları yapar:
1.  Belirtilen `SURVEY_TOKEN` ile sınav başlangıç sayfasına gider.
2.  "Start" butonuna basarak sınavı başlatır.
3.  Soruları rastgele şıklar seçerek cevaplar.
4.  Sınav bitene kadar sayfa sayfa ilerler.

## Dikkat Edilmesi Gerekenler

*   Bu testi **PROD (Canlı)** ortamda yaparken dikkatli olun. Veritabanında çok sayıda test kaydı (`survey.user_input`) oluşacaktır.
*   Testi tercihen bir **Staging** veya **Test** ortamında gerçekleştirin.
*   Sunucu kaynaklarını (CPU, RAM) izleyerek darboğazları tespit edebilirsiniz.
