# ak_learning Expansions

## Genel Bakış

**ak_learning Expansions**, Odoo 18 CE için geliştirilmiş bir e-öğrenme ve sertifika sınavı genişletme modülüdür. Bu modül, etkinlik yönetimi ile e-öğrenme platformunu entegre ederek ve sınavlarda soru karıştırma özelliği ekleyerek eğitim süreçlerini geliştirir.

## Özellikler

### 1. Etkinlik-Eğitim Entegrasyonu
- **Eğitim Alanı**: Etkinliklere eğitim kursu (slide.channel) seçme imkanı
- **Eğitim Etkinliği Tanımlama**: Etkinliklerin eğitim etkinliği olup olmadığını otomatik belirleme
- **Sunucu Eylemi**: Etkinlik katılımcılarını otomatik olarak kurs katılımcısı olarak atama

### 2. Sınav Sorusu Karıştırma
- **Rastgele Soru Sıralaması**: Her kullanıcı için farklı soru sırası
- **Kullanıcı Bazlı Karıştırma**: Her sınava giren kullanıcı soruları farklı sırada görür
- **Bölüm Bazlı Seçimle Birlikte**: Mevcut rastgele soru seçimi özelliğine ek olarak çalışır
- **Esnek Yapılandırma**: Soru karıştırma özelliği isteğe bağlı olarak aktifleştirilebilir

## Teknik Detaylar

### Genişletilen Modeller

#### 1. Survey (survey.survey)
[`models/models.py`](models/models.py)
```python
- shuffle_questions: Boolean alan - Soru karıştırmayı etkinleştirir
- _prepare_user_input_predefined_questions(): Override edilmiş metod
```

#### 2. Event (event.event)
[`models/event.py`](models/event.py)
```python
- training_id: Many2one alan - Eğitim kanalı seçimi
- is_training_event: Computed Boolean alan - Etkinlik türü kontrolü
- _compute_is_training_event(): Hesaplama metodu
```

## Bağımlılıklar

Bu modül aşağıdaki Odoo modüllerine bağımlıdır:

- `event` - Etkinlik yönetimi
- `website_slides` - E-öğrenme platformu
- `website_sale` - Web satış
- `website_sale_slides` - E-öğrenme satış entegrasyonu

## Kurulum

1. Modülü `addons-custom` dizinine yerleştirin:
   ```bash
   /opt/odoo18/addons-custom/ak_learning/
   ```

2. Odoo yapılandırma dosyanızı güncelleyin (`odoo.conf`):
   ```ini
   addons_path = /opt/odoo18/addons,/opt/odoo18/addons-custom
   ```

3. Odoo sunucusunu yeniden başlatın:
   ```bash
   sudo systemctl restart odoo
   ```

4. Odoo arayüzünden:
   - **Uygulamalar** menüsüne gidin
   - **Uygulama Listesini Güncelle** butonuna tıklayın
   - "ak_learning Expansions" modülünü arayın
   - **Yükle** butonuna tıklayın

## Kullanım

### Soru Karıştırmayı Etkinleştirme

1. **Anketler** uygulamasına gidin
2. Bir anket/sınav açın veya yeni bir tane oluşturun
3. **Seçenekler** sekmesinde **"Shuffled Question Order"** (Karıştırılmış Soru Sırası) kutusunu işaretleyin
4. Anketi kaydedin

Artık her kullanıcı sınavı açtığında sorular rastgele sıralanacaktır.

### Etkinliklere Eğitim Atama

1. **Etkinlikler** uygulamasına gidin
2. Bir etkinlik açın veya yeni bir tane oluşturun
3. **Training** (Eğitim) alanından ilgili eğitim kursunu seçin
4. Etkinliği kaydedin

Bu özellik, etkinlik katılımcılarının otomatik olarak seçilen eğitim kursuna kaydedilmesini sağlar.

## Günlük Kaydı

Modül, soru karıştırma işlemleri için detaylı günlük kaydı tutar:

- Orijinal soru sırası loglanır
- Karıştırılmış soru sırası loglanır
- Hatalar yakalanır ve loglanır

Günlükleri kontrol etmek için:
```bash
tail -f /var/log/odoo/odoo-server.log | grep "question order"
```

## Yapılandırma Dosyaları

### Görünümler
- [`views/event_views.xml`](views/event_views.xml) - Etkinlik formu görünüm uzantıları
- [`views/website_slides_templates.xml`](views/website_slides_templates.xml) - Web site şablonları

### Güvenlik
- `security/ir.model.access.csv` - Erişim kontrol kuralları (isteğe bağlı)

## Geliştirme Notları

### Gelecek Geliştirmeler

- Soru karıştırma için farklı algoritmalar
- Bölüm bazında karıştırma seçenekleri
- Katılımcı otomatik kayıt sunucu eylemi
- Gelişmiş raporlama özellikleri

### Bilinen Sınırlamalar

- `is_training_event` hesaplaması sabit kodlanmış etkinlik türü ID'si kullanır (ID=2)
- XML ID veya yapılandırma parametresi kullanımı önerilir

## Destek ve Katkı

Hatalar, öneriler veya katkılar için lütfen modül deposuna issue açın veya pull request gönderin.

## Yazar

**Kardan.Digital**
- Website: [https://kardan.digital](https://kardan.digital)

## Lisans

Bu modül, Odoo Community Edition lisansı altında dağıtılmaktadır.

## Versiyon Geçmişi

### v0.1 (Mevcut)
- İlk sürüm
- Soru karıştırma özelliği
- Etkinlik-eğitim entegrasyonu
- Temel işlevsellik

---

**Not**: Bu modül Odoo 18 Community Edition için geliştirilmiştir. Diğer versiyonlarda uyumluluk test edilmemiştir.
