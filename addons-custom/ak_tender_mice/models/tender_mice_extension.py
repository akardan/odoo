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
    
    # Sadece ilk seviye senaryolar (Bölge/Lokasyon)
    root_scenario_ids = fields.One2many(
        'ak.tender.scenario',
        'tender_id',
        string=_('Ana Senaryolar'),
        domain=[('parent_id', '=', False)],
        help=_("Sadece üst seviye (bölge) senaryolar.")
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

    # ===== TEDARİKÇİ TEKLIF KARTLARI =====
    supplier_offer_cards_html = fields.Html(
        compute='_compute_supplier_offer_cards_html',
        string=_('Tedarikçi Teklif Kartları'),
        sanitize=False,
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

    @api.depends(
        'invited_partners',
        'scenario_ids.offer_ids.state',
        'scenario_ids.offer_ids.quote_price',
        'scenario_ids.offer_ids.partner_id',
        'scenario_ids.offer_ids.round',
        'scenario_ids.offer_ids.scenario_line_id',
        'scenario_ids.child_ids.offer_ids',
    )
    def _compute_supplier_offer_cards_html(self):
        """
        Davetli her tedarikçi için ayrı bir kart HTML'i üretir.
        Her kart, mevcut Teklifler kanban kartıyla aynı senaryo ağacını gösterir —
        ancak yalnızca o tedarikçinin fiyat sütunuyla.
        """
        for tender in self:
            if tender.tender_type != 'mice' or not tender.invited_partners:
                tender.supplier_offer_cards_html = ''
                continue

            root_scenarios = tender.scenario_ids.filtered(lambda s: not s.parent_id)
            status_labels = {
                'active': ('Aktif', 'text-bg-primary'),
                'shortlisted': ('Kısa Listede', 'text-bg-success'),
                'eliminated': ('Elendi', 'text-bg-danger'),
                'awarded': ('Kazanan', 'text-bg-warning'),
            }

            # Her kart bir sütun: yan yana dizilir, ekran genişliğine göre 1-2 kart
            html = '<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start;">'

            for partner in tender.invited_partners:
                # --- Kart body: senaryo ağacı bu partner için ---
                body_parts = []
                for scenario in root_scenarios.sorted('sequence'):
                    # Senaryo başlığı (kart içindeki senaryo bölümü)
                    st_label, st_badge = status_labels.get(
                        scenario.scenario_status, ('', 'text-bg-secondary')
                    )
                    sc_header = (
                        f'<div style="margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #dee2e6;">'
                        f'<strong style="font-size:0.95em;">Senaryo: {scenario.name}</strong>'
                    )
                    if scenario.scenario_type_id:
                        sc_header += (
                            f'<span class="badge text-bg-info ms-1">{scenario.scenario_type_id.name}</span>'
                        )
                    if scenario.is_mandatory:
                        sc_header += '<span class="badge text-bg-warning ms-1">Zorunlu</span>'
                    if st_label:
                        sc_header += f'<span class="badge {st_badge} ms-1">{st_label}</span>'
                    sc_header += '</div>'

                    # Lokasyon ve kişi bilgisi
                    meta = ''
                    if scenario.location_id:
                        meta += (
                            f'<div style="font-size:0.85em;margin-bottom:2px;">'
                            f'&#128205; {scenario.location_id.name}</div>'
                        )
                    if scenario.person_count:
                        vip_str = f' ({scenario.vip_count} VIP)' if scenario.vip_count else ''
                        meta += (
                            f'<div style="font-size:0.85em;margin-bottom:6px;">'
                            f'&#128101; {scenario.person_count} kişi{vip_str}</div>'
                        )

                    # Senaryo ağacı (sadece bu partner sütunu)
                    tree_html = scenario._render_offer_tree_html(partner=partner)

                    body_parts.append(sc_header + meta + tree_html)

                card_body = ''.join(body_parts) or (
                    '<div style="color:#aaa;font-size:0.85em;">Henüz teklif yok</div>'
                )

                html += (
                    '<div style="flex:1;min-width:400px;max-width:600px;'
                    'border:1px solid #dee2e6;border-radius:8px;background:#fff;'
                    'overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);">'

                    # Kart başlığı — tedarikçi adı
                    '<div style="background:#343a40;color:#fff;padding:10px 16px;'
                    'font-weight:600;font-size:1em;display:flex;align-items:center;gap:8px;">'
                    '<span style="font-size:1.1em;">&#127968;</span>'
                    f'{partner.name}'
                    '</div>'

                    # İçerik
                    f'<div style="padding:14px 16px;">{card_body}</div>'

                    '</div>'
                )

            html += '</div>'
            tender.supplier_offer_cards_html = html

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

    def create_purchase_orders_for_suppliers(self):
        """
        MICE ihalelerde PO yerine senaryo teklif talepleri oluşturur.
        Diğer ihale tiplerinde standart davranışı devam ettirir.
        """
        self.ensure_one()
        if self.tender_type != 'mice':
            return super().create_purchase_orders_for_suppliers()

        # MICE: invited_partners kontrolü
        partners = self.invited_partners
        if not partners:
            # Fallback: senaryolardaki hotel_partner_id'leri kullan
            partners = self.scenario_ids.mapped('hotel_partner_id').filtered(bool)

        if not partners:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Uyarı'),
                    'message': _('Davetli tedarikçi bulunamadı. Lütfen önce tedarikçi ekleyin.'),
                    'sticky': False,
                    'type': 'warning',
                },
            }

        round_num = self.tender_round or 1
        created = self.create_mice_offer_requests(round_num, partner_ids=partners)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Teklif Talepleri Oluşturuldu'),
                'message': _(
                    'Tur %d için %d tedarikçiye %d teklif talebi oluşturuldu.'
                ) % (round_num, len(partners), len(created)),
                'sticky': False,
                'type': 'success' if created else 'warning',
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

    def create_mice_offer_requests(self, round_num, partner_ids=None):
        """
        Senaryo ağacını tarayarak teklif talebi (ak.tender.scenario.offer) kayıtları oluşturur.

        Kural:
            - Kök (region) senaryolar atlanır.
            - Senaryo kalemleri (scenario_line_ids) varsa → kalem bazında offer
            - Senaryo kalemleri yoksa → senaryo geneli (paket) offer
            - Zaten var olan (scenario, line, round, partner) kombinasyonları atlanır.

        :param round_num:   Tur numarası (int)
        :param partner_ids: res.partner kayıtları (recordset); None ise tüm senaryoların
                            hotel_partner_id'si kullanılır.
        :return: oluşturulan offer kayıtları
        """
        self.ensure_one()
        Offer = self.env['ak.tender.scenario.offer']
        created = Offer

        # Kök olmayan, elenmemiş tüm senaryolar
        scenarios = self.scenario_ids.filtered(
            lambda s: not s.type_is_root and s.scenario_status not in ('eliminated',)
        )

        # Tedarikçi listesi belirle
        if partner_ids is None:
            # Senaryolarda tanımlı otel/mekan partnerları kullan
            partner_ids = scenarios.mapped('hotel_partner_id').filtered(bool)

        if not partner_ids:
            return created

        for scenario in scenarios:
            lines = scenario.scenario_line_ids or self.env['ak.tender.scenario.line']

            for partner in partner_ids:
                if lines:
                    for line in lines:
                        offer = self._create_single_offer(
                            Offer, scenario, line, None, partner, round_num
                        )
                        if offer:
                            created |= offer
                else:
                    # Kalem yok — senaryo geneli paket fiyatı
                    offer = self._create_single_offer(
                        Offer, scenario, None, None, partner, round_num
                    )
                    if offer:
                        created |= offer

        return created

    def _create_single_offer(self, Offer, scenario, line, date_opt, partner, round_num):
        """Tek bir offer oluştur. Zaten varsa False döndür."""
        domain = [
            ('scenario_id', '=', scenario.id),
            ('round', '=', round_num),
            ('partner_id', '=', partner.id),
            ('scenario_line_id', '=', line.id if line else False),
            ('date_option_id', '=', date_opt.id if date_opt else False),
        ]
        if Offer.search_count(domain):
            return False
        return Offer.create({
            'scenario_id': scenario.id,
            'round': round_num,
            'partner_id': partner.id,
            'scenario_line_id': line.id if line else False,
            'date_option_id': date_opt.id if date_opt else False,
        })

    def action_open_offer_entry(self):
        """Tedarikçi fiyat giriş kanban'ını aç."""
        self.ensure_one()
        return {
            'name': _('%s — Teklif Girişi') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.scenario',
            'view_mode': 'kanban,list,form',
            'views': [
                (self.env.ref('ak_tender_mice.view_scenario_offer_entry_kanban').id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': [
                ('tender_id', '=', self.id),
                ('parent_id', '=', False),
            ],
            'context': {
                'default_tender_id': self.id,
                'offer_entry_mode': True,
                'active_round': getattr(self, 'tender_round', 1) or 1,
            },
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
        """Satır tipi değiştiğinde uygun UoM otomatik ayarla.
        Türkçe UoM adı aramak yerine 'Time' veya 'Unit' kategorisi üzerinden arar.
        """
        if self.line_type == 'accommodation':
            # Konaklama için: zaman/gün kategorisinde day/gece UoM ara
            uom = self.env['uom.uom'].search(
                [('category_id.name', 'in', ['Time', 'Zaman', 'Days'])],
                limit=1
            )
            if not uom:
                # Kategori bulunamazsa isimle ara (yedek)
                uom = self.env['uom.uom'].search(
                    [('name', 'in', ['day(s)', 'Days', 'Gece', 'Day'])],
                    limit=1
                )
            if uom:
                self.uom_id = uom
        elif self.line_type in ('meal', 'service'):
            # Kişi için: birim/adet kategorisinde ara
            uom = self.env['uom.uom'].search(
                [('category_id.name', 'in', ['Unit(s)', 'Units', 'Birim'])],
                limit=1
            )
            if not uom:
                # Yedek: isimle ara
                uom = self.env['uom.uom'].search(
                    [('name', 'in', ['Unit(s)', 'Units', 'Kişi', 'Person'])],
                    limit=1
                )
            if uom:
                self.uom_id = uom
