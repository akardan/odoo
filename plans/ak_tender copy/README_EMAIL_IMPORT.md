# SAT Email Import - Otomatik Email İşleme Sistemi

## Genel Bakış

Bu sistem, `ilkoisdata@ilko.com.tr` email kutusunu otomatik olarak kontrol eder ve "ME5A Günlük Rapor Sonuçları" konulu yeni gelen emaillerdeki "ME5A Günlük Rapor Sonuçları.ZIP" dosyasını otomatik olarak import eder.

## Sistem Bileşenleri

### 1. Email Import Fonksiyonu
**Dosya:** `wizards/import_sat_wizard.py`
**Metod:** `import_sat_from_email()`

Bu fonksiyon:
- `ilkoisdata@ilko.com.tr` email kutusuna IMAP üzerinden bağlanır
- Sadece **okunmamış** emailleri kontrol eder
- Konu satırı "ME5A Günlük Rapor Sonuçları" olan emailleri filtreler
- Her emaildeki ekleri kontrol eder
- "ME5A Günlük Rapor Sonuçları.ZIP" dosyasını bulur (büyük/küçük harf duyarsız)
- ZIP dosyasını otomatik olarak import eder
- İşlem tamamlandıktan sonra emaili "okundu" olarak işaretler
- Detaylı log kaydı tutar

### 2. Scheduled Action (Cron Job)
**Dosya:** `data/email_import_cron.xml`
**Model:** `ak.tender.email.import`
**Metod:** `scheduled_email_import()`

Zamanlanmış görev özellikleri:
- **Çalışma Sıklığı:** Her 1 saatte bir
- **Durum:** Varsayılan olarak pasif (manuel olarak aktif edilmeli)
- **Kullanıcı:** System Administrator (root)
- **Sonsuz Tekrar:** Sürekli çalışır (-1)

### 3. Email Import Scheduler Model
**Dosya:** `models/email_import.py`
**Model:** `ak.tender.email.import`

Bu model, scheduled action ile wizard arasında köprü görevi görür ve:
- Zamanlanmış görev tarafından çağrılır
- Import wizard'ın `import_sat_from_email()` metodunu çalıştırır
- İstatistikleri loglar
- Hata yönetimi yapar

## Kurulum ve Yapılandırma

### 1. Email Şifresini Ayarlama

Email şifresi sistem parametresi olarak saklanır. İki yöntemle ayarlanabilir:

#### Yöntem A: Odoo Arayüzünden
1. Ayarlar > Teknik > Parametreler > Sistem Parametreleri
2. Yeni parametre oluştur:
   - **Anahtar:** `ak_tender.email_password`
   - **Değer:** Email şifresi

#### Yöntem B: Python/XML ile
```python
self.env['ir.config_parameter'].sudo().set_param('ak_tender.email_password', 'şifre_buraya')
```

**NOT:** Şu anda kod içinde hardcoded şifre var (`Ilko2019*`). Güvenlik için bu şifre sistem parametresine taşınmalı.

### 2. Scheduled Action'ı Aktif Etme

1. Ayarlar > Teknik > Otomasyon > Zamanlanmış Eylemler
2. "SAT Email Import" eylemini bul
3. "Aktif" kutusunu işaretle
4. Kaydet

### 3. Manuel Test

Email import fonksiyonunu manuel olarak test etmek için:

```python
# Odoo shell veya kod içinden
wizard = env['import.sat.wizard']
stats = wizard.import_sat_from_email()
print(stats)
```

## Çalışma Akışı

```
1. Cron Job Tetiklenir (Her saat)
   ↓
2. scheduled_email_import() çağrılır
   ↓
3. import_sat_from_email() çalıştırılır
   ↓
4. Email Kutusuna Bağlan (IMAP SSL)
   ↓
5. Okunmamış + "ME5A Günlük Rapor Sonuçları" konulu emailleri bul
   ↓
6. Her email için:
   ├─ Ekleri kontrol et
   ├─ "ME5A Günlük Rapor Sonuçları.ZIP" dosyasını bul
   ├─ ZIP içindeki Excel dosyasını çıkar
   ├─ import_sat_from_file() ile import et
   ├─ İstatistikleri topla
   └─ Emaili "okundu" olarak işaretle
   ↓
7. Sonuçları logla ve döndür
```

## Özellikler

### ✅ Yapılanlar
- [x] IMAP SSL bağlantısı
- [x] Okunmamış email filtreleme
- [x] Konu satırı filtreleme
- [x] Büyük/küçük harf duyarsız dosya adı kontrolü
- [x] ZIP dosyası otomatik çıkarma
- [x] Excel import (xlsx, xls, XML Excel formatları)
- [x] Email'i okundu olarak işaretleme
- [x] Detaylı loglama
- [x] Hata yönetimi
- [x] İstatistik toplama
- [x] Scheduled action entegrasyonu

### 🔄 İyileştirme Önerileri
- [ ] Email şifresini hardcoded'dan sistem parametresine taşı
- [ ] Email gönderen adresini kontrol et (güvenlik)
- [ ] İşlenen emailleri ayrı bir klasöre taşı
- [ ] Başarısız importlar için retry mekanizması
- [ ] Email bildirimleri (başarı/hata durumları)
- [ ] Dashboard widget (son import istatistikleri)

## Log Mesajları

Sistem aşağıdaki log mesajlarını üretir:

```
INFO: Email bağlantısı kuruluyor: ilkoisdata@ilko.com.tr@mail.ilko.com.tr
INFO: Email kutusuna bağlanıldı, okunmamış emailler aranıyor...
INFO: X adet okunmamış 'ME5A Günlük Rapor Sonuçları' konulu email bulundu
INFO: Email işleniyor: ID=XXX
INFO: Email konusu: ME5A Günlük Rapor Sonuçları
INFO: Ek dosya bulundu: ME5A Günlük Rapor Sonuçları.ZIP
INFO: Hedef ZIP dosyası bulundu: ME5A Günlük Rapor Sonuçları.ZIP
INFO: Dosya boyutu: XXXX bytes
INFO: Import işlemi başlatılıyor: ME5A Günlük Rapor Sonuçları.ZIP
INFO: Dosya import edildi: ME5A Günlük Rapor Sonuçları.ZIP
INFO: Email okundu olarak işaretlendi: ID=XXX
INFO: Email import tamamlandı. İşlenen email sayısı: X
```

## Hata Durumları

### Email Şifresi Ayarlanmamış
```
ERROR: Email şifresi ayarlanmamış. Lütfen ak_tender.email_password parametresini ayarlayın.
```
**Çözüm:** Sistem parametresini ayarlayın (yukarıdaki kurulum bölümüne bakın)

### IMAP Bağlantı Hatası
```
ERROR: IMAP bağlantı hatası: [hata mesajı]
```
**Çözüm:** 
- Email sunucu ayarlarını kontrol edin
- Şifrenin doğru olduğundan emin olun
- Firewall/network ayarlarını kontrol edin

### ZIP Dosyası Bulunamadı
```
WARNING: Email'de 'ME5A Günlük Rapor Sonuçları.ZIP' dosyası bulunamadı
```
**Çözüm:** Email'in doğru eki içerdiğinden emin olun

## Güvenlik Notları

1. **Şifre Güvenliği:** Email şifresi sistem parametresinde saklanmalı, kod içinde hardcoded olmamalı
2. **SSL Bağlantı:** IMAP bağlantısı SSL üzerinden yapılıyor (güvenli)
3. **Kullanıcı Yetkileri:** Scheduled action root kullanıcısı ile çalışıyor
4. **Email İşaretleme:** İşlenen emailler okundu olarak işaretleniyor (tekrar işlenmesini önler)

## Teknik Detaylar

### Kullanılan Kütüphaneler
- `imaplib`: IMAP email protokolü
- `email`: Email mesaj parsing
- `base64`: Dosya encoding/decoding
- `zipfile`: ZIP dosya işleme
- `pandas`: Excel okuma
- `xml.etree.ElementTree`: XML Excel parsing

### Email Arama Kriterleri
```python
# IMAP search komutu
mail.search(None, '(UNSEEN SUBJECT "ME5A Günlük Rapor Sonuçları")')
```

- `UNSEEN`: Okunmamış emailler
- `SUBJECT`: Konu satırı içeren emailler

### Desteklenen Dosya Formatları
- ZIP (içinde Excel dosyası)
- XLSX (Excel 2007+)
- XLS (Excel 97-2003)
- XML Excel (SpreadsheetML)

## Sorun Giderme

### Scheduled Action Çalışmıyor
1. Scheduled action'ın aktif olduğunu kontrol edin
2. Odoo cron worker'ın çalıştığından emin olun
3. Log dosyalarını kontrol edin

### Email İmport Edilmiyor
1. Email şifresinin doğru olduğunu kontrol edin
2. Email konusunun tam olarak "ME5A Günlük Rapor Sonuçları" olduğunu kontrol edin
3. Ek dosya adının "ME5A Günlük Rapor Sonuçları.ZIP" olduğunu kontrol edin
4. Log dosyalarında detaylı hata mesajlarını kontrol edin

### Manuel Test
```python
# Odoo shell
./odoo-bin shell -d database_name

# Python shell içinde
wizard = env['import.sat.wizard']
stats = wizard.import_sat_from_email()
print(stats)
```

## İletişim ve Destek

Sorularınız için: Kardan.Digital