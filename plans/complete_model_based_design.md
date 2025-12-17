# Complete Model-Based Tender Architecture
## Tam Model Tabanlı Tasarım - tender_type Dahil

**Tarih:** 17.12.2025  
**Versiyon:** 7.0 (Complete Model-Based)

---

## 🎯 TAM MODEL TABANLI YAKLAŞIM

`tender_type` dahil **tüm selection alanları** model tabanlı olacak:
- ✅ `ak.tender.type` - İhale tipleri
- ✅ `ak.tender.sub.type` - İhale alt tipleri
- ✅ `ak.tender.line.category` - Satır kategorileri

---

## 📋 MASTER DATA MODELLERİ

### 1. ak.tender.type - İhale Tipleri (YENİ)

```python
class AkTenderType(models.Model):
    _name = 'ak.tender.type'
    _description = 'İhale Tipleri'
    _order = 'sequence, name'
    
    name = fields.Char('İhale Tipi', required=True, translate=True,
                      help='Örn: Direkt Satınalma, MICE İhaleler, Sigorta İhalesi')
    code = fields.Char('Kod', required=True,
                      help='Teknik kod, örn: direct, mice, insurance')
    sequence = fields.Integer('Sıra', default=10)
    active = fields.Boolean('Aktif', default=True)
    description = fields.Text('Açıklama', translate=True)
    color = fields.Integer('Renk', help='Kanban view için renk')
    icon = fields.Char('İkon', help='Font Awesome icon class')
    
    # İlişkili kayıtlar
    sub_type_ids = fields.One2many('ak.tender.sub.type', 'tender_type_id', 
                                   string='Alt Tipler')
    line_category_ids = fields.One2many('ak.tender.line.category', 'tender_type_id',
                                       string='Satır Kategorileri')
    
    # İstatistikler
    tender_count = fields.Integer('İhale Sayısı', compute='_compute_tender_count')
    
    @api.depends('code')
    def _compute_tender_count(self):
        for record in self:
            record.tender_count = self.env['ak.tender'].search_count([
                ('tender_type_id', '=', record.id)
            ])
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'İhale tipi kodu benzersiz olmalıdır!'),
    ]
    
    def action_view_tenders(self):
        """Bu tipe ait ihaleleri göster"""
        self.ensure_one()
        return {
            'name': f'{self.name} İhaleleri',
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender',
            'view_mode': 'tree,form',
            'domain': [('tender_type_id', '=', self.id)],
            'context': {'default_tender_type_id': self.id}
        }
```

**Örnek Veriler:**
```xml
<!-- data/tender_type_data.xml -->
<odoo>
    <data noupdate="1">
        <record id="tender_type_direct" model="ak.tender.type">
            <field name="name">Direkt Satınalma</field>
            <field name="code">direct</field>
            <field name="sequence">10</field>
            <field name="icon">fa-shopping-cart</field>
            <field name="color">1</field>
        </record>
        
        <record id="tender_type_indirect" model="ak.tender.type">
            <field name="name">Endirekt Satınalma</field>
            <field name="code">indirect</field>
            <field name="sequence">20</field>
            <field name="icon">fa-industry</field>
            <field name="color">2</field>
        </record>
        
        <record id="tender_type_mice" model="ak.tender.type">
            <field name="name">MICE İhaleler</field>
            <field name="code">mice</field>
            <field name="sequence">30</field>
            <field name="icon">fa-plane</field>
            <field name="color">3</field>
            <field name="description">Toplantı, Motivasyon, Kongre ve Etkinlik ihaleleri</field>
        </record>
        
        <record id="tender_type_insurance" model="ak.tender.type">
            <field name="name">Sigorta İhalesi</field>
            <field name="code">insurance</field>
            <field name="sequence">40</field>
            <field name="icon">fa-shield-alt</field>
            <field name="color">4</field>
            <field name="description">Kurumsal sigorta ihaleleri</field>
        </record>
        
        <record id="tender_type_promotion" model="ak.tender.type">
            <field name="name">Promosyon ve Kırtasiye</field>
            <field name="code">promotion</field>
            <field name="sequence">50</field>
            <field name="icon">fa-gift</field>
            <field name="color">5</field>
        </record>
    </data>
</odoo>
```

---

### 2. ak.tender.sub.type - İhale Alt Tipleri (GÜNCELLEME)

```python
class AkTenderSubType(models.Model):
    _name = 'ak.tender.sub.type'
    _description = 'İhale Alt Tipleri'
    _order = 'tender_type_id, sequence, name'
    
    name = fields.Char('Alt Tip Adı', required=True, translate=True)
    code = fields.Char('Kod', required=True)
    tender_type_id = fields.Many2one('ak.tender.type', 'İhale Tipi', 
                                     required=True, ondelete='cascade')
    sequence = fields.Integer('Sıra', default=10)
    active = fields.Boolean('Aktif', default=True)
    description = fields.Text('Açıklama', translate=True)
    
    # İstatistikler
    tender_count = fields.Integer('İhale Sayısı', compute='_compute_tender_count')
    
    @api.depends('code')
    def _compute_tender_count(self):
        for record in self:
            record.tender_count = self.env['ak.tender'].search_count([
                ('tender_sub_type_id', '=', record.id)
            ])
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Alt tip kodu benzersiz olmalıdır!'),
    ]
```

**Örnek Veriler:**
```xml
<!-- data/tender_sub_type_data.xml -->
<odoo>
    <data noupdate="1">
        <!-- MICE Alt Tipleri -->
        <record id="tender_sub_type_mice_meeting" model="ak.tender.sub.type">
            <field name="name">Toplantı</field>
            <field name="code">mice_meeting</field>
            <field name="tender_type_id" ref="tender_type_mice"/>
            <field name="sequence">10</field>
        </record>
        
        <record id="tender_sub_type_mice_incentive" model="ak.tender.sub.type">
            <field name="name">Motivasyon</field>
            <field name="code">mice_incentive</field>
            <field name="tender_type_id" ref="tender_type_mice"/>
            <field name="sequence">20</field>
        </record>
        
        <record id="tender_sub_type_mice_congress" model="ak.tender.sub.type">
            <field name="name">Kongre</field>
            <field name="code">mice_congress</field>
            <field name="tender_type_id" ref="tender_type_mice"/>
            <field name="sequence">30</field>
        </record>
        
        <record id="tender_sub_type_mice_event" model="ak.tender.sub.type">
            <field name="name">Etkinlik</field>
            <field name="code">mice_event</field>
            <field name="tender_type_id" ref="tender_type_mice"/>
            <field name="sequence">40</field>
        </record>
        
        <!-- Sigorta Alt Tipleri -->
        <record id="tender_sub_type_insurance_health" model="ak.tender.sub.type">
            <field name="name">Sağlık Sigortası</field>
            <field name="code">insurance_health</field>
            <field name="tender_type_id" ref="tender_type_insurance"/>
            <field name="sequence">10</field>
        </record>
        
        <record id="tender_sub_type_insurance_life" model="ak.tender.sub.type">
            <field name="name">Hayat Sigortası</field>
            <field name="code">insurance_life</field>
            <field name="tender_type_id" ref="tender_type_insurance"/>
            <field name="sequence">20</field>
        </record>
        
        <record id="tender_sub_type_insurance_vehicle" model="ak.tender.sub.type">
            <field name="name">Araç Sigortası</field>
            <field name="code">insurance_vehicle</field>
            <field name="tender_type_id" ref="tender_type_insurance"/>
            <field name="sequence">30</field>
        </record>
        
        <record id="tender_sub_type_insurance_property" model="ak.tender.sub.type">
            <field name="name">Mülk Sigortası</field>
            <field name="code">insurance_property</field>
            <field name="tender_type_id" ref="tender_type_insurance"/>
            <field name="sequence">40</field>
        </record>
    </data>
</odoo>
```

---

### 3. ak.tender.line.category - Satır Kategorileri (GÜNCELLEME)

```python
class AkTenderLineCategory(models.Model):
    _name = 'ak.tender.line.category'
    _description = 'İhale Satır Kategorileri'
    _order = 'tender_type_id, sequence, name'
    
    name = fields.Char('Kategori Adı', required=True, translate=True)
    code = fields.Char('Kod', required=True)
    tender_type_id = fields.Many2one('ak.tender.type', 'İhale Tipi',
                                     required=True, ondelete='cascade')
    sequence = fields.Integer('Sıra', default=10)
    active = fields.Boolean('Aktif', default=True)
    description = fields.Text('Açıklama', translate=True)
    icon = fields.Char('İkon', help='Font Awesome icon class')
    
    # İstatistikler
    line_count = fields.Integer('Satır Sayısı', compute='_compute_line_count')
    
    @api.depends('code')
    def _compute_line_count(self):
        for record in self:
            record.line_count = self.env['ak.tender.line'].search_count([
                ('line_category_id', '=', record.id)
            ])
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Kategori kodu benzersiz olmalıdır!'),
    ]
```

**Örnek Veriler:** (Önceki tasarımdaki gibi, sadece `tender_type` yerine `tender_type_id` ref kullanılacak)

---

## 💻 GÜNCEL MODEL TASARIMI

### 1. ak.tender - 9 Alan (Many2one ile)

```python
class AkTender(models.Model):
    _inherit = 'ak.tender'
    
    # ============ TEMEL ALAN DEĞİŞİKLİĞİ ============
    # Eski: tender_type = fields.Selection([...])
    # Yeni: Many2one
    
    tender_type_id = fields.Many2one(
        'ak.tender.type',
        string='İhale Tipi',
        required=True,
        default=lambda self: self.env.ref('ak_tender.tender_type_direct', raise_if_not_found=False),
        help='İhale tipi seçimi'
    )
    
    # Geriye uyumluluk için computed field (opsiyonel)
    tender_type = fields.Char(
        string='İhale Tipi (Kod)',
        related='tender_type_id.code',
        store=True,
        readonly=True,
        help='Geriye uyumluluk için ihale tipi kodu'
    )
    
    # ============ ORTAK ALANLAR (8 alan) ============
    
    # 1. Alt tip (Many2one - dinamik filtreleme)
    tender_sub_type_id = fields.Many2one(
        'ak.tender.sub.type',
        string='Alt Tip',
        domain="[('tender_type_id', '=', tender_type_id), ('active', '=', True)]",
        help='İhale alt tipi'
    )
    
    # 2-3. Hizmet/Poliçe tarihleri
    service_start_date = fields.Date('Hizmet/Poliçe Başlangıç',
        help='MICE: Etkinlik başlangıç | Sigorta: Poliçe başlangıç')
    service_end_date = fields.Date('Hizmet/Poliçe Bitiş',
        help='MICE: Etkinlik bitiş | Sigorta: Poliçe bitiş')
    
    # 4. Toplam kişi sayısı (computed)
    total_person_count = fields.Integer('Toplam Kişi',
                                        compute='_compute_total_person_count',
                                        store=True,
                                        help='MICE: Katılımcı | Sigorta: Sigortalı')
    
    # 5. Mevcut tedarikçi
    current_supplier_id = fields.Many2one('res.partner', 'Mevcut Tedarikçi',
                                         domain=[('supplier_rank', '>', 0)],
                                         help='MICE: Mevcut acente | Sigorta: Mevcut sigortacı')
    
    # 6. Mevcut toplam tutar
    current_total_amount = fields.Monetary('Mevcut Toplam Tutar',
                                          currency_field='currency_id',
                                          help='MICE: Mevcut bütçe | Sigorta: Mevcut prim')
    
    # 7. Sigorta spesifik: HP oranı
    current_hp_ratio = fields.Float('Mevcut HP Oranı (%)',
                                    help='Hasar/Prim oranı (sadece sigorta)')
    
    # 8. Sigorta spesifik: Sigortalı şirket
    insured_company_name = fields.Char('Sigortalı Şirket',
                                       help='Sigortalanan şirket (sadece sigorta)')
    
    # 9. MICE spesifik: VIP sayısı
    vip_person_count = fields.Integer('VIP Kişi Sayısı',
                                      help='VIP katılımcı (sadece MICE)')
    
    @api.depends('tender_lines.quantity')
    def _compute_total_person_count(self):
        """Toplam kişi sayısını hesapla"""
        for record in self:
            if record.tender_type_id.code in ('mice', 'insurance'):
                record.total_person_count = sum(
                    line.quantity for line in record.tender_lines 
                    if line.display_type == False
                )
            else:
                record.total_person_count = 0
    
    @api.onchange('tender_type_id')
    def _onchange_tender_type_clear_sub_type(self):
        """tender_type_id değiştiğinde tender_sub_type_id'yi temizle"""
        if self.tender_type_id:
            self.tender_sub_type_id = False
```

**Toplam: 9 alan** (1 Many2one + 1 related + 7 yeni)

---

### 2. ak.tender.line - 4 Alan (Değişmedi)

```python
class AkTenderLine(models.Model):
    _inherit = 'ak.tender.line'
    
    # 1. Kategori/Plan (Many2one - dinamik filtreleme)
    line_category_id = fields.Many2one(
        'ak.tender.line.category',
        string='Kategori/Plan',
        domain="[('tender_type_id', '=', parent.tender_type_id), ('active', '=', True)]",
        help='MICE: Hizmet kategorisi | Sigorta: Plan tipi'
    )
    
    # 2. Esnek JSON alan
    line_spec_data = fields.Json('Özel Veriler',
        help='MICE: oda tipi, yemek planı | Sigorta: teminat limitleri, katılım oranı')
    
    # 3. Özet bilgi
    line_summary = fields.Text('Özet Bilgi',
        help='MICE: Otel özellikleri | Sigorta: Teminat özeti')
    
    # 4. Computed helper
    is_special_tender_line = fields.Boolean(
        compute='_compute_is_special_tender_line',
        help='MICE veya Sigorta satırı mı?')
    
    @api.depends('tender_id.tender_type_id', 'line_category_id')
    def _compute_is_special_tender_line(self):
        """MICE veya Sigorta satırı olup olmadığını belirle"""
        for line in self:
            line.is_special_tender_line = (
                line.tender_id.tender_type_id.code in ('mice', 'insurance') and
                line.line_category_id
            )
    
    @api.onchange('tender_id.tender_type_id')
    def _onchange_tender_type_clear_category(self):
        """tender_type_id değiştiğinde line_category_id'yi temizle"""
        if self.tender_id.tender_type_id:
            self.line_category_id = False
```

---

### 3. purchase.order - 3 Alan (Değişmedi)

```python
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    offer_special_terms = fields.Text('Özel Koşullar ve Şartlar',
        help='MICE: İptal koşulları | Sigorta: Kar paylaşımı, kapsam dışı')
    offer_attachment_file = fields.Binary('Teklif Dosyası')
    offer_attachment_filename = fields.Char('Dosya Adı')
```

---

### 4. purchase.order.line - 2 Alan (Değişmedi)

```python
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    insurance_price_increase_rate = fields.Float('Artış Oranı (%)',
                                                 compute='_compute_insurance_price_increase',
                                                 store=True)
    line_offer_data = fields.Json('Teklif Detayları')
    
    @api.depends('price_unit', 'product_id', 'order_id.tender_id')
    def _compute_insurance_price_increase(self):
        for line in self:
            tender = line.order_id.tender_id
            if not tender or tender.tender_type_id.code != 'insurance':
                line.insurance_price_increase_rate = 0.0
                continue
            # ... (önceki mantık aynı)
```

---

## 📊 COMPLETE MODEL SAYISI

| Model | Tip | Alan Sayısı | Açıklama |
|-------|-----|-------------|----------|
| `ak.tender.type` | **YENİ** | 10 alan | İhale tipleri master |
| `ak.tender.sub.type` | **YENİ** | 8 alan | Alt tipler master |
| `ak.tender.line.category` | **YENİ** | 9 alan | Kategoriler master |
| `ak.tender` | Extension | 9 alan | Many2one ilişkiler |
| `ak.tender.line` | Extension | 4 alan | Many2one ilişkiler |
| `purchase.order` | Extension | 3 alan | Teklif alanları |
| `purchase.order.line` | Extension | 2 alan | Teklif satır alanları |
| **TOPLAM** | **3 yeni + 4 ext** | **45 alan** | |

---

## 🎨 VIEW TASARIMI

### Master Data - ak.tender.type

```xml
<!-- views/tender_type_views.xml -->
<record id="view_tender_type_tree" model="ir.ui.view">
    <field name="name">ak.tender.type.tree</field>
    <field name="model">ak.tender.type</field>
    <field name="arch" type="xml">
        <list>
            <field name="sequence" widget="handle"/>
            <field name="icon" widget="icon"/>
            <field name="name"/>
            <field name="code"/>
            <field name="tender_count"/>
            <field name="active"/>
        </list>
    </field>
</record>

<record id="view_tender_type_form" model="ir.ui.view">
    <field name="name">ak.tender.type.form</field>
    <field name="model">ak.tender.type</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_view_tenders" type="object" 
                        string="İhaleleri Görüntüle" class="oe_highlight"
                        attrs="{'invisible': [('tender_count', '=', 0)]}"/>
            </header>
            <sheet>
                <div class="oe_button_box" name="button_box">
                    <button name="toggle_active" type="object" 
                            class="oe_stat_button" icon="fa-archive">
                        <field name="active" widget="boolean_button" 
                               options='{"terminology": "archive"}'/>
                    </button>
                    <button name="action_view_tenders" type="object" 
                            class="oe_stat_button" icon="fa-file-text">
                        <field name="tender_count" widget="statinfo" 
                               string="İhaleler"/>
                    </button>
                </div>
                <group>
                    <group>
                        <field name="name"/>
                        <field name="code"/>
                    </group>
                    <group>
                        <field name="sequence"/>
                        <field name="icon"/>
                        <field name="color" widget="color_picker"/>
                    </group>
                </group>
                <group>
                    <field name="description"/>
                </group>
                <notebook>
                    <page string="Alt Tipler">
                        <field name="sub_type_ids">
                            <list editable="bottom">
                                <field name="sequence" widget="handle"/>
                                <field name="name"/>
                                <field name="code"/>
                                <field name="active"/>
                            </list>
                        </field>
                    </page>
                    <page string="Satır Kategorileri">
                        <field name="line_category_ids">
                            <list editable="bottom">
                                <field name="sequence" widget="handle"/>
                                <field name="icon" widget="icon"/>
                                <field name="name"/>
                                <field name="code"/>
                                <field name="active"/>
                            </list>
                        </field>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>

<record id="view_tender_type_kanban" model="ir.ui.view">
    <field name="name">ak.tender.type.kanban</field>
    <field name="model">ak.tender.type</field>
    <field name="arch" type="xml">
        <kanban>
            <field name="name"/>
            <field name="code"/>
            <field name="icon"/>
            <field name="color"/>
            <field name="tender_count"/>
            <templates>
                <t t-name="kanban-box">
                    <div t-attf-class="oe_kanban_color_#{kanban_getcolor(record.color.raw_value)} oe_kanban_card oe_kanban_global_click">
                        <div class="o_kanban_card_header">
                            <div class="o_kanban_card_header_title">
                                <div class="o_primary">
                                    <i t-att-class="record.icon.value"/> 
                                    <field name="name"/>
                                </div>
                                <div class="o_secondary">
                                    <field name="code"/>
                                </div>
                            </div>
                        </div>
                        <div class="o_kanban_card_body">
                            <field name="description"/>
                        </div>
                        <div class="o_kanban_card_footer">
                            <div class="o_kanban_record_bottom">
                                <div class="oe_kanban_bottom_left">
                                    <span><field name="tender_count"/> İhale</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </t>
            </templates>
        </kanban>
    </field>
</record>
```

### Menu Structure

```xml
<!-- views/menu.xml -->
<menuitem id="menu_tender_configuration" 
          name="Yapılandırma" 
          parent="menu_tender_root" 
          sequence="100"/>

<menuitem id="menu_tender_type" 
          name="İhale Tipleri" 
          parent="menu_tender_configuration" 
          action="action_tender_type" 
          sequence="5"/>

<menuitem id="menu_tender_sub_type" 
          name="İhale Alt Tipleri" 
          parent="menu_tender_configuration" 
          action="action_tender_sub_type" 
          sequence="10"/>

<menuitem id="menu_tender_line_category" 
          name="Satır Kategorileri" 
          parent="menu_tender_configuration" 
          action="action_tender_line_category" 
          sequence="20"/>
```

---

## 🚀 GELİŞTİRME PLANI

### Faz 1: Master Data Models (2 gün)
- [ ] `ak.tender.type` model + views + data
- [ ] `ak.tender.sub.type` model + views + data
- [ ] `ak.tender.line.category` model + views + data
- [ ] Security (ir.model.access.csv)
- [ ] Menu yapısı

### Faz 2: Core Extension (2 gün)
- [ ] `ak.tender` - tender_type_id migration
- [ ] `ak.tender` - 8 yeni alan
- [ ] `ak.tender.line` - 4 alan
- [ ] `purchase.order` - 3 alan
- [ ] `purchase.order.line` - 2 alan

### Faz 3: Migration Script (1 gün)
- [ ] Mevcut tender_type Selection → Many2one migration
- [ ] Data migration script
- [ ] Backward compatibility

### Faz 4: View Tasarımı (1 gün)
- [ ] Form view'lar güncelleme
- [ ] Domain'ler güncelleme
- [ ] Kanban view'lar

### Faz 5: Test (1 gün)
- [ ] Master data testleri
- [ ] Migration testleri
- [ ] MICE senaryoları
- [ ] Sigorta senaryoları

**TOPLAM: 7 gün** 🎉

---

## ✅ TAM MODEL TABANLI YAKLAŞIMIN AVANTAJLARI

### 1. Tam Esneklik
- ✅ Tüm tipler kullanıcı tarafından yönetilebilir
- ✅ Yeni ihale tipi eklemek kod değişikliği gerektirmez
- ✅ Alt tipler ve kategoriler dinamik

### 2. Hiyerarşik Yapı
- ✅ Tip → Alt Tip → Kategori ilişkisi
- ✅ One2many ilişkiler ile kolay yönetim
- ✅ Cascade delete ile veri bütünlüğü

### 3. İstatistikler ve Raporlama
- ✅ Her tip için ihale sayısı
- ✅ Kanban view ile görsel yönetim
- ✅ Renk ve ikon desteği

### 4. Çoklu Dil
- ✅ Tüm master data translate
- ✅ Global kullanım

### 5. Geriye Uyumluluk
- ✅ `tender_type` computed field
- ✅ Migration script
- ✅ Mevcut kod çalışmaya devam eder

---

## 🎯 SONUÇ

Bu complete model-based tasarım:

1. ✅ **3 yeni master data modeli**
2. ✅ **Tam dinamik ve yönetilebilir**
3. ✅ **Hiyerarşik yapı**
4. ✅ **18 extension alanı**
5. ✅ **7 günde tamamlanır**
6. ✅ **Geriye uyumlu**
7. ✅ **Çoklu dil desteği**

**Production-Ready Tasarım!** 🚀

---

**Tasarım Sahibi:** Roo AI Architect  
**Durum:** Complete - Production Ready  
**Yaklaşım:** Tam Model Tabanlı (3 master model + 18 extension alan, 7 gün)