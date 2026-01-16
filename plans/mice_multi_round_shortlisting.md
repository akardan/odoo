# MICE Çok Turlu İhale ve Senaryo Bazlı Kısa Liste

## İhtiyaç

MICE ihalelerinde **tedarikçi bağımsız**, **senaryo bazlı** değerlendirme ve çok turlu teklif alma:

### İş Akışı

1. **Tur 1:** Tüm senaryolar için teklifler toplanır
2. **Değerlendirme:** Her senaryo BAĞIMSIZ olarak incelenir (tedarikçi karıştırılmadan)
3. **Kısa Liste:** Beğenilen senaryolar işaretlenir
4. **Tur 2:** Sadece kısa listedeki senaryolar için yeni teklif turu
5. **Rekabet:** Tedarikçiler fiyat revizyonu yapar
6. **(Opsiyonel) Tur 3, 4...:** Süreç tekrarlanabilir

## Klasik Örnek Akış

### İlk Durum (Tur 1)

```
İHALE: Yıllık Satış Toplantısı 2026

SENARYOLAR:
1. Chamada Prestige (Antalya) - HB
2. Chamada Prestige (Antalya) - FB
3. Flexus Hotel (Antalya) - HB
4. Flexus Hotel (Antalya) - AI
5. Les Ambassadeurs (Kıbrıs) - AI
6. Rixos Downtown (Antalya) - HB [Tedarikçi karşı teklifi]
7. Titanic Beach (Belek) - AI [Tedarikçi karşı teklifi]

Davet Edilen Tedarikçiler: 8 firma
Teklif Süresi: 10 gün
```

### Tur 1 Sonuçları

Alıcı her senaryoyu bağımsız olarak değerlendirir:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 1: Chamada Prestige (Antalya) - HB                              │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ Tedarikçi        │ Fiyat         │ NPV           │ Değerlendirme        │
├──────────────────┼───────────────┼───────────────┼──────────────────────┤
│ ABC Turizm       │ 32,000€ (60g) │ 30,800€       │ ⭐ Makul             │
│ XYZ Otel Grup    │ 34,500€ (30g) │ 34,150€       │ ❌ Yüksek            │
│ DEF Tourism      │ 31,500€ (90g) │ 29,200€ ⭐    │ ⭐ En düşük NPV      │
│ GHI Travel       │ Teklif yok    │ -             │ -                    │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ✅ KISA LİSTEYE ALINSIN                                          │
│ NOT: DEF Tourism ve ABC Turizm rekabetçi, 2. tura alalım                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 2: Chamada Prestige (Antalya) - FB                              │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ ABC Turizm       │ 39,500€       │ 38,000€       │ Makul                │
│ XYZ Otel Grup    │ 41,000€       │ 40,600€       │ Yüksek               │
│ DEF Tourism      │ 38,000€       │ 38,000€ ⭐    │ İyi                  │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ❌ ELENDİ                                                         │
│ NOT: HB versiyonu daha avantajlı, FB'ye gerek yok                       │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 3: Flexus Hotel (Antalya) - HB                                  │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ ABC Turizm       │ Teklif yok    │ -             │ -                    │
│ XYZ Otel Grup    │ 28,500€       │ 27,450€ ⭐    │ ⭐ Çok iyi           │
│ DEF Tourism      │ 29,000€       │ 28,710€       │ İyi                  │
│ JKL Hotels       │ 27,800€       │ 27,800€ ⭐    │ ⭐ En düşük          │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ✅ KISA LİSTEYE ALINSIN                                          │
│ NOT: 3 rekabetçi teklif var, fiyat daha düşebilir                       │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 5: Les Ambassadeurs (Kıbrıs) - AI                               │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ ABC Turizm       │ 48,000€       │ 46,200€       │ Çok yüksek           │
│ MNO Cyprus       │ 52,000€       │ 51,480€       │ Çok yüksek           │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ❌ ELENDİ                                                         │
│ NOT: Bütçe aşımı, başka alternatifler daha iyi                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 6: Rixos Downtown (Antalya) - HB [Tedarikçi karşı teklifi]     │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ ABC Turizm       │ 30,840€ ⭐    │ 29,700€       │ ⭐ Çok iyi           │
│ Diğerleri        │ Teklif yok    │ -             │ (Henüz açılmadı)     │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ✅ KISA LİSTEYE ALINSIN                                          │
│ NOT: İlginç alternatif, diğer tedarikçilere de açalım                   │
└──────────────────────────────────────────────────────────────────────────┘

ÖZET:
- Toplam 7 senaryo değerlendirildi
- ✅ Kısa Liste: 3 senaryo (Senaryo 1, 3, 6)
- ❌ Elendi: 4 senaryo
```

### Tur 2 Başlatma

Alıcı şu aksiyonu alacak:

```
[📋 İkinci Tur Başlat]

Kısa Liste Senaryolar:
  ✓ Senaryo 1: Chamada Prestige - HB
  ✓ Senaryo 3: Flexus Hotel - HB
  ✓ Senaryo 6: Rixos Downtown - HB

İkinci tura davet edilecek tedarikçiler:
  • Tüm davetli tedarikçiler (8 firma) ← Default
  ☐ Sadece Tur 1'de teklif verenler (6 firma)
  ☐ Sadece kısa listedeki senaryolara teklif verenler (4 firma)

Teklif süresi: [5] gün

Tedarikçilere mesaj:
┌──────────────────────────────────────────────────────────────────────────┐
│ Sayın Tedarikçimiz,                                                      │
│                                                                          │
│ İlk tur teklifleriniz için teşekkür ederiz. Aşağıdaki senaryolar        │
│ kısa listeye alınmıştır. İyileştirilmiş tekliflerinizi bekliyoruz:      │
│                                                                          │
│ 1. Chamada Prestige (Antalya) - HB                                      │
│ 2. Flexus Hotel (Antalya) - HB                                          │
│ 3. Rixos Downtown (Antalya) - HB                                        │
│                                                                          │
│ Lütfen en iyi fiyatlarınızı sunun.                                      │
│                                                                          │
│ Son teklif tarihi: 10 Aralık 2025, 17:00                                │
└──────────────────────────────────────────────────────────────────────────┘

[🚀 Tur 2'yi Başlat] [❌ İptal]
```

### Tur 2 Sonuçları

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 1: Chamada Prestige (Antalya) - HB - TUR 2                      │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ Tedarikçi        │ Tur 1         │ Tur 2 ⭐      │ İyileştirme          │
├──────────────────┼───────────────┼───────────────┼──────────────────────┤
│ ABC Turizm       │ 32,000€       │ 30,500€       │ ⬇️ -4.7% (1,500€)   │
│ DEF Tourism      │ 31,500€       │ 29,800€ ⭐    │ ⬇️ -5.4% (1,700€)   │
│ XYZ Otel Grup    │ 34,500€       │ 31,200€       │ ⬇️ -9.6% (3,300€)   │
│ JKL Hotels       │ Teklif yok    │ 30,000€ 🆕    │ Yeni katılımcı!      │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ✅ DEF Tourism ile anlaş (29,800€)                               │
│ Tasarruf: İlk hedeften (35,000€) %14.9 düşük!                           │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO 3: Flexus Hotel (Antalya) - HB - TUR 2                          │
├──────────────────┬───────────────┬───────────────┬──────────────────────┤
│ XYZ Otel Grup    │ 28,500€       │ 27,200€       │ ⬇️ -4.6%            │
│ DEF Tourism      │ 29,000€       │ 28,500€       │ ⬇️ -1.7%            │
│ JKL Hotels       │ 27,800€       │ 26,900€ ⭐    │ ⬇️ -3.2%            │
├──────────────────┴───────────────┴───────────────┴──────────────────────┤
│ KARAR: ✅ JKL Hotels ile anlaş (26,900€)                                │
└──────────────────────────────────────────────────────────────────────────┘
```

**Sonuç:** Çok turlu sistem sayesinde:
- Senaryo 1: %4.7-9.6 arası fiyat iyileştirmesi
- Senaryo 3: %1.7-4.6 arası fiyat iyileştirmesi
- Yeni tedarikçiler katıldı (JKL Hotels)
- Toplam tasarruf: ~5,000€

## Veri Modeli Güncellemeleri

### `ak.tender.scenario` - Kısa Liste Alanları

```python
class AkTenderScenario(models.Model):
    _name = 'ak.tender.scenario'
    # ... mevcut alanlar ...
    
    # ===== KISA LİSTE MEKANİZMASI =====
    
    is_shortlisted = fields.Boolean(
        string='Kısa Listede',
        default=False,
        help='Bu senaryo sonraki turlarda değerlendirilecek mi?'
    )
    
    shortlist_round = fields.Integer(
        string='Kısa Listeye Alınma Turu',
        help='Hangi turda kısa listeye alındı?'
    )
    
    shortlist_date = fields.Datetime(
        string='Kısa Liste Tarihi',
        readonly=True
    )
    
    shortlist_by = fields.Many2one(
        'res.users',
        string='Kısa Listeye Ekleyen',
        readonly=True
    )
    
    shortlist_notes = fields.Text(
        string='Kısa Liste Notları',
        help='Bu senaryonun neden kısa listeye alındığı'
    )
    
    elimination_reason = fields.Text(
        string='Eleme Gerekçesi',
        help='Bu senaryo neden elenmiş?'
    )
    
    # Senaryo durumu
    scenario_status = fields.Selection([
        ('active', 'Aktif - Teklif Alınıyor'),
        ('shortlisted', 'Kısa Listede'),
        ('eliminated', 'Elendi'),
        ('awarded', 'Kazanan')
    ], default='active', string='Senaryo Durumu', required=True)
    
    # Her turda en iyi teklif (referans için)
    best_offer_round_1 = fields.Monetary(
        compute='_compute_best_offers',
        string='Tur 1 En İyi Teklif',
        store=True
    )
    
    best_offer_round_2 = fields.Monetary(
        compute='_compute_best_offers',
        string='Tur 2 En İyi Teklif',
        store=True
    )
    
    improvement_percentage = fields.Float(
        compute='_compute_improvement',
        string='İyileştirme %',
        help='Tur 2 vs Tur 1 fiyat iyileştirmesi',
        store=True
    )
    
    @api.depends('tender_id.purchase_order_ids.order_line.tender_line_id.scenario_id')
    def _compute_best_offers(self):
        """Her tur için en düşük teklifi hesapla"""
        for scenario in self:
            # Purchase order lines filtrele
            po_lines = self.env['purchase.order.line'].search([
                ('tender_line_id.scenario_id', '=', scenario.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])
            
            # Tur bazlı grupla
            round_1_lines = po_lines.filtered(lambda l: l.order_id.tender_round == 1)
            round_2_lines = po_lines.filtered(lambda l: l.order_id.tender_round == 2)
            
            # En düşük fiyatları bul (NPV bazlı)
            if round_1_lines:
                scenario.best_offer_round_1 = min(round_1_lines.mapped('price_subtotal'))
            
            if round_2_lines:
                scenario.best_offer_round_2 = min(round_2_lines.mapped('price_subtotal'))
    
    @api.depends('best_offer_round_1', 'best_offer_round_2')
    def _compute_improvement(self):
        """Tur 2'deki iyileştirme yüzdesini hesapla"""
        for scenario in self:
            if scenario.best_offer_round_1 and scenario.best_offer_round_2:
                improvement = (scenario.best_offer_round_1 - scenario.best_offer_round_2)
                scenario.improvement_percentage = (improvement / scenario.best_offer_round_1) * 100
            else:
                scenario.improvement_percentage = 0.0
    
    def action_add_to_shortlist(self):
        """Senaryoyu kısa listeye ekle"""
        self.ensure_one()
        self.write({
            'is_shortlisted': True,
            'scenario_status': 'shortlisted',
            'shortlist_round': self.tender_id.tender_round,
            'shortlist_date': fields.Datetime.now(),
            'shortlist_by': self.env.user.id
        })
        return True
    
    def action_eliminate_scenario(self):
        """Senaryoyu elenle"""
        self.ensure_one()
        return {
            'name': 'Senaryo Eleme',
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.eliminate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scenario_id': self.id}
        }
```

### `ak.tender` - Çok Tur Mekanizması

```python
class AkTender(models.Model):
    _inherit = 'ak.tender'
    
    # tender_round zaten var mevcut sistemde
    
    # Senaryo istatistikleri
    total_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string='Toplam Senaryo'
    )
    
    shortlisted_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string='Kısa Liste Senaryolar'
    )
    
    eliminated_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string='Elenen Senaryolar'
    )
    
    @api.depends('scenario_ids.scenario_status')
    def _compute_scenario_stats(self):
        for tender in self:
            tender.total_scenarios = len(tender.scenario_ids)
            tender.shortlisted_scenarios = len(
                tender.scenario_ids.filtered(lambda s: s.is_shortlisted)
            )
            tender.eliminated_scenarios = len(
                tender.scenario_ids.filtered(lambda s: s.scenario_status == 'eliminated')
            )
    
    def action_start_next_round(self):
        """Sonraki turu başlat (sadece kısa listedeki senaryolar için)"""
        self.ensure_one()
        
        shortlisted = self.scenario_ids.filtered(lambda s: s.is_shortlisted)
        
        if not shortlisted:
            raise UserError("Kısa listeye alınmış senaryo yok!")
        
        # Wizard aç
        return {
            'name': 'Yeni Tur Başlat',
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.next.round.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
                'default_next_round': self.tender_round + 1,
                'default_shortlisted_scenario_ids': shortlisted.ids
            }
        }
```

## UI Tasarımları

### Senaryo Değerlendirme Ekranı

```
┌──────────────────────────────────────────────────────────────────────────┐
│ İHALE: Yıllık Satış Toplantısı 2026 - TUR 1 DEĞERLENDİRME              │
│ Toplam: 7 senaryo | Kısa Liste: 0 | Elendi: 0                           │
└──────────────────────────────────────────────────────────────────────────┘

[🔍 Tümü] [✅ Kısa Liste] [❌ Elenenler] [🏆 Kazananlar]

┌─────┬──────────────────────────┬──────────┬────────────┬────────────────┐
│ ○/✓ │ Senaryo                  │ Teklifler│ En İyi NPV │ Aksiyon        │
├─────┼──────────────────────────┼──────────┼────────────┼────────────────┤
│ ☐   │ Chamada Prestige - HB    │ 3/8      │ 29,200€    │ [✅][❌][📊]  │
│     │ Antalya, 2-4 Kas         │          │ DEF Tourism│                │
│     │                          │          │            │                │
├─────┼──────────────────────────┼──────────┼────────────┼────────────────┤
│ ☐   │ Chamada Prestige - FB    │ 3/8      │ 38,000€    │ [✅][❌][📊]  │
│     │ Antalya, 2-4 Kas         │          │ DEF Tourism│                │
│     │                          │          │ ⚠️ HB daha iyi│             │
├─────┼──────────────────────────┼──────────┼────────────┼────────────────┤
│ ☐   │ Flexus Hotel - HB        │ 3/8      │ 27,450€ ⭐ │ [✅][❌][📊]  │
│     │ Antalya, 2-4 Kas         │          │ XYZ Otel   │                │
│     │                          │          │            │                │
├─────┼──────────────────────────┼──────────┼────────────┼────────────────┤
│ ☐   │ Les Ambassadeurs - AI    │ 2/8      │ 46,200€    │ [✅][❌][📊]  │
│     │ Kıbrıs, 16-18 Kas        │          │ ABC Turizm │                │
│     │                          │          │ ⚠️ Bütçe aşımı│             │
└─────┴──────────────────────────┴──────────┴────────────┴────────────────┘

[✅] = Kısa Listeye Ekle
[❌] = Elenle
[📊] = Detaylı Karşılaştır

TOPLU İŞLEM:
[☑ Seçilenleri Kısa Listeye Ekle] [☑ Seçilenleri Elenle]

Durum: 0 senaryo seçili

─────────────────────────────────────────────────────────────────────────────

Kısa Liste tamamlandıktan sonra:

[🚀 İkinci Turu Başlat]
```

### Çok Turlu Karşılaştırma Görünümü

```
┌──────────────────────────────────────────────────────────────────────────┐
│ SENARYO: Chamada Prestige (Antalya) - HB                                │
│ Durum: ✅ Kısa Listede | Tur: 2/2                                       │
└──────────────────────────────────────────────────────────────────────────┘

TUR BAZLI KARŞILAŞTIRMA:

| Tedarikçi     | Tur 1        | Tur 2 ⭐     | Değişim      | Kazanan |
|---------------|--------------|--------------|--------------|---------|
| ABC Turizm    | 32,000€      | 30,500€      | ⬇️ -4.7%    | ✅ ❌   |
|               | (60 gün NPV) | (60 gün NPV) |              |         |
|---------------|--------------|--------------|--------------|---------|
| DEF Tourism   | 31,500€      | 29,800€ ⭐   | ⬇️ -5.4%    | ✅ ✅   |
|               | (90 gün NPV) | (90 gün NPV) |              |         |
|---------------|--------------|--------------|--------------|---------|
| XYZ Otel Grup | 34,500€      | 31,200€      | ⬇️ -9.6%    | ✅ ❌   |
|               | (30 gün NPV) | (30 gün NPV) | En çok düşen |         |
|---------------|--------------|--------------|--------------|---------|
| JKL Hotels    | -            | 30,000€ 🆕   | Yeni katılım | ✅ ❌   |
|               |              | (Peşin)      |              |         |

📊 İSTATİSTİKLER:
- Ortalama fiyat düşüş: %6.6
- En iyi iyileştirme: XYZ Otel Grup (-9.6%)
- Yeni katılımcı: 1 firma

💰 TASARRUF:
- Hedef fiyat: 35,000€
- Tur 1 en iyi: 31,500€ (DEF) → %10 tasarruf
- Tur 2 en iyi: 29,800€ (DEF) → %14.9 tasarruf
- Ek kazanç (Tur 2): 1,700€

[🏆 DEF Tourism'u Kazanan İlan Et]
```

## Wizard: Yeni Tur Başlatma

```python
class AkTenderNextRoundWizard(models.TransientModel):
    _name = 'ak.tender.next.round.wizard'
    _description = 'Yeni İhale Turu Başlat'
    
    tender_id = fields.Many2one('ak.tender', required=True)
    next_round = fields.Integer(string='Yeni Tur', required=True)
    
    shortlisted_scenario_ids = fields.Many2many(
        'ak.tender.scenario',
        string='Kısa Listedeki Senaryolar',
        readonly=True
    )
    
    invitation_mode = fields.Selection([
        ('all', 'Tüm Davetli Tedarikçiler'),
        ('previous_bidders', 'Önceki Turda Teklif Verenler'),
        ('shortlist_bidders', 'Kısa Listedeki Senaryolara Teklif Verenler'),
        ('custom', 'Özel Seçim')
    ], default='all', required=True, string='Davet Modu')
    
    invited_partners = fields.Many2many(
        'res.partner',
        string='Davet Edilecekler',
        compute='_compute_invited_partners',
        readonly=False,
        store=True
    )
    
    deadline_days = fields.Integer(string='Teklif Süresi (Gün)', default=5)
    
    message_to_suppliers = fields.Html(
        string='Tedarikçilere Mesaj',
        default=lambda self: self._default_message()
    )
    
    @api.depends('invitation_mode')
    def _compute_invited_partners(self):
        for wizard in self:
            if wizard.invitation_mode == 'all':
                wizard.invited_partners = wizard.tender_id.invited_partners
            elif wizard.invitation_mode == 'previous_bidders':
                # Önceki turda teklif verenleri bul
                po_ids = self.env['purchase.order'].search([
                    ('tender_id', '=', wizard.tender_id.id),
                    ('tender_round', '=', wizard.next_round - 1)
                ])
                wizard.invited_partners = po_ids.mapped('partner_id')
            elif wizard.invitation_mode == 'shortlist_bidders':
                # Kısa listedeki senaryolara teklif verenleri bul
                po_lines = self.env['purchase.order.line'].search([
                    ('tender_line_id.scenario_id', 'in', wizard.shortlisted_scenario_ids.ids)
                ])
                wizard.invited_partners = po_lines.mapped('order_id.partner_id')
    
    def _default_message(self):
        return """
        <p>Sayın Tedarikçimiz,</p>
        <p>İlk tur teklifleriniz için teşekkür ederiz. Aşağıdaki senaryolar 
        kısa listeye alınmıştır:</p>
        <ul>
        <!-- Senaryolar buraya eklenecek -->
        </ul>
        <p>Lütfen <strong>en iyi fiyatlarınızı</strong> sunun.</p>
        <p>Saygılarımızla,</p>
        """
    
    def action_start_next_round(self):
        """Yeni turu başlat"""
        self.ensure_one()
        
        # Tender round'ı artır
        self.tender_id.tender_round = self.next_round
        
        # Sadece kısa listedeki senaryoları aktif et
        self.tender_id.scenario_ids.write({'scenario_status': 'eliminated'})
        self.shortlisted_scenario_ids.write({'scenario_status': 'active'})
        
        # Tedarikçilere bildirim gönder
        for partner in self.invited_partners:
            # Email gönder
            template = self.env.ref('ak_tender.email_template_next_round_invitation')
            template.send_mail(self.id, force_send=True, 
                             email_values={'email_to': partner.email})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Yeni Tur Başlatıldı!',
                'message': f'Tur {self.next_round} başarıyla başlatıldı. '
                          f'{len(self.invited_partners)} tedarikçiye bildirim gönderildi.',
                'type': 'success',
                'sticky': False,
            }
        }
```

## Avantajlar

### Alıcı (Satın Alma) İçin
✅ Senaryo bazlı temiz değerlendirme
✅ Tedarikçi karışmadan en iyi paketi seç
✅ Fiyat rekabeti oluştur
✅ %5-10 ekstra tasarruf (ortalama)
✅ Tedarikçi commitment artar (kısa listeye girdim = ciddiyim)

### Tedarikçi İçin
✅ Kısa listeye girme motivasyonu
✅ İkinci şans (fiyat revizyonu)
✅ Rekabeti görebilir (dolaylı olarak)
✅ Kazanma şansını artırabilir

### Sistem İçin
✅ Gerçek piyasa fiyatlarına yaklaşma
✅ Quality-price optimizasyonu
✅ Süreç şeffaflığı
✅ Audit trail (her tur kaydedilir)

## Özet

**Senaryo Bazlı Çok Turlu İhale** MICE için ideal çünkü:

1. Her senaryo (Otel+Pansiyon+Tarih) bağımsız değerlendirilir
2. Tedarikçi faktörü karışmaz (Firma X iyi, ama Senaryo Y kötü olabilir)
3. Kısa liste = En ümit vadeden kombinasyonlar
4. İkinci tur = Fiyat savaşı, rekabet maksimize
5. Sonuç = Doğru senaryo + doğru fiyat

Mevcut `tender_round` field'i zaten var, sadece senaryo seviyesinde shortlist mekanizması eklenecek!
