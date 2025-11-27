# Çeviri Sistemi Kullanım Kılavuzu / Translation System Guide

## Odoo Standart Translation Sistemi

Bu modül, Odoo'nun yerleşik çeviri sistemini kullanır. Hardcoded dil kontrolleri yerine, Odoo'nun otomatik çeviri mekanizması kullanılmıştır.

## Çeviri Dosyaları / Translation Files

- **POT Template**: `i18n/supplier_registration.pot` - Çeviri şablonu
- **Turkish (TR)**: `i18n/tr.po` - Türkçe çeviriler

## Çevirileri Aktif Etme / Activating Translations

### 1. Türkçe Dilini Yükleyin / Load Turkish Language

```bash
# Odoo Settings > General Settings > Languages
# Click "Add a language" and select "Turkish"
```

Veya komut satırından:
```bash
./odoo-bin -c odoo.conf -d your_database --load-language=tr_TR
```

### 2. Çevirileri Güncelleyin / Update Translations

Modülü güncelledikten sonra:

```bash
# Settings > Translations > Import/Export > Update Installed Terms
# Veya komut satırından:
./odoo-bin -c odoo.conf -d your_database -u ak_tender --i18n-overwrite
```

### 3. Kullanıcı Dilini Ayarlayın / Set User Language

```bash
# User Menu (top right) > Preferences > Language > Turkish
```

## Yeni Çeviri Eklemek / Adding New Translations

### 1. Kodu Güncelleyin / Update Code

Template'de veya Python kodunda yeni metin ekleyin:

**XML/QWeb:**
```xml
<h1>New Text to Translate</h1>
```

**Python:**
```python
from odoo import _

raise ValidationError(_('Error message to translate'))
```

### 2. POT Dosyasını Güncelleyin / Update POT File

```bash
# Odoo otomatik olarak yeni metinleri bulur
# Settings > Translations > Import/Export > Export Translation
# Dil: English (Source)
# Format: PO File
```

### 3. Türkçe Çevirileri Ekleyin / Add Turkish Translations

`i18n/tr.po` dosyasını düzenleyin:

```po
msgid "New Text to Translate"
msgstr "Çevrilecek Yeni Metin"
```

### 4. Çevirileri Yeniden Yükleyin / Reload Translations

```bash
./odoo-bin -c odoo.conf -d your_database -u ak_tender --i18n-overwrite
```

## Çeviri Kapsamı / Translation Coverage

### Website Templates (QWeb)
✅ Tüm form başlıkları ve etiketler
✅ Buton metinleri
✅ Hata ve başarı mesajları
✅ Bilgilendirme metinleri

### Backend Views
✅ Form ve list view başlıkları
✅ Alan isimleri (field labels)
✅ Buton metinleri
✅ Durum değerleri (Draft, Submitted, etc.)

### Python Code
✅ Validation hata mesajları
✅ UserError mesajları
✅ Bildirim mesajları
✅ Log mesajları

### Email Templates
✅ E-posta başlıkları
✅ E-posta içerikleri (data/supplier_application_mail_templates.xml'de iki dilli)

## Çeviri Kontrolü / Translation Check

Çevirilerin doğru çalıştığını kontrol etmek için:

1. **Dil değiştirin** (User > Preferences > Language > Turkish)
2. **Website formunu açın**: `/supplier/register`
3. **Backend'i kontrol edin**: Purchases > Supplier Applications
4. **E-postaları test edin**: Başvuru gönderip e-postaları kontrol edin

## Best Practices

### ✅ Yapılması Gerekenler

- Tüm kullanıcı görünür metinler için `_()` kullanın
- QWeb template'lerde metinleri doğrudan yazın (Odoo otomatik algılar)
- Çeviri dosyalarını düzenli güncelleyin
- Teknik terimleri tutarlı çevirin (VAT = Vergi No)

### ❌ Yapılmaması Gerekenler

- Hardcoded dil kontrolleri (`if lang == 'tr_TR'`)
- String concatenation ile cümle oluşturma
- Formatting içinde çeviri (`_('Total: %s') % amount` yerine `_('Total: %(amount)s') % {'amount': amount}`)
- Dinamik string'lerde çeviri

## Troubleshooting

### Çeviriler Görünmüyor

**Çözüm 1**: Tarayıcı cache'ini temizleyin
```bash
Ctrl + Shift + Delete (Chrome/Firefox)
```

**Çözüm 2**: Odoo assets'leri yeniden oluşturun
```bash
# Settings > Technical > Assets > Rebuild Assets
```

**Çözüm 3**: Çevirileri yeniden yükleyin
```bash
./odoo-bin -c odoo.conf -d your_database -u ak_tender --i18n-overwrite
```

### Bazı Alanlar Çevrilmiyor

- `i18n/tr.po` dosyasında eksik olabilir
- Çeviri dosyasını güncelleyin ve modülü upgrade edin

### Email Çevirileri Çalışmıyor

Email template'ler iki dilli olarak tasarlandı (TR/EN birlikte gösterilir).
Tek dil istiyorsanız, `data/supplier_application_mail_templates.xml` dosyasını düzenleyin.

## Ek Diller Eklemek / Adding More Languages

Örnek: İngilizce formlar için

1. POT dosyasından EN çeviri oluşturun
2. `i18n/en.po` oluşturun
3. Çevirileri ekleyin (genelde aynı kalır)
4. Modülü güncelleyin

## Otomatik Çeviri / Auto Translation

Odoo'nun auto-translation özelliğini kullanabilirsiniz:

```bash
# Settings > Translations > Auto Translation
# Provider seçin (Google, DeepL, etc.)
```

**Not**: Otomatik çeviriler sonrası mutlaka manuel kontrol yapın!

## Çeviri İstatistikleri / Translation Stats

Çeviri durumunu kontrol etmek için:

```bash
# Settings > Translations > Languages
# Turkish satırında "% Translated" sütununa bakın
```

## Sonuç

Odoo'nun standart translation sistemi kullanılarak:
- ✅ Merkezi çeviri yönetimi
- ✅ Kolay bakım
- ✅ Çoklu dil desteği
- ✅ Otomatik güncelleme
- ✅ Profesyonel çeviri workflow

sağlanmıştır.