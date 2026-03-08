# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AkTender(models.Model):
    """
    ak.tender modelini MICE ihaleleri için genişletir.

    tender_type='mice' olduğunda senaryolar, kısa liste istatistikleri
    ve MICE özel alanlar (kişi sayısı, VIP) eklenir.
    """
    _inherit = 'ak.tender'

    # ===== SENARYO İLİŞKİSİ =====
    scenario_ids = fields.One2many(
        'ak.tender.scenario',
        'tender_id',
        string=_('Senaryolar'),
        help=_(
            "MICE ihaleleri için alternatif senaryolar. "
            "Her senaryo bir lokasyon-otel paketi ve tarih seçenekleri içerir."
        )
    )
    scenario_count = fields.Integer(
        compute='_compute_scenario_count',
        string=_('Senaryo Sayısı')
    )

    # ===== SENARYO İSTATİSTİKLERİ =====
    total_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string=_('Toplam Senaryo')
    )
    shortlisted_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string=_('Kısa Liste')
    )
    eliminated_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string=_('Elenen')
    )
    awarded_scenarios = fields.Integer(
        compute='_compute_scenario_stats',
        string=_('Kazanan')
    )

    # ===== MICE ÖZEL ALANLAR =====
    total_person_count = fields.Integer(
        string=_('Toplam Kişi Sayısı'),
        help=_("Etkinliğe katılacak toplam katılımcı sayısı."),
        tracking=True
    )
    vip_person_count = fields.Integer(
        string=_('VIP Kişi Sayısı'),
        help=_("Özel konuk listesindeki VIP katılımcı sayısı."),
        tracking=True
    )

    # ===== COMPUTED METHODS =====

    @api.depends('scenario_ids')
    def _compute_scenario_count(self):
        for tender in self:
            tender.scenario_count = len(tender.scenario_ids)

    @api.depends('scenario_ids.scenario_status', 'scenario_ids.is_shortlisted')
    def _compute_scenario_stats(self):
        for tender in self:
            all_scenarios = tender.scenario_ids
            tender.total_scenarios = len(all_scenarios)
            tender.shortlisted_scenarios = len(
                all_scenarios.filtered(lambda s: s.is_shortlisted)
            )
            tender.eliminated_scenarios = len(
                all_scenarios.filtered(lambda s: s.scenario_status == 'eliminated')
            )
            tender.awarded_scenarios = len(
                all_scenarios.filtered(lambda s: s.scenario_status == 'awarded')
            )

    # ===== ACTIONS =====

    def action_create_scenario(self):
        """Yeni senaryo oluşturma sihirbazını aç."""
        self.ensure_one()
        return {
            'name': _('Yeni Senaryo Oluştur'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
                'default_person_count': self.total_person_count or 0,
                'default_vip_count': self.vip_person_count or 0,
            },
        }

    def action_start_next_round(self):
        """Kısa listedeki senaryolar için sonraki tur sihirbazını aç."""
        self.ensure_one()
        shortlisted = self.scenario_ids.filtered(lambda s: s.is_shortlisted)
        if not shortlisted:
            raise UserError(_("Kısa listeye alınmış senaryo yok! Önce senaryoları kısa listeye ekleyin."))
        return {
            'name': _('Sonraki Tur Başlat'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.next.round.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
                'default_next_round': self.tender_round + 1,
                'default_shortlisted_scenario_ids': shortlisted.ids,
            },
        }

    def action_view_scenarios(self):
        """Senaryo listesini ayrı pencerede görüntüle."""
        self.ensure_one()
        return {
            'name': _('%s — Senaryolar') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario',
            'view_mode': 'list,form,kanban',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id},
        }


class AkTenderLine(models.Model):
    """
    ak.tender.line modelini MICE ihaleleri için genişletir.

    Her kalem bir senaryoya (ak.tender.scenario) bağlanır, böylece
    hangi lokasyon-otel paketine ait olduğu takip edilir.
    MICE özel alanlar: oda tipi, manzara, pansiyon, özel talepler.
    """
    _inherit = 'ak.tender.line'

    # ===== SENARYO İLİŞKİSİ =====
    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Senaryo'),
        ondelete='set null',
        index=True,
        domain="[('tender_id', '=', tender_id)]",
        help=_("Bu kalemin ait olduğu MICE senaryosu (otel/lokasyon paketi).")
    )

    # ===== SATIR TİPİ =====
    line_type = fields.Selection([
        ('accommodation', _('Konaklama')),
        ('meal', _('Yemek / F&B')),
        ('transfer', _('Transfer')),
        ('technical', _('Teknik Hizmet')),
        ('flight', _('Uçuş')),
        ('service', _('Diğer Hizmet')),
        ('package', _('Paket')),
    ], string=_('Satır Tipi'),
        help=_("MICE hizmet kategorisi. Raporlama ve filtrelemede kullanılır.")
    )

    # ===== MICE ÖZEL ALANLAR — KONAKLAMA =====
    mice_room_type = fields.Selection([
        ('single', _('Single')),
        ('double', _('Double')),
        ('triple', _('Triple')),
        ('suite', _('Suite')),
        ('presidential', _('Presidential Suite')),
    ], string=_('Oda Tipi'))

    mice_view_type = fields.Selection([
        ('city', _('Şehir Manzarası')),
        ('sea', _('Deniz Manzarası')),
        ('mountain', _('Dağ Manzarası')),
        ('garden', _('Bahçe Manzarası')),
        ('pool', _('Havuz Manzarası')),
    ], string=_('Manzara'))

    mice_meal_plan = fields.Selection([
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', _('Half Board')),
        ('fb', _('Full Board')),
        ('ai', 'All Inclusive'),
        ('uai', 'Ultra All Inclusive'),
    ], string=_('Pansiyon Tipi'),
        help=_("Bu satır için pansiyon tipi. Genellikle senaryodan gelir ama override edilebilir.")
    )

    mice_amenities = fields.Char(
        string=_('Özel Hizmetler'),
        help=_("Virgülle ayrılmış: WiFi, Havuz, Spa, Butler, Minibar")
    )

    mice_special_requests = fields.Text(
        string=_('Özel İstekler'),
        help=_("Tedarikçiye iletilecek özel talepler ve notlar.")
    )

    # ===== HESAPLANAN TOPLAM =====
    computed_target_total = fields.Monetary(
        compute='_compute_target_total',
        store=True,
        string=_('Toplam Hedef'),
        help=_('Miktar × Gün × Birim Fiyat'),
        currency_field='currency_id'
    )

    # ===== ÖZET BİLGİ =====
    line_summary = fields.Char(
        compute='_compute_line_summary',
        store=True,
        string=_('Özet'),
        help=_("Otomatik oluşturulan kullanıcı dostu özet (Otel | Oda Tipi | Pansiyon)")
    )

    # ===== COMPUTED METHODS =====

    @api.depends('quantity', 'days', 'target_price')
    def _compute_target_total(self):
        for line in self:
            q = line.quantity or 0.0
            d = line.days or 1
            p = line.target_price or 0.0
            # MICE konaklama: gün × kişi × birim fiyat
            if line.tender_id and line.tender_id.tender_type == 'mice':
                line.computed_target_total = q * d * p
            else:
                line.computed_target_total = q * p

    @api.depends(
        'mice_room_type', 'mice_view_type', 'mice_amenities',
        'mice_meal_plan', 'scenario_id.meal_plan',
        'scenario_id.hotel_partner_id', 'name'
    )
    def _compute_line_summary(self):
        """Otomatik özet oluştur: Otel | Oda | Pansiyon | Manzara."""
        room_labels = dict(self._fields['mice_room_type'].selection)
        view_labels = dict(self._fields['mice_view_type'].selection)

        for line in self:
            if line.scenario_id and line.tender_id.tender_type == 'mice':
                parts = []
                if line.scenario_id.hotel_partner_id:
                    parts.append(line.scenario_id.hotel_partner_id.name)
                if line.mice_room_type:
                    parts.append(room_labels.get(line.mice_room_type, ''))
                meal = line.mice_meal_plan or (line.scenario_id.meal_plan if line.scenario_id else False)
                if meal:
                    meal_labels = dict(line._fields['mice_meal_plan'].selection)
                    parts.append(meal_labels.get(meal, ''))
                if line.mice_view_type:
                    parts.append(view_labels.get(line.mice_view_type, ''))
                if line.mice_amenities:
                    top_amenities = line.mice_amenities.split(',')[:3]
                    parts.append(f"({', '.join(a.strip() for a in top_amenities)})")
                line.line_summary = ' | '.join(filter(None, parts))
            else:
                line.line_summary = line.name or ''

    # ===== ONCHANGE =====

    @api.onchange('scenario_id')
    def _onchange_scenario_id(self):
        """Senaryo seçildiğinde pansiyon tipini otomatik doldur."""
        if self.scenario_id and self.scenario_id.meal_plan:
            if not self.mice_meal_plan:
                self.mice_meal_plan = self.scenario_id.meal_plan

    @api.onchange('line_type')
    def _onchange_line_type(self):
        """Satır tipi değiştiğinde uygun UoM otomatik ayarla."""
        if self.line_type == 'accommodation':
            uom = self.env['uom.uom'].search([('name', 'ilike', 'Gece')], limit=1)
            if uom:
                self.uom_id = uom
        elif self.line_type in ('meal', 'service'):
            uom = self.env['uom.uom'].search([('name', 'ilike', 'Kişi')], limit=1)
            if uom:
                self.uom_id = uom
