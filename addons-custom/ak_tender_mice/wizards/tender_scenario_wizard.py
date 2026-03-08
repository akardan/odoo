# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TenderScenarioWizard(models.TransientModel):
    """
    Senaryo Oluşturma Sihirbazı

    Hem bölge (region) hem de otel (location_hotel) düzeyinde senaryolar oluşturur.
    Hiyerarşi:
        - parent_id = None  →  Bölge senaryosu (Antalya, Kıbrıs, İstanbul...)
        - parent_id = S1    →  Otel senaryosu (Titanic Beach, Grand Prestige...)

    Tarih seçenekleri (date_option_ids) otel senaryolarına eklenir.
    """
    _name = 'ak.tender.scenario.wizard'
    _description = 'Senaryo Oluşturma Sihirbazı'

    # ===== ZORUNLU ALANLAR =====
    tender_id = fields.Many2one(
        'ak.tender',
        string=_('İhale'),
        required=True
    )
    name = fields.Char(
        string=_('Senaryo Adı'),
        required=True,
        help=_("Örn: 'Antalya' veya 'Titanic Beach 5★ — HB'")
    )
    scenario_type = fields.Selection([
        ('region', _('Bölge / Lokasyon')),
        ('location_hotel', _('Lokasyon-Otel Paketi')),
        ('transfer', _('Transfer Paketi')),
        ('meal', _('Yemek Paketi')),
        ('technical', _('Teknik Paket')),
        ('flight', _('Uçuş Paketi')),
        ('custom', _('Özel Paket')),
    ], string=_('Senaryo Tipi'), default='location_hotel', required=True)

    is_mandatory = fields.Boolean(
        string=_('Zorunlu Senaryo'),
        default=False,
        help=_("Tedarikçiler bu senaryoya mutlaka teklif vermeli mi?")
    )

    # ===== HİYERARŞİ =====
    parent_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Üst Senaryo (Bölge)'),
        domain="[('tender_id', '=', tender_id), ('scenario_type', '=', 'region')]",
        help=_("Bölge senaryosu seçin. Otel bu bölgeye eklenecek.")
    )

    # ===== LOKASYON VE OTEL =====
    location_id = fields.Many2one(
        'res.country.state',
        string=_('İl / Bölge'),
        help=_("Antalya, İstanbul, Kıbrıs Kuzey vb.")
    )
    hotel_partner_id = fields.Many2one(
        'res.partner',
        string=_('Otel / Mekan'),
        domain=[('is_company', '=', True)],
        help=_("Teklife davet edilecek otel veya etkinlik mekanı.")
    )
    meal_plan = fields.Selection([
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', _('Half Board (Yarım Pansiyon)')),
        ('fb', _('Full Board (Tam Pansiyon)')),
        ('ai', 'All Inclusive'),
        ('uai', 'Ultra All Inclusive'),
    ], string=_('Pansiyon Tipi'))

    # ===== KATILIMCı BİLGİLERİ =====
    person_count = fields.Integer(
        string=_('Kişi Sayısı'),
        help=_("Varsayılan olarak ihaledeki toplam kişi sayısından gelir.")
    )
    vip_count = fields.Integer(string=_('VIP Sayısı'))

    # ===== TARİH SEÇENEKLERİ =====
    add_dates = fields.Boolean(
        string=_('Tarih Seçenekleri Ekle'),
        default=True,
        help=_("Otel senaryolarına birden fazla tarih aralığı tanımlayabilirsiniz.")
    )
    date_option_ids = fields.One2many(
        'ak.tender.scenario.wizard.date',
        'wizard_id',
        string=_('Tarih Seçenekleri')
    )

    # ===== COMPUTED =====
    @api.onchange('scenario_type')
    def _onchange_scenario_type(self):
        """Bölge tipinde hotel ve tarih alanlarını zorunlu değil yap."""
        if self.scenario_type == 'region':
            self.hotel_partner_id = False
            self.meal_plan = False
            self.add_dates = False

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        """Üst senaryo seçildiğinde lokasyonu kopyala."""
        if self.parent_id and self.parent_id.location_id:
            self.location_id = self.parent_id.location_id

    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """İhale değişince kişi sayısını doldur."""
        if self.tender_id:
            self.person_count = self.tender_id.total_person_count or 0
            self.vip_count = self.tender_id.vip_person_count or 0

    # ===== ACTION =====
    def action_create_scenario(self):
        """Senaryoyu oluştur ve forma aç."""
        self.ensure_one()

        vals = {
            'tender_id': self.tender_id.id,
            'name': self.name,
            'scenario_type': self.scenario_type,
            'parent_id': self.parent_id.id if self.parent_id else False,
            'location_id': self.location_id.id if self.location_id else False,
            'hotel_partner_id': self.hotel_partner_id.id if self.hotel_partner_id else False,
            'meal_plan': self.meal_plan,
            'person_count': self.person_count,
            'vip_count': self.vip_count,
            'is_mandatory': self.is_mandatory,
            'scenario_source': 'buyer',
        }
        scenario = self.env['ak.tender.scenario'].create(vals)

        # Tarih seçeneklerini ekle
        if self.add_dates and self.date_option_ids:
            for date_line in self.date_option_ids:
                self.env['ak.tender.scenario.date'].create({
                    'scenario_id': scenario.id,
                    'date_start': date_line.date_start,
                    'date_end': date_line.date_end,
                    'season_type': date_line.season_type,
                    'cost_multiplier': date_line.cost_multiplier,
                    'estimated_total_cost': date_line.estimated_total_cost,
                    'is_preferred': date_line.is_preferred,
                    'notes': date_line.notes,
                })

        # Oluşturulan senaryoyu aç
        return {
            'name': _('Senaryo: %s') % scenario.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario',
            'res_id': scenario.id,
            'view_mode': 'form',
            'target': 'current',
        }


class TenderScenarioWizardDate(models.TransientModel):
    """Senaryo sihirbazı içinde tarih seçeneklerini toplamak için yardımcı model."""
    _name = 'ak.tender.scenario.wizard.date'
    _description = 'Senaryo Wizard Tarih Seçeneği'

    wizard_id = fields.Many2one(
        'ak.tender.scenario.wizard',
        required=True,
        ondelete='cascade'
    )
    date_start = fields.Date(string=_('Başlangıç'), required=True)
    date_end = fields.Date(string=_('Bitiş'), required=True)
    season_type = fields.Selection([
        ('low', _('Düşük Sezon')),
        ('mid', _('Orta Sezon')),
        ('high', _('Yüksek Sezon')),
        ('peak', _('Pik Sezon')),
    ], string=_('Sezon Tipi'))
    cost_multiplier = fields.Float(string=_('Maliyet Çarpanı'), default=1.0)
    estimated_total_cost = fields.Monetary(
        string=_('Tahmini Maliyet'),
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        related='wizard_id.tender_id.currency_id',
        string=_('Para Birimi')
    )
    is_preferred = fields.Boolean(string=_('Tercih Edilen'))
    notes = fields.Text(string=_('Notlar'))


class TenderScenarioEliminateWizard(models.TransientModel):
    """
    Senaryo Eleme Sihirbazı

    Bir veya birden fazla senaryoyu gerekçe ile eler.
    """
    _name = 'ak.tender.scenario.eliminate.wizard'
    _description = 'Senaryo Eleme Sihirbazı'

    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Senaryo'),
        required=True
    )
    elimination_reason = fields.Text(
        string=_('Eleme Gerekçesi'),
        required=True,
        help=_("Senaryo neden eleniyor? (fiyat yüksek, kapasite yetersiz, lokasyon uygun değil vb.)")
    )

    def action_eliminate(self):
        """Senaryoyu elenmiş olarak işaretle."""
        self.ensure_one()
        self.scenario_id.write({
            'scenario_status': 'eliminated',
            'is_shortlisted': False,
            'elimination_reason': self.elimination_reason,
        })
        self.scenario_id.message_post(
            body=_('Senaryo elendi. Gerekçe: %s') % self.elimination_reason,
            subtype_xmlid='mail.mt_note'
        )
        return {'type': 'ir.actions.act_window_close'}


class TenderNextRoundWizard(models.TransientModel):
    """
    Sonraki Tur Sihirbazı

    Kısa listedeki senaryolar için yeni ihale turunu başlatır.
    Tender_round arttırılır, tedarikçilere bildirim gönderilebilir.
    """
    _name = 'ak.tender.next.round.wizard'
    _description = 'Sonraki Tur Sihirbazı'

    tender_id = fields.Many2one(
        'ak.tender',
        string=_('İhale'),
        required=True
    )
    next_round = fields.Integer(
        string=_('Yeni Tur'),
        required=True
    )
    shortlisted_scenario_ids = fields.Many2many(
        'ak.tender.scenario',
        'next_round_wizard_scenario_rel',
        'wizard_id',
        'scenario_id',
        string=_('Kısa Listedeki Senaryolar'),
        domain="[('tender_id', '=', tender_id), ('is_shortlisted', '=', True)]"
    )
    invite_all_suppliers = fields.Boolean(
        string=_('Tüm Tedarikçileri Davet Et'),
        default=False,
        help=_(
            "İşaretliyse ihalenin tüm davetli tedarikçileri, "
            "işaretli değilse sadece önceki turda teklif verenler davet edilir."
        )
    )
    deadline_days = fields.Integer(
        string=_('Süre (Gün)'),
        default=5,
        help=_("Tedarikçilerin teklif vermesi için verilen gün sayısı.")
    )
    notes = fields.Text(
        string=_('Tedarikçiye Notlar'),
        help=_("Tedarikçilere gönderilecek ek notlar / fiyat beklentisi.")
    )

    def action_start_round(self):
        """Yeni turu başlat: tender_round arttır."""
        self.ensure_one()

        if not self.shortlisted_scenario_ids:
            raise UserError(_('Kısa listeye alınmış senaryo seçmelisiniz!'))

        # Tender turunu güncelle
        self.tender_id.write({'tender_round': self.next_round})

        # Kısa listeden çıkmış senaryoları aktif duruma geri al
        # (sadece kısa listede kalanlar bu turda aktif)
        all_scenarios = self.tender_id.scenario_ids.filtered(
            lambda s: s.scenario_status not in ('eliminated', 'awarded')
        )
        non_shortlisted = all_scenarios - self.shortlisted_scenario_ids
        non_shortlisted.write({'is_shortlisted': False, 'scenario_status': 'active'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Tur %s Başlatıldı') % self.next_round,
                'message': _('%s senaryo için Tur %s başlatıldı.') % (
                    len(self.shortlisted_scenario_ids),
                    self.next_round
                ),
                'type': 'success',
                'sticky': False,
            },
        }
