# Supplier Application Türkçe Tercüme Kurulum Rehberi

Bu rehber, `ak_tender` modülündeki Supplier Application (Tedarikçi Başvuru) formunun Türkçe tercümelerinin nasıl yükleneceğini ve kullanılacağını açıklar.

## Tercüme Dosyası

Supplier Application için Türkçe tercümeler aşağıdaki dosyada bulunmaktadır:
- **Dosya Yolu**: `addons-custom/ak_tender/i18n/tr_TR.po`

## Tercümelerin Yüklenmesi

### Adım 1: Türkçe Dil Paketinin Yüklenmesi

Eğer Odoo sisteminizde Türkçe dil paketi yüklü değilse:

1. Odoo'ya yönetici olarak giriş yapın
2. **Ayarlar (Settings)** > **Çeviriler (Translations)** > **Dilleri Yükle (Load a Translation)** menüsüne gidin
3. Listeden **Turkish / Türkçe (tr_TR)** seçin
4. **Yükle (Load)** butonuna tıklayın

### Adım 2: Modülün Güncellenmesi

Tercüme dosyasının Odoo tarafından tanınması için modülün güncellenmesi gerekir:

#### Yöntem 1: Geliştirici Modu ile (Önerilen)

1. **Geliştirici modunu** aktif edin:
   - Ayarlar > Aktif Geliştirici Modu (Settings > Activate Developer Mode)

2. **Uygulamalar (Apps)** menüsüne gidin

3. Filtreler kısmından **Yüklü (Installed)** filtresini seçin

4. Arama kutusuna `ak_tender` veya `İhale` yazın

5. Modülü bulun ve **Güncelle (Upgrade)** butonuna tıklayın

#### Yöntem 2: CLI ile

```bash
cd /opt/odoo18
./odoo-bin -d VERITABANI_ADI -u ak_tender --stop-after-init
```

### Adım 3: Tercümelerin Yüklenmesi

Modül güncellendikten sonra tercümeler otomatik olarak yüklenmelidir. Ancak manuel yükleme için:

1. **Ayarlar (Settings)** > **Çeviriler (Translations)** > **İçe Aktar / Dışa Aktar (Import / Export)** > **Çeviri İçe Aktar (Import Translation)** menüsüne gidin

2. Aşağıdaki bilgileri girin:
   - **Dil (Language)**: Turkish / Türkçe
   - **Kod (Code)**: tr_TR
   - **Dosya**: `/opt/odoo18/addons-custom/ak_tender/i18n/tr_TR.po` dosyasını seçin

3. **İçe Aktar (Import)** butonuna tıklayın

### Adım 4: Kullanıcı Tercihlerini Ayarlama

Tercümelerin görünmesi için kullanıcıların dil tercihlerinin Türkçe olarak ayarlanması gerekir:

1. Sağ üst köşedeki kullanıcı adına tıklayın
2. **Tercihler (Preferences)** seçin
3. **Dil (Language)** alanından **Turkish / Türkçe** seçin
4. **Kaydet (Save)** butonuna tıklayın

## Tercüme Edilen Alanlar

Aşağıdaki alanlar ve mesajlar Türkçe'ye çevrilmiştir:

### Model Alanları
- ✅ Application Number → Başvuru Numarası
- ✅ Status → Durum (Draft/Taslak, Submitted/Gönderildi, Under Review/İnceleniyor, Approved/Onaylandı, Rejected/Reddedildi)
- ✅ Company Name → Firma Adı
- ✅ VAT Number → Vergi Numarası
- ✅ Tax Office → Vergi Dairesi
- ✅ T.C. ID Number → T.C. Kimlik Numarası
- ✅ Company Address → Firma Adresi
- ✅ Company Phone → Firma Telefonu
- ✅ KEP Address → KEP Adresi
- ✅ MERSIS Number → MERSİS Numarası
- ✅ Goods (Group)/Service (Group) → Mal (Grubu)/Hizmet (Grubu)
- ✅ Contact Person Name → İletişim Kişisi Adı
- ✅ Contact Email → İletişim E-postası
- ✅ Payment Term → Ödeme Vadesi
- ✅ Payment Method → Ödeme Yöntemi
- ✅ Bank Name → Banka Adı
- ✅ IBAN (TRY) → IBAN (TL)
- ✅ IBAN (USD) → IBAN (USD)
- ✅ IBAN (EUR) → IBAN (EUR)
- ✅ SWIFT Code → SWIFT Kodu
- ✅ Tax Certificate → Vergi Levhası
- ✅ Signature Circular → İmza Sirküleri
- ✅ Trade Registry Gazette → Ticaret Sicil Gazetesi
- ✅ Bank Information (Stamped) → Banka Bilgileri (Kaşeli)

### Hata ve Bilgi Mesajları
- ✅ "Please enter a valid email address." → "Lütfen geçerli bir e-posta adresi girin."
- ✅ "Only draft applications can be submitted." → "Sadece taslak başvurular gönderilebilir."
- ✅ "Please fill in all required fields" → "Lütfen tüm zorunlu alanları doldurun"
- ✅ "Application approved. Partner created/updated" → "Başvuru onaylandı. İş ortağı oluşturuldu/güncellendi"
- Ve daha fazlası...

## Doğrulama

Tercümelerin doğru yüklendiğini kontrol etmek için:

1. Kullanıcı tercihlerinizi Türkçe olarak ayarlayın
2. **İhale** > **Tedarikçi Başvuruları** menüsüne gidin
3. Yeni bir başvuru oluşturun veya mevcut birini açın
4. Tüm alan etiketlerinin ve butonların Türkçe olduğunu doğrulayın

## Sorun Giderme

### Tercümeler Görünmüyor

1. Kullanıcı dil tercihlerinin Türkçe olduğunu doğrulayın
2. Modülü tekrar güncelleyin: `./odoo-bin -d DBNAME -u ak_tender --stop-after-init`
3. Tarayıcı önbelleğini temizleyin (Ctrl+F5)
4. Odoo sunucusunu yeniden başlatın

### Bazı Tercümeler Eksik

1. `tr_TR.po` dosyasının doğru yolda olduğundan emin olun: `addons-custom/ak_tender/i18n/tr_TR.po`
2. PO dosyası formatının doğru olduğunu kontrol edin (msgid/msgstr çiftleri)
3. Tercümeleri manuel olarak içe aktarmayı deneyin (Adım 3)

### Tercümeler Yüklenemedi

```bash
# Log dosyasını kontrol edin
tail -f /var/log/odoo/odoo-server.log

# Veritabanını temizleyip yeniden yükleyin
./odoo-bin -d DBNAME -u ak_tender --stop-after-init
```

## Ek Tercümeler Ekleme

Eğer yeni işlevsellik eklenir ve tercüme gerekiyorsa:

1. `tr_TR.po` dosyasını düzenleyin
2. Yeni `msgid` ve `msgstr` çiftlerini ekleyin
3. Modülü güncelleyin
4. Tercümeleri içe aktarın

### Örnek Format:

```po
#. module: ak_tender
#: code:addons/ak_tender/models/supplier_application.py:0
#, python-format
msgid "Your English text here"
msgstr "Türkçe karşılığı buraya"
```

## Destek

Tercümelerle ilgili sorunlar için:
- GitHub Issues: [Proje repo linki]
- E-posta: [Destek e-postası]

## Güncelleme Geçmişi

- **2025-12-01**: İlk Türkçe tercüme dosyası (tr_TR.po) oluşturuldu
- Supplier Application modeli için tüm alan ve mesaj tercümeleri eklendi

---

**Not**: Bu tercümeler Odoo 18 Community Edition için hazırlanmıştır.