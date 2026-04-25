# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AkTenderScenarioDate(models.Model):
    """
    Senaryo için alternatif tarih seçenekleri.

    Her otel senaryosunun birden fazla tarih alternatifi olabilir.
    Tarih seçeneği senaryonun MALİYET BOYUTUDUR:
        - 2-4 Kasım (Düşük Sezon) → 30.000 €
        - 9-11 Kasım (Yüksek Sezon) → 35.000 €

    Tedarikçiler hangi tarih için teklif verdiklerini
    ak.tender.scenario.offer.date_option_id ile belirtirler.
    """
    _name = 'ak.tender.scenario.date'
    _description = 'Senaryo Alternatif Tarihleri'
    _order = 'sequence, date_start'

    # ===== TEMEL İLİŞKİ =====
    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        required=True,
        ondelete='cascade',
        string=_('Senaryo')
    )

    # ===== AD (OTOMATİK HESAPLAMA) =====
    name = fields.Char(
        string=_('Tarih Açıklaması'),
        compute='_compute_name',
        store=True
    )
    # Örn: "2-4 Kas 2025 (Düşük Sezon)"

    # ===== TARİHLER =====
    date_start = fields.Date(string=_('Başlangıç'), required=True)
    date_end = fields.Date(string=_('Bitiş'), required=True)
    days = fields.Integer(
        compute='_compute_days',
        store=True,
        string=_('Gün Sayısı'),
        help=_('Bitiş - Başlangıç + 1 (başlangıç günü dahil)')
    )

    sequence = fields.Integer(default=10, string=_('Sıra'))
    is_preferred = fields.Boolean(
        string=_('Tercih Edilen Tarih'),
        help=_('Bu tarih aralığı müşteri tarafından tercih edilen seçenektir.')
    )
    notes = fields.Text(string=_('Notlar'))

    # ===== MALİYET BOYUTU =====
    currency_id = fields.Many2one(
        related='scenario_id.currency_id',
        string=_('Para Birimi'),
        store=True
    )
    estimated_total_cost = fields.Monetary(
        string=_('Tahmini Toplam Maliyet'),
        currency_field='currency_id',
        help=_('Bu tarih için beklenen toplam maliyet (sezon farkı, müsaitlik vb.)')
    )
    cost_multiplier = fields.Float(
        string=_('Maliyet Çarpanı'),
        default=1.0,
        help=_('Sezon farkı çarpanı (1.0=normal, 1.2=%20 artış, 0.9=%10 indirim)')
    )
    season_type = fields.Selection([
        ('low', _('Düşük Sezon')),
        ('mid', _('Orta Sezon')),
        ('high', _('Yüksek Sezon')),
        ('peak', _('Pik Sezon')),
    ], string=_('Sezon Tipi'))

    # ===== TEKLIF ANALİZİ =====
    best_offer_amount = fields.Monetary(
        compute='_compute_best_offer',
        store=True,
        string=_('En İyi Teklif'),
        currency_field='currency_id',
        help=_('Bu tarih seçeneği için alınan tekliflerin en iyisi.')
    )
    best_offer_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_best_offer',
        store=True,
        string=_('En İyi Teklif Veren')
    )
    offer_count = fields.Integer(
        compute='_compute_offer_count',
        string=_('Teklif Sayısı')
    )

    # ===== COMPUTED METHODS =====
    @api.depends('date_start', 'date_end', 'season_type')
    def _compute_name(self):
        season_labels = {
            'low': _('Düşük Sezon'),
            'mid': _('Orta Sezon'),
            'high': _('Yüksek Sezon'),
            'peak': _('Pik Sezon'),
        }
        for record in self:
            if record.date_start and record.date_end:
                start_str = record.date_start.strftime('%d %b')
                end_str = record.date_end.strftime('%d %b %Y')
                name = f"{start_str} - {end_str}"
                if record.season_type:
                    name += f" ({season_labels.get(record.season_type, '')})"
                record.name = name
            else:
                record.name = _("Tarih Belirtilmedi")

    @api.depends('date_start', 'date_end')
    def _compute_days(self):
        for record in self:
            if record.date_start and record.date_end:
                delta = record.date_end - record.date_start
                record.days = delta.days + 1  # başlangıç günü dahil
            else:
                record.days = 0

    def _compute_best_offer(self):
        """Bu tarih seçeneği için en iyi teklifi offer_ids üzerinden hesapla."""
        for date_option in self:
            offers = self.env['ak.tender.scenario.offer'].search([
                ('date_option_id', '=', date_option.id),
                ('state', 'in', ['submitted', 'accepted']),
                ('round', '>', 0),
            ])
            if offers:
                by_partner = {}
                for offer in offers:
                    if not offer.partner_id:
                        continue
                    pid = offer.partner_id.id
                    if pid not in by_partner:
                        by_partner[pid] = {'total': 0.0, 'partner': offer.partner_id}
                    by_partner[pid]['total'] += offer.quote_price
                if by_partner:
                    best = min(by_partner.values(), key=lambda x: x['total'])
                    date_option.best_offer_amount = best['total']
                    date_option.best_offer_partner_id = best['partner']
                else:
                    date_option.best_offer_amount = 0.0
                    date_option.best_offer_partner_id = False
            else:
                date_option.best_offer_amount = 0.0
                date_option.best_offer_partner_id = False

    def _compute_offer_count(self):
        """Bu tarih seçeneği için benzersiz tedarikçi teklif sayısı."""
        for date_option in self:
            offers = self.env['ak.tender.scenario.offer'].search([
                ('date_option_id', '=', date_option.id),
                ('state', 'in', ['submitted', 'accepted']),
                ('round', '>', 0),
            ])
            date_option.offer_count = len(offers.mapped('partner_id'))

    # ===== CONSTRAINTS =====
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
                raise ValidationError(_('Başlangıç tarihi bitiş tarihinden sonra olamaz!'))

    # ===== ACTIONS =====
    def action_view_offers(self):
        """Bu tarih seçeneği için verilen teklifleri görüntüle."""
        self.ensure_one()
        return {
            'name': _('%s — Teklifler') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.offer',
            'view_mode': 'list,form',
            'domain': [('date_option_id', '=', self.id)],
            'context': {
                'default_date_option_id': self.id,
                'default_scenario_id': self.scenario_id.id,
                'group_by': 'round',
            },
        }
