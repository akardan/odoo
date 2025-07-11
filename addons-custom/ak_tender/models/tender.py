# -*- coding: utf-8 -*-

# ak_tender/models/tender.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AkTenderLine(models.Model):
    _name = 'ak.tender.line'
    _description = _('İhale Kalemi')
    _order = 'sequence, id'

    sequence = fields.Integer(string=_('Sıra'), default=10)
    tender_id = fields.Many2one('ak.tender', string=_('İhale'), required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string=_('Ürün/Malzeme'), required=True,
                                 help=_("İhale edilecek ürün veya malzeme."))
    name = fields.Char(string=_('Açıklama'), related='product_id.name', readonly=True)
    quantity = fields.Float(string=_('Miktar'), required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', string=_('Birim'), related='product_id.uom_id', readonly=True)
    required_delivery_date = fields.Date(string=_('Gerekli Teslim Tarihi'),
                                         help=_("İstenen teslimat tarihi."))

class AkTender(models.Model):
    _name = 'ak.tender'
    _description = _('İLKOis Tender')
    _inherit = ['ak.workflow.mixin', 'mail.thread', 'mail.activity.mixin']
    # Dummy field to allow smooth upgrade from previous versions
    state = fields.Char(string="State (deprecated)", help="Technical field for upgrade purpose. Not used anymore.", store=False)

    name = fields.Char(string=_('İhale Adı'), required=True, copy=False,
                       help=_("İhale sürecinin başlığı veya kısa adı."))
    code = fields.Char(string=_('İhale Kodu'), required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    
    # ERP Entegrasyon Alanları (Simülasyon)
    erp_pr_id = fields.Char(string=_('ERP SAT No'), copy=False,
                             help=_("İlgili ERP Satın Alma Talebi Numarası (entegrasyon ile gelecek)."))
    erp_company_code = fields.Char(string=_('ERP Şirket Kodu'), help=_("İlgili ERP Şirket Kodu (entegrasyon ile gelecek)."))
    erp_plant_code = fields.Char(string=_('ERP Tesis Kodu'), help=_("İlgili ERP Tesis Kodu (entegrasyon ile gelecek)."))
    
    # TEKLİF DOKÜMANINA GÖRE REVİZE EDİLEN DURUM ALANI

    tender_type = fields.Selection([
        ('standard', _('Standart İhale')), # Tek bir tur
        ('open_auction', _('Açık Eksiltme (Açık İhale)')), # Birden fazla tur, hedef fiyat ile
        ('sealed_bid', _('Kapalı Zarf Teklif')), # Genelde tek tur ama hedef fiyat ile revizyon olabilir
    ], string=_('İhale Tipi'), default='standard', required=True)

    start_date = fields.Datetime(string=_('Başlangıç Tarihi'), default=fields.Datetime.now(), required=True)
    end_date = fields.Datetime(string=_('Bitiş Tarihi'), required=True)
    description = fields.Html(string=_('İhale Açıklaması'),
                              help=_("İhale ile ilgili detaylı bilgiler ve şartnameler."))
    
    # İhale Kalemleri (One2many ilişki) - İhalenin temelini oluşturur
    tender_lines = fields.One2many('ak.tender.line', 'tender_id', string=_('İhale Kalemleri'), required=True)

    # Davetli Tedarikçiler (Many2many ilişki)
    invited_partners = fields.Many2many('res.partner', string=_('Davetli Tedarikçiler'),
                                       domain=[('supplier_rank', '>=', 0)],
                                       help=_("Bu ihaleye davet edilecek tedarikçiler."))

    # İhale Sonuçları (One2many ilişki)
    purchase_order_ids = fields.One2many('purchase.order', 'tender_id', string=_('Teklifler (SAT)'))
    
    # Kazanan Teklif ve Hedef Fiyat (Raporlama için)
    winning_order_id = fields.Many2one('purchase.order', string=_('Kazanan Teklif (SAS)'), compute='_compute_winning_order', store=True, readonly=True)
    
    # TEKLİF DOKÜMANINA GÖRE KRİTİK ALAN: HEDEF FİYAT
    target_price = fields.Monetary(string=_('Hedef Fiyat'), currency_field='currency_id',
                                   help=_("Satın Alma Direktörü tarafından belirlenen hedef fiyat."),
                                   tracking=True) # Değişiklikleri takip et
    currency_id = fields.Many2one('res.currency', string=_('Para Birimi'), default=lambda self: self.env.company.currency_id)
    
    # Onay Mekanizması için alanlar
    
    # Akıllı Butonlar için compute field'lar
    purchase_order_count = fields.Integer(string=_('SAS Sayısı'), compute='_compute_purchase_order_count')
    
    offer_count = fields.Integer(string=_('Teklif Sayısı'), compute='_compute_offer_count')

    @api.depends('purchase_order_ids', 'workflow_current_state_id')
    def _compute_offer_count(self):
        for tender in self:
            state_technical_name = tender.workflow_current_state_id.technical_name if tender.workflow_current_state_id else None
            # State'e göre teklif filtreleme
            if state_technical_name == 'first_tender_round':
                # 1. tur teklifleri say
                tender.offer_count = len(tender.purchase_order_ids.filtered(lambda o: o.tender_round == 1))
            elif state_technical_name in ('second_tender_round', 'target_price_set'):
                # 2. tur teklifleri say
                tender.offer_count = len(tender.purchase_order_ids.filtered(lambda o: o.tender_round == 2))
            elif state_technical_name in ('evaluation', 'approved', 'done'):
                # Değerlendirme ve sonraki aşamalarda tüm teklifleri say
                tender.offer_count = len(tender.purchase_order_ids)
            else:
                # Diğer durumlarda (draft, cancel) sıfır
                tender.offer_count = 0

    
    @api.depends('purchase_order_ids.amount_total', 'purchase_order_ids.tender_offer_status')
    def _compute_winning_order(self):
        # Bu prototipte en düşük fiyatlı teklifi kazanan kabul edelim
        for tender in self:
            if tender.purchase_order_ids:
                # Sadece 'selected' (seçilmiş) veya en düşük fiyatlı teklifi bul
                selected_order = tender.purchase_order_ids.filtered(lambda o: o.tender_offer_status == 'selected')
                if selected_order:
                    tender.winning_order_id = selected_order[0]
                else: # Henüz seçilmemişse en düşüğü göster
                    tender.winning_order_id = min(tender.purchase_order_ids, key=lambda o: o.amount_total)
            else:
                tender.winning_order_id = False
    
    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for tender in self:
            # Bu ihale ile ilişkili Purchase Order sayısını hesapla
            tender.purchase_order_count = len(tender.purchase_order_ids)
            
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('ak.tender.sequence') or _('New')
        
        # The workflow initialization is now correctly handled by the ak.workflow.mixin's create method.
        records = super().create(vals_list)
        return records

    @api.onchange('workflow_definition_id')
    def _onchange_workflow_definition_id(self):
        """
        İş akışı tanımı değiştirildiğinde, mevcut durumu
        yeni iş akışının başlangıç durumuna günceller.
        """
        if self.workflow_definition_id and self.workflow_definition_id.initial_state_id:
            self.workflow_current_state_id = self.workflow_definition_id.initial_state_id
            if self._origin:  # Sadece mevcut kayıtlarda başlangıç tarihini güncelle
                self.workflow_start_date = fields.Datetime.now()
        else:
            self.workflow_current_state_id = False

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("Başlangıç Tarihi, Bitiş Tarihinden sonra olamaz!"))

    def _create_purchase_order(self):
        self.ensure_one()
        winning_order = self.winning_order_id
        if winning_order:
            # The winning_order is already a purchase.order, we just need to confirm it.
            if winning_order.state in ('draft', 'sent'):
                 winning_order.button_confirm()
            
            # Set other orders to 'rejected'
            other_orders = self.purchase_order_ids.filtered(lambda o: o.id != winning_order.id)
            other_orders.write({'tender_offer_status': 'rejected'})

            notification_message = _('İhale başarıyla onaylandı. Kazanan teklif (%s) için Satın Alma Siparişi onaylandı.') % (winning_order.name)
        else:
            notification_message = _('İhale başarıyla onaylandı. Ancak kazanan bir teklif bulunamadığı için SAS onaylanamadı.')
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'display_notification',
            {
                'title': _('İhale Onaylandı'),
                'message': notification_message,
            }
        )

            
    # NOT: Durum geçiş metotları artık iş akışı (`ak.workflow.mixin`) tarafından yönetilmektedir.
    # `action_start_first_round`, `action_complete_tender` gibi metotlar yerine
    # iş akışı tanımında (`ak.workflow.definition`) belirtilen geçişler (`ak.workflow.transition`) kullanılır.
    # Geçişler, sunucu aksiyonları (`ir.actions.server`) aracılığıyla tetiklenebilir
    # ve bu aksiyonlar `execute_code` alanında bu model üzerindeki metotları çağırabilir.
    # Örneğin, bir geçiş "Onayla" ise ve `_create_purchase_order` metodunu çağırması gerekiyorsa,
    # bu geçişin sunucu aksiyonunda `model._create_purchase_order()` kodu yer alır.
    
    def action_view_offers(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['domain'] = [('tender_id', '=', self.id)]
        action['context'] = {'default_tender_id': self.id, 'default_partner_id': False}
        # We want to show our custom fields, so we might need a custom view
        # For now, let's use the standard views.
        return action
    
    def action_view_purchase_orders(self):
        self.ensure_one()
        # This action now shows the same as action_view_offers, but we can filter for confirmed orders
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['domain'] = [('tender_id', '=', self.id), ('state', 'in', ['purchase', 'done'])]
        return action
    




