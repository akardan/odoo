# Odoo Shell Komutları - Hızlı Referans

## 🚀 Odoo Shell'i Açma

### Standart Komut (Odoo çalışırken)

```bash
/opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
```

**Notlar:**
- `od18` - Veritabanı adınız (kendi veritabanınızı yazın)
- `/etc/odoo.conf` - Odoo config dosyası (sisteminize göre değişebilir)
- `--http-port=8070` - Port çakışmasını önlemek için farklı port (Odoo zaten 8069'da çalışıyorsa)

### Odoo Kapalıyken

```bash
/opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf
```

## 🔧 Yaygın Hatalar ve Çözümleri

### Hata 1: Config dosyası bulunamadı

**Hata:**
```
error: The config file '/etc/odoo18.conf' selected with -c/--config doesn't exist
```

**Çözüm:**
```bash
# Config dosyasını bulun
find /etc -name "odoo*.conf" 2>/dev/null

# Muhtemelen /etc/odoo.conf olacaktır
/opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
```

### Hata 2: Port zaten kullanımda

**Hata:**
```
OSError: [Errno 98] Address already in use
```

**Çözüm 1 - Farklı port kullan:**
```bash
/opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
```

**Çözüm 2 - Odoo'yu durdur, shell'i aç, sonra tekrar başlat:**
```bash
# Odoo'yu durdur
sudo systemctl stop odoo18

# Shell'i aç (port problemi olmadan)
/opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf

# İşiniz bitince shell'den çıkın (Ctrl+D)

# Odoo'yu tekrar başlat
sudo systemctl start odoo18
```

### Hata 3: Permission denied

**Hata:**
```
PermissionError: [Errno 13] Permission denied
```

**Çözüm:**
```bash
# Root olarak veya sudo ile çalıştırın
sudo /opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
```

## 📝 Faydalı Shell Komutları

### AI Asistan Kontrolü

```python
# Aktif asistanı kontrol et
assistant = env['ak_ai.assistant'].search([('active', '=', True)], limit=1)
if assistant:
    print(f"✅ Aktif asistan: {assistant.name}")
    print(f"✅ Provider: {assistant.ai_provider}")
    print(f"✅ Model: {assistant.model_name}")
    print(f"✅ API Key var: {bool(assistant.api_key)}")
else:
    print("❌ Aktif asistan bulunamadı!")
```

### Model Mixin Kontrolü

```python
# ak_tender modelinin mixin'lerini kontrol et
tender = env['ak.tender'].search([], limit=1)
print(f"Model _inherit: {tender._inherit}")
print(f"ak_ai.mixin var mı: {'ak_ai.mixin' in tender._inherit}")
```

### Son Conversation'ları Listele

```python
# Son 5 conversation
conversations = env['ak_ai.conversation'].search([], limit=5, order='create_date desc')
for conv in conversations:
    print(f"ID: {conv.id} | {conv.title} | {conv.integration_type} | Messages: {len(conv.message_ids)}")
```

### Test Mesajı Gönder

```python
# Yeni conversation oluştur ve mesaj gönder
conversation = env['ak_ai.conversation'].create({
    'title': 'Shell Test',
    'user_id': env.user.id,
    'integration_type': 'standalone'
})

message = env['ak_ai.message'].create({
    'conversation_id': conversation.id,
    'user_id': env.user.id,
    'message_type': 'user',
    'content': 'Merhaba KAI, test mesajı'
})

env.cr.commit()
print(f"✅ Conversation oluşturuldu: {conversation.id}")
print(f"✅ Mesaj gönderildi: {message.id}")
```

### Modülü Programatik Olarak Yükselt

```python
# ak_tender modülünü yükselt
module = env['ir.module.module'].search([('name', '=', 'ak_tender')], limit=1)
if module:
    module.button_immediate_upgrade()
    env.cr.commit()
    print("✅ ak_tender modülü yükseltildi")
else:
    print("❌ ak_tender modülü bulunamadı")
```

## 🔍 Debug Komutları

### Interaction Logs İnceleme

```python
# Son 10 log kaydı
logs = env['ak_ai.interaction_log'].search([], limit=10, order='create_date desc')
for log in logs:
    status = "✅" if not log.error_message else "❌"
    print(f"{status} {log.create_date} | {log.user_id.name} | Tokens: {log.tokens_used}")
    if log.error_message:
        print(f"  Hata: {log.error_message}")
```

### Specific Record için Conversation

```python
# Belirli bir ihale için conversation bul
tender_id = 123  # İhale ID'nizi yazın
tender = env['ak.tender'].browse(tender_id)
if tender.ai_conversation_id:
    print(f"Conversation ID: {tender.ai_conversation_id.id}")
    print(f"Messages: {len(tender.ai_conversation_id.message_ids)}")
else:
    print("Bu ihale için conversation yok")
```

## 🚪 Shell'den Çıkış

```python
# Exit veya Ctrl+D
exit()
# veya
quit()
# veya basitçe: Ctrl+D
```

## 💡 İpuçları

1. **Tab completion:** Shell'de `env['` yazdıktan sonra Tab'a basın, model isimlerini gösterir
2. **History:** Önceki komutları görmek için ↑ ↓ ok tuşları
3. **Commit etmeyi unutmayın:** Değişiklik yaptıysanız `env.cr.commit()` çağırın
4. **Test sonrası temizlik:** Test kayıtlarını silmeyi unutmayın

## 📚 Daha Fazla Bilgi

- [CHATTER_QUICK_FIX_TR.md](./CHATTER_QUICK_FIX_TR.md) - Chatter buton sorunu hızlı çözüm
- [TESTING_GUIDE_TR.md](./TESTING_GUIDE_TR.md) - Kapsamlı test kılavuzu
- [CHATTER_TESTING_GUIDE_TR.md](./CHATTER_TESTING_GUIDE_TR.md) - Chatter entegrasyonu test kılavuzu
