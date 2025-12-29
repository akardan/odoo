# AK AI Chatter Entegrasyonu Test Kılavuzu

Bu kılavuz, özellikle `ak_tender` modeli gibi modellerde chatter'da "Ask KAI" butonunun nasıl çıkacağını ve nasıl test edileceğini açıklar.

## 📋 Ön Gereksinimler

Bu testleri yapmadan önce [TESTING_GUIDE_TR.md](./TESTING_GUIDE_TR.md) dokümanındaki temel kurulum adımlarını tamamladığınızdan emin olun:

1. ✅ `ak_ai` modülü yüklü ve aktif
2. ✅ AI asistan yapılandırılmış (API anahtarı ayarlanmış)
3. ✅ Python kütüphaneleri yüklü (`openai`, `anthropic`, `tiktoken`)

## 🔧 Adım 1: Model Yapılandırması

Chatter'da "Ask KAI" butonu göstermek için model [`ak_ai.mixin`](../../models/ak_ai_mixin.py) mixin'ini inherit etmelidir.

### ak_tender Modeli için Kontrol

1. **Model dosyasını kontrol edin:**
   - Dosya: [`addons-custom/ak_tender/models/tender.py`](../../../ak_tender/models/tender.py)

2. **`_inherit` listesini kontrol edin:**

   ```python
   class AkTender(models.Model):
       _name = 'ak.tender'
       _description = _('İLKOis Tender')
       _inherit = ['ak.workflow.mixin', 'mail.thread', 'mail.activity.mixin']  # ❌ Eksik!
   ```

3. **`ak_ai.mixin` ekleyin:**

   ```python
   class AkTender(models.Model):
       _name = 'ak.tender'
       _description = _('İLKOis Tender')
       _inherit = ['ak.workflow.mixin', 'mail.thread', 'mail.activity.mixin', 'ak_ai.mixin']  # ✅ Eklendi!
   ```

4. **Modülü güncelleyin:**
   ```bash
   # Terminal'de:
   # 1. Odoo'yu yeniden başlatın
   sudo systemctl restart odoo18
   
   # 2. Odoo arayüzünde:
   # Uygulamalar → ak_tender modülünü bulun → "Yükselt" butonuna tıklayın
   ```

### Başka Bir Model için Ekleme

Herhangi bir modelde AI chat desteği eklemek için:

```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['mail.thread', 'ak_ai.mixin']  # ✅ mail.thread + ak_ai.mixin gerekli
    
    # Modelinizin diğer alanları...
```

**Önemli Notlar:**
- ✅ Model **MUTLAKA** `mail.thread` inherit etmeli (chatter için)
- ✅ Model **MUTLAKA** `ak_ai.mixin` inherit etmeli (AI butonu için)
- ⚠️ Her iki inherit de eksikse buton görünmez

## 🔧 Adım 2: View Yapılandırması (Opsiyonel)

View'da chatter widget'ı varsa, AI entegrasyonu otomatik çalışır. Ancak kontrol etmek için:

### Mevcut View'ı Kontrol Edin

1. **Tender form view dosyası:**
   - Dosya: [`addons-custom/ak_tender/views/tender_views.xml`](../../../ak_tender/views/tender_views.xml)

2. **Chatter widget'ını bulun:**

   ```xml
   <form>
       <!-- Form alanları... -->
       
       <div class="oe_chatter">
           <field name="message_follower_ids" widget="mail_followers"/>
           <field name="activity_ids" widget="mail_activity"/>
           <field name="message_ids" widget="mail_thread"/>
       </div>
   </form>
   ```

3. **Beklenen Sonuç:**
   - ✅ `message_ids` alanı `mail_thread` widget ile tanımlanmış olmalı
   - ✅ Chatter bölümü form'un alt kısmında olmalı
   - ✅ Başka bir şey eklemenize gerek yok (AI butonu otomatik gelir)

## 🎯 Adım 3: Chatter'da "Ask KAI" Butonunu Test Etme

### Test 3.1: Yeni Tender Kaydı Oluşturma

1. **Odoo arayüzünde Tender modülüne gidin:**
   - Satınalma → İhaleler → İhaleler (veya doğrudan menü yolunuz)

2. **Yeni ihale oluşturun:**
   - "Oluştur" butonuna tıklayın
   - Gerekli alanları doldurun:
     * İhale Adı: "Test AI İhalesi"
     * İhale Tipi: Seçin (örn: "Standart")
     * Başlangıç Tarihi: Bugünün tarihi
   - "Kaydet" butonuna tıklayın

3. **Chatter bölümüne gidin:**
   - Sayfayı aşağı kaydırın
   - Chatter bölümünü bulun (genelde form'un en altında)

4. **"Ask KAI" butonunu bulun:**
   - ✅ Chatter'ın üst kısmında "Ask KAI" butonu görünmelidir
   - ✅ Buton message input alanının yanında veya üstünde olmalı

5. **Buton görünmüyorsa kontrol edin:**
   - ❌ Model `ak_ai.mixin` inherit ediyor mu? → Adım 1'e dönün
   - ❌ Modül güncellendi mi? → `ak_tender` modülünü yükseltin
   - ❌ Tarayıcı cache'i → Ctrl+Shift+R ile sayfayı yenileyin
   - ❌ JavaScript hatası → F12 ile Console'u açın, hata var mı bakın

### Test 3.2: AI ile Sohbet Başlatma

1. **"Ask KAI" butonuna tıklayın:**
   - Bir dialog/modal pencere açılmalı
   - Veya inline bir chat alanı görünmelidir

2. **Örnek soru sorun:**
   ```
   Bu ihale hakkında bilgi verir misin?
   ```

3. **Beklenen Sonuç:**
   - ✅ AI asistan yanıt vermelidir
   - ✅ Yanıt Türkçe olmalıdır
   - ✅ Yanıt ihale bağlamında anlamlı olmalıdır
   - ✅ Yanıt birkaç saniye içinde gelmelidir

### Test 3.3: Conversation Oluşturma Kontrolü

1. **Conversation kaydını kontrol edin:**
   - Ayarlar → AI Asistan → AI Conversations
   - Son oluşturulan conversation'ı açın

2. **Kontrol edilmesi gerekenler:**
   - ✅ **Integration Type:** "chatter"
   - ✅ **Context Model:** "ak.tender"
   - ✅ **Context Record ID:** İhale kaydınızın ID'si
   - ✅ **Messages:** Sorduğunuz soru ve AI'nın yanıtı

3. **ihale kaydında conversation bağlantısı:**
   - İhale formunu tekrar açın
   - Chatter'da "Ask KAI" butonuna tekrar tıklayın
   - ✅ Aynı conversation devam etmelidir (yeni oluşturmamalı)

### Test 3.4: Context-Aware Soru Sorma

AI, ihalenin detaylarını anlayarak context-aware yanıt vermeli. Test edin:

1. **İhaleye veri ekleyin:**
   - İhale formunda:
     * Hedef Fiyat: 50000 TRY
     * Hedef İndirim: %15
     * Birkaç ihale kalemi ekleyin
   - Kaydet

2. **Context-aware sorular sorun:**
   ```
   Bu ihalenin hedef fiyatı nedir?
   ```
   
   ```
   Bu ihalede kaç kalem var?
   ```
   
   ```
   Bu ihaleyi nasıl optimize edebilirim?
   ```

3. **Beklenen Sonuçlar:**
   - ✅ AI, ihale verilerini doğru okuyabilmeli
   - ✅ Hedef fiyatı, kalemleri, tarihleri doğru söylemeli
   - ✅ İhale süreçleri hakkında öneriler sunmalı

## 🐛 Sorun Giderme

### Problem 1: "Ask KAI" Butonu Görünmüyor

**Çözüm Adımları:**

1. **Mixin kontrolü:**
   ```python
   # Shell'de kontrol edin
   tender = env['ak.tender'].search([], limit=1)
   print('ak_ai.mixin' in tender._inherit)  # True olmalı
   print(tender._inherit)  # Liste içinde 'ak_ai.mixin' olmalı
   ```

2. **Modül bağımlılığı:**
   - [`addons-custom/ak_tender/__manifest__.py`](../../../ak_tender/__manifest__.py) dosyasını açın
   - `depends` listesinde `'ak_ai'` olduğundan emin olun:
     ```python
     'depends': ['base', 'mail', 'ak_workflow', 'ak_ai'],  # ✅ ak_ai eklendi
     ```

3. **Modülü tekrar yükseltin:**
   ```bash
   # Terminal'de Odoo shell
   /opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
   
   # Shell içinde:
   env['ir.module.module'].search([('name', '=', 'ak_tender')]).button_immediate_upgrade()
   env.cr.commit()
   ```

4. **Tarayıcı cache'ini temizle:**
   - Chrome/Edge: Ctrl+Shift+Delete → Tümünü temizle
   - Firefox: Ctrl+Shift+Delete → Tümünü temizle
   - Veya Gizli/Incognito modda test edin

### Problem 2: Buton Var Ama Çalışmıyor

**Debug Adımları:**

1. **Browser Console'u açın:**
   - F12 → Console sekmesi
   - "Ask KAI" butonuna tıklayın
   - Hata mesajı var mı kontrol edin

2. **AI Asistan aktif mi:**
   ```python
   # Shell'de kontrol
   assistant = env['ak_ai.assistant'].search([('active', '=', True)], limit=1)
   if not assistant:
       print("❌ Aktif asistan bulunamadı!")
       # Asistan oluşturun veya aktif edin
   else:
       print(f"✅ Aktif asistan: {assistant.name}")
   ```

3. **API anahtarı kontrolü:**
   ```python
   # Shell'de
   assistant = env['ak_ai.assistant'].get_active_assistant()
   if not assistant.api_key:
       print("❌ API anahtarı ayarlanmamış!")
   else:
       print(f"✅ API anahtarı: {assistant.api_key[:10]}...")
   ```

4. **Test conversation oluştur:**
   ```python
   # Manuel conversation oluşturma
   tender = env['ak.tender'].search([], limit=1)
   conversation = env['ak_ai.conversation'].create_conversation(
       integration_type='chatter',
       context_model='ak.tender',
       context_res_id=tender.id
   )
   print(f"✅ Conversation oluşturuldu: {conversation.id}")
   
   # İhale kaydına bağla
   tender.write({'ai_conversation_id': conversation.id})
   env.cr.commit()
   ```

### Problem 3: AI Yanıt Vermiyor

**Kontrol Edilecekler:**

1. **Log kayıtlarını inceleyin:**
   ```bash
   # Terminal'de
   tail -f /var/log/odoo/odoo.log | grep -i "ai\|error"
   ```

2. **Interaction Log kontrolü:**
   - Ayarlar → AI Asistan → Interaction Logs
   - Son kayıtları açın
   - **Error Message** alanında hata var mı bakın

3. **Manuel API testi:**
   ```python
   # Shell'de direkt AI servisi
   service = env['ak_ai.service'].get_service()
   context = {
       'user': {
           'user': {'name': env.user.name, 'company_name': env.user.company_id.name},
           'permissions': {},
           'preferences': {'language': 'tr_TR', 'currency': 'TRY'}
       }
   }
   
   try:
       response = service.generate_response('Test mesajı', context)
       print(f"✅ AI Yanıt: {response}")
   except Exception as e:
       print(f"❌ Hata: {e}")
   ```

### Problem 4: Conversation Chatter'da Görünmüyor

**Çözüm:**

1. **AI conversation alanı ekleme:**
   - [`addons-custom/ak_tender/views/tender_views.xml`](../../../ak_tender/views/tender_views.xml) dosyasını açın
   - Form view'a conversation alanı ekleyin (opsiyonel, debug için):
   
   ```xml
   <notebook>
       <!-- Mevcut page'ler... -->
       
       <page string="AI Conversation" attrs="{'invisible': [('ai_conversation_id', '=', False)]}">
           <field name="ai_conversation_id" readonly="1"/>
           <button name="open_ai_chat" string="Open AI Chat" type="object" class="btn-primary"/>
       </page>
   </notebook>
   ```

2. **View'ı güncelleyin:**
   - Modülü yükseltin veya Odoo'yu yeniden başlatın

## 📊 Test Senaryoları

### Senaryo 1: İhale Optimizasyonu

1. **İhale oluşturun:**
   - 5-10 kalem ekleyin
   - Hedef fiyatlar belirleyin

2. **AI'ya sorun:**
   ```
   Bu ihaleyi nasıl daha verimli hale getirebilirim?
   ```

3. **Beklenen AI Yanıtı:**
   - İhale kalemlerini gruplandırma önerileri
   - Fiyat optimizasyonu tavsiyeleri
   - Tedarikçi seçimi stratejileri

### Senaryo 2: İhale Analizi

1. **Dolu bir ihale kaydı açın:**

2. **AI'ya sorun:**
   ```
   Bu ihalenin durumunu analiz et ve risk faktörlerini söyle
   ```

3. **Beklenen AI Yanıtı:**
   - Workflow durumu analizi
   - Eksik bilgiler
   - Potansiyel riskler

### Senaryo 3: Fiyat Karşılaştırması

1. **İhale kalemlerinde fiyat bilgileri olsun:**

2. **AI'ya sorun:**
   ```
   Hangi kalemlerde hedef fiyatın üzerinde teklifler var?
   ```

3. **Beklenen AI Yanıtı:**
   - Fiyat karşılaştırması
   - Hedefin üzerindeki kalemler
   - Öneriler

## 🎓 İleri Seviye Testler

### Context Injection Testi

AI'nın ihale kaydının tüm detaylarını okuyup okumadığını test edin:

```python
# Shell'de
tender = env['ak.tender'].browse(IHALE_ID)  # İhale ID'nizi yazın
conversation = tender.ai_conversation_id

# Context'i kontrol edin
if conversation:
    # Son mesajı inceleyin
    last_message = conversation.message_ids[-1] if conversation.message_ids else None
    if last_message:
        print(f"Son mesaj context'i:")
        print(last_message.context_data)  # Context bilgisini gösterir
```

### Multi-User Test

1. **Farklı kullanıcılar oluşturun:**
   - Ayarlar → Kullanıcılar → Yeni kullanıcı

2. **Her kullanıcı ile giriş yapın:**
   - Aynı ihale kaydını açın
   - "Ask KAI" butonuna tıklayın

3. **Kontrol edin:**
   - ✅ Her kullanıcı kendi conversation'ına sahip olmalı
   - ✅ Conversations birbirinden bağımsız olmalı
   - ✅ Güvenlik kuralları çalışmalı (yetkisiz kayıt erişimi engellenm eli)

## 📝 Özet Kontrol Listesi

Chatter'da "Ask KAI" butonunun çalışması için:

- ✅ `ak_ai` modülü yüklü ve yapılandırılmış
- ✅ Model `mail.thread` inherit ediyor
- ✅ Model `ak_ai.mixin` inherit ediyor
- ✅ `__manifest__.py`'da `ak_ai` dependency var
- ✅ Modül güncellendi (upgrade)
- ✅ Odoo yeniden başlatıldı
- ✅ AI asistan aktif ve API anahtarı ayarlanmış
- ✅ Form view'da chatter widget tanımlı
- ✅ Tarayıcı cache temizlendi

Hepsi ✅ ise "Ask KAI" butonu görünecektir!

## 🆘 Yardım

Sorun yaşıyorsanız:

1. **Log dosyalarını kontrol edin:**
   ```bash
   tail -100 /var/log/odoo/odoo.log
   ```

2. **Python shell'de debug edin:**
   ```bash
   /opt/odoo18-venv/bin/python /opt/odoo18/odoo-bin shell -d od18 -c /etc/odoo.conf --http-port=8070
   ```

3. **Interaction Logs'a bakın:**
   - Ayarlar → AI Asistan → Interaction Logs
   - Hata mesajlarını inceleyin

4. **Ana test kılavuzuna bakın:**
   - [TESTING_GUIDE_TR.md](./TESTING_GUIDE_TR.md)
