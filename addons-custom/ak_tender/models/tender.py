# -*- coding: utf-8 -*-

# ak_tender/models/tender.py

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class AkTenderLine(models.Model):
    _name = 'ak.tender.line'
    _description = _('İhale Kalemi')
    _order = 'sequence, id'

    sequence = fields.Integer(string=_('Sıra'), default=10)
    tender_id = fields.Many2one('ak.tender', string=_('İhale'), required=True, ondelete='cascade')
    
    # Satır Tipi (Ürün, Bölüm, Not)
    display_type = fields.Selection([
        ('line_section', _('Bölüm')),
        ('line_note', _('Not')),
        ('product', _('Ürün/Hizmet')),
    ], default='product', string=_('Satır Tipi'))
    
    product_id = fields.Many2one('product.product', string=_('Ürün/Malzeme'),
                                 required=False,
                                 domain="['|', ('purchase_ok', '=', True), ('type', '=', 'service')]",
                                 help=_("İhale edilecek ürün veya malzeme."))
    
    # Otel seçimi için
    hotel_partner_id = fields.Many2one(
        'res.partner',
        string=_("Otel"),
        domain=[('is_hotel', '=', True)],
        help=_("Konaklama için otel seçin")
    )
    
    name = fields.Text(string=_('Açıklama'))
    days = fields.Integer(string=_('Gün'), default=1,
                         help=_("Konaklama gibi hizmetler için gün sayısı."))
    quantity = fields.Float(string=_('Miktar'), default=1.0)
    uom_id = fields.Many2one('uom.uom', string=_('Birim'))
    required_delivery_date = fields.Date(string=_('Gerekli Teslim Tarihi'),
                                           help=_("İstenen teslimat tarihi."),
                                           default=lambda self: self.tender_id.required_delivery_date)
    lead_time_days = fields.Integer(string=_('Tedarik Süresi (Gün)'),
                                   help=_("Sipariş verilmesinden teslimata kadar geçen süre."))
    
    # Ek Özellikler
    required = fields.Boolean(string=_('Zorunlu'), default=False,
                             help=_("Bu satır ihale için zorunludur."))
    allow_alternative = fields.Boolean(string=_('Alternatif Kabul Edilir'), default=True,
                                      help=_("Bu satır için alternatif teklifler kabul edilir."))
    
    # Hedef Fiyat ve Para Birimi
    currency_id = fields.Many2one('res.currency',
                                  string=_('Para Birimi'),
                                  default=lambda self: self.tender_id.currency_id or self.env.company.currency_id,
                                  required=True,
                                  store=True)
    target_price = fields.Monetary(string=_('Hedef Fiyat'),
                                    currency_field='currency_id',
                                    help=_("Bu kalem için belirlenen hedef fiyat."))
    # We don't need these fields anymore since we're using the standard product configurator
    
    # Computed field to access product's is_hotel_accommodation
    is_hotel_accommodation = fields.Boolean(
        string=_('Otel Konaklaması'),
        compute='_compute_is_hotel_accommodation',
        store=False,
        help=_("Bu ürün otel konaklaması mı?")
    )
    
    @api.depends('product_id')
    def _compute_is_hotel_accommodation(self):
        for line in self:
            line.is_hotel_accommodation = line.product_id.is_hotel_accommodation if line.product_id else False
    
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        
        self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        if not self.name:
            # Ürünün Satınalma açıklamasını kullan, yoksa satış açıklamasına geri dön
            if self.product_id.description_purchase:
                self.name = self.product_id.description_purchase
            else:
                self.name = self.product_id.get_product_multiline_description_sale()
        
        # Calculate target price based on days and quantity
        if self.product_id and self.product_id.list_price:
            if self.tender_id.tender_type == 'mice' and self.days > 0:
                self.target_price = self.product_id.list_price * self.quantity * self.days
            else:
                self.target_price = self.product_id.list_price * self.quantity
        
        # Otel konaklaması ürünü seçildiğinde
        self._onchange_product_id_hotel()
        
    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """Update currency when tender changes"""
        if self.tender_id and self.tender_id.currency_id:
            self.currency_id = self.tender_id.currency_id
    
    @api.onchange('product_id')
    def _onchange_product_id_hotel(self):
        """Otel konaklaması ürünü seçildiğinde"""
        if self.product_id and self.product_id.is_hotel_accommodation:
            # Varsayılan değerler
            if not self.days:
                self.days = 1
            if not self.quantity:
                self.quantity = 1
            if not self.uom_id or not self.uom_id.name:
                # Uygun bir birim bul veya varsayılan olarak "Single-BB" kullan
                uom = self.env['uom.uom'].search([('name', '=', 'Single-BB')], limit=1)
                if uom:
                    self.uom_id = uom.id
            
            # Name alanını temizle, otel seçilince dolacak
            if not self.hotel_partner_id:
                self.name = _("Otel seçiniz...")
    
    @api.onchange('hotel_partner_id')
    def _onchange_hotel_partner_id(self):
        """Otel seçildiğinde name alanını güncelle"""
        if self.product_id and self.product_id.is_hotel_accommodation and self.hotel_partner_id:
            # Name alanına otel bilgilerini yaz
            hotel_name = self.hotel_partner_id.name
            if self.hotel_partner_id.hotel_star_rating:
                hotel_name += f" {self.hotel_partner_id.hotel_star_rating}*"
            
            # Mevcut name alanını güncelle
            self.name = hotel_name
    
    @api.onchange('uom_id', 'days', 'quantity')
    def _onchange_hotel_calculation_fields(self):
        """Hesaplama alanları değiştiğinde hedef toplam güncelle"""
        if self.product_id and self.product_id.is_hotel_accommodation:
            # Target price'ı birim fiyat olarak kullan
            # Toplam hedef: gün × adet × birim fiyat
            if self.target_price and self.days and self.quantity:
                total_target = self.days * self.quantity * self.target_price
                # Bu değeri göstermek için computed field eklenebilir
    
    def _get_lang(self):
        """
        Get the language for the current record.
        This method is used by the product configurator.
        """
        return self.tender_id._get_lang()
        
    def action_view_purchase_history(self):
        """
        Show purchase history for the product in this tender line.
        This method is called when the user clicks on the 'Purchase History' button.
        """
        self.ensure_one()
        if not self.product_id:
            raise ValidationError(_("Satınalma geçmişini görüntülemek için bir ürün seçmelisiniz."))
            
        # Search for purchase order lines with this product
        domain = [('product_id', '=', self.product_id.id)]
        
        # Create an action to show the purchase order lines
        action = {
            'name': _('Satınalma Geçmişi: %s') % self.product_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
            'target': 'new',
        }
        
        return action

@api.constrains('days', 'product_id', 'tender_id.tender_type')
def _check_days_for_accommodation(self):
    """
    Validate that accommodation products (for MICE tender type) have a days value greater than 0.
    This is important for hotel bookings and similar services where duration matters.
    """
    for line in self:
        if line.tender_id.tender_type == 'mice' and line.product_id and line.product_id.type == 'service':
            # Check if the product name or category contains accommodation-related keywords
            accommodation_keywords = ['hotel', 'konaklama', 'accommodation', 'room', 'oda']
            product_name_lower = line.product_id.name.lower() if line.product_id.name else ''
            category_name_lower = line.product_id.categ_id.name.lower() if line.product_id.categ_id else ''
            
            is_accommodation = any(keyword in product_name_lower or keyword in category_name_lower
                                  for keyword in accommodation_keywords)
            
            if is_accommodation and line.days <= 0:
                raise ValidationError(_(
                    "Konaklama ürünleri için gün sayısı 0'dan büyük olmalıdır. "
                    "Lütfen '%s' ürünü için gün sayısını belirtin."
                ) % line.product_id.name)

class AkTender(models.Model):
    _name = 'ak.tender'
    _description = _('İLKOis Tender')
    _inherit = ['ak.workflow.mixin', 'mail.thread', 'mail.activity.mixin']
    # Dummy field to allow smooth upgrade from previous versions
    state = fields.Char(string="State (deprecated)",
                        help="Technical field for upgrade purpose. Not used anymore. Use workflow_state instead.",
                        compute="_compute_legacy_state", store=False)
    
    @api.depends('workflow_current_state_id')
    def _compute_legacy_state(self):
        """Compute the legacy state field based on the current workflow state for backward compatibility."""
        for record in self:
            if record.workflow_current_state_id:
                record.state = record.workflow_current_state_id.code
            else:
                record.state = 'draft'

    name = fields.Char(string=_('İhale Adı'), required=True, copy=False,
                       help=_("İhale sürecinin başlığı veya kısa adı."))
    code = fields.Char(string=_('İhale Kodu'), required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    
    # ERP Entegrasyon Alanları (Simülasyon)
    erp_pr_id = fields.Char(string=_('ERP SAT No'), copy=False,
                             help=_("İlgili ERP Satın Alma Talebi Numarası (entegrasyon ile gelecek)."))
    erp_company_code = fields.Char(string=_('ERP Şirket Kodu'), help=_("İlgili ERP Şirket Kodu (entegrasyon ile gelecek)."))
    erp_plant_code = fields.Char(string=_('ERP Tesis Kodu'), help=_("İlgili ERP Tesis Kodu (entegrasyon ile gelecek)."))
    
    # Toplu Satın Alma Optimizasyonu için alanlar
    related_pr_ids = fields.Char(string=_('İlişkili SAT Numaraları'),
                                help=_("Toplu satın alma optimizasyonu için birleştirilen SAT numaraları (virgülle ayrılmış)."))
    is_bulk_purchase = fields.Boolean(string=_('Toplu Satın Alma'),
                                     help=_("Bu ihale, toplu satın alma optimizasyonu ile oluşturulmuştur."))
    bulk_purchase_count = fields.Integer(string=_('Birleştirilen SAT Sayısı'), compute='_compute_bulk_purchase_count')
    
    # Acil Talep Desteği için alanlar
    is_urgent = fields.Boolean(string=_('Acil Talep'),
                              help=_("Bu ihale, acil talep olarak işaretlenmiştir."))
    urgent_reason = fields.Text(string=_('Aciliyet Nedeni'),
                               help=_("Acil talebin nedeni."))
    urgent_deadline = fields.Date(string=_('Acil Teslim Tarihi'),
                                 help=_("Acil talebin teslim edilmesi gereken son tarih."))
    
    # Ekonomik Veri Entegrasyonu için alanlar
    use_economic_data = fields.Boolean(string=_('Ekonomik Veri Kullan'),
                                      help=_("Ekonomik verileri ihale değerlendirmesinde kullan."))
    exchange_rate_date = fields.Date(string=_('Kur Tarihi'),
                                    help=_("Döviz kurlarının alınacağı tarih."))
    inflation_rate = fields.Float(string=_('Enflasyon Oranı (%)'),
                                 help=_("Değerlendirmede kullanılacak yıllık enflasyon oranı."))
    economic_data_source = fields.Selection([
        ('tcmb', _('TCMB')),
        ('tuik', _('TÜİK')),
        ('manual', _('Manuel'))
    ], string=_('Veri Kaynağı'), default='tcmb',
        help=_("Ekonomik verilerin alınacağı kaynak."))
    economic_notes = fields.Text(string=_('Ekonomik Değerlendirme Notları'),
                                help=_("Ekonomik değerlendirme ile ilgili notlar."))
    
    # TEKLİF DOKÜMANINA GÖRE REVİZE EDİLEN DURUM ALANI

    tender_type = fields.Selection([
        ('direct', _('Direkt Satın Alma')),
        ('indirect', _('Endirekt Satın Alma')),
        ('mice', _('MICE İhaleler')),
        ('promotion', _('Promosyon ve Kırtasiye'))
    ], string=_('İhale Tipi'), default='direct', required=True)
    
    # MICE İhaleleri için Şablon
    tender_template_id = fields.Many2one('ak.tender.template', string=_('İhale Şablonu'),
                                         help=_("MICE ve diğer ihaleler için kullanılacak ihale şablonu."))
    
    # Coğrafi Filtreleme
    country_id = fields.Many2one('res.country', string=_('Ülke'),
                                help=_("İhalenin gerçekleştirileceği ülke."))
    state_id = fields.Many2one('res.country.state', string=_('İl'),
                              domain="[('country_id', '=', country_id)]",
                              help=_("İhalenin gerçekleştirileceği il."))
    city = fields.Char(string=_('Şehir'),
                      help=_("İhalenin gerçekleştirileceği şehir."))

    start_date = fields.Datetime(string=_('Başlangıç Tarihi'), default=fields.Datetime.now(), required=True)
    end_date = fields.Datetime(string=_('Bitiş Tarihi'), required=True)
    tender_round = fields.Integer(string=_('Teklif Turu'), default=1, help=_("Bu ihalenin hangi turda olduğu (1, 2, 3...)."))
    required_delivery_date = fields.Date(string=_('Gerekli Teslim Tarihi'),
                               help=_("Satın alma siparişlerinde kullanılacak gerekli teslim tarihi."))
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
    currency_id = fields.Many2one('res.currency', string=_('Para Birimi'), default=lambda self: self.env.company.currency_id)
    target_price = fields.Monetary(string=_('Hedef Fiyat'), currency_field='currency_id',
                                   help=_("Satın Alma Direktörü tarafından belirlenen hedef fiyat."))
    
    company_id = fields.Many2one('res.company', string=_('Şirket'), default=lambda self: self.env.company)
    pricelist_id = fields.Many2one('product.pricelist', string=_('Fiyat Listesi'),
                                  default=lambda self: self.env['product.pricelist'].search([], limit=1))
    
    # NPV (Net Present Value) Hesaplama Alanları
    npv_value = fields.Monetary(string=_('NPV Değeri'), currency_field='currency_id',
                               help=_("Net Bugünkü Değer hesaplaması sonucu."), readonly=True)
    npv_rate = fields.Float(
        string=_('NPV Oranı (%)'),
        default=0.0,  # Varsayılan değer olarak 0.0 kullanılıyor
        help=_("NPV hesaplaması için kullanılacak yıllık oran (enflasyon oranı).")
    )
    discount_rate = fields.Float(string=_('İskonto Oranı (%)'), default=10.0,
                                 help=_("İhale sürecinde kullanılacak iskonto oranı."))
                                 
    @api.onchange('workflow_current_state_id', 'currency_id')
    def _onchange_workflow_current_state_id_for_npv(self):
        """
        İş akışı durumu veya para birimi değiştiğinde, ekonomik verilerden NPV oranını güncelle
        """
        # Ekonomik verilerden NPV oranını al
        try:
            economic_data_model = self.env['ak.tender.economic.data']
            if economic_data_model:
                # Para birimine özgü NPV oranını al
                self.npv_rate = economic_data_model.get_default_npv_rate(self.currency_id.id if self.currency_id else None)
        except Exception:
            # Tablo henüz oluşturulmamış olabilir, varsayılan değeri kullan
            pass
                                 
    @api.onchange('workflow_current_state_id', 'currency_id')
    def _onchange_workflow_current_state_id(self):
        """
        İş akışı durumu veya para birimi değiştiğinde, ekonomik verilerden NPV oranını güncelle
        """
        # Ekonomik verilerden NPV oranını al
        try:
            economic_data_model = self.env['ak.tender.economic.data']
            if economic_data_model:
                # Para birimine özgü NPV oranını al
                self.npv_rate = economic_data_model.get_default_npv_rate(self.currency_id.id if self.currency_id else None)
        except Exception:
            # Tablo henüz oluşturulmamış olabilir, varsayılan değeri kullan
            pass
            
    def calculate_all_npv_values(self):
        """
        Tüm Purchase Order'lar için NPV değerlerini hesapla
        """
        self.ensure_one()
        
        # Ekonomik verilerden para birimine özgü NPV oranını güncelle
        try:
            economic_data_model = self.env['ak.tender.economic.data']
            model_count = self.env['ak.tender.economic.data'].search_count([])
            currency_id = self.currency_id.id if self.currency_id else None
            
            # Directly use the model's method without any conditions
            if model_count > 0:  # Only try to get economic data if there are records
                self.npv_rate = self.env['ak.tender.economic.data'].get_default_npv_rate(currency_id)
        except Exception:
            # Tablo henüz oluşturulmamış olabilir, varsayılan değeri kullan
            pass
        
        # Tüm Purchase Order'lar için NPV değerlerini hesapla
        total_calculated = 0
        for po in self.purchase_order_ids:
            po.calculate_total_npv()
            total_calculated += 1
            
        # Hesaplanan toplam NPV değerlerini topla
        total_calculated_npv = sum(po.total_npv for po in self.purchase_order_ids)
        
        # Kullanıcıya detaylı bildirim göster
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('NPV Değerleri Hesaplandı'),
                'message': _('%s adet teklif için NPV değerleri başarıyla hesaplandı. Toplam NPV: %.2f') % (total_calculated, total_calculated_npv),
                'sticky': True,
                'type': 'success',
            }
        }
    
    # Onay Mekanizması için alanlar
    
    # Akıllı Butonlar için compute field'lar
    purchase_order_count = fields.Integer(string=_('SAS Sayısı'), compute='_compute_purchase_order_count')
    
    offer_count = fields.Integer(string=_('Teklif Sayısı'), compute='_compute_offer_count')
    
    def action_review_offers(self):
        """
        Open a list view of all purchase orders related to this tender.
        Uses the standard purchase order tree view with additional context.
        The list is grouped by tender_round and sorted by total_npv and amount_untaxed.
        Filters out purchase orders with 0 amount.
        """
        self.ensure_one()
        
        # Use the standard tree view with our extensions
        tree_view_id = self.env.ref('ak_tender.purchase_order_tree_tender').id
        search_view_id = self.env.ref('ak_tender.purchase_order_search_tender').id

        return {
            'name': _('Teklifleri İncele'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'views': [(tree_view_id, 'list'), (False, 'form')],
            'search_view_id': [search_view_id, 'search'],
            'domain': [
                ('tender_id', '=', self.id),
            ],
            'context': {
                'default_tender_id': self.id,
                'search_default_non_zero_amount': 1,  # Automatically apply the non-zero filter
                'search_default_group_by_tender_round': 1,  # Group by tender round
                'order': 'tender_round desc, total_npv asc, amount_untaxed asc',  # Sort by round, NPV, and amount
            },
            'target': 'current',
        }

    @api.depends('purchase_order_ids', 'workflow_current_state_id')
    def _compute_offer_count(self):
        for tender in self:
            state_code = tender.workflow_current_state_id.code if tender.workflow_current_state_id else None
            # State'e göre teklif filtreleme
            if state_code == 'first_tender_round':
                # 1. tur teklifleri say
                tender.offer_count = len(tender.purchase_order_ids.filtered(lambda o: o.tender_round == 1))
            elif state_code in ('second_tender_round', 'target_price_set'):
                # 2. tur teklifleri say
                tender.offer_count = len(tender.purchase_order_ids.filtered(lambda o: o.tender_round == 2))
            elif state_code in ('evaluation', 'approved', 'done'):
                # Değerlendirme ve sonraki aşamalarda tüm teklifleri say
                tender.offer_count = len(tender.purchase_order_ids)
            else:
                # Diğer durumlarda (draft, cancel) sıfır
                tender.offer_count = 0

    
    @api.depends('purchase_order_ids.amount_total', 'purchase_order_ids.state', 'workflow_current_state_id')
    def _compute_winning_order(self):
        for tender in self:
            # Sadece onaylanmış siparişleri göster
            selected_order = tender.purchase_order_ids.filtered(lambda o: o.state == 'purchase')
            
            # Eğer onaylanmış sipariş varsa, onu göster
            if selected_order:
                tender.winning_order_id = selected_order[0]
            # Eğer ihale 'approved' veya 'done' durumundaysa ve onaylanmış sipariş yoksa
            # en düşük fiyatlı teklifi göster
            elif tender.workflow_current_state_id.code in ('approved', 'done') and tender.purchase_order_ids:
                tender.winning_order_id = min(tender.purchase_order_ids, key=lambda o: o.amount_total)
            # Diğer durumlarda kazanan teklif gösterme
            else:
                tender.winning_order_id = False
    
    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for tender in self:
            # Bu ihale ile ilişkili Purchase Order sayısını hesapla
            tender.purchase_order_count = len(tender.purchase_order_ids)
    
    @api.depends('related_pr_ids')
    def _compute_bulk_purchase_count(self):
        """Compute the number of purchase requests combined in this tender."""
        for tender in self:
            if tender.related_pr_ids:
                tender.bulk_purchase_count = len(tender.related_pr_ids.split(','))
            else:
                tender.bulk_purchase_count = 0
            
    @api.model_create_multi
    def _get_lang(self):
        """
        Get the language for the current record.
        This method is used by the product configurator.
        """
        return self.env.lang or 'en_US'
        
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('ak.tender.sequence') or _('New')
        
        # The workflow initialization is now correctly handled by the ak.workflow.mixin's create method.
        records = super().create(vals_list)
        return records
        
    def increment_tender_round(self):
        """
        Increment the tender round counter.
        This method is called from workflow transition action when
        'Yeni Teklif Turu Başlat' button is clicked.
        
        Before incrementing, it checks if there are any purchase orders
        for the current round. If not, it shows a warning and does not increment.
        """
        self.ensure_one()
        
        # Check if there are any purchase orders for the current round
        current_round_pos = self.env['purchase.order'].search([
            ('tender_id', '=', self.id),
            ('tender_round', '=', self.tender_round)
        ])
        
        # If there are no purchase orders for the current round, show a warning and don't increment
        if not current_round_pos:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Uyarı'),
                    'message': _('Mevcut teklif turu (%s) için henüz teklif oluşturulmamış. '
                                'Lütfen önce tedarikçi tekliflerini oluşturun.') % self.tender_round,
                    'sticky': True,
                    'type': 'warning',
                }
            }
        
        old_round = self.tender_round
        self.tender_round += 1
        
        # Force write to ensure changes are committed
        self.write({'tender_round': self.tender_round})
        
        self.message_post(
            body=_("Teklif turu %s olarak güncellendi.") % self.tender_round,
            subtype_xmlid='mail.mt_note'
        )
        
        return True

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
    
    @api.constrains('tender_type', 'tender_lines', 'tender_lines.product_id')
    def _check_product_erp_code(self):
        """
        Direkt ihale tipinde, tüm ürünlerin ERP kodu olması gereklidir.
        Bu kısıt, direkt ihale kaydı oluştururken yeni ürün oluşturulmasını engeller.
        """
        for record in self:
            if record.tender_type == 'direct':
                for line in record.tender_lines:
                    if line.display_type == 'product' and not line.product_id.default_code:
                        raise ValidationError(_(
                            "Direkt ihale tipinde tüm ürünlerin ERP kodu olmalıdır. "
                            "Ürün '%s' için ERP kodu bulunamadı."
                        ) % line.product_id.name)

    @api.constrains('tender_type', 'tender_lines', 'tender_lines.lead_time_days')
    def _check_lead_time(self):
        """
        Direkt ihale tipinde, tedarik süresi maksimum izin verilen değeri aşamaz.
        Bu kısıt, direkt ihale kaydı oluştururken veya güncellerken kontrol edilir.
        """
        for record in self:
            if record.tender_type == 'direct':
                # Ayarlardan maksimum tedarik süresini al
                max_lead_time = int(self.env['ir.config_parameter'].sudo().get_param(
                    'ak_tender_max_lead_time', default=30))
                
                for line in record.tender_lines:
                    if line.lead_time_days and line.lead_time_days > max_lead_time:
                        raise ValidationError(_(
                            "Direkt ihale tipinde tedarik süresi %s günü aşamaz. "
                            "Ürün '%s' için tedarik süresi %s gün olarak belirlenmiş."
                        ) % (max_lead_time, line.product_id.name, line.lead_time_days))
    
    @api.constrains('tender_type', 'use_economic_data')
    def _check_economic_data(self):
        """
        Check if economic data integration is allowed for the tender type.
        Only promotion tenders can use economic data integration.
        """
        for record in self:
            if record.use_economic_data and record.tender_type != 'promotion':
                raise ValidationError(_(
                    "Ekonomik veri entegrasyonu sadece Promosyon ihale tipi için kullanılabilir."
                ))
                
            if record.use_economic_data and not record.exchange_rate_date:
                raise ValidationError(_(
                    "Ekonomik veri entegrasyonu için kur tarihi belirtilmelidir."
                ))
    
    def fetch_economic_data(self):
        """
        Fetch economic data from external sources.
        This is a simulated method for the prototype.
        In a real implementation, this would connect to TCMB or TÜİK APIs.
        """
        self.ensure_one()
        
        if not self.use_economic_data:
            return False
            
        if self.tender_type != 'promotion':
            raise ValidationError(_("Ekonomik veri entegrasyonu sadece Promosyon ihale tipi için kullanılabilir."))
            
        if not self.exchange_rate_date:
            raise ValidationError(_("Kur tarihi belirtilmelidir."))
            
        # Simulated data
        exchange_rates = {
            'USD': 28.5,
            'EUR': 31.2,
            'GBP': 36.8,
            'CHF': 32.1
        }
        
        inflation_data = {
            'annual': 38.2,
            'monthly': 3.2
        }
        
        # Update the inflation rate if not manually set
        if self.economic_data_source != 'manual' and not self.inflation_rate:
            self.inflation_rate = inflation_data['annual']
            
        # Log the data fetch
        self.message_post(
            body=_("Ekonomik veriler güncellendi. Kur tarihi: %s, Kaynak: %s") %
                 (self.exchange_rate_date, dict(self._fields['economic_data_source'].selection).get(self.economic_data_source)),
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'exchange_rates': exchange_rates,
            'inflation_data': inflation_data
        }
    
    def action_fetch_economic_data(self):
        """
        Action to fetch economic data from external sources.
        This is called from a button in the UI.
        """
        self.ensure_one()
        
        try:
            data = self.fetch_economic_data()
            if data:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Ekonomik Veriler Güncellendi'),
                        'message': _('Döviz kurları ve enflasyon verileri başarıyla güncellendi.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Ekonomik Veri Yok'),
                        'message': _('Ekonomik veri entegrasyonu etkin değil.'),
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Hata'),
                    'message': str(e),
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    @api.constrains('tender_type', 'is_urgent')
    def _check_urgent_request(self):
        """
        Check if urgent request is allowed for the tender type.
        Only indirect and promotion tenders can be marked as urgent.
        """
        for record in self:
            if record.is_urgent and record.tender_type not in ('indirect', 'promotion'):
                raise ValidationError(_(
                    "Acil talep desteği sadece Endirekt ve Promosyon ihale tipleri için kullanılabilir."
                ))
                
            if record.is_urgent and not record.urgent_reason:
                raise ValidationError(_(
                    "Acil talep için aciliyet nedeni belirtilmelidir."
                ))
                
            if record.is_urgent and not record.urgent_deadline:
                raise ValidationError(_(
                    "Acil talep için acil teslim tarihi belirtilmelidir."
                ))
    def _create_purchase_order(self):
        """
        This method is called when a tender is approved.
        It confirms the winning purchase order and marks other orders as rejected.
        
        This method is typically called from a workflow transition action.
        """
        self.ensure_one()
        winning_order = self.winning_order_id
        if winning_order:
            # The winning_order is already a purchase.order, we just need to confirm it.
            if winning_order.state in ('draft', 'sent'):
                 winning_order.button_confirm()
            
            # Cancel other orders
            other_orders = self.purchase_order_ids.filtered(lambda o: o.id != winning_order.id)
            other_orders.button_cancel()

            notification_message = _('İhale başarıyla onaylandı. Kazanan teklif (%s) için Satın Alma Siparişi onaylandı.') % (winning_order.name)
        else:
            notification_message = _('İhale başarıyla onaylandı. Ancak kazanan bir teklif bulunamadığı için SAS onaylanamadı.')
        
        # Send notification
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'display_notification',
            {
                'title': _('İhale Onaylandı'),
                'message': notification_message,
            }
        )
        
        # Post message in chatter
        self.message_post(
            body=notification_message,
            subtype_xmlid='mail.mt_note'
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
        # Open the vendor comparison report
        return self.env.ref('ak_tender.action_report_vendor_comparison').report_action(self)
        
    def get_comparison_data(self):
        """
        Get data for the vendor comparison widget.
        
        Returns:
            dict: A dictionary containing vendors and tender lines data
        """
        self.ensure_one()
        
        # Get vendors (purchase orders)
        vendors = []
        for po in self.purchase_order_ids:
            vendors.append({
                'id': po.id,
                'partner_id': po.partner_id.id,
                'partner_name': po.partner_id.name,
            })
        
        # Get tender lines with vendor data
        tender_lines = []
        for line in self.tender_lines:
            line_data = {
                'id': line.id,
                'name': line.name,
                'display_type': line.display_type,
                'product_id': line.product_id.id if line.product_id else False,
                'product_name': line.product_id.display_name if line.product_id else line.name,
                'product_description': line.product_id.description_purchase if line.product_id else '',
                'required_delivery_date': line.required_delivery_date.strftime('%Y-%m-%d') if line.required_delivery_date else False,
                'vendor_lines': [],
            }
            
            # Add vendor-specific data for this line
            for po in self.purchase_order_ids:
                po_line = po.order_line.filtered(lambda l: l.tender_line_id.id == line.id)
                if po_line:
                    po_line = po_line[0]  # Take the first one if multiple
                    line_data['vendor_lines'].append({
                        'vendor_id': po.id,
                        'product_qty': po_line.product_qty,
                        'product_uom_name': po_line.product_uom.name if po_line.product_uom else '',
                        'alt_materials': po_line.alt_materials if hasattr(po_line, 'alt_materials') else '',
                        'discount': po_line.discount,
                        'price_subtotal': po_line.price_subtotal,
                        'currency_name': po_line.currency_id.name if po_line.currency_id else '',
                        'npv_value': po_line.npv_value if hasattr(po_line, 'npv_value') else 0,
                        'date_planned': po_line.date_planned.strftime('%Y-%m-%d') if po_line.date_planned else '',
                        'warranty_period': po_line.warranty_period if hasattr(po_line, 'warranty_period') else '',
                        'alt_materials': po_line.alt_materials if hasattr(po_line, 'alt_materials') else '',
                    })
            
            tender_lines.append(line_data)
        
        return {
            'vendors': vendors,
            'tender_lines': tender_lines,
        }
    
    
    def action_view_purchase_orders(self):
        self.ensure_one()
        # This action now shows the same as action_view_offers, but we can filter for confirmed orders
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['domain'] = [('tender_id', '=', self.id), ('state', 'in', ['purchase', 'done'])]
        action['context'] = {
            'default_tender_id': self.id,
            'default_partner_id': False,
        }
        # Use standard views to avoid any issues
        action['views'] = [(self.env.ref('purchase.purchase_order_view_tree').id, 'list'),
                          (self.env.ref('purchase.purchase_order_form').id, 'form')]
        return action
    
    @api.model
    def create_bulk_purchase_tender(self, pr_ids, name=None, tender_type='indirect'):
        """
        Create a new tender by combining multiple purchase requests.
        
        Args:
            pr_ids (list): List of ERP PR IDs to combine
            name (str, optional): Name for the new tender
            tender_type (str, optional): Type of tender ('indirect' or 'promotion')
            
        Returns:
            ak.tender: The newly created tender record
        """
        if not pr_ids:
            raise ValidationError(_("En az bir SAT numarası belirtilmelidir."))
            
        if tender_type not in ('indirect', 'promotion'):
            raise ValidationError(_("Toplu satın alma optimizasyonu sadece Endirekt ve Promosyon ihale tipleri için kullanılabilir."))
            
        # Check if bulk purchase optimization is enabled
        enable_bulk_purchase = self.env['ir.config_parameter'].sudo().get_param(
            'ak_tender_enable_bulk_purchase', 'True') == 'True'
            
        if not enable_bulk_purchase:
            raise ValidationError(_("Toplu satın alma optimizasyonu ayarlarda devre dışı bırakılmıştır."))
            
        # Create a new tender
        if not name:
            name = _("Toplu Satın Alma: %s") % ', '.join(pr_ids[:3])
            if len(pr_ids) > 3:
                name += _(" ve %s diğer") % (len(pr_ids) - 3)
                
        vals = {
            'name': name,
            'tender_type': tender_type,
            'related_pr_ids': ','.join(pr_ids),
            'is_bulk_purchase': True,
            'start_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now() + fields.Datetime.to_timedelta(days=7),  # Default 7 days
        }
        
        # Create the tender
        tender = self.create(vals)
        
        # Log the creation
        tender.message_post(
            body=_("Bu ihale, toplu satın alma optimizasyonu ile oluşturulmuştur. İlişkili SAT numaraları: %s") %
                 tender.related_pr_ids,
            subtype_xmlid='mail.mt_note'
        )
        
        return tender
        
    @api.onchange('tender_type')
    def _onchange_tender_type(self):
        """İhale tipi değiştiğinde ilgili alanları güncelle."""
        if self.tender_type != 'mice':
            self.tender_template_id = False
            
    @api.onchange('required_delivery_date')
    def _onchange_required_delivery_date(self):
        """Gerekli teslim tarihi değiştiğinde tüm ihale kalemlerini güncelle."""
        if self.required_delivery_date and self.tender_lines:
            for line in self.tender_lines:
                if not line.required_delivery_date:
                    line.required_delivery_date = self.required_delivery_date
    
    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        """
        Update currency on all tender lines when the tender's currency changes.
        """
        if self.currency_id and self.tender_lines:
            for line in self.tender_lines:
                line.currency_id = self.currency_id
    
    @api.onchange('tender_template_id')
    def _onchange_tender_template_id(self):
        """İhale şablonu seçildiğinde şablonu uygula."""
        if not self.tender_template_id:
            return
        
        # Şablonu uygula - her ihale tipi için kendi şablonu uygulanabilir
        
        # Coğrafi bilgileri güncelle
        if self.tender_template_id.country_ids:
            # Şablonda ülke kısıtlaması varsa, ilk ülkeyi seç
            self.country_id = self.tender_template_id.country_ids[0].id
        if self.tender_template_id.state_ids:
            # Şablonda il kısıtlaması varsa ve seçilen ülkeye uygunsa, ilk ili seç
            states = self.tender_template_id.state_ids.filtered(lambda s: s.country_id.id == self.country_id.id)
            if states:
                self.state_id = states[0].id
        if self.tender_template_id.city:
            self.city = self.tender_template_id.city
        
        # Mevcut satırları temizle
        self.tender_lines = [(5, 0, 0)]
        
        # Şablon satırlarını ekle
        lines = []
        for template_line in self.tender_template_id.line_ids:
            if template_line.display_type in ['line_section', 'line_note']:
                # Bölüm veya not satırı
                vals = {
                    'display_type': template_line.display_type,
                    'name': template_line.name,
                    'sequence': template_line.sequence,
                }
                lines.append((0, 0, vals))
            elif template_line.product_id:
                # Ürün satırı
                vals = {
                    'display_type': 'product',
                    'product_id': template_line.product_id.id,
                    'name': template_line.name or template_line.product_id.name,
                    'days': template_line.days,
                    'quantity': template_line.product_qty,
                    'uom_id': template_line.product_uom_id.id,
                    'sequence': template_line.sequence,
                    'required': template_line.required,
                    'allow_alternative': template_line.allow_alternative,
                }
                lines.append((0, 0, vals))
        
        self.tender_lines = lines
    
    def action_apply_template(self):
        """Seçili şablonu ihaleye uygula."""
        self.ensure_one()
        if not self.tender_template_id:
            raise ValidationError(_("Önce bir ihale şablonu seçmelisiniz."))
        
        # Şablonu uygula
        self._onchange_tender_template_id()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Şablon Uygulandı'),
                'message': _('Hizmet şablonu başarıyla uygulandı.'),
                'sticky': False,
                'type': 'success',
            }
        }
        
    def action_add_supplier(self):
        """
        Open the Add Supplier wizard.
        This method is called from the 'Tedarikçi Ekle' button in the UI.
        """
        self.ensure_one()
        
        return {
            'name': _('Tedarikçi Ekle'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.add.supplier.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
            }
        }
        
    def create_purchase_orders_for_suppliers(self):
        """
        Create purchase orders for all invited suppliers.
        This method creates a purchase order for each invited supplier
        with all tender items included.
        
        For new tender rounds, it copies the offers from the previous round
        but only for suppliers who have submitted offers (total amount > 0).
        """
        self.ensure_one()
        
        # Validate preconditions
        validation_result = self._validate_purchase_order_creation()
        if validation_result:
            return validation_result
        
        # Get suppliers to process
        suppliers_to_process = self._get_suppliers_to_process()
        
        # Create purchase orders for each supplier
        created_count = self._create_purchase_orders(suppliers_to_process)
        
        # Return success notification
        return self._get_success_notification(created_count)
    
    def _validate_purchase_order_creation(self):
        """
        Validate that all preconditions for purchase order creation are met.
        Returns a notification dictionary if validation fails, None otherwise.
        """
        if not self.invited_partners:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Uyarı'),
                    'message': _('Davetli tedarikçi bulunamadı. Lütfen önce tedarikçi ekleyin.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        if not self.tender_lines.filtered(lambda l: l.display_type == 'product'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Uyarı'),
                    'message': _('İhale kalemi bulunamadı. Lütfen önce ihale kalemi ekleyin.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        return None
    
    def _get_suppliers_to_process(self):
        """
        Determine which suppliers need purchase orders created.
        Returns a list of supplier information dictionaries.
        """
        suppliers_to_process = []
        
        if self.tender_round == 1:
            # First round: Process all invited suppliers that don't have an order yet
            suppliers_to_process = self._get_first_round_suppliers()
        else:
            # Subsequent rounds: Copy from previous round for suppliers with valid offers
            suppliers_to_process = self._get_subsequent_round_suppliers()
        
        return suppliers_to_process
    
    def _get_first_round_suppliers(self):
        """
        Get suppliers for the first tender round.
        Returns a list of supplier information dictionaries.
        """
        suppliers_to_process = []
        
        # Count existing purchase orders for this tender
        existing_pos = self.env['purchase.order'].search([
            ('tender_id', '=', self.id),
            ('tender_round', '=', 1)
        ])
        existing_supplier_ids = existing_pos.mapped('partner_id.id')
        
        # Create purchase orders for suppliers that don't have one yet
        for supplier in self.invited_partners:
            if supplier.id not in existing_supplier_ids:
                suppliers_to_process.append({
                    'partner_id': supplier.id,
                    'prev_po': None,  # No previous PO for first round
                    'round': 1
                })
        
        return suppliers_to_process
    
    def _get_subsequent_round_suppliers(self):
        """
        Get suppliers for subsequent tender rounds.
        Returns a list of supplier information dictionaries.
        """
        suppliers_to_process = []
        previous_round = self.tender_round - 1
        
        # Get purchase orders from the previous round
        previous_pos = self.env['purchase.order'].search([
            ('tender_id', '=', self.id),
            ('tender_round', '=', previous_round)
        ])
        
        # Only copy purchase orders with total amount > 0 (supplier has submitted an offer)
        valid_previous_pos = previous_pos.filtered(lambda po: po.amount_total > 0)
        
        for prev_po in valid_previous_pos:
            # Check if a purchase order already exists for this supplier in the current round
            existing_po = self.env['purchase.order'].search([
                ('tender_id', '=', self.id),
                ('partner_id', '=', prev_po.partner_id.id),
                ('tender_round', '=', self.tender_round)
            ], limit=1)
            
            if not existing_po:
                suppliers_to_process.append({
                    'partner_id': prev_po.partner_id.id,
                    'prev_po': prev_po,  # Store previous PO for copying lines
                    'round': self.tender_round
                })
        
        return suppliers_to_process
    
    def _create_purchase_orders(self, suppliers_to_process):
        """
        Create purchase orders for the specified suppliers.
        Returns the count of created purchase orders.
        """
        created_count = 0
        
        for supplier_info in suppliers_to_process:
            # Create purchase order
            new_po = self._create_purchase_order(supplier_info)
            
            # Create purchase order lines
            self._create_purchase_order_lines(new_po, supplier_info)
            
            created_count += 1
        
        return created_count
    
    def _create_purchase_order(self, supplier_info):
        """
        Create a purchase order for the specified supplier.
        Returns the created purchase order.
        """
        po_vals = {
            'partner_id': supplier_info['partner_id'],
            'tender_id': self.id,
            'date_order': self.end_date,
            'tender_round': supplier_info['round'],
            'company_id': self.env.company.id,
            'currency_id': self.currency_id.id,
        }
        
        # If this is a subsequent round, copy payment terms from the previous purchase order
        prev_po = supplier_info.get('prev_po')
        if prev_po and hasattr(prev_po, 'payment_term_id'):
            po_vals['payment_term_id'] = prev_po.payment_term_id.id if prev_po.payment_term_id else False
        
        # Create the purchase order with a context to prevent auto-creation of lines
        return self.env['purchase.order'].with_context(from_tender=True).create(po_vals)
    
    def _create_purchase_order_lines(self, purchase_order, supplier_info):
        """
        Create purchase order lines for the specified purchase order.
        """
        prev_po = supplier_info['prev_po']
        
        if prev_po:
            # Copy lines from previous purchase order (subsequent rounds)
            for prev_line in prev_po.order_line:
                self._create_line_from_previous(purchase_order, prev_line)
        else:
            # Create new lines from tender lines (first round)
            for tender_line in self.tender_lines:
                self._create_line_from_tender(purchase_order, tender_line)
    
    def _create_line_from_previous(self, purchase_order, prev_line):
        """
        Create a purchase order line from a previous purchase order line.
        Returns the created purchase order line.
        """
        if prev_line.display_type in ('line_section', 'line_note'):
            return self._create_section_or_note_line(
                purchase_order,
                prev_line.name,
                prev_line.display_type,
                prev_line.sequence
            )
        else:
            # Product line - copy values from previous round
            product_qty = prev_line.product_qty
            if not product_qty or product_qty <= 0:
                product_qty = 1.0
                
            product_uom = prev_line.product_uom.id
            if not product_uom and prev_line.product_id:
                product_uom = prev_line.product_id.uom_po_id.id or prev_line.product_id.uom_id.id
            
            if not product_uom:
                product_uom = self.env['uom.uom'].search([], limit=1).id
                
            date_planned = prev_line.date_planned or fields.Date.today()
            
            line_vals = {
                'order_id': purchase_order.id,
                'product_id': prev_line.product_id.id,
                'name': prev_line.name or prev_line.product_id.name,
                'product_qty': product_qty,
                'product_uom': product_uom,
                'price_unit': prev_line.price_unit or 0.0,
                'date_planned': date_planned,
                'taxes_id': [(6, 0, prev_line.taxes_id.ids)],
                'tender_line_id': prev_line.tender_line_id.id if prev_line.tender_line_id else False,
                'sequence': prev_line.sequence,
                'alt_materials': prev_line.alt_materials if hasattr(prev_line, 'alt_materials') else False,
                'discount': prev_line.discount if hasattr(prev_line, 'discount') else 0.0,
            }
            
            return self.env['purchase.order.line'].create(line_vals)
    
    def _create_line_from_tender(self, purchase_order, tender_line):
        """
        Create a purchase order line from a tender line.
        Returns the created purchase order line.
        """
        if tender_line.display_type in ('line_section', 'line_note'):
            return self._create_section_or_note_line(
                purchase_order,
                tender_line.name or 'Section/Note',
                tender_line.display_type,
                tender_line.sequence
            )
        elif tender_line.display_type == 'product' and tender_line.product_id:
            # Product line
            product_uom = tender_line.uom_id.id
            if not product_uom and tender_line.product_id:
                product_uom = tender_line.product_id.uom_po_id.id or tender_line.product_id.uom_id.id
            
            if not product_uom:
                product_uom = self.env['uom.uom'].search([], limit=1).id
                
            quantity = tender_line.quantity
            if not quantity or quantity <= 0:
                quantity = 1.0
                
            date_planned = tender_line.required_delivery_date or self.required_delivery_date or fields.Date.today()
            
            line_vals = {
                'order_id': purchase_order.id,
                'product_id': tender_line.product_id.id,
                'name': tender_line.name or tender_line.product_id.name,
                'product_qty': quantity,
                'product_uom': product_uom,
                'price_unit': tender_line.target_price or 0.0,
                'date_planned': date_planned,
                'tender_line_id': tender_line.id,
            }
            
            return self.env['purchase.order.line'].create(line_vals)
        
        return None
    
    def _create_section_or_note_line(self, purchase_order, name, display_type, sequence):
        """
        Create a section or note line for a purchase order.
        Returns the created purchase order line.
        """
        line_vals = {
            'order_id': purchase_order.id,
            'name': name,
            'display_type': display_type,
            'sequence': sequence,
            # For non-accountable lines, these fields should be NULL
            'product_id': False,
            'product_qty': 0.0,
            'product_uom': False,
            'price_unit': 0.0,
            'date_planned': fields.Date.today(),
        }
        
        return self.env['purchase.order.line'].create(line_vals)
    
    def _get_success_notification(self, created_count):
        """
        Get the success notification for purchase order creation.
        Returns a notification dictionary.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Başarılı'),
                'message': _('%s tedarikçi için satın alma talebi oluşturuldu.') % created_count,
                'sticky': False,
                'type': 'success',
            }
        }
    
    def action_send_bulk_emails(self):
        """
        Send emails to all suppliers with purchase orders for the current tender round.
        This method finds all purchase orders for the current round of the tender
        and triggers the email sending action for each one.
        
        This method uses a custom email template that includes the "View Quotation" button
        with the exact design requested.
        """
        self.ensure_one()
        
        # Find all purchase orders for this tender and current round
        purchase_orders = self.env['purchase.order'].search([
            ('tender_id', '=', self.id),
            ('tender_round', '=', self.tender_round),  # Only current round
            ('state', 'not in', ['cancel', 'purchase', 'done'])
        ])
        
        if not purchase_orders:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Uyarı'),
                    'message': _('Gönderilecek teklif bulunamadı. Lütfen önce tedarikçiler için SAT oluşturun.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Get our custom mail template
        template_id = False
        try:
            # Use our custom template with the View Quotation button
            template_id = self.env['ir.model.data']._xmlid_lookup('ak_tender.email_template_edi_purchase_custom')[1]
        except ValueError:
            # Fall back to the standard template if our custom one is not found
            try:
                template_id = self.env['ir.model.data']._xmlid_lookup('purchase.email_template_edi_purchase')[1]
            except ValueError:
                pass
            
        if not template_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Hata'),
                    'message': _('E-posta şablonu bulunamadı.'),
                    'sticky': True,
                    'type': 'danger',
                }
            }
        
        # Send email for each purchase order and mark as sent
        sent_count = 0
        for po in purchase_orders:
            try:
                # Get the template with proper rendering
                template = self.env['mail.template'].browse(template_id)
                
                # Set up the context exactly like action_rfq_send does
                ctx = {
                    'default_model': 'purchase.order',
                    'default_res_id': po.id,
                    'default_template_id': template_id,
                    'default_composition_mode': 'comment',
                    'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
                    'force_email': True,
                    'mark_rfq_as_sent': True,
                    'model_description': _('Request for Quotation') if po.state in ['draft', 'sent'] else _('Purchase Order'),
                }
                
                # Get the language for proper template rendering
                lang = po.partner_id.lang or self.env.user.lang or 'en_US'
                template = template.with_context(lang=lang)
                
                # Send the email with all the proper context
                template.with_context(ctx).send_mail(po.id, force_send=True)
                
                # Mark the RFQ as sent (change state to 'sent')
                if po.state == 'draft':
                    po.write({'state': 'sent'})
                
                sent_count += 1
            except Exception as e:
                _logger.error("Failed to send email for purchase order %s: %s", po.name, str(e))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Başarılı'),
                'message': _('%s tedarikçi için e-posta gönderildi ve RFQ durumu güncellendi.') % sent_count,
                'sticky': False,
                'type': 'success',
            }
        }
        
    def action_add_from_template(self):
        """Open wizard to select a template and add its items to the tender."""
        self.ensure_one()
        
        # Check if there are templates available for this tender type
        templates = self.env['ak.tender.template'].search([
            ('tender_type', '=', self.tender_type),
            ('active', '=', True)
        ])
        
        if not templates:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Uygun Şablon Bulunamadı'),
                    'message': _('Bu ihale tipi için uygun şablon bulunamadı.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Open the template selection wizard
        return {
            'name': _('Şablon Seçimi'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.template.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
            }
        }
        
    def apply_template_items(self, template):
        """Add items from the selected template to the tender."""
        self.ensure_one()
        
        # Create new lines from template
        for template_line in template.line_ids:
            vals = template_line._prepare_tender_line_values()
            
            # Map field names correctly
            if 'product_qty' in vals:
                vals['quantity'] = vals.pop('product_qty')
                
            if 'product_uom_id' in vals:
                vals['uom_id'] = vals.pop('product_uom_id')
                
            # Remove price_unit and set target_price to 0
            if 'price_unit' in vals:
                vals.pop('price_unit')
            
            vals['target_price'] = 0.0
            vals['tender_id'] = self.id
            self.env['ak.tender.line'].create(vals)
            
        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Şablon Uygulandı'),
                'message': _('Şablondan %s kalem eklendi.') % len(template.line_ids),
                'sticky': False,
                'type': 'success',
            }
        }
