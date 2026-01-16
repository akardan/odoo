# MICE Projected vs Actual - Basitleştirilmiş Yaklaşım

## Temel Prensip

**Yeni model OLUŞTURMA** yerine **mevcut modellere alan ekleme**:

- `ak.tender.line` → Hem projected (teklif) hem actual (gerçekleşen) alanları
- `purchase.order.line` → Gerçekleşen sayıları ve fatura referansı

Bu şekilde:
✅ Tek satırda projected vs actual karşılaştırma
✅ Daha az tablo, daha az karmaşıklık
✅ Mevcut ilişkiler korunur
✅ Migration daha basit

---

## Veri Modeli - Basitleştirilmiş

### `ak.tender.line` (Güncellenmiş)

```python
class AkTenderLine(models.Model):
    _inherit = 'ak.tender.line'
    
    # ===== MEVCUT ALANLAR =====
    # tender_id, scenario_id, product_id, name, quantity, days, target_price, vb.
    
    # ===== YENİ: PROJECTED (Teklif Edilen) =====
    # Bu alanlar zaten var, sadece net tanımlama için:
    
    projected_quantity = fields.Float(
        string='Teklif Miktar',
        related='quantity',  # Mevcut quantity field'ı projected olarak kullan
        store=True,
        help='İhaledeki hedef/teklif miktarı'
    )
    
    projected_days = fields.Integer(
        string='Teklif Gün',
        related='days',  # Mevcut days field'ı projected olarak kullan
        store=True
    )
    
    # ===== YENİ: ACTUAL (Gerçekleşen) =====
    
    actual_quantity = fields.Float(
        string='Gerçekleşen Miktar',
        digits='Product Unit of Measure',
        help='Etkinlik sonrası gerçekleşen miktar',
        readonly=False,
        copy=False
    )
    
    actual_days = fields.Integer(
        string='Gerçekleşen Gün',
        help='Gerçekte kullanılan gün sayısı',
        readonly=False,
        copy=False
    )
    
    # Gerçekleşen tutar (purchase order line'dan alınır veya manuel girilir)
    actual_total = fields.Monetary(
        string='Gerçekleşen Toplam',
        compute='_compute_actual_total',
        inverse='_inverse_actual_total',
        store=True,
        currency_field='currency_id',
        help='Gerçekleşen: actual_quantity × actual_days × unit_price'
    )
    
    # Tutar manuel mi girildi yoksa hesaplanan mı?
    actual_total_manual = fields.Monetary(
        string='Manuel Gerçekleşen Tutar',
        currency_field='currency_id',
        copy=False,
        help='Eğer manuel tutar girilirse bu kullanılır (paket fiyat gibi)'
    )
    
    actual_unit_price = fields.Monetary(
        string='Gerçekleşen Birim Fiyat',
        currency_field='currency_id',
        help='Kazanan teklifin birim fiyatı (PO line\'dan)',
        compute='_compute_actual_unit_price',
        store=True,
        readonly=False
    )
    
    # ===== FARKLAR (Variance) =====
    
    variance_quantity = fields.Float(
        string='Fark (Miktar)',
        compute='_compute_variance',
        store=True,
        help='Gerçekleşen - Teklif'
    )
    
    variance_days = fields.Integer(
        string='Fark (Gün)',
        compute='_compute_variance',
        store=True
    )
    
    variance_total = fields.Monetary(
        string='Fark (Tutar)',
        compute='_compute_variance',
        store=True,
        currency_field='currency_id'
    )
    
    variance_percentage = fields.Float(
        string='Fark (%)',
        compute='_compute_variance',
        store=True,
        help='(Gerçekleşen - Teklif) / Teklif × 100'
    )
    
    # ===== DURUM VE NOTLAR =====
    
    has_variance = fields.Boolean(
        string='Fark Var',
        compute='_compute_variance',
        store=True,
        help='Gerçekleşen ≠ Teklif'
    )
    
    variance_reason = fields.Text(
        string='Fark Nedeni',
        help='Neden gerçekleşen sayılar tekliften farklı?'
    )
    
    is_additional_service = fields.Boolean(
        string='Ek Hizmet',
        default=False,
        help='Bu kalem orijinal teklifte yoktu, sonradan eklendi'
    )
    
    # Gerçekleşme durumu
    actual_state = fields.Selection([
        ('not_started', 'Başlamadı'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('invoiced', 'Faturalandı')
    ], string='Gerçekleşme Durumu', default='not_started', copy=False)
    
    # ===== COMPUTED METHODS =====
    
    @api.depends('actual_quantity', 'actual_days', 'actual_unit_price', 'actual_total_manual')
    def _compute_actual_total(self):
        """Gerçekleşen toplam hesapla (veya manuel değeri kullan)"""
        for line in self:
            if line.actual_total_manual:
                # Manuel girilmiş paket fiyat
                line.actual_total = line.actual_total_manual
            elif line.actual_quantity and line.actual_unit_price:
                # Otomatik hesaplama
                days = line.actual_days or 1
                line.actual_total = line.actual_quantity * days * line.actual_unit_price
            else:
                line.actual_total = 0.0
    
    def _inverse_actual_total(self):
        """Eğer actual_total manuel değiştirilirse, actual_total_manual'a yaz"""
        for line in self:
            if line.actual_total and not line.actual_unit_price:
                line.actual_total_manual = line.actual_total
    
    @api.depends('purchase_order_line_ids.price_unit')
    def _compute_actual_unit_price(self):
        """Kazanan PO line'dan birim fiyatı al"""
        for line in self:
            # Kazanan (awarded) PO'nun line'ını bul
            awarded_po_line = line.purchase_order_line_ids.filtered(
                lambda l: l.order_id.state in ['purchase', 'done'] and 
                          l.order_id.is_tender_winner
            )
            if awarded_po_line:
                line.actual_unit_price = awarded_po_line[0].price_unit
            else:
                line.actual_unit_price = 0.0
    
    @api.depends('quantity', 'days', 'actual_quantity', 'actual_days', 
                 'target_price', 'actual_total')
    def _compute_variance(self):
        """Farkları hesapla"""
        for line in self:
            # Miktar farkı
            line.variance_quantity = (line.actual_quantity or 0) - (line.quantity or 0)
            
            # Gün farkı
            line.variance_days = (line.actual_days or 0) - (line.days or 0)
            
            # Tutar farkı
            projected_total = (line.quantity or 0) * (line.days or 1) * (line.target_price or 0)
            line.variance_total = (line.actual_total or 0) - projected_total
            
            # Yüzde farkı
            if projected_total:
                line.variance_percentage = (line.variance_total / projected_total) * 100
            else:
                line.variance_percentage = 0.0
            
            # Fark var mı?
            line.has_variance = (
                abs(line.variance_quantity) > 0.01 or 
                abs(line.variance_days) > 0 or 
                abs(line.variance_total) > 0.01
            )
    
    # ===== AKSİYONLAR =====
    
    def action_fill_actual_from_projected(self):
        """Gerçekleşen değerleri teklif değerleriyle doldur (başlangıç için)"""
        for line in self:
            line.write({
                'actual_quantity': line.quantity,
                'actual_days': line.days,
            })
    
    def action_copy_from_invoice(self):
        """Faturadan gerçekleşen değerleri çek"""
        # Invoice line'dan actual quantity'yi al
        # Bu method fatura entegrasyonu yapılırken implement edilir
        pass
```

### `ak.tender.scenario` (Eklenti)

```python
class AkTenderScenario(models.Model):
    _inherit = 'ak.tender.scenario'
    
    # Senaryo seviyesinde projected vs actual
    projected_total = fields.Monetary(
        string='Teklif Tutarı',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Tüm teklif kalemlerinin toplamı'
    )
    
    actual_total = fields.Monetary(
        string='Gerçekleşen Tutarı',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Tüm gerçekleşen kalemlerin toplamı'
    )
    
    variance_total = fields.Monetary(
        string='Fark',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    
    variance_percentage = fields.Float(
        string='Fark (%)',
        compute='_compute_totals',
        store=True
    )
    
    @api.depends('line_ids.quantity', 'line_ids.days', 'line_ids.target_price',
                 'line_ids.actual_total')
    def _compute_totals(self):
        for scenario in self:
            # Projected
            scenario.projected_total = sum(
                (line.quantity or 0) * (line.days or 1) * (line.target_price or 0)
                for line in scenario.line_ids
                if not line.display_type
            )
            
            # Actual
            scenario.actual_total = sum(
                line.actual_total or 0
                for line in scenario.line_ids
                if not line.display_type
            )
            
            # Variance
            scenario.variance_total = scenario.actual_total - scenario.projected_total
            
            if scenario.projected_total:
                scenario.variance_percentage = (
                    scenario.variance_total / scenario.projected_total
                ) * 100
            else:
                scenario.variance_percentage = 0.0
```

### `purchase.order` (Eklenti)

```python
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # İhale kazananı mı?
    is_tender_winner = fields.Boolean(
        string='İhale Kazananı',
        default=False,
        copy=False,
        help='Bu PO ihaleyi kazandı mı?'
    )
    
    # Gerçekleşme durumu
    actual_submitted = fields.Boolean(
        string='Gerçekleşme Gönderildi',
        default=False,
        copy=False,
        help='Tedarikçi gerçekleşme verilerini gönderdi mi?'
    )
    
    actual_submitted_date = fields.Datetime(
        string='Gerçekleşme Gönderim Tarihi',
        readonly=True,
        copy=False
    )
    
    actual_approved = fields.Boolean(
        string='Gerçekleşme Onaylandı',
        default=False,
        copy=False
    )
    
    actual_approved_by = fields.Many2one(
        'res.users',
        string='Onaylayan',
        readonly=True,
        copy=False
    )
    
    def action_submit_actual_to_buyer(self):
        """Tedarikçi gerçekleşmeyi alıcıya gönderir"""
        self.ensure_one()
        
        # Tender line'lara gerçekleşen değerleri kopyala
        for po_line in self.order_line:
            if po_line.tender_line_id:
                po_line.tender_line_id.write({
                    'actual_quantity': po_line.product_qty,
                    'actual_unit_price': po_line.price_unit,
                    'actual_state': 'completed',
                })
        
        self.write({
            'actual_submitted': True,
            'actual_submitted_date': fields.Datetime.now()
        })
        
        # Bildirim gönder
        self.tender_id.message_post(
            body=f"Tedarikçi {self.partner_id.name} gerçekleşme verilerini gönderdi.",
            subject="Gerçekleşme Bildirimi"
        )
```

---

## UI Görünümleri

### Tender Line Tree View (Projected vs Actual)

```xml
<tree string="İhale Kalemleri">
    <field name="sequence" widget="handle"/>
    <field name="product_id"/>
    <field name="name"/>
    
    <!-- PROJECTED -->
    <field name="quantity" string="Teklif Miktar"/>
    <field name="days" string="Teklif Gün"/>
    <field name="target_price" string="Hedef Fiyat"/>
    <field name="projected_total" string="Teklif Toplam" sum="Teklif Toplam"/>
    
    <!-- ACTUAL -->
    <field name="actual_quantity" string="Gerçekleşen Miktar"/>
    <field name="actual_days" string="Gerçekleşen Gün"/>
    <field name="actual_unit_price" string="Gerçek Fiyat"/>
    <field name="actual_total" string="Gerçekleşen Toplam" sum="Gerçekleşen Toplam"/>
    
    <!-- VARIANCE -->
    <field name="variance_quantity" decoration-danger="variance_quantity &lt; 0"
           decoration-success="variance_quantity == 0"/>
    <field name="variance_total" decoration-danger="variance_total &gt; 0"
           decoration-success="variance_total &lt;= 0"/>
    <field name="variance_percentage" widget="percentage"/>
    
    <field name="has_variance" invisible="1"/>
    <field name="actual_state"/>
</tree>
```

### Tender Line Form View (Detaylı)

```xml
<form string="İhale Kalemi">
    <sheet>
        <group>
            <group string="Genel">
                <field name="product_id"/>
                <field name="name"/>
            </group>
            <group string="Durum">
                <field name="actual_state"/>
                <field name="is_additional_service"/>
            </group>
        </group>
        
        <notebook>
            <page string="Teklif (Projected)" name="projected">
                <group>
                    <group>
                        <field name="quantity"/>
                        <field name="days"/>
                        <field name="uom_id"/>
                    </group>
                    <group>
                        <field name="target_price"/>
                        <field name="currency_id" invisible="1"/>
                        <field name="projected_total" readonly="1"/>
                    </group>
                </group>
            </page>
            
            <page string="Gerçekleşen (Actual)" name="actual">
                <group>
                    <group>
                        <field name="actual_quantity"/>
                        <field name="actual_days"/>
                    </group>
                    <group>
                        <field name="actual_unit_price"/>
                        <field name="actual_total"/>
                        <field name="actual_total_manual" 
                               attrs="{'invisible': [('actual_total_manual', '=', 0)]}"/>
                    </group>
                </group>
                
                <group string="Fark Bilgileri" attrs="{'invisible': [('has_variance', '=', False)]}">
                    <field name="variance_reason" placeholder="Neden farklı?"/>
                </group>
                
                <div class="oe_button_box" name="button_box">
                    <button name="action_fill_actual_from_projected" 
                            type="object" 
                            string="Teklif Değerlerini Kopyala"
                            class="oe_stat_button" 
                            icon="fa-copy"/>
                </div>
            </page>
            
            <page string="Farklar (Variance)" name="variance" 
                  attrs="{'invisible': [('has_variance', '=', False)]}">
                <group>
                    <group>
                        <label for="variance_quantity" string="Miktar Farkı"/>
                        <div>
                            <field name="variance_quantity" class="oe_inline"/>
                            <span class="oe_inline" 
                                  attrs="{'invisible': [('variance_quantity', '=', 0)]}">
                                (Teklif: <field name="quantity" readonly="1" class="oe_inline"/> → 
                                 Gerçek: <field name="actual_quantity" readonly="1" class="oe_inline"/>)
                            </span>
                        </div>
                    </group>
                    <group>
                        <label for="variance_total" string="Tutar Farkı"/>
                        <div>
                            <field name="variance_total" class="oe_inline"/>
                            <span class="oe_inline">
                                (<field name="variance_percentage" widget="percentage" class="oe_inline"/>)
                            </span>
                        </div>
                    </group>
                </group>
            </page>
        </notebook>
    </sheet>
</form>
```

### Senaryo Özet Görünümü

```xml
<form string="Senaryo">
    <sheet>
        <div class="oe_button_box" name="button_box">
            <button name="action_view_variance_report" 
                    type="object" 
                    class="oe_stat_button" 
                    icon="fa-bar-chart"
                    attrs="{'invisible': [('actual_total', '=', 0)]}">
                <div class="o_field_widget o_stat_info">
                    <span class="o_stat_value">
                        <field name="variance_percentage" widget="percentage"/>
                    </span>
                    <span class="o_stat_text">Fark</span>
                </div>
            </button>
            
            <button name="action_create_proforma_invoice" 
                    type="object" 
                    class="oe_stat_button" 
                    icon="fa-file-text-o"
                    string="Proforma Oluştur"
                    attrs="{'invisible': ['|', ('actual_total', '=', 0), ('actual_state', '!=', 'completed')]}"/>
        </div>
        
        <group>
            <group string="Teklif (Projected)">
                <field name="projected_total" widget="monetary"/>
            </group>
            <group string="Gerçekleşen (Actual)">
                <field name="actual_total" widget="monetary"/>
            </group>
        </group>
        
        <group string="Fark" attrs="{'invisible': [('variance_total', '=', 0)]}">
            <group>
                <field name="variance_total" widget="monetary"
                       decoration-danger="variance_total &gt; 0"
                       decoration-success="variance_total &lt; 0"/>
            </group>
            <group>
                <field name="variance_percentage" widget="percentage"/>
            </group>
        </group>
        
        <notebook>
            <page string="Kalemler" name="lines">
                <field name="line_ids">
                    <tree editable="bottom">
                        <!-- Projected vs Actual tree view -->
                    </tree>
                </field>
            </page>
        </notebook>
    </sheet>
</form>
```

---

## Tedarikçi Portal - Gerçekleşme Girişi (Basitleştirilmiş)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ GERÇEKLEŞMERETİ: Yıllık Satış Toplantısı 2026                           │
│ Senaryo: Chamada Prestige (Antalya) - HB                                │
└──────────────────────────────────────────────────────────────────────────┘

SAT NO: #PO-2025-0089

┌──────────────────────────────────────────────────────────────────────────┐
│ Hizmet          │ Teklif │ Gerçekleşen │ Gün │ Birim │ Teklif  │ Gerçek │
│                 │ Miktar │             │     │ Fiyat │ Toplam  │ Toplam │
├─────────────────┼────────┼─────────────┼─────┼───────┼─────────┼────────┤
│ Single Room HB  │  65    │ [__63___]   │  3  │ 150€  │29,250€  │28,350€││
│ Double Room HB  │   1    │ [___2___]   │  3  │ 200€  │  600€   │ 1,200€││
│ Gala Yemeği     │  65    │ [__68___]   │  1  │  55€  │ 3,575€  │ 3,740€││
├─────────────────┼────────┼─────────────┼─────┼───────┼─────────┼────────┤
│ TOPLAM          │        │             │     │       │33,425€  │33,290€││
└──────────────────────────────────────────────────────────────────────────┘

⚠️ Farklı olan kalemlerin açıklamasını girin:

Single Room HB:
[2 kişi hastalık nedeniyle iptal__________________________]

Double Room HB:
[1 ek yönetici last minute katıldı_______________________]

Gala Yemeği:
[3 davetli ek katıldı____________________________________]

─────────────────────────────────────────────────────────────────────────────

➕ EK HİZMETLER (Sonradan eklenen)

[+ Yeni Kalem Ekle]

Araç Kiralama (VIP Transfer): 2 × 1 gün × 120€ = 240€
Açıklama: [2 üst düzey yönetici için havalimanı VIP transferi]

─────────────────────────────────────────────────────────────────────────────

📊 ÖZET
Teklif:       33,425€
Ek:              240€
Gerçekleşen:  33,530€
Fark:           +105€ (+0.3%)

[💾 Kaydet] [📤 Gönder ve Proforma Talep Et]
```

---

## Avantajlar (Basitleştirilmiş Yaklaşım)

| Kriter | Yeni Model Yaklaşımı | Mevcut Alan Yaklaşımı ✅ |
|--------|---------------------|-------------------------|
| **Karmaşıklık** | Yüksek (2 yeni model) | Düşük (alan ekleme) |
| **Migration** | Zor (yeni tablolar) | Kolay (ALTER TABLE) |
| **Sorgu Performansı** | JOIN gerekir | Tek SELECT |
| **Veri Tutarlılığı** | 2 yerde senkronize | Tek kayıt |
| **UI Basitliği** | 2 ayrı ekran | Tek form, 2 kolon |
| **Kod Bakımı** | Daha fazla kod | Daha az kod |
| **Esneklik** | Daha esnek | Yeterli |

**Sonuç:** Basitleştirilmiş yaklaşım (alan ekleme) **%80 use case için yeterli ve çok daha basit**.

---

## Implementasyon Planı

### Adım 1: Model Güncellemeleri (1 Gün)

```python
# ak_tender/models/tender.py

class AkTenderLine(models.Model):
    _inherit = 'ak.tender.line'
    
    # 10-15 yeni alan ekle (yukarıdaki gibi)
    # Computed methods ekle
```

### Adım 2: Views (1 Gün)

```xml
<!-- Tree view: projected ve actual kolonlar -->
<!-- Form view: notebook ile projected/actual/variance tabs -->
<!-- Senaryo summary widget -->
```

### Adım 3: Portal (1 Gün)

```python
# Portal controller: gerçekleşme girişi
# Template: projected vs actual table
```

### Adım 4: Proforma (0.5 Gün)

```python
# Proforma invoice oluşturma
# actual values kullan
```

### Adım 5: Raporlar (0.5 Gün)

```python
# Variance report
# PDF proforma template
```

**Toplam:** 4 gün (önceki plandan 4-5 gün daha kısa!)

---

## Özet

**Basitleştirilmiş Yaklaşım:**

✅ Mevcut `ak.tender.line` modeline `actual_*` alanları ekle
✅ `ak.tender.scenario` için aggregated actual totals
✅ `purchase.order` için winner flag ve actual submission tracking
✅ Tek satırda projected vs actual comparison
✅ Daha az kod, daha az karmaşıklık, daha hızlı geliştirme

**Önerilen Yapı:**
```
ak.tender.line:
  ├─ quantity (projected)      → actual_quantity
  ├─ days (projected)          → actual_days  
  ├─ target_price (projected)  → actual_unit_price
  └─ computed: variance_*, has_variance, variance_reason
```

Bu yaklaşım **KISS prensibine** (Keep It Simple, Stupid) uygun ve **yeterli çözüm** sağlıyor.

---

**Karar:** Mevcut modellere alan ekleme yaklaşımını mı uygulayalım?
