# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AkTenderScenario(models.Model):
    """
    MICE İhalesi Senaryo Modeli

    Hiyerarşik yapı desteklenir:

        S1: Antalya (Bölge — parent_id=None, scenario_type='region')
          S11: Titanic Beach 5★ (Otel — parent_id=S1, scenario_type='location_hotel')
               ├── date_option: 2-4 Kasım (Düşük Sezon)
               ├── date_option: 9-11 Kasım (Yüksek Sezon)
               └── line_ids: Konaklama, Transfer, F&B kalemleri
          S12: Grand Prestige (Otel — parent_id=S1)
          S13: Titanic Mardan Palace (Otel — parent_id=S1)
        S2: Kıbrıs (Bölge — parent_id=None)
          S21: Merit Royal (Otel — parent_id=S2)

    Tedarikçilerin kısa listeye alınması, elenmesi ve kazananın seçilmesi
    bu modelin action metodlarıyla yönetilir.
    """
    _name = 'ak.tender.scenario'
    _description = 'İhale Senaryosu'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _parent_name = 'parent_id'
    _parent_store = True

    # ===== HİYERARŞİ =====
    parent_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Üst Senaryo'),
        ondelete='cascade',
        index=True,
        domain="[('tender_id', '=', tender_id), ('id', '!=', id)]",
        help=_("Bölge altındaki otel için üst senaryo (bölge senaryosu) seçin.")
    )
    child_ids = fields.One2many(
        'ak.tender.scenario',
        'parent_id',
        string=_('Alt Senaryolar'),
        help=_("Bu bölge altındaki otel senaryoları.")
    )
    child_count = fields.Integer(
        compute='_compute_child_count',
        string=_('Alt Senaryo Sayısı'),
        store=True
    )
    parent_path = fields.Char(index=True, unaccent=False)
    level = fields.Integer(
        compute='_compute_level',
        store=True,
        string=_('Düzey'),
        help=_("0=Bölge, 1=Otel, 2+=Alt senaryo")
    )

    # ===== TEMEL BİLGİLER =====
    tender_id = fields.Many2one(
        'ak.tender',
        required=True,
        ondelete='cascade',
        string=_('İhale'),
        index=True
    )
    name = fields.Char(
        string=_('Senaryo Adı'),
        required=True,
        tracking=True
    )
    # Örn: "Chamada Prestige 5⭐ (Antalya) - Yarım Pansiyon"

    sequence = fields.Integer(default=10, string=_('Sıra'))
    active = fields.Boolean(default=True, string=_('Aktif'), tracking=True)

    scenario_type = fields.Selection([
        ('region', _('Bölge / Lokasyon')),
        ('location_hotel', _('Lokasyon-Otel Paketi')),
        ('transfer', _('Transfer Paketi')),
        ('meal', _('Yemek Paketi')),
        ('technical', _('Teknik Paket')),
        ('flight', _('Uçuş Paketi')),
        ('custom', _('Özel Paket')),
    ], string=_('Senaryo Tipi'), default='location_hotel', tracking=True)

    # ===== LOKASYON VE OTEL =====
    location_id = fields.Many2one(
        'res.country.state',
        string=_('İl / Bölge'),
        help=_("Antalya, İstanbul, Kıbrıs Kuzey vb.")
    )
    country_id = fields.Many2one(
        'res.country',
        string=_('Ülke'),
        related='location_id.country_id',
        store=True,
        readonly=True
    )
    hotel_partner_id = fields.Many2one(
        'res.partner',
        string=_('Otel / Mekan'),
        domain=[('is_company', '=', True)],
        help=_("Teklif alınacak otel veya etkinlik mekanı.")
    )

    # ===== MICE ÖZEL ALANLAR =====
    meal_plan = fields.Selection([
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', _('Half Board (Yarım Pansiyon)')),
        ('fb', _('Full Board (Tam Pansiyon)')),
        ('ai', 'All Inclusive'),
        ('uai', 'Ultra All Inclusive'),
    ], string=_('Pansiyon Tipi'), tracking=True)

    person_count = fields.Integer(
        string=_('Kişi Sayısı'),
        help=_("Bu senaryo için katılımcı sayısı.")
    )
    vip_count = fields.Integer(
        string=_('VIP Sayısı'),
        help=_("Bu senaryo için VIP katılımcı sayısı.")
    )

    # ===== TARİH SEÇENEKLERİ =====
    date_option_ids = fields.One2many(
        'ak.tender.scenario.date',
        'scenario_id',
        string=_('Alternatif Tarihler'),
        help=_(
            "Bu senaryo için birden fazla tarih aralığı tanımlayabilirsiniz. "
            "Tedarikçiler hangi tarih için teklif verdiklerini belirtir."
        )
    )
    date_option_count = fields.Integer(
        compute='_compute_date_option_count',
        string=_('Tarih Sayısı')
    )

    # ===== İHALE KALEMLERİ =====
    line_ids = fields.One2many(
        'ak.tender.line',
        'scenario_id',
        string=_('Kalemler'),
        help=_("Bu senaryoya ait ihale kalemleri (konaklama, transfer, F&B, teknik...)")
    )
    line_count = fields.Integer(
        compute='_compute_line_count',
        string=_('Kalem Sayısı')
    )

    # ===== FİYATLANDIRMA =====
    currency_id = fields.Many2one(
        related='tender_id.currency_id',
        string=_('Para Birimi'),
        store=True
    )
    total_target_price = fields.Monetary(
        compute='_compute_total_target',
        store=True,
        string=_('Toplam Hedef Fiyat'),
        currency_field='currency_id',
        help=_("Bu senaryonun tüm kalemlerinin hedef fiyat toplamı.")
    )

    # ===== SENARYO KAYNAĞI =====
    scenario_source = fields.Selection([
        ('buyer', _('Alıcı Talebi')),
        ('supplier_counter', _('Tedarikçi Karşı Teklifi')),
    ], default='buyer', string=_('Kaynak'), tracking=True)

    supplier_id = fields.Many2one(
        'res.partner',
        string=_('Öneren Tedarikçi'),
        help=_("Karşı teklif ise hangi tedarikçi önerdi?")
    )

    # ===== ZORUNLULUK =====
    is_mandatory = fields.Boolean(
        string=_('Zorunlu Senaryo'),
        default=False,
        help=_("Tedarikçiler bu senaryoya mutlaka teklif vermeli mi?"),
        tracking=True
    )

    # ===== KISA LİSTE MEKANİZMASI =====
    is_shortlisted = fields.Boolean(
        string=_('Kısa Listede'),
        default=False,
        tracking=True
    )
    shortlist_round = fields.Integer(
        string=_('Kısa Listeye Alınma Turu'),
        readonly=True
    )
    shortlist_date = fields.Datetime(
        string=_('Kısa Liste Tarihi'),
        readonly=True
    )
    shortlist_by = fields.Many2one(
        'res.users',
        string=_('Kısa Listeye Ekleyen'),
        readonly=True
    )
    shortlist_notes = fields.Text(string=_('Kısa Liste Notları'))

    scenario_status = fields.Selection([
        ('active', _('Aktif — Teklif Alınıyor')),
        ('shortlisted', _('Kısa Listede')),
        ('eliminated', _('Elendi')),
        ('awarded', _('Kazanan')),
    ], default='active', string=_('Durum'), required=True, tracking=True)

    elimination_reason = fields.Text(
        string=_('Eleme Gerekçesi'),
        tracking=True
    )

    # ===== TUR BAZLI EN İYİ TEKLİFLER =====
    best_offer_round_1 = fields.Monetary(
        compute='_compute_best_offers',
        store=False,
        string=_('Tur 1 En İyi Teklif'),
        currency_field='currency_id'
    )
    best_offer_round_2 = fields.Monetary(
        compute='_compute_best_offers',
        store=False,
        string=_('Tur 2 En İyi Teklif'),
        currency_field='currency_id'
    )
    improvement_percentage = fields.Float(
        compute='_compute_improvement',
        store=False,
        string=_('İyileştirme %'),
        help=_('Tur 2 vs Tur 1 fiyat iyileştirmesi')
    )

    # ===== NPV BAZLI EN İYİ TEKLİF =====
    best_npv_offer = fields.Monetary(
        compute='_compute_best_npv_offer',
        store=False,
        string=_('En İyi NPV Teklif'),
        currency_field='currency_id',
        help=_('NPV bazında en düşük teklif (vade iskontosu dahil)')
    )
    best_npv_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_best_npv_offer',
        store=False,
        string=_('En İyi NPV Tedarikçi')
    )

    # ===== COMPUTED METHODS =====

    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for scenario in self:
            if not scenario.parent_id:
                scenario.level = 0
            else:
                scenario.level = (scenario.parent_id.level or 0) + 1

    @api.depends('child_ids')
    def _compute_child_count(self):
        for scenario in self:
            scenario.child_count = len(scenario.child_ids)

    @api.depends('date_option_ids')
    def _compute_date_option_count(self):
        for scenario in self:
            scenario.date_option_count = len(scenario.date_option_ids)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for scenario in self:
            scenario.line_count = len(scenario.line_ids)

    @api.depends('line_ids.computed_target_total')
    def _compute_total_target(self):
        for scenario in self:
            scenario.total_target_price = sum(
                scenario.line_ids.mapped('computed_target_total')
            )

    @api.depends('line_ids')
    def _compute_best_offers(self):
        """Her tur için en düşük toplam teklifi hesapla."""
        for scenario in self:
            po_lines = self.env['purchase.order.line'].search([
                ('tender_line_id.scenario_id', '=', scenario.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])

            def _best_by_round(round_num):
                lines = po_lines.filtered(lambda l: l.order_id.tender_round == round_num)
                if not lines:
                    return 0.0
                partner_totals = {}
                for line in lines:
                    pid = line.order_id.partner_id.id
                    partner_totals[pid] = partner_totals.get(pid, 0.0) + line.price_subtotal
                return min(partner_totals.values()) if partner_totals else 0.0

            scenario.best_offer_round_1 = _best_by_round(1)
            scenario.best_offer_round_2 = _best_by_round(2)

    @api.depends('best_offer_round_1', 'best_offer_round_2')
    def _compute_improvement(self):
        for scenario in self:
            r1 = scenario.best_offer_round_1
            r2 = scenario.best_offer_round_2
            if r1 and r2:
                scenario.improvement_percentage = ((r1 - r2) / r1) * 100
            else:
                scenario.improvement_percentage = 0.0

    @api.depends('line_ids')
    def _compute_best_npv_offer(self):
        """NPV bazında en iyi teklifi bul."""
        for scenario in self:
            po_lines = self.env['purchase.order.line'].search([
                ('tender_line_id.scenario_id', '=', scenario.id),
                ('order_id.state', 'in', ['draft', 'sent', 'to approve', 'purchase', 'done'])
            ])
            if not po_lines:
                scenario.best_npv_offer = 0.0
                scenario.best_npv_partner_id = False
                continue

            partner_npv = {}
            for line in po_lines:
                pid = line.order_id.partner_id.id
                if pid not in partner_npv:
                    partner_npv[pid] = {'total_npv': 0.0, 'partner': line.order_id.partner_id}
                # ak_tender'daki mevcut npv_value alanını kullan
                partner_npv[pid]['total_npv'] += (line.npv_value or line.price_subtotal or 0.0)

            if partner_npv:
                best = min(partner_npv.values(), key=lambda x: x['total_npv'])
                scenario.best_npv_offer = best['total_npv']
                scenario.best_npv_partner_id = best['partner']
            else:
                scenario.best_npv_offer = 0.0
                scenario.best_npv_partner_id = False

    # ===== CONSTRAINTS =====

    @api.constrains('parent_id')
    def _check_parent_id(self):
        """Kendine ya da kendi alt senaryosuna parent set edilemez."""
        if not self._check_recursion():
            raise ValidationError(_('Döngüsel senaryo hiyerarşisi oluşturulamaz!'))

    @api.constrains('parent_id', 'tender_id')
    def _check_parent_tender(self):
        """Parent senaryo aynı ihaleden olmalı."""
        for scenario in self:
            if scenario.parent_id and scenario.parent_id.tender_id != scenario.tender_id:
                raise ValidationError(
                    _("Üst senaryo aynı ihaleye ait olmalıdır: %s") % scenario.tender_id.name
                )

    # ===== ACTIONS =====

    def action_add_to_shortlist(self):
        """Senaryoyu kısa listeye ekle."""
        self.ensure_one()
        self.write({
            'is_shortlisted': True,
            'scenario_status': 'shortlisted',
            'shortlist_round': self.tender_id.tender_round,
            'shortlist_date': fields.Datetime.now(),
            'shortlist_by': self.env.user.id,
        })
        return True

    def action_remove_from_shortlist(self):
        """Senaryoyu kısa listeden çıkar."""
        self.ensure_one()
        self.write({
            'is_shortlisted': False,
            'scenario_status': 'active',
        })
        return True

    def action_eliminate_scenario(self):
        """Senaryo eleme sihirbazını aç."""
        self.ensure_one()
        return {
            'name': _('Senaryo Eleme'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.eliminate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_scenario_id': self.id},
        }

    def action_award(self):
        """Senaryoyu kazanan olarak işaretle."""
        self.ensure_one()
        self.write({'scenario_status': 'awarded'})
        self.message_post(
            body=_('Bu senaryo kazanan olarak seçildi.'),
            subtype_xmlid='mail.mt_note'
        )
        return True

    def action_view_comparison(self):
        """Senaryo bazlı teklif karşılaştırma (purchase.order.line listesi)."""
        self.ensure_one()
        return {
            'name': _('Karşılaştırma: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'list',
            'domain': [('tender_line_id.scenario_id', '=', self.id)],
            'context': {'group_by': 'order_id'},
        }

    def action_view_lines(self):
        """Senaryo kalemlerini görüntüle."""
        self.ensure_one()
        return {
            'name': _('%s — Kalemler') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.line',
            'view_mode': 'list,form',
            'domain': [('scenario_id', '=', self.id)],
            'context': {
                'default_scenario_id': self.id,
                'default_tender_id': self.tender_id.id,
            },
        }

    def action_add_child_scenario(self):
        """Bu senaryonun altına yeni bir alt senaryo (otel) oluşturma sihirbazını aç."""
        self.ensure_one()
        return {
            'name': _('Alt Senaryo Oluştur'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.tender_id.id,
                'default_parent_id': self.id,
                'default_location_id': self.location_id.id if self.location_id else False,
                'default_scenario_type': 'location_hotel',
            },
        }

    def action_view_children(self):
        """Alt senaryoları görüntüle."""
        self.ensure_one()
        return {
            'name': _('%s — Alt Senaryolar') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario',
            'view_mode': 'list,form,kanban',
            'domain': [('parent_id', '=', self.id)],
            'context': {
                'default_tender_id': self.tender_id.id,
                'default_parent_id': self.id,
            },
        }

    # ===== KOPYALAMA =====

    def copy(self, default=None):
        """Senaryo kopyala: tarih seçenekleri ve adı 'Kopya' öneki ile."""
        self.ensure_one()
        default = dict(default or {})
        default.setdefault('name', _('%s (Kopya)') % self.name)
        default.setdefault('scenario_status', 'active')
        default.setdefault('is_shortlisted', False)
        default.setdefault('shortlist_round', 0)
        default.setdefault('shortlist_date', False)
        default.setdefault('shortlist_by', False)
        default.setdefault('elimination_reason', False)
        new_scenario = super().copy(default)
        for date_opt in self.date_option_ids:
            date_opt.copy({'scenario_id': new_scenario.id})
        return new_scenario

    def action_copy_scenario(self):
        """Senaryoyu kopyala ve yeni senaryoyu forma aç."""
        self.ensure_one()
        new_scenario = self.copy()
        return {
            'name': _('Senaryo: %s') % new_scenario.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario',
            'res_id': new_scenario.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ===== ONCHANGE =====

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        """Parent seçildiğinde lokasyonu otomatik doldur."""
        if self.parent_id and self.parent_id.location_id:
            self.location_id = self.parent_id.location_id

    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """Tender değiştiğinde person_count otomatik doldur."""
        if self.tender_id and self.tender_id.total_person_count:
            self.person_count = self.tender_id.total_person_count
        if self.tender_id and self.tender_id.vip_person_count:
            self.vip_count = self.tender_id.vip_person_count
