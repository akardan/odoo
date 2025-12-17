# JSON Fields UI Design
## line_spec_data ve line_offer_data Kullanıcı Arayüzü

**Tarih:** 17.12.2025  
**Versiyon:** 1.0

---

## 🎯 PROBLEM

JSON alanları (`line_spec_data`, `line_offer_data`) için kullanıcı dostu arayüz gerekiyor:
- ✅ Kolay veri girişi
- ✅ Validasyon
- ✅ Tip-spesifik alanlar
- ✅ Görsel düzenleyici

---

## 💡 ÇÖZÜM SEÇENEKLERİ

### Seçenek 1: Widget ile JSON Editor (Basit)
### Seçenek 2: Dinamik Form Alanları (Orta)
### Seçenek 3: Wizard ile Yapılandırma (Gelişmiş)

---

## 📋 SEÇ

ENEK 1: WIDGET İLE JSON EDITOR

### Avantajlar:
- ✅ Hızlı implementasyon
- ✅ Odoo'nun built-in widget'ı
- ✅ Tüm JSON yapılarını destekler

### Dezavantajlar:
- ❌ Teknik kullanıcılar için
- ❌ Validasyon zor
- ❌ Kullanıcı dostu değil

### Implementasyon:

```xml
<!-- Basit JSON widget -->
<field name="line_spec_data" widget="ace" options="{'mode': 'json'}"/>
```

**Sonuç:** ❌ Kullanıcı dostu değil, önerilmez

---

## 📋 SEÇ

ENEK 2: DİNAMİK FORM ALANLARI (ÖNERİLEN)

### Yaklaşım:
JSON verilerini **computed field'lar** ile normal form alanlarına dönüştür.

### Avantajlar:
- ✅ Kullanıcı dostu
- ✅ Validasyon kolay
- ✅ Tip-spesifik alanlar
- ✅ Odoo standart widget'ları

### Implementasyon:

#### 1. Model Extension - Computed Fields

```python
class AkTenderLine(models.Model):
    _inherit = 'ak.tender.line'
    
    # JSON alan (backend storage)
    line_spec_data = fields.Json('Özel Veriler')
    
    # ============ MICE SPESİFİK COMPUTED FIELDS ============
    
    # Oda Tipi
    mice_room_type = fields.Selection([
        ('standard', 'Standard'),
        ('deluxe', 'Deluxe'),
        ('suite', 'Suite'),
        ('presidential', 'Presidential'),
    ], string='Oda Tipi', compute='_compute_mice_fields', inverse='_inverse_mice_fields', store=False)
    
    # Yemek Planı
    mice_meal_plan = fields.Selection([
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', 'Half Board'),
        ('fb', 'Full Board'),
        ('ai', 'All Inclusive'),
    ], string='Yemek Planı', compute='_compute_mice_fields', inverse='_inverse_mice_fields', store=False)
    
    # Manzara
    mice_view_type = fields.Selection([
        ('city', 'Şehir Manzarası'),
        ('sea', 'Deniz Manzarası'),
        ('mountain', 'Dağ Manzarası'),
        ('garden', 'Bahçe Manzarası'),
    ], string='Manzara', compute='_compute_mice_fields', inverse='_inverse_mice_fields', store=False)
    
    # Özel Hizmetler (Many2many tags gibi)
    mice_amenities = fields.Char('Özel Hizmetler', 
                                 compute='_compute_mice_fields', 
                                 inverse='_inverse_mice_fields', 
                                 store=False,
                                 help='Virgülle ayrılmış: WiFi, Pool, Spa, Butler')
    
    # ============ SİGORTA SPESİFİK COMPUTED FIELDS ============
    
    # Ayakta Tedavi Limiti
    insurance_outpatient_limit = fields.Float('Ayakta Tedavi Limiti (TL)',
                                              compute='_compute_insurance_fields',
                                              inverse='_inverse_insurance_fields',
                                              store=False)
    
    # Ayakta Katılım Oranı
    insurance_outpatient_participation = fields.Float('Ayakta Katılım Oranı (%)',
                                                      compute='_compute_insurance_fields',
                                                      inverse='_inverse_insurance_fields',
                                                      store=False)
    
    # Yatarak Tedavi Limiti
    insurance_inpatient_limit = fields.Char('Yatarak Tedavi Limiti',
                                            compute='_compute_insurance_fields',
                                            inverse='_inverse_insurance_fields',
                                            store=False,
                                            help='Tutar veya "unlimited"')
    
    # Doğum Limiti
    insurance_maternity_limit = fields.Float('Doğum Limiti (TL)',
                                            compute='_compute_insurance_fields',
                                            inverse='_inverse_insurance_fields',
                                            store=False)
    
    # Diş Limiti
    insurance_dental_limit = fields.Float('Diş Tedavi Limiti (TL)',
                                         compute='_compute_insurance_fields',
                                         inverse='_inverse_insurance_fields',
                                         store=False)
    
    # Göz Limiti
    insurance_optical_limit = fields.Float('Göz Tedavi Limiti (TL)',
                                          compute='_compute_insurance_fields',
                                          inverse='_inverse_insurance_fields',
                                          store=False)
    
    # ============ COMPUTE METHODS ============
    
    @api.depends('line_spec_data')
    def _compute_mice_fields(self):
        """JSON'dan MICE alanlarını oku"""
        for line in self:
            if line.line_spec_data and isinstance(line.line_spec_data, dict):
                data = line.line_spec_data
                line.mice_room_type = data.get('room_type', False)
                line.mice_meal_plan = data.get('meal_plan', False)
                line.mice_view_type = data.get('view', False)
                line.mice_amenities = ', '.join(data.get('amenities', []))
            else:
                line.mice_room_type = False
                line.mice_meal_plan = False
                line.mice_view_type = False
                line.mice_amenities = False
    
    def _inverse_mice_fields(self):
        """MICE alanlarını JSON'a yaz"""
        for line in self:
            if not line.line_spec_data:
                line.line_spec_data = {}
            
            data = line.line_spec_data.copy() if isinstance(line.line_spec_data, dict) else {}
            
            if line.mice_room_type:
                data['room_type'] = line.mice_room_type
            if line.mice_meal_plan:
                data['meal_plan'] = line.mice_meal_plan
            if line.mice_view_type:
                data['view'] = line.mice_view_type
            if line.mice_amenities:
                data['amenities'] = [a.strip() for a in line.mice_amenities.split(',') if a.strip()]
            
            line.line_spec_data = data
    
    @api.depends('line_spec_data')
    def _compute_insurance_fields(self):
        """JSON'dan Sigorta alanlarını oku"""
        for line in self:
            if line.line_spec_data and isinstance(line.line_spec_data, dict):
                data = line.line_spec_data
                line.insurance_outpatient_limit = data.get('outpatient_limit', 0.0)
                line.insurance_outpatient_participation = data.get('outpatient_participation', 0.0)
                line.insurance_inpatient_limit = str(data.get('inpatient_limit', ''))
                line.insurance_maternity_limit = data.get('maternity_limit', 0.0)
                line.insurance_dental_limit = data.get('dental_limit', 0.0)
                line.insurance_optical_limit = data.get('optical_limit', 0.0)
            else:
                line.insurance_outpatient_limit = 0.0
                line.insurance_outpatient_participation = 0.0
                line.insurance_inpatient_limit = ''
                line.insurance_maternity_limit = 0.0
                line.insurance_dental_limit = 0.0
                line.insurance_optical_limit = 0.0
    
    def _inverse_insurance_fields(self):
        """Sigorta alanlarını JSON'a yaz"""
        for line in self:
            if not line.line_spec_data:
                line.line_spec_data = {}
            
            data = line.line_spec_data.copy() if isinstance(line.line_spec_data, dict) else {}
            
            data['outpatient_limit'] = line.insurance_outpatient_limit
            data['outpatient_participation'] = line.insurance_outpatient_participation
            data['inpatient_limit'] = line.insurance_inpatient_limit if line.insurance_inpatient_limit else 0
            data['maternity_limit'] = line.insurance_maternity_limit
            data['dental_limit'] = line.insurance_dental_limit
            data['optical_limit'] = line.insurance_optical_limit
            
            line.line_spec_data = data
```

#### 2. View Design - Dinamik Alanlar

```xml
<!-- views/tender_views.xml -->
<record id="view_tender_form_mice_insurance" model="ir.ui.view">
    <field name="name">ak.tender.form.mice.insurance</field>
    <field name="model">ak.tender</field>
    <field name="inherit_id" ref="ak_tender.view_tender_form"/>
    <field name="arch" type="xml">
        
        <!-- MICE/Sigorta Detayları Sekmesi -->
        <xpath expr="//notebook" position="inside">
            <page string="MICE/Sigorta Detayları" 
                  attrs="{'invisible': [('tender_type_id.code', 'not in', ['mice', 'insurance'])]}">
                
                <group string="Kategoriler / Planlar">
                    <field name="tender_lines" nolabel="1">
                        <tree editable="bottom">
                            <field name="display_type" invisible="1"/>
                            <field name="tender_id" invisible="1"/>
                            <field name="line_category_id"
                                   attrs="{'invisible': [('display_type', '!=', False)]}"/>
                            <field name="product_id"
                                   attrs="{'invisible': [('display_type', '!=', False)]}"/>
                            <field name="name"/>
                            <field name="quantity"
                                   attrs="{'invisible': [('display_type', '!=', False)]}"/>
                            <field name="days" 
                                   attrs="{'invisible': ['|', ('display_type', '!=', False), 
                                                        ('tender_id.tender_type_id.code', '!=', 'mice')]}"/>
                            <field name="target_price"
                                   attrs="{'invisible': [('display_type', '!=', False)]}"/>
                        </tree>
                        
                        <!-- Form view ile detaylı düzenleme -->
                        <form>
                            <sheet>
                                <group>
                                    <group>
                                        <field name="line_category_id"/>
                                        <field name="product_id"/>
                                        <field name="quantity"/>
                                        <field name="days" 
                                               attrs="{'invisible': [('tender_id.tender_type_id.code', '!=', 'mice')]}"/>
                                        <field name="target_price"/>
                                    </group>
                                </group>
                                
                                <notebook>
                                    <!-- MICE Özel Alanları -->
                                    <page string="MICE Detayları" 
                                          attrs="{'invisible': [('tender_id.tender_type_id.code', '!=', 'mice')]}">
                                        <group>
                                            <group>
                                                <field name="mice_room_type"/>
                                                <field name="mice_meal_plan"/>
                                            </group>
                                            <group>
                                                <field name="mice_view_type"/>
                                                <field name="mice_amenities" 
                                                       placeholder="WiFi, Pool, Spa, Butler"/>
                                            </group>
                                        </group>
                                    </page>
                                    
                                    <!-- Sigorta Özel Alanları -->
                                    <page string="Teminat Detayları" 
                                          attrs="{'invisible': [('tender_id.tender_type_id.code', '!=', 'insurance')]}">
                                        <group string="Ayakta Tedavi">
                                            <field name="insurance_outpatient_limit"/>
                                            <field name="insurance_outpatient_participation"/>
                                        </group>
                                        <group string="Yatarak Tedavi">
                                            <field name="insurance_inpatient_limit" 
                                                   placeholder="Tutar veya 'unlimited'"/>
                                        </group>
                                        <group string="Diğer Teminatlar">
                                            <field name="insurance_maternity_limit"/>
                                            <field name="insurance_dental_limit"/>
                                            <field name="insurance_optical_limit"/>
                                        </group>
                                    </page>
                                    
                                    <!-- Özet Bilgi -->
                                    <page string="Özet">
                                        <field name="line_summary" 
                                               placeholder="Kullanıcı dostu özet bilgi..."/>
                                    </page>
                                </notebook>
                            </sheet>
                        </form>
                    </field>
                </group>
            </page>
        </xpath>
        
    </field>
</record>
```

#### 3. Otomatik Özet Oluşturma

```python
class AkTenderLine(models.Model):
    _inherit = 'ak.tender.line'
    
    @api.onchange('mice_room_type', 'mice_meal_plan', 'mice_view_type', 'mice_amenities')
    def _onchange_mice_fields_update_summary(self):
        """MICE alanları değiştiğinde özet güncelle"""
        if self.tender_id.tender_type_id.code == 'mice':
            summary_parts = []
            
            if self.mice_room_type:
                room_dict = dict(self._fields['mice_room_type'].selection)
                summary_parts.append(room_dict.get(self.mice_room_type, ''))
            
            if self.mice_meal_plan:
                meal_dict = dict(self._fields['mice_meal_plan'].selection)
                summary_parts.append(meal_dict.get(self.mice_meal_plan, ''))
            
            if self.mice_view_type:
                view_dict = dict(self._fields['mice_view_type'].selection)
                summary_parts.append(view_dict.get(self.mice_view_type, ''))
            
            if self.mice_amenities:
                summary_parts.append(f"Özellikler: {self.mice_amenities}")
            
            self.line_summary = ', '.join(summary_parts)
    
    @api.onchange('insurance_outpatient_limit', 'insurance_inpatient_limit', 'insurance_maternity_limit')
    def _onchange_insurance_fields_update_summary(self):
        """Sigorta alanları değiştiğinde özet güncelle"""
        if self.tender_id.tender_type_id.code == 'insurance':
            summary_parts = []
            
            if self.insurance_outpatient_limit:
                summary_parts.append(f"Ayakta: {self.insurance_outpatient_limit:,.0f} TL")
            
            if self.insurance_inpatient_limit:
                if self.insurance_inpatient_limit.lower() == 'unlimited':
                    summary_parts.append("Yatarak: Limitsiz")
                else:
                    try:
                        limit = float(self.insurance_inpatient_limit)
                        summary_parts.append(f"Yatarak: {limit:,.0f} TL")
                    except:
                        summary_parts.append(f"Yatarak: {self.insurance_inpatient_limit}")
            
            if self.insurance_maternity_limit:
                summary_parts.append(f"Doğum: {self.insurance_maternity_limit:,.0f} TL")
            
            self.line_summary = ', '.join(summary_parts)
```

---

## 📋 SEÇ

ENEK 3: WIZARD İLE YAPILANDIRMA

### Kullanım Senaryosu:
Karmaşık yapılandırmalar için wizard kullan.

### Implementasyon:

```python
class TenderLineConfigWizard(models.TransientModel):
    _name = 'tender.line.config.wizard'
    _description = 'İhale Satırı Yapılandırma Sihirbazı'
    
    tender_line_id = fields.Many2one('ak.tender.line', required=True)
    tender_type_code = fields.Char(related='tender_line_id.tender_id.tender_type_id.code')
    
    # MICE alanları
    mice_room_type = fields.Selection([...])
    mice_meal_plan = fields.Selection([...])
    # ... diğer alanlar
    
    # Sigorta alanları
    insurance_outpatient_limit = fields.Float()
    # ... diğer alanlar
    
    def action_apply(self):
        """Yapılandırmayı uygula"""
        self.ensure_one()
        
        if self.tender_type_code == 'mice':
            self.tender_line_id.write({
                'line_spec_data': {
                    'room_type': self.mice_room_type,
                    'meal_plan': self.mice_meal_plan,
                    # ...
                }
            })
        elif self.tender_type_code == 'insurance':
            self.tender_line_id.write({
                'line_spec_data': {
                    'outpatient_limit': self.insurance_outpatient_limit,
                    # ...
                }
            })
        
        return {'type': 'ir.actions.act_window_close'}
```

```xml
<!-- Wizard button -->
<button name="action_open_config_wizard" 
        type="object" 
        string="Detaylı Yapılandırma" 
        icon="fa-cog"
        attrs="{'invisible': [('tender_id.tender_type_id.code', 'not in', ['mice', 'insurance'])]}"/>
```

---

## 🎯 ÖNERİLEN YAKLAŞIM

### Hibrit Çözüm:

1. **Seçenek 2 (Dinamik Form Alanları)** - Ana yöntem
   - Tree view'da hızlı giriş
   - Form view'da detaylı düzenleme
   - Otomatik özet oluşturma

2. **Seçenek 3 (Wizard)** - Opsiyonel
   - Karmaşık yapılandırmalar için
   - Toplu düzenleme için
   - İleri seviye kullanıcılar için

3. **JSON Debug View** - Geliştirici modu
   - Sadece debug mode'da görünür
   - Ham JSON düzenleme
   - Sorun giderme için

---

## 📊 KARŞILAŞTIRMA

| Özellik | Widget | Dinamik Form | Wizard |
|---------|--------|--------------|--------|
| Kullanıcı Dostu | ❌ | ✅ | ✅ |
| Hızlı Giriş | ❌ | ✅ | ❌ |
| Validasyon | ❌ | ✅ | ✅ |
| Esneklik | ✅ | ⚠️ | ⚠️ |
| Geliştirme Süresi | 1 saat | 1 gün | 2 gün |
| Bakım | Kolay | Orta | Zor |

**Önerilen:** Dinamik Form Alanları ✅

---

## 🚀 IMPLEMENTASYON PLANI

### Faz 1: Computed Fields (4 saat)
- [ ] MICE computed fields (6 alan)
- [ ] Sigorta computed fields (6 alan)
- [ ] Compute ve inverse methodlar

### Faz 2: View Tasarımı (4 saat)
- [ ] Tree view inline editing
- [ ] Form view notebook pages
- [ ] Attrs ve görünürlük

### Faz 3: Otomatik Özet (2 saat)
- [ ] Onchange methodlar
- [ ] Özet formatla

ma
- [ ] Test senaryoları

### Faz 4: Wizard (Opsiyonel) (4 saat)
- [ ] Wizard model
- [ ] Wizard view
- [ ] Action button

**TOPLAM: 1 gün (wizard hariç)**

---

## ✅ SONUÇ

JSON alanları için **Dinamik Form Alanları** yaklaşımı:

1. ✅ **Kullanıcı dostu**
2. ✅ **Hızlı veri girişi**
3. ✅ **Otomatik validasyon**
4. ✅ **Tip-spesifik alanlar**
5. ✅ **Otomatik özet**
6. ✅ **1 günde implementasyon**

**Production-Ready Çözüm!** 🚀

---

**Tasarım Sahibi:** Roo AI Architect  
**Durum:** Onaya hazır  
**Önerilen Yaklaşım:** Dinamik Form Alanları (Computed Fields)