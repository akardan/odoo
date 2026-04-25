# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AkTenderScenarioOffer(models.Model):
    """
    MICE İhalesi Senaryo Teklif Modeli

    Her teklif kaydı = Senaryo + Senaryo Kalemi + Tarih Seçeneği + Tur + Tedarikçi

    Tur mantığı:
        round = 0  →  Plan / Bütçe turu (alıcı tarafından girilir, partner opsiyonel)
        round = 1  →  1. Teklif turu (tedarikçi fiyatı)
        round = 2  →  2. Teklif turu (pazarlık sonrası)
        round = N  →  N. Teklif turu

    Granülarite:
        scenario_line_id NULL   → Senaryo geneli / paket fiyatı
        scenario_line_id dolu   → Kalem bazında fiyat (konaklama, transfer, F&B...)

    PO/PR kullanılmaz — bu model tamamen bağımsızdır.
    """
    _name = 'ak.tender.scenario.offer'
    _description = 'MICE Senaryo Teklifi'
    _order = 'scenario_id, round, partner_id'

    # ===== BAĞLANTILAR =====
    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Senaryo'),
        required=True,
        ondelete='cascade',
        index=True,
    )
    tender_id = fields.Many2one(
        'ak.tender',
        related='scenario_id.tender_id',
        store=True,
        readonly=True,
        string=_('İhale'),
        index=True,
    )
    date_option_id = fields.Many2one(
        'ak.tender.scenario.date',
        string=_('Tarih Seçeneği'),
        domain="[('scenario_id', '=', scenario_id)]",
    )
    scenario_line_id = fields.Many2one(
        'ak.tender.scenario.line',
        string=_('Senaryo Kalemi'),
        domain="[('scenario_id', '=', scenario_id)]",
        ondelete='cascade',
        help=_('Boş bırakılırsa senaryo geneli / paket fiyatı. Doldurulursa kalem bazında fiyat.')
    )
    # Kalem tipini doğrudan göstermek için
    line_type = fields.Selection(
        related='scenario_line_id.line_type',
        string=_('Kalem Tipi'),
        readonly=True,
        store=False,
    )

    # ===== TUR =====
    round = fields.Integer(
        string=_('Tur'),
        default=1,
        help=_('0: Plan/Bütçe turu (alıcı tarafından), 1+: Teklif turları (tedarikçi)')
    )

    # ===== TEDARİKÇİ =====
    partner_id = fields.Many2one(
        'res.partner',
        string=_('Tedarikçi'),
        index=True,
        help=_('Tur 0 (plan) için opsiyonel, Tur 1+ için tedarikçi seçilmeli.')
    )

    # ===== FİYAT & MİKTAR =====
    currency_id = fields.Many2one(
        'res.currency',
        related='scenario_id.currency_id',
        store=True,
        readonly=True,
        string=_('Para Birimi'),
    )
    quote_price = fields.Monetary(
        string=_('Teklif Fiyatı'),
        currency_field='currency_id',
    )
    quote_qty = fields.Float(
        string=_('Teklif Adedi'),
        default=1.0,
    )
    realized_price = fields.Monetary(
        string=_('Gerçekleşen Fiyat'),
        currency_field='currency_id',
    )
    realized_qty = fields.Float(
        string=_('Gerçekleşen Adet'),
    )

    # ===== DURUM =====
    state = fields.Selection([
        ('draft', _('Taslak')),
        ('submitted', _('Gönderildi')),
        ('accepted', _('Kabul')),
        ('rejected', _('Red')),
    ], string=_('Durum'), default='draft', required=True)

    submission_date = fields.Datetime(
        string=_('Gönderim Tarihi'),
        readonly=True,
    )
    notes = fields.Text(string=_('Notlar'))

    # ===== SQL CONSTRAINT =====
    # NOT: scenario_line_id ve date_option_id NULL olabileceğinden SQL UNIQUE
    # beklendiği gibi çalışmaz. Uniqueness Python constraint ile sağlanır.
    _sql_constraints = []

    # ===== ACTIONS =====
    def action_submit(self):
        """Teklifi gönderildi olarak işaretle."""
        for rec in self:
            if rec.state == 'draft':
                rec.write({
                    'state': 'submitted',
                    'submission_date': fields.Datetime.now(),
                })

    def action_accept(self):
        """Teklifi kabul et."""
        self.filtered(lambda r: r.state == 'submitted').write({'state': 'accepted'})

    def action_reject(self):
        """Teklifi reddet."""
        self.filtered(lambda r: r.state in ('draft', 'submitted')).write({'state': 'rejected'})

    def action_reset_draft(self):
        """Teklifi taslağa al."""
        self.write({'state': 'draft', 'submission_date': False})

    # ===== CONSTRAINTS =====
    @api.constrains('round')
    def _check_round(self):
        for rec in self:
            if rec.round < 0:
                raise ValidationError(_('Tur numarası 0 veya daha büyük olmalıdır!'))

    @api.constrains('date_option_id', 'scenario_id')
    def _check_date_option_scenario(self):
        for rec in self:
            if rec.date_option_id and rec.date_option_id.scenario_id != rec.scenario_id:
                raise ValidationError(_('Tarih seçeneği bu senaryoya ait olmalıdır!'))

    @api.constrains('scenario_line_id', 'scenario_id')
    def _check_line_scenario(self):
        for rec in self:
            if rec.scenario_line_id and rec.scenario_line_id.scenario_id != rec.scenario_id:
                raise ValidationError(_('Senaryo kalemi bu senaryoya ait olmalıdır!'))

    @api.constrains('round', 'partner_id')
    def _check_partner_required_for_offer_round(self):
        for rec in self:
            if rec.round > 0 and not rec.partner_id:
                raise ValidationError(
                    _('Tur 1 ve üzeri teklif turları için tedarikçi seçilmesi zorunludur!')
                )

    @api.constrains('scenario_id', 'date_option_id', 'round', 'partner_id', 'scenario_line_id')
    def _check_unique_offer(self):
        for rec in self:
            domain = [
                ('id', '!=', rec.id),
                ('scenario_id', '=', rec.scenario_id.id),
                ('round', '=', rec.round),
                ('partner_id', '=', rec.partner_id.id if rec.partner_id else False),
                ('date_option_id', '=', rec.date_option_id.id if rec.date_option_id else False),
                ('scenario_line_id', '=', rec.scenario_line_id.id if rec.scenario_line_id else False),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _('Bu senaryo, kalem, tarih, tur ve tedarikçi kombinasyonu için zaten bir teklif mevcut!')
                )
