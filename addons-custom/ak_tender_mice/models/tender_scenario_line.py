# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AkTenderScenarioLine(models.Model):
    """
    Senaryo Kalemleri (Scenario Items)
    
    İhale kalemlerinden (ak.tender.line) farklı olarak, senaryoya özel
    kalemlerdir. Senaryo planlaması sırasında kullanılır ve daha sonra
    ihale kalemlerine dönüştürülebilir.
    
    Kullanım Alanları:
    - Senaryo oluşturma aşamasında tahmini kalemler
    - Farklı senaryo alternatifleri için özel kalemler
    - Tedarikçi karşı tekliflerindeki özel kalemler
    """
    _name = 'ak.tender.scenario.line'
    _description = 'Senaryo Kalemi'
    _order = 'sequence, id'

    # ===== TEMEL BİLGİLER =====
    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        required=True,
        ondelete='cascade',
        string=_('Senaryo'),
        index=True
    )

    name = fields.Char(
        string=_('Açıklama'),
        required=True,
        help=_("Kalem açıklaması (örn: 'Deluxe Oda - Deniz Manzaralı')")
    )
    sequence = fields.Integer(default=10, string=_('Sıra'))
    active = fields.Boolean(default=True, string=_('Aktif'))

    # ===== ÜRÜN BİLGİSİ =====
    product_id = fields.Many2one(
        'product.product',
        string=_('Ürün'),
        domain=[('purchase_ok', '=', True)],
        help=_("İlişkili ürün (opsiyonel)")
    )
    product_template_id = fields.Many2one(
        'product.template',
        related='product_id.product_tmpl_id',
        string=_('Ürün Şablonu'),
        readonly=True
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
        default='accommodation',
        required=True,
        help=_("MICE hizmet kategorisi. Raporlama ve filtrelemede kullanılır.")
    )

    # ===== MİKTAR VE BİRİM =====
    quantity = fields.Float(
        string=_('Miktar'),
        default=1.0,
        digits='Product Unit of Measure',
        help=_("Kişi sayısı, oda sayısı veya hizmet adedi")
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string=_('Birim'),
        domain="[('category_id', '=', product_uom_category_id)]",
        help=_("Ölçü birimi (Kişi, Gece, Adet vb.)")
    )
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
        readonly=True
    )
    
    days = fields.Integer(
        string=_('Gün Sayısı'),
        default=1,
        help=_("Konaklama için gece sayısı, diğer hizmetler için süre")
    )

    # ===== FİYATLANDIRMA =====
    currency_id = fields.Many2one(
        related='scenario_id.currency_id',
        string=_('Para Birimi'),
        store=True,
        readonly=True
    )
    
    target_price = fields.Monetary(
        string=_('Hedef Birim Fiyat'),
        currency_field='currency_id',
        help=_("Kişi başı veya birim başı hedef fiyat")
    )
    
    computed_target_total = fields.Monetary(
        compute='_compute_target_total',
        store=True,
        string=_('Toplam Hedef'),
        help=_('Miktar × Gün × Birim Fiyat'),
        currency_field='currency_id'
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

    # ===== TRANSFER ÖZEL ALANLAR =====
    transfer_type = fields.Selection([
        ('airport_hotel', _('Havalimanı - Otel')),
        ('hotel_airport', _('Otel - Havalimanı')),
        ('hotel_venue', _('Otel - Etkinlik Mekanı')),
        ('city_tour', _('Şehir Turu')),
        ('custom', _('Özel Transfer')),
    ], string=_('Transfer Tipi'))
    
    vehicle_type = fields.Selection([
        ('sedan', _('Sedan')),
        ('minivan', _('Minivan')),
        ('minibus', _('Minibüs')),
        ('bus', _('Otobüs')),
        ('vip', _('VIP Araç')),
    ], string=_('Araç Tipi'))

    # ===== YEMEK ÖZEL ALANLAR =====
    meal_type = fields.Selection([
        ('breakfast', _('Kahvaltı')),
        ('lunch', _('Öğle Yemeği')),
        ('dinner', _('Akşam Yemeği')),
        ('coffee_break', _('Kahve Molası')),
        ('cocktail', _('Kokteyl')),
        ('gala_dinner', _('Gala Yemeği')),
    ], string=_('Yemek Tipi'))
    
    menu_type = fields.Selection([
        ('buffet', _('Açık Büfe')),
        ('set_menu', _('Set Menü')),
        ('a_la_carte', _('A la Carte')),
    ], string=_('Menü Tipi'))

    # ===== TEKNİK HİZMET ÖZEL ALANLAR =====
    technical_service_type = fields.Selection([
        ('av_equipment', _('Ses/Görüntü Ekipmanı')),
        ('stage_setup', _('Sahne Kurulumu')),
        ('lighting', _('Işıklandırma')),
        ('internet', _('İnternet/WiFi')),
        ('translation', _('Tercüme/Simultane')),
        ('recording', _('Kayıt/Yayın')),
    ], string=_('Teknik Hizmet Tipi'))

    # ===== ÖZET BİLGİ =====
    line_summary = fields.Char(
        compute='_compute_line_summary',
        store=True,
        string=_('Özet'),
        help=_("Otomatik oluşturulan kullanıcı dostu özet")
    )

    # ===== NOTLAR =====
    notes = fields.Text(string=_('Notlar'))

    # ===== COMPUTED METHODS =====

    @api.depends('quantity', 'days', 'target_price')
    def _compute_target_total(self):
        for line in self:
            q = line.quantity or 0.0
            d = line.days or 1
            p = line.target_price or 0.0
            # MICE konaklama: gün × kişi × birim fiyat
            line.computed_target_total = q * d * p

    @api.depends(
        'mice_room_type', 'mice_view_type', 'mice_amenities',
        'mice_meal_plan', 'scenario_id.meal_plan',
        'scenario_id.hotel_partner_id', 'name', 'line_type',
        'transfer_type', 'vehicle_type', 'meal_type', 'menu_type',
        'technical_service_type'
    )
    def _compute_line_summary(self):
        """Otomatik özet oluştur: tip bazlı bilgiler."""
        room_labels = dict(self._fields['mice_room_type']._description_selection(self.env))
        view_labels = dict(self._fields['mice_view_type']._description_selection(self.env))

        for line in self:
            parts = []
            
            # Senaryo oteli
            if line.scenario_id and line.scenario_id.hotel_partner_id:
                parts.append(line.scenario_id.hotel_partner_id.name)
            
            # Satır tipine göre özel bilgiler
            if line.line_type == 'accommodation':
                if line.mice_room_type:
                    parts.append(room_labels.get(line.mice_room_type, ''))
                meal = line.mice_meal_plan or (line.scenario_id.meal_plan if line.scenario_id else False)
                if meal:
                    meal_labels = dict(line._fields['mice_meal_plan']._description_selection(self.env))
                    parts.append(meal_labels.get(meal, ''))
                if line.mice_view_type:
                    parts.append(view_labels.get(line.mice_view_type, ''))
                if line.mice_amenities:
                    top_amenities = line.mice_amenities.split(',')[:2]
                    parts.append(f"({', '.join(a.strip() for a in top_amenities)})")
            
            elif line.line_type == 'transfer':
                if line.transfer_type:
                    transfer_labels = dict(line._fields['transfer_type']._description_selection(self.env))
                    parts.append(transfer_labels.get(line.transfer_type, ''))
                if line.vehicle_type:
                    vehicle_labels = dict(line._fields['vehicle_type']._description_selection(self.env))
                    parts.append(vehicle_labels.get(line.vehicle_type, ''))
            
            elif line.line_type == 'meal':
                if line.meal_type:
                    meal_type_labels = dict(line._fields['meal_type']._description_selection(self.env))
                    parts.append(meal_type_labels.get(line.meal_type, ''))
                if line.menu_type:
                    menu_labels = dict(line._fields['menu_type']._description_selection(self.env))
                    parts.append(menu_labels.get(line.menu_type, ''))
            
            elif line.line_type == 'technical':
                if line.technical_service_type:
                    tech_labels = dict(line._fields['technical_service_type']._description_selection(self.env))
                    parts.append(tech_labels.get(line.technical_service_type, ''))
            
            line.line_summary = ' | '.join(filter(None, parts)) or line.name or ''

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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Ürün seçildiğinde adı ve UoM'u otomatik doldur."""
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name
            if not self.uom_id:
                self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id


    # ===== CONSTRAINTS =====

    @api.constrains('quantity', 'days')
    def _check_positive_values(self):
        """Miktar ve gün sayısı pozitif olmalı."""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Miktar sıfırdan büyük olmalıdır!'))
            if line.days <= 0:
                raise ValidationError(_('Gün sayısı sıfırdan büyük olmalıdır!'))
