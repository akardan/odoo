# MICE Entegrasyonu - İmplementasyon Özeti

## Genel Bakış
Bu doküman, `ak_tender` modülüne eklenen MICE (Meeting, Incentive, Conference, Event) entegrasyonunun teknik detaylarını içerir.

## Oluşturulan/Değiştirilen Dosyalar

### 1. Model Dosyaları

#### [`models/tender_scenario.py`](../models/tender_scenario.py)
**Amaç:** MICE senaryolarını yönetmek için ana model

**Özellikler:**
- Senaryo tipi (otel, toplantı salonu, transfer, vb.)
- Lokasyon ve otel bilgileri
- Tarih seçenekleri (One2many ilişki)
- İhale kalemleri (One2many ilişki)
- NPV hesaplamaları
- Kısa liste ve eleme mekanizması
- Mail thread desteği (chatter)

**Önemli Metodlar:**
- `_compute_line_count()`: Kalem sayısını hesaplar
- `_compute_total_target_price()`: Hedef toplam fiyatı hesaplar
- `_compute_best_npv_offer()`: En iyi NPV teklifini bulur
- `action_add_to_shortlist()`: Senaryoyu kısa listeye ekler
- `action_eliminate()`: Senaryoyu eler
- `action_award()`: Senaryoyu kazanan olarak işaretler

#### [`models/tender_scenario_date.py`](../models/tender_scenario_date.py)
**Amaç:** Senaryo için alternatif tarih seçenekleri

**Özellikler:**
- Başlangıç ve bitiş tarihleri
- Gün sayısı hesaplama
- Öncelik sıralaması
- Senaryo ile ilişki

#### [`models/tender_mice_extension.py`](../models/tender_mice_extension.py)
**Amaç:** `ak.tender` ve `ak.tender.line` modellerini MICE için genişletir

**ak.tender Uzantıları:**
- `tender_type`: 'mice' seçeneği eklendi
- `total_person_count`: Toplam katılımcı sayısı
- `vip_person_count`: VIP katılımcı sayısı
- `scenario_ids`: Senaryolar (One2many)
- Senaryo istatistikleri (toplam, kısa liste, elenen, kazanan)

**ak.tender.line Uzantıları:**
- `scenario_id`: Bağlı senaryo
- `line_type`: Kalem tipi (konaklama, toplantı, transfer, vb.)
- MICE özel alanlar:
  - `mice_room_type`: Oda tipi
  - `mice_view_type`: Manzara tipi
  - `mice_meal_plan`: Yemek planı
  - `mice_amenities`: Olanaklar
  - `mice_special_requests`: Özel talepler
- `line_summary`: Otomatik özet oluşturma

#### [`models/purchase_order_line_mice_extension.py`](../models/purchase_order_line_mice_extension.py)
**Amaç:** Satınalma sipariş kalemlerine NPV hesaplama ekler

**Özellikler:**
- `scenario_id`: Bağlı senaryo
- `scenario_date_id`: Bağlı senaryo tarihi
- `payment_term_days`: Ödeme vadesi (gün)
- `price_npv`: Net Bugünkü Değer
- `npv_discount_amount`: İskonto tutarı
- `is_package_price`: Paket fiyat mı?

**NPV Hesaplama:**
```python
discount_rate = 0.10  # %10 yıllık
days = payment_term.nb_days
discount_factor = 1 / ((1 + discount_rate) ** (days / 365.0))
price_npv = price_subtotal * discount_factor
```

### 2. View Dosyaları

#### [`views/tender_scenario_views.xml`](../views/tender_scenario_views.xml)
**İçerik:**
- Senaryo form view (detaylı)
- Senaryo tree view
- Senaryo kanban view
- Senaryo tarih form/tree view'ları
- Senaryo karşılaştırma pivot/graph view'ları
- Menü ve action tanımları

**Önemli Özellikler:**
- Odoo 18 uyumlu (`<list>` kullanımı)
- `attrs` kullanımı kaldırıldı
- Dinamik görünürlük kontrolleri
- Chatter desteği

#### [`views/tender_mice_views.xml`](../views/tender_mice_views.xml)
**İçerik:**
- İhale form view'a senaryo tab'ı ekleme
- İhale kalemlerine MICE alanları ekleme
- Satınalma sipariş view'larına NPV alanları ekleme

**Değişiklikler:**
- `view_tender_line_form` inherit'i kaldırıldı (inline form kullanılıyor)
- Tender line tree view'a MICE alanları eklendi
- Purchase order line view'larına NPV alanları eklendi

### 3. Wizard Dosyaları

#### [`wizards/tender_scenario_wizard.py`](../wizards/tender_scenario_wizard.py)
**Wizardlar:**
1. **ScenarioCreationWizard**: Toplu senaryo oluşturma
2. **ScenarioEliminationWizard**: Toplu eleme
3. **NextRoundWizard**: Sonraki tur başlatma

#### [`wizards/tender_scenario_wizard_views.xml`](../wizards/tender_scenario_wizard_views.xml)
**İçerik:**
- Wizard form view'ları
- Action tanımları

### 4. Güvenlik Dosyaları

#### [`security/ir.model.access.csv`](../security/ir.model.access.csv)
**Eklenen Kayıtlar:**
```csv
access_ak_tender_scenario_user,ak.tender.scenario.user,model_ak_tender_scenario,base.group_user,1,1,1,0
access_ak_tender_scenario_manager,ak.tender.scenario.manager,model_ak_tender_scenario,base.group_system,1,1,1,1
access_ak_tender_scenario_date_user,ak.tender.scenario.date.user,model_ak_tender_scenario_date,base.group_user,1,1,1,0
access_ak_tender_scenario_date_manager,ak.tender.scenario.date.manager,model_ak_tender_scenario_date,base.group_system,1,1,1,1
# ... (toplam 10 kayıt)
```

### 5. Manifest Dosyası

#### [`__manifest__.py`](../__manifest__.py)
**Güncellemeler:**
- Versiyon: 18.0.1.1.0
- Yeni model dosyaları eklendi
- Yeni view dosyaları eklendi
- Yeni wizard dosyaları eklendi
- Bağımlılıklar: `purchase`, `account`

## Odoo 18 Uyumluluk Değişiklikleri

### 1. View Tipi Değişikliği
```xml
<!-- ESKİ (Odoo 16 ve öncesi) -->
<tree>...</tree>

<!-- YENİ (Odoo 18) -->
<list>...</list>
```

### 2. attrs Kullanımı Kaldırıldı
```xml
<!-- ESKİ -->
<field name="field_name" attrs="{'invisible': [('state', '!=', 'draft')]}"/>

<!-- YENİ -->
<field name="field_name" invisible="state != 'draft'"/>
```

### 4. Mail Thread Inherit
```python
class TenderScenario(models.Model):
    _name = 'ak.tender.scenario'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Chatter için
    _description = 'Tender Scenario'
```

## Kullanım Senaryosu

### 1. MICE İhalesi Oluşturma
1. İhale oluştur, tip olarak "MICE" seç
2. Toplam katılımcı sayısını gir
3. VIP katılımcı sayısını gir (opsiyonel)

### 2. Senaryo Oluşturma
1. İhale formunda "Senaryolar" tab'ına git
2. "Yeni Senaryo" butonuna tıkla
3. Senaryo detaylarını doldur:
   - Senaryo tipi (otel, toplantı salonu, vb.)
   - Lokasyon
   - Otel/tedarikçi
   - Yemek planı
4. Alternatif tarihleri ekle
5. İhale kalemlerini ekle (konaklama, toplantı, transfer, vb.)

### 3. Teklif Alma
1. Tedarikçilere RFQ gönder
2. Tedarikçiler tekliflerini girer
3. Sistem otomatik NPV hesaplar
4. Her senaryo için en iyi NPV teklifi gösterilir

### 4. Kısa Liste ve Eleme
1. Senaryoları karşılaştır (pivot/graph view)
2. İstenmeyen senaryoları ele
3. Uygun senaryoları kısa listeye ekle
4. "Sonraki Tur" butonuyla yeni tur başlat

### 5. Kazanan Belirleme
1. Final değerlendirmesi yap
2. Kazanan senaryoyu işaretle
3. İlgili satınalma siparişlerini onayla

## NPV (Net Bugünkü Değer) Hesaplama

### Formül
```
NPV = Fiyat / (1 + r)^(t/365)

Burada:
- r = İskonto oranı (varsayılan: %10)
- t = Ödeme vadesi (gün)
```

### Örnek
```
Fiyat: 10,000 TL
Vade: 90 gün
İskonto oranı: %10

NPV = 10,000 / (1 + 0.10)^(90/365)
    = 10,000 / 1.0241
    = 9,764.52 TL

İskonto tutarı = 10,000 - 9,764.52 = 235.48 TL
```

## Test Edilmesi Gerekenler

### Fonksiyonel Testler
- [ ] MICE ihalesi oluşturma
- [ ] Senaryo oluşturma ve düzenleme
- [ ] Alternatif tarih ekleme
- [ ] İhale kalemi ekleme (MICE alanlarıyla)
- [ ] RFQ gönderme
- [ ] Teklif girişi
- [ ] NPV hesaplama doğruluğu
- [ ] Senaryo karşılaştırma
- [ ] Kısa liste mekanizması
- [ ] Eleme işlemi
- [ ] Sonraki tur başlatma
- [ ] Kazanan belirleme

### Teknik Testler
- [ ] Model ilişkileri (One2many, Many2one)
- [ ] Computed field'lar
- [ ] Domain filtreleri
- [ ] View görünürlük kontrolleri
- [ ] Güvenlik kuralları
- [ ] Chatter fonksiyonalitesi
- [ ] Wizard işlemleri

## Bilinen Sorunlar ve Çözümler

### 1. External ID Hatası
**Sorun:** `ak_tender.view_tender_line_form` bulunamadı
**Çözüm:** Tender line için ayrı form view yok, inline kullanılıyor. Inherit kaldırıldı.

### 2. attrs Deprecation
**Sorun:** Odoo 18'de `attrs` kullanımı kaldırıldı
**Çözüm:** Tüm `attrs` kullanımları Python expression'lara dönüştürüldü

### 3. Payment Term Alan Adı
**Sorun:** `payment_term.days` Odoo 18'de yok
**Çözüm:** `payment_term.nb_days` kullanıldı

## Gelecek Geliştirmeler

### Öncelikli
1. Demo data oluşturma
2. Otomatik test yazma
3. Raporlama iyileştirmeleri
4. Email template'leri

### İsteğe Bağlı
1. Dashboard widget'ları
2. Gantt view (tarih planlaması için)
3. Bütçe kontrolü
4. Onay akışı (approval workflow)
5. Tedarikçi portal entegrasyonu
6. Mobil uygulama desteği

## Katkıda Bulunanlar
- İmplementasyon: Roo (AI Assistant)
- Tasarım: MICE_UNIFIED_DESIGN_AND_IMPLEMENTATION_PLAN.md
- Tarih: 2026-01-23

## Lisans
Bu modül, ak_tender modülünün bir parçasıdır ve aynı lisans altındadır.
