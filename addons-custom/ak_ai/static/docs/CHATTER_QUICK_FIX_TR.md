# Chatter'da "Ask KAI" Butonu Hızlı Çözüm Kılavuzu

## ❓ Sorun: ak_tender modelinde chatter'da "Ask KAI" butonu görünmüyor

## ✅ Hızlı Çözüm (5 Dakika)

### Adım 1: Model Dosyasına Mixin Ekleyin

**Dosya:** [`addons-custom/ak_tender/models/tender.py`](../../../ak_tender/models/tender.py)

**ÖNCE (Buton yok ❌):**
```python
class AkTender(models.Model):
    _name = 'ak.tender'
    _description = _('İLKOis Tender')
    _inherit = ['ak.workflow.mixin', 'mail.thread', 'mail.activity.mixin']
```

**SONRA (Buton çıkacak ✅):**
```python
class AkTender(models.Model):
    _name = 'ak.tender'
    _description = _('İLKOis Tender')
    _inherit = ['ak.workflow.mixin', 'mail.thread', 'mail.activity.mixin', 'ak_ai.mixin']
    #                                                                         ^^^^^^^^^ EKLE
```

### Adım 2: Manifest'e Bağımlılık Ekleyin

**Dosya:** [`addons-custom/ak_tender/__manifest__.py`](../../../ak_tender/__manifest__.py)

**Bulun:**
```python
'depends': ['base', 'mail', 'ak_workflow', ...],
```

**Ekleyin:**
```python
'depends': ['base', 'mail', 'ak_workflow', 'ak_ai'],
#                                          ^^^^^^^ EKLE
```

### Adım 3: Modülü Güncelleyin

**Terminal'de:**
```bash
sudo systemctl restart odoo18
```

**Odoo Arayüzünde:**
1. Uygulamalar menüsüne gidin
2. "ak_tender" modülünü bulun
3. "Yükselt" (Upgrade) butonuna tıklayın

### Adım 4: Test Edin

1. **Bir ihale kaydı açın:**
   - Satınalma → İhaleler → Herhangi bir ihale

2. **Chatter'a bakın:**
   - Sayfanın alt kısmında chatter bölümü
   - "Ask KAI" butonu görünmeli ✅

3. **Teste tıklayın:**
   - "Ask KAI" butonuna tıklayın
   - Bir soru sorun: "Bu ihale hakkında bilgi verir misin?"
   - AI yanıt vermelidir

## 🔍 Hala Çalışmıyor mu?

### Kontrol Listesi

1. **ak_ai modülü yüklü mü?**
   ```
   Uygulamalar → Ara: "ak_ai" → "Yüklü" olarak işaretli olmalı
   ```

2. **AI Asistan yapılandırıldı mı?**
   ```
   Ayarlar → AI Asistan → Asistanlar → En az 1 aktif asistan olmalı
   ```

3. **API anahtarı var mı?**
   ```
   Ayarlar → AI Asistan → Asistanlar → KAI → API Anahtarı dolu olmalı
   ```

4. **Tarayıcı cache'i:**
   ```
   Ctrl + Shift + R ile sayfayı yenileyin
   ```

### Python Shell ile Kontrol

```bash
# Terminal'de (Odoo çalışırken)
# Port çakışması varsa --http-port ile farklı port kullanın
/opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
```

```python
# Shell içinde - Mixin kontrolü
tender = env['ak.tender'].search([], limit=1)
print('ak_ai.mixin' in tender._inherit)  # True dönmeli
print(tender._inherit)  # Liste içinde 'ak_ai.mixin' olmalı

# AI asistan kontrolü
assistant = env['ak_ai.assistant'].search([('active', '=', True)], limit=1)
if assistant:
    print(f"✅ Aktif asistan bulundu: {assistant.name}")
    print(f"✅ API Key var: {bool(assistant.api_key)}")
else:
    print("❌ Aktif asistan bulunamadı!")
```

## 📚 Detaylı Kılavuzlar

Daha fazla bilgi için:

- **[CHATTER_TESTING_GUIDE_TR.md](./CHATTER_TESTING_GUIDE_TR.md)** - Tam test kılavuzu
- **[TESTING_GUIDE_TR.md](./TESTING_GUIDE_TR.md)** - Genel test kılavuzu
- **[README.md](./README.md)** - Ana dokümantasyon

## 🎯 Özet

Chatter'da "Ask KAI" butonu için gerekli:

1. ✅ Model `mail.thread` inherit etmeli (zaten var)
2. ✅ Model `ak_ai.mixin` inherit etmeli (**EKLE**)
3. ✅ Manifest'te `ak_ai` dependency (**EKLE**)
4. ✅ Modül upgrade edilmeli
5. ✅ `ak_ai` modülü yüklü ve yapılandırılmış olmalı

**5 dakikada hallolur!** 🚀
