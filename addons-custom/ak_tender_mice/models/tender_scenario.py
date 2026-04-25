# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


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

    scenario_type_id = fields.Many2one(
        'ak.tender.scenario.type',
        string=_('Senaryo Tipi'),
        ondelete='restrict',
        tracking=True,
        index=True,
    )
    # Geriye dönük uyumluluk: domain'lerde, lambda'larda ve invisible koşullarında
    # ('region', 'location_hotel' gibi string değerlerle) çalışmaya devam eder.
    scenario_type = fields.Char(
        related='scenario_type_id.code',
        string=_('Senaryo Tipi Kodu'),
        store=True,
        readonly=True,
    )

    # View invisible koşulları için boolean yardımcı alanlar
    type_is_root = fields.Boolean(
        related='scenario_type_id.is_root',
        string=_('Kök Tip mi?'),
        store=True,
    )
    type_can_have_children = fields.Boolean(
        related='scenario_type_id.can_have_children',
        string=_('Alt Paket Eklenebilir mi?'),
        store=True,
    )

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

    # ===== SENARYO KALEMLERİ =====
    scenario_line_ids = fields.One2many(
        'ak.tender.scenario.line',
        'scenario_id',
        string=_('Senaryo Kalemleri'),
        help=_("Bu senaryoya ait senaryo kalemleri (planlama aşaması)")
    )
    scenario_line_count = fields.Integer(
        compute='_compute_scenario_line_count',
        string=_('Senaryo Kalem Sayısı')
    )

    # ===== İHALE KALEMLERİ =====
    line_ids = fields.One2many(
        'ak.tender.line',
        'scenario_id',
        string=_('İhale Kalemleri'),
        help=_("Bu senaryoya ait ihale kalemleri (konaklama, transfer, F&B, teknik...)")
    )
    line_count = fields.Integer(
        compute='_compute_line_count',
        string=_('İhale Kalem Sayısı')
    )

    # ===== TEKLİFLER =====
    offer_ids = fields.One2many(
        'ak.tender.scenario.offer',
        'scenario_id',
        string=_('Teklifler'),
        help=_("Bu senaryo için alınan tedarikçi teklifleri (PO/PR bağımsız)")
    )
    offer_count = fields.Integer(
        compute='_compute_offer_count',
        string=_('Teklif Sayısı')
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
    best_offer_round_1_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_best_offers',
        store=False,
        string=_('Tur 1 En İyi Tedarikçi')
    )
    best_offer_round_2 = fields.Monetary(
        compute='_compute_best_offers',
        store=False,
        string=_('Tur 2 En İyi Teklif'),
        currency_field='currency_id'
    )
    best_offer_round_2_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_best_offers',
        store=False,
        string=_('Tur 2 En İyi Tedarikçi')
    )
    improvement_percentage = fields.Float(
        compute='_compute_improvement',
        store=False,
        string=_('İyileştirme %'),
        help=_('Tur 2 vs Tur 1 fiyat iyileştirmesi')
    )

    # ===== EN İYİ TEKLİF (tüm aktif turlar) =====
    best_npv_offer = fields.Monetary(
        compute='_compute_best_npv_offer',
        store=False,
        string=_('En İyi Teklif'),
        currency_field='currency_id',
        help=_('Gönderilmiş/kabul edilmiş teklifler arasındaki en düşük fiyat')
    )
    best_npv_partner_id = fields.Many2one(
        'res.partner',
        compute='_compute_best_npv_offer',
        store=False,
        string=_('En İyi Teklif Tedarikçisi')
    )

    # ===== KANBAN DISPLAY FIELDS =====
    kanban_date_summary = fields.Html(
        compute='_compute_kanban_summaries',
        sanitize=False,
        string=_('Tarih Özeti (Kanban)'),
        help=_('Kanban kartında gösterilecek tarih özeti')
    )
    kanban_line_summary = fields.Html(
        compute='_compute_kanban_summaries',
        sanitize=False,
        string=_('Kalem Özeti (Kanban)'),
        help=_('Kanban kartında gösterilecek senaryo kalem özeti')
    )
    kanban_child_summary = fields.Html(
        compute='_compute_kanban_summaries',
        sanitize=False,
        string=_('Alt Senaryo Özeti (Kanban)'),
        help=_('Kanban kartında gösterilecek alt senaryo özeti')
    )
    kanban_offer_entry_html = fields.Html(
        compute='_compute_kanban_offer_entry_html',
        sanitize=False,
        string=_('Teklif Giriş Özeti (Kanban)'),
        help=_('Tedarikçi fiyat giriş kanbanında gösterilecek offer tablosu')
    )

    # ===== COMPUTED METHODS =====
    
    def _get_scenario_lines_html(self, scenario, font_size):
        """Senaryo kalemlerini HTML olarak döndür."""
        _logger.info('KANBAN LINES | scenario=%s (id=%s) | scenario_line_ids count=%s',
                     scenario.name, scenario.id, len(scenario.scenario_line_ids))
        if not scenario.scenario_line_ids:
            _logger.info('KANBAN LINES | scenario=%s | NO LINES FOUND', scenario.name)
            return ''
        
        lines = scenario.scenario_line_ids.sorted('sequence')
        line_type_icons = {
            'accommodation': 'fa-bed',
            'meal': 'fa-cutlery',
            'transfer': 'fa-bus',
            'technical': 'fa-cogs',
            'flight': 'fa-plane',
            'service': 'fa-wrench',
            'package': 'fa-cube',
            'custom': 'fa-star',
        }
        line_type_labels = {
            'accommodation': 'Konaklama',
            'meal': 'Yemek/F&B',
            'transfer': 'Transfer',
            'technical': 'Teknik',
            'flight': 'Uçuş',
            'service': 'Hizmet',
            'package': 'Paket',
            'custom': 'Diğer',
        }
        line_items = []
        for line in lines:
            icon = line_type_icons.get(line.line_type, 'fa-check-square-o')
            type_label = line_type_labels.get(line.line_type, line.line_type or '')
            display_name = line.name or f'Kalem #{line.sequence}'
            qty_info = f'{int(line.quantity)} kişi' if line.quantity else ''

            # Tip'e özgü ek bilgiler
            type_extras = []
            if line.line_type in ('accommodation', 'package'):
                if line.mice_room_type:
                    type_extras.append(dict(line._fields['mice_room_type'].selection).get(line.mice_room_type, line.mice_room_type))
                if line.mice_meal_plan:
                    type_extras.append(dict(line._fields['mice_meal_plan'].selection).get(line.mice_meal_plan, line.mice_meal_plan))
            elif line.line_type == 'transfer':
                if line.transfer_type:
                    type_extras.append(dict(line._fields['transfer_type'].selection).get(line.transfer_type, line.transfer_type))
            elif line.line_type == 'meal':
                if line.meal_type:
                    type_extras.append(dict(line._fields['meal_type'].selection).get(line.meal_type, line.meal_type))
            elif line.line_type == 'technical':
                if line.technical_service_type:
                    type_extras.append(dict(line._fields['technical_service_type'].selection).get(line.technical_service_type, line.technical_service_type))

            extra_parts = list(filter(None, [qty_info] + type_extras))
            extra_str = f' <span style="color:#6c757d;">({", ".join(extra_parts)})</span>' if extra_parts else ''
            type_badge = f'<span style="display:inline-block;background:#6c757d;color:#fff;border-radius:3px;padding:0 4px;font-size:0.8em;margin-right:4px;">{type_label}</span>'
            line_items.append(
                f'<div style="margin-bottom:3px;font-size:{font_size * 0.9}em;">'
                f'<i class="fa {icon}" style="color:#198754;margin-right:4px;"></i>'
                f'{type_badge}{display_name}{extra_str}'
                f'</div>'
            )

        return f'<div class="mb-2"><small style="color:#6c757d;"><i class="fa fa-tasks" style="margin-right:4px;"></i>Hizmetler ({len(line_items)}):</small><div style="margin-top:4px;">{"".join(line_items)}</div></div>'

    def _get_scenario_dates_html(self, scenario, font_size):
        """Senaryo tarih seçeneklerini HTML olarak döndür."""
        if not scenario.date_option_ids:
            return ''
        dates = scenario.date_option_ids.sorted('sequence')
        date_items = []
        season_colors = {'low': 'success', 'mid': 'info', 'high': 'warning', 'peak': 'danger'}
        for date_opt in dates:
            season_badge = ''
            if date_opt.season_type:
                color = season_colors.get(date_opt.season_type, 'secondary')
                season_label = dict(date_opt._fields["season_type"]._description_selection(self.env)).get(date_opt.season_type, "")
                season_badge = f'<span class="badge text-bg-{color} ms-1" style="font-size: {font_size * 0.75}em;">{season_label}</span>'
            preferred_badge = '<span class="badge text-bg-primary ms-1" style="font-size: {fs}em;">⭐ Tercih Edilen</span>'.format(fs=font_size * 0.75) if date_opt.is_preferred else ''
            date_items.append(f'<div class="mb-1" style="font-size: {font_size * 0.9}em;"><i class="fa fa-calendar-o me-1 text-muted"></i><strong>{date_opt.name or ""}</strong>{season_badge}{preferred_badge}</div>')
        return f'<div class="mb-2"><small class="text-muted"><i class="fa fa-calendar me-1"></i>Tarihler ({len(date_items)}):</small><div class="mt-1">{"".join(date_items)}</div></div>'

    def _get_scenario_header_html(self, scenario, level, font_size):
        """Senaryo başlığını HTML olarak döndür."""
        hotel_name = scenario.hotel_partner_id.name if scenario.hotel_partner_id else scenario.name
        scenario_type_label = scenario.scenario_type_id.name if scenario.scenario_type_id else ""
        type_badge = f'<span class="badge text-bg-info ms-1" style="font-size: {font_size * 0.75}em;">{scenario_type_label}</span>' if scenario_type_label else ''
        icon = 'fa-angle-right' if level == 1 else 'fa-angle-double-right' if level == 2 else 'fa-caret-right'

        # Durum badge'i
        status_map = {
            'active':      ('primary', 'Aktif'),
            'shortlisted': ('success', 'Kısa Listede'),
            'eliminated':  ('danger',  'Elendi'),
            'awarded':     ('warning', '🏆 Kazanan'),
        }
        status_color, status_label = status_map.get(scenario.scenario_status, ('secondary', scenario.scenario_status or ''))
        status_badge = f'<span class="badge text-bg-{status_color} ms-1" style="font-size: {font_size * 0.75}em;">{status_label}</span>'

        # Zorunlu badge'i
        mandatory_badge = f'<span class="badge text-bg-warning ms-1" style="font-size: {font_size * 0.75}em;">Zorunlu</span>' if scenario.is_mandatory else ''

        return f'<div class="mb-2"><strong class="text-primary" style="font-size: {font_size}em;"><i class="fa {icon} me-1"></i>{hotel_name}</strong>{type_badge}{status_badge}{mandatory_badge}</div>'

    @api.depends(
        'date_option_ids', 'date_option_ids.season_type', 'date_option_ids.is_preferred',
        'scenario_line_ids', 'child_ids',
        'scenario_status', 'is_mandatory', 'is_shortlisted',
        'offer_ids', 'offer_ids.state', 'offer_ids.quote_price', 'offer_ids.partner_id',
    )
    def _compute_kanban_summaries(self):
        """Kanban kartı için özet HTML'leri oluştur - 5 Seviye Manuel."""
        season_colors = {'low': 'success', 'mid': 'info', 'high': 'warning', 'peak': 'danger'}
        for scenario in self:
            # 1. Tarih Özeti
            date_html = ''
            if scenario.date_option_ids:
                dates = scenario.date_option_ids.sorted('sequence')
                date_items = []
                for date_opt in dates:
                    season_badge = ''
                    if date_opt.season_type:
                        color = season_colors.get(date_opt.season_type, 'secondary')
                        season_label = dict(date_opt._fields["season_type"]._description_selection(self.env)).get(date_opt.season_type, "")
                        season_badge = f'<span class="badge text-bg-{color} ms-1">{season_label}</span>'
                    preferred_badge = '<span class="badge text-bg-primary ms-1">⭐ Tercih Edilen</span>' if date_opt.is_preferred else ''
                    date_items.append(f'<div class="mb-1 small"><i class="fa fa-calendar-o me-1 text-muted"></i><strong>{date_opt.name or ""}</strong>{season_badge}{preferred_badge}</div>')
                date_html = ''.join(date_items)
            scenario.kanban_date_summary = date_html

            # 2. Ana Senaryo Kalem Özeti
            line_html = ''
            if scenario.scenario_line_ids:
                lines = scenario.scenario_line_ids.sorted('sequence')
                line_type_icons = {
                    'accommodation': 'fa-bed',
                    'meal': 'fa-cutlery',
                    'transfer': 'fa-bus',
                    'technical': 'fa-cogs',
                    'flight': 'fa-plane',
                    'service': 'fa-wrench',
                    'package': 'fa-cube',
                    'custom': 'fa-star',
                }
                line_type_labels = {
                    'accommodation': 'Konaklama',
                    'meal': 'Yemek/F&B',
                    'transfer': 'Transfer',
                    'technical': 'Teknik',
                    'flight': 'Uçuş',
                    'service': 'Hizmet',
                    'package': 'Paket',
                    'custom': 'Diğer',
                }
                line_items = []
                for line in lines:
                    icon = line_type_icons.get(line.line_type, 'fa-check-square-o')
                    type_label = line_type_labels.get(line.line_type, line.line_type or '')
                    display_name = line.name or f'Kalem #{line.sequence}'
                    qty_info = f'{int(line.quantity)} kişi' if line.quantity else ''
                    days_info = f'{int(line.days)} gün' if line.days and line.days > 1 else ''

                    # Tip'e özgü ek bilgiler
                    type_extras = []
                    if line.line_type in ('accommodation', 'package'):
                        if line.mice_room_type:
                            type_extras.append(dict(line._fields['mice_room_type'].selection).get(line.mice_room_type, line.mice_room_type))
                        if line.mice_meal_plan:
                            type_extras.append(dict(line._fields['mice_meal_plan'].selection).get(line.mice_meal_plan, line.mice_meal_plan))
                    elif line.line_type == 'transfer':
                        if line.transfer_type:
                            type_extras.append(dict(line._fields['transfer_type'].selection).get(line.transfer_type, line.transfer_type))
                        if line.vehicle_type:
                            type_extras.append(dict(line._fields['vehicle_type'].selection).get(line.vehicle_type, line.vehicle_type))
                    elif line.line_type == 'meal':
                        if line.meal_type:
                            type_extras.append(dict(line._fields['meal_type'].selection).get(line.meal_type, line.meal_type))
                    elif line.line_type == 'technical':
                        if line.technical_service_type:
                            type_extras.append(dict(line._fields['technical_service_type'].selection).get(line.technical_service_type, line.technical_service_type))

                    extra_parts = list(filter(None, [qty_info, days_info] + type_extras))
                    extra_str = ''
                    if extra_parts:
                        extra_str = f' <span style="color:#6c757d;font-size:0.85em;">({", ".join(extra_parts)})</span>'

                    type_badge = (
                        f'<span style="display:inline-block;background:#6c757d;color:#fff;'
                        f'border-radius:3px;padding:0 4px;font-size:0.75em;margin-right:4px;">'
                        f'{type_label}</span>'
                    )
                    line_items.append(
                        f'<div style="margin-bottom:3px;font-size:0.875em;">'
                        f'<i class="fa {icon}" style="color:#198754;margin-right:4px;"></i>'
                        f'{type_badge}'
                        f'{display_name}'
                        f'{extra_str}'
                        f'</div>'
                    )
                line_html = ''.join(line_items)
            scenario.kanban_line_summary = line_html

            # 3. Alt Senaryolar - 5 Seviye Manuel
            all_children_html = []
            _logger.info('KANBAN CHILD | parent=%s (id=%s) | child_ids count=%s | ids=%s',
                         scenario.name, scenario.id, len(scenario.child_ids), scenario.child_ids.ids)
            
            # SEVİYE 1
            for s1 in scenario.child_ids.sorted('sequence'):
                _logger.info('KANBAN S1 | %s | child_ids count=%s | scenario_line_ids count=%s',
                             s1.name, len(s1.child_ids), len(s1.scenario_line_ids))
                fs1 = max(0.75, 1 - 0.05)
                h1 = self._get_scenario_header_html(s1, 1, fs1)
                d1 = self._get_scenario_dates_html(s1, fs1)
                l1 = self._get_scenario_lines_html(s1, fs1)

                # SEVİYE 2
                s2_htmls = []
                for s2 in s1.child_ids.sorted('sequence'):
                    fs2 = max(0.75, 1 - 0.10)
                    h2 = self._get_scenario_header_html(s2, 2, fs2)
                    d2 = self._get_scenario_dates_html(s2, fs2)
                    l2 = self._get_scenario_lines_html(s2, fs2)

                    # SEVİYE 3
                    s3_htmls = []
                    for s3 in s2.child_ids.sorted('sequence'):
                        fs3 = max(0.75, 1 - 0.15)
                        h3 = self._get_scenario_header_html(s3, 3, fs3)
                        d3 = self._get_scenario_dates_html(s3, fs3)
                        l3 = self._get_scenario_lines_html(s3, fs3)

                        # SEVİYE 4
                        s4_htmls = []
                        for s4 in s3.child_ids.sorted('sequence'):
                            fs4 = max(0.75, 1 - 0.20)
                            h4 = self._get_scenario_header_html(s4, 4, fs4)
                            d4 = self._get_scenario_dates_html(s4, fs4)
                            l4 = self._get_scenario_lines_html(s4, fs4)

                            # SEVİYE 5
                            s5_htmls = []
                            for s5 in s4.child_ids.sorted('sequence'):
                                fs5 = max(0.75, 1 - 0.25)
                                h5 = self._get_scenario_header_html(s5, 5, fs5)
                                d5 = self._get_scenario_dates_html(s5, fs5)
                                l5 = self._get_scenario_lines_html(s5, fs5)
                                s5_htmls.append(f'<div class="mb-2 p-2 border-start border-1 border-muted bg-white" style="margin-left: 60px;">{h5}{d5}{l5}</div>')

                            s4_content = f'{h4}{d4}{l4}'
                            if s5_htmls:
                                s4_content += f'<div class="mt-1">{"".join(s5_htmls)}</div>'
                            s4_htmls.append(f'<div class="mb-2 p-2 border-start border-1 border-muted bg-white" style="margin-left: 45px;">{s4_content}</div>')

                        s3_content = f'{h3}{d3}{l3}'
                        if s4_htmls:
                            s3_content += f'<div class="mt-1">{"".join(s4_htmls)}</div>'
                        s3_htmls.append(f'<div class="mb-2 p-2 border-start border-2 border-secondary bg-white" style="margin-left: 30px;">{s3_content}</div>')

                    s2_content = f'{h2}{d2}{l2}'
                    if s3_htmls:
                        s2_content += f'<div class="mt-1">{"".join(s3_htmls)}</div>'
                    s2_htmls.append(f'<div class="mb-2 p-2 border-start border-3 border-secondary bg-white" style="margin-left: 15px;">{s2_content}</div>')

                s1_content = f'{h1}{d1}{l1}'
                if s2_htmls:
                    s1_content += f'<div class="mt-1">{"".join(s2_htmls)}</div>'
                all_children_html.append(f'<div class="mb-3 p-2 border rounded bg-white">{s1_content}</div>')
            
            scenario.kanban_child_summary = "".join(all_children_html)

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

    @api.depends('scenario_line_ids')
    def _compute_scenario_line_count(self):
        for scenario in self:
            scenario.scenario_line_count = len(scenario.scenario_line_ids)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for scenario in self:
            scenario.line_count = len(scenario.line_ids)

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for scenario in self:
            scenario.offer_count = len(scenario.offer_ids)

    @api.depends('line_ids.computed_target_total')
    def _compute_total_target(self):
        for scenario in self:
            scenario.total_target_price = sum(
                scenario.line_ids.mapped('computed_target_total')
            )

    @api.depends(
        'offer_ids', 'offer_ids.round', 'offer_ids.quote_price',
        'offer_ids.state', 'offer_ids.partner_id'
    )
    def _compute_best_offers(self):
        """Her tur için en düşük teklifi offer_ids üzerinden hesapla."""
        for scenario in self:
            active_offers = scenario.offer_ids.filtered(
                lambda o: o.state in ('submitted', 'accepted')
            )

            def _best_by_round(round_num):
                """İlgili turdaki en iyi (en düşük fiyatlı) teklifi döndür."""
                round_offers = active_offers.filtered(lambda o: o.round == round_num)
                if not round_offers:
                    return 0.0, False
                # Tedarikçi başına toplam fiyat
                by_partner = {}
                for offer in round_offers:
                    pid = offer.partner_id.id if offer.partner_id else 0
                    if pid not in by_partner:
                        by_partner[pid] = {'total': 0.0, 'partner': offer.partner_id}
                    by_partner[pid]['total'] += offer.quote_price
                best = min(by_partner.values(), key=lambda x: x['total'])
                return best['total'], best['partner']

            r1_price, r1_partner = _best_by_round(1)
            r2_price, r2_partner = _best_by_round(2)
            scenario.best_offer_round_1 = r1_price
            scenario.best_offer_round_1_partner_id = r1_partner
            scenario.best_offer_round_2 = r2_price
            scenario.best_offer_round_2_partner_id = r2_partner

    @api.depends('best_offer_round_1', 'best_offer_round_2')
    def _compute_improvement(self):
        for scenario in self:
            r1 = scenario.best_offer_round_1
            r2 = scenario.best_offer_round_2
            if r1 and r2:
                scenario.improvement_percentage = ((r1 - r2) / r1) * 100
            else:
                scenario.improvement_percentage = 0.0

    @api.depends(
        'offer_ids', 'offer_ids.partner_id', 'offer_ids.round',
        'offer_ids.quote_price', 'offer_ids.state',
        'offer_ids.scenario_line_id', 'offer_ids.scenario_line_id.name',
        'offer_ids.scenario_line_id.line_type',
        'child_ids', 'child_ids.offer_ids',
        'child_ids.scenario_line_ids',
        'scenario_line_ids',
    )
    def _compute_kanban_offer_entry_html(self):
        """
        Teklif giriş kanbanı için senaryo ağacını HTML olarak render eder.
        Tüm tedarikçilerin teklifleri gösterilir:
          satır = senaryo kalemi, kolon = tedarikçi adı + fiyatı
        """
        line_type_labels = {
            'accommodation': 'Konaklama', 'meal': 'Yemek/F&B',
            'transfer': 'Transfer', 'technical': 'Teknik',
            'flight': 'Uçuş', 'service': 'Hizmet',
            'package': 'Paket', 'custom': 'Diğer',
        }
        state_colors = {
            'draft': '#fff3cd', 'submitted': '#d1ecf1',
            'accepted': '#d4edda', 'rejected': '#f8d7da',
        }
        status_colors_map = {
            'active': '#0d6efd', 'shortlisted': '#198754',
            'eliminated': '#dc3545', 'awarded': '#ffc107',
        }

        is_supplier = self.env.user.has_group('ak_tender_mice.group_tender_supplier')
        current_partner = self.env.user.partner_id if is_supplier else None

        for scenario in self:
            html = scenario._render_offer_tree_html(partner=current_partner)
            scenario.kanban_offer_entry_html = html or (
                '<div style="color:#aaa;font-size:0.85em;">İçerik yok</div>'
            )

    # ===== OFFER AĞACI RENDER METODU =====

    _OFFER_LINE_TYPE_LABELS = {
        'accommodation': 'Konaklama', 'meal': 'Yemek/F&B',
        'transfer': 'Transfer', 'technical': 'Teknik',
        'flight': 'Uçuş', 'service': 'Hizmet',
        'package': 'Paket', 'custom': 'Diğer',
    }
    _OFFER_STATE_COLORS = {
        'draft': '#fff3cd', 'submitted': '#d1ecf1',
        'accepted': '#d4edda', 'rejected': '#f8d7da',
    }
    _OFFER_STATUS_COLORS = {
        'active': '#0d6efd', 'shortlisted': '#198754',
        'eliminated': '#dc3545', 'awarded': '#ffc107',
    }

    def _fmt_offer_price(self, offer):
        """Fiyatı formatlar; fiyat yoksa tire döner."""
        if not offer or not offer.quote_price:
            return '<span style="color:#aaa;">—</span>'
        sym = offer.currency_id.symbol or ''
        bg = self._OFFER_STATE_COLORS.get(offer.state, '')
        style = f'background:{bg};padding:0 3px;border-radius:2px;' if bg else ''
        return f'<span style="{style}font-weight:600;">{offer.quote_price:,.0f} {sym}</span>'

    def _render_offer_tree_html(self, partner=None, indent_px=0):
        """
        Bu senaryonun kalemlerini + alt senaryolarını HTML olarak render eder.

        :param partner: res.partner kaydı — sadece bu tedarikçinin kolonu gösterilir.
                        None ise tüm tedarikçi kolonları gösterilir.
        :param indent_px: sol girinti (px)
        :return: HTML string
        """
        self.ensure_one()
        parts = []

        # --- Senaryo başlığı ---
        hotel = self.hotel_partner_id.name or self.name
        type_label = self.scenario_type_id.name or ''
        type_badge = (
            f'<span style="background:#17a2b8;color:#fff;border-radius:3px;'
            f'padding:0 4px;font-size:0.78em;margin-right:4px;">{type_label}</span>'
            if type_label else ''
        )
        s_color = self._OFFER_STATUS_COLORS.get(self.scenario_status, '#6c757d')
        header = (
            f'<div style="margin-left:{indent_px}px;margin-bottom:4px;'
            f'border-left:3px solid {s_color};padding-left:6px;">'
            f'<strong style="font-size:0.92em;">{type_badge}{hotel}</strong>'
        )
        if self.meal_plan:
            meal_labels = dict(self._fields['meal_plan'].selection)
            header += (
                f' <span style="color:#6c757d;font-size:0.8em;">'
                f'· {meal_labels.get(self.meal_plan, "")}</span>'
            )
        header += '</div>'
        parts.append(header)

        # --- Offer tablosu ---
        all_offers = self.offer_ids.filtered(lambda o: o.round > 0)
        if all_offers:
            max_round = max(all_offers.mapped('round'), default=1)
            round_offers = all_offers.filtered(lambda o: o.round == max_round)

            if partner:
                partners = round_offers.mapped('partner_id').filtered(
                    lambda p: p.id == partner.id
                ).sorted('name')
            else:
                partners = round_offers.mapped('partner_id').sorted('name')

            if not partners:
                parts.append(
                    f'<div style="margin-left:{indent_px + 12}px;color:#aaa;'
                    f'font-size:0.82em;margin-bottom:4px;">Henüz teklif yok</div>'
                )
            else:
                all_lines = round_offers.mapped('scenario_line_id').filtered(bool).sorted('sequence')
                has_package = round_offers.filtered(lambda o: not o.scenario_line_id)

                offer_map = {}
                for o in round_offers:
                    key = (o.scenario_line_id.id if o.scenario_line_id else False, o.partner_id.id)
                    offer_map[key] = o

                th_partner = ''.join(
                    f'<th style="padding:2px 5px;background:#495057;color:#fff;'
                    f'text-align:right;white-space:nowrap;">{p.name}</th>'
                    for p in partners
                )
                table = (
                    f'<div style="margin-left:{indent_px + 12}px;margin-bottom:8px;overflow-x:auto;">'
                    f'<table style="width:100%;border-collapse:collapse;font-size:0.83em;">'
                    f'<thead><tr>'
                    f'<th style="padding:2px 5px;background:#495057;color:#fff;text-align:left;">Kalem</th>'
                    f'{th_partner}'
                    f'</tr></thead><tbody>'
                )

                def _row(line_id, line_label):
                    tds = ''.join(
                        f'<td style="padding:2px 5px;text-align:right;">'
                        f'{self._fmt_offer_price(offer_map.get((line_id, p.id)))}</td>'
                        for p in partners
                    )
                    return f'<tr><td style="padding:2px 5px;">{line_label}</td>{tds}</tr>'

                for line in all_lines:
                    tl = self._OFFER_LINE_TYPE_LABELS.get(line.line_type, '')
                    badge = (
                        f'<span style="background:#6c757d;color:#fff;border-radius:3px;'
                        f'padding:0 3px;font-size:0.75em;margin-right:3px;">{tl}</span>'
                        if tl else ''
                    )
                    table += _row(line.id, f'{badge}{line.name or "(İsimsiz)"}')

                if has_package:
                    table += _row(False, '<em>Genel / Paket</em>')

                table += '</tbody></table></div>'
                parts.append(table)
        elif not self.child_ids:
            parts.append(
                f'<div style="margin-left:{indent_px + 12}px;color:#aaa;'
                f'font-size:0.82em;margin-bottom:4px;">Henüz teklif yok</div>'
            )

        # --- Alt senaryolar (recursive) ---
        for child in self.child_ids.sorted('sequence'):
            parts.append(child._render_offer_tree_html(partner=partner, indent_px=indent_px + 16))

        return ''.join(parts)

    @api.depends(
        'offer_ids', 'offer_ids.quote_price',
        'offer_ids.state', 'offer_ids.partner_id', 'offer_ids.round'
    )
    def _compute_best_npv_offer(self):
        """Gönderilmiş/kabul edilmiş teklifler arasındaki en iyi fiyatı bul."""
        for scenario in self:
            active_offers = scenario.offer_ids.filtered(
                lambda o: o.state in ('submitted', 'accepted') and o.round > 0
            )
            if not active_offers:
                scenario.best_npv_offer = 0.0
                scenario.best_npv_partner_id = False
                continue

            # Tedarikçi başına toplam teklif fiyatı (tüm aktif turlar dahil son tur alınır)
            # En güncel turu bulmak için: en yüksek round numaralı teklifleri kullan
            max_round = max(active_offers.mapped('round'), default=0)
            latest_offers = active_offers.filtered(lambda o: o.round == max_round)

            by_partner = {}
            for offer in latest_offers:
                if not offer.partner_id:
                    continue
                pid = offer.partner_id.id
                if pid not in by_partner:
                    by_partner[pid] = {'total': 0.0, 'partner': offer.partner_id}
                by_partner[pid]['total'] += offer.quote_price

            if by_partner:
                best = min(by_partner.values(), key=lambda x: x['total'])
                scenario.best_npv_offer = best['total']
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

    # ===== DEFAULT GET =====

    @api.model
    def default_get(self, fields_list):
        """Context'teki default_scenario_type (code string) → scenario_type_id'ye çevir.
        Kod verilmemişse is_default=True olan tipi varsayılan seç."""
        res = super().default_get(fields_list)
        if 'scenario_type_id' not in res:
            ScenarioType = self.env['ak.tender.scenario.type']
            code = self.env.context.get('default_scenario_type')
            if code:
                stype = ScenarioType.search([('code', '=', code)], limit=1)
            else:
                stype = ScenarioType.search([('is_default', '=', True)], limit=1)
            if stype:
                res['scenario_type_id'] = stype.id
        return res

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
        """Senaryo bazlı teklif karşılaştırma (ak.tender.scenario.offer listesi)."""
        self.ensure_one()
        return {
            'name': _('Teklifler: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.offer',
            'view_mode': 'list,form',
            'domain': [('scenario_id', '=', self.id)],
            'context': {
                'default_scenario_id': self.id,
                'group_by': 'round',
            },
        }

    def action_view_offers(self):
        """Bu senaryonun tekliflerini listele."""
        self.ensure_one()
        return {
            'name': _('Teklifler: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.offer',
            'view_mode': 'list,form',
            'domain': [('scenario_id', '=', self.id)],
            'context': {
                'default_scenario_id': self.id,
            },
        }

    def action_view_scenario_lines(self):
        """Senaryo kalemlerini görüntüle."""
        self.ensure_one()
        return {
            'name': _('%s — Senaryo Kalemleri') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario.line',
            'view_mode': 'list,form,kanban',
            'domain': [('scenario_id', '=', self.id)],
            'context': {
                'default_scenario_id': self.id,
            },
        }

    def action_view_lines(self):
        """İhale kalemlerini görüntüle."""
        self.ensure_one()
        return {
            'name': _('%s — İhale Kalemleri') % self.name,
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
                'default_scenario_type': 'location_hotel',  # default_get bunu scenario_type_id'ye çevirir
            },
        }

    def action_add_packages(self):
        """Paket ekleme sihirbazını aç."""
        self.ensure_one()
        return {
            'name': _('Paket Ekle'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.add.packages.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_scenario_id': self.id,
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

    def _deep_copy_with_children(self, new_parent_id=None, default=None):
        """
        Senaryoyu tüm alt senaryolar, senaryo kalemleri ve tarih seçenekleriyle
        birlikte derin (recursive) kopya yapar.

        Alt senaryolar da aynı şekilde kopyalanır (sınırsız derinlik).
        """
        self.ensure_one()
        copy_defaults = {
            'scenario_status': 'active',
            'is_shortlisted': False,
            'shortlist_round': 0,
            'shortlist_date': False,
            'shortlist_by': False,
            'elimination_reason': False,
            # Alt kayıtları manuel kopyalayacağız — auto-copy'yi engelle
            'child_ids': [(5, 0, 0)],
            'date_option_ids': [(5, 0, 0)],
            'scenario_line_ids': [(5, 0, 0)],
        }
        # Üst seviye kopyalamada ad sonuna "(Kopya)" ekle
        if not new_parent_id:
            copy_defaults['name'] = _('%s (Kopya)') % self.name
        if new_parent_id:
            copy_defaults['parent_id'] = new_parent_id
        if default:
            copy_defaults.update(default)

        new_scenario = super(AkTenderScenario, self).copy(copy_defaults)

        # 1. Tarih seçeneklerini kopyala
        for date_opt in self.date_option_ids.sorted('sequence'):
            date_opt.copy({'scenario_id': new_scenario.id})

        # 2. Senaryo kalemlerini kopyala
        for line in self.scenario_line_ids.sorted('sequence'):
            line.copy({'scenario_id': new_scenario.id})

        # 3. Alt senaryoları recursive kopyala
        for child in self.child_ids.sorted('sequence'):
            child._deep_copy_with_children(
                new_parent_id=new_scenario.id,
                default={'tender_id': new_scenario.tender_id.id},
            )

        _logger.info(
            'DEEP COPY | "%s" (id=%s) → "%s" (id=%s) | lines=%s dates=%s children=%s',
            self.name, self.id,
            new_scenario.name, new_scenario.id,
            len(self.scenario_line_ids),
            len(self.date_option_ids),
            len(self.child_ids),
        )
        return new_scenario

    def copy(self, default=None):
        """Senaryo kopyala: tüm alt senaryolar, kalemleri ve tarih seçenekleriyle derin kopya."""
        self.ensure_one()
        return self._deep_copy_with_children(default=default)

    def action_copy_scenario(self):
        """Senaryoyu tüm içeriğiyle kopyala ve yeni senaryoyu forma aç."""
        self.ensure_one()
        new_scenario = self._deep_copy_with_children()
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
