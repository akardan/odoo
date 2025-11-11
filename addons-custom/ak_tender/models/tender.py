# -*- coding: utf-8 -*-

# ak_tender/models/tender.py

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError
from odoo.addons.ak_workflow.models.ak_workflow_dynamic_parameter import WorkflowDynamicParameter
import io
import base64
import subprocess
import sys
import json
import logging

_logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
        import pandas as pd
    except Exception:
        raise UserError(_("Pandas kütüphanesi bulunamadı ve otomatik olarak kurulamadı. Lütfen manuel olarak kurun: pip install pandas"))

try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
        from bs4 import BeautifulSoup
    except Exception:
        raise UserError(_("BeautifulSoup4 kütüphanesi bulunamadı ve otomatik olarak kurulamadı. Lütfen manuel olarak kurun: pip install beautifulsoup4"))

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
                                       default=0.0,
                                       help=_("Bu kalem için belirlenen hedef fiyat."))
    # Attachment fields for tender line
    attachment1 = fields.Binary(string=_('Ek1'), help=_("Upload image or PDF attachment 1"))
    attachment1_filename = fields.Char(string=_('Ek1 Dosya Adı'))
    attachment2 = fields.Binary(string=_('Ek2'), help=_("Upload image or PDF attachment 2"))
    attachment2_filename = fields.Char(string=_('Ek2 Dosya Adı'))
    
    # Computed fields for attachment type detection
    is_image1 = fields.Boolean(string="Is Image 1", compute="_compute_attachment_types")
    is_pdf1 = fields.Boolean(string="Is PDF 1", compute="_compute_attachment_types")
    is_image2 = fields.Boolean(string="Is Image 2", compute="_compute_attachment_types")
    
    # Product Matrix fields for variant support
    product_template_id = fields.Many2one(
        'product.template',
        string='Product Template',
        related="product_id.product_tmpl_id",
        store=True,
        readonly=False,
        domain=[('purchase_ok', '=', True)]
    )
    is_configurable_product = fields.Boolean(
        'Is the product configurable?', 
        related="product_template_id.has_configurable_attributes"
    )
    product_template_attribute_value_ids = fields.Many2many(
        related='product_id.product_template_attribute_value_ids', 
        readonly=True
    )
    product_no_variant_attribute_value_ids = fields.Many2many(
        'product.template.attribute.value', 
        string='Product attribute values that do not create variants', 
        ondelete='restrict'
    )
    is_pdf2 = fields.Boolean(string="Is PDF 2", compute="_compute_attachment_types")
    
    @api.depends('attachment1_filename', 'attachment2_filename')
    def _compute_attachment_types(self):
        """Compute if attachments are images or PDFs based on filename"""
        for line in self:
            # Default values
            line.is_image1 = False
            line.is_pdf1 = False
            line.is_image2 = False
            line.is_pdf2 = False
            
            # Check attachment1 type
            if line.attachment1 and line.attachment1_filename:
                filename = line.attachment1_filename.lower()
                if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                    line.is_image1 = True
                elif filename.endswith('.pdf'):
                    line.is_pdf1 = True
            
            # Check attachment2 type
            if line.attachment2 and line.attachment2_filename:
                filename = line.attachment2_filename.lower()
                if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                    line.is_image2 = True
                elif filename.endswith('.pdf'):
                    line.is_pdf2 = True
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
            
    @api.model
    def create(self, vals):
        """Yeni bir satır oluşturulduğunda tender'ın hedef fiyatını güncelle"""
        line = super(AkTenderLine, self).create(vals)
        if line.tender_id and line.display_type == 'product':
            line.tender_id.calculate_total_target_price()
        return line
    
    def write(self, vals):
        """Satır güncellendiğinde tender'ın hedef fiyatını güncelle"""
        result = super(AkTenderLine, self).write(vals)
        # Eğer target_price, quantity veya currency_id değişmişse tender'ın hedef fiyatını güncelle
        if 'target_price' in vals or 'quantity' in vals or 'currency_id' in vals:
            for line in self:
                if line.tender_id and line.display_type == 'product':
                    line.tender_id.calculate_total_target_price()
        return result
    
    
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
        
        # Add variant attributes to name
        for no_variant_attribute_value in self.product_no_variant_attribute_value_ids:
            self.name += "\n" + no_variant_attribute_value.attribute_id.name + ': ' + no_variant_attribute_value.name
        
        # Calculate target price based on days and quantity
        if self.product_id and self.product_id.list_price:
            if self.tender_id.tender_type == 'mice' and self.days > 0:
                self.target_price = self.product_id.list_price * self.quantity * self.days
            else:
                self.target_price = self.product_id.list_price * self.quantity
        
        # Otel konaklaması ürünü seçildiğinde
        self._onchange_product_id_hotel()
        
    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        """Para birimi değiştiğinde tender'ın hedef fiyatını güncelle"""
        if self.display_type == 'product' and self.tender_id:
            self.tender_id.calculate_total_target_price()
    
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
    
    @api.onchange('target_price', 'quantity')
    def _onchange_target_price(self):
        """Hedef fiyat veya miktar değiştiğinde tender'ın hedef fiyatını güncelle"""
        if self.display_type == 'product' and self.tender_id:
            self.tender_id.calculate_total_target_price()
    
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
        
    def action_preview_attachment1(self):
        """
        Open a preview dialog for attachment1 based on file type
        """
        self.ensure_one()
        if not self.attachment1:
            raise UserError(_("Önizleme için dosya bulunamadı."))
            
        # Get file extension to determine preview type
        filename = self.attachment1_filename or ''
        file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Create the action based on file type
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            # Image preview
            return {
                'name': _('Ek1 Önizleme: %s') % self.attachment1_filename,
                'type': 'ir.actions.act_window',
                'res_model': 'ak.tender.line',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'flags': {'mode': 'readonly'},
                'views': [(self.env.ref('ak_tender.ak_tender_line_attachment_preview_form').id, 'form')],
                'context': {
                    'form_view_initial_mode': 'view',
                    'force_detailed_view': True,
                    'preview_attachment': 'attachment1',
                }
            }
        elif file_extension == 'pdf':
            # PDF preview using the form view with improved height
            return {
                'name': _('Ek1 Önizleme: %s') % self.attachment1_filename,
                'type': 'ir.actions.act_window',
                'res_model': 'ak.tender.line',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'flags': {'mode': 'readonly'},
                'views': [(self.env.ref('ak_tender.ak_tender_line_attachment_preview_form').id, 'form')],
                'context': {
                    'form_view_initial_mode': 'view',
                    'force_detailed_view': True,
                    'preview_attachment': 'attachment1',
                }
            }
        else:
            # For other file types, just return to form view
            return {'type': 'ir.actions.act_window_close'}
            
    def action_preview_attachment2(self):
        """
        Open a preview dialog for attachment2 based on file type
        """
        self.ensure_one()
        if not self.attachment2:
            raise UserError(_("Önizleme için dosya bulunamadı."))
            
        # Get file extension to determine preview type
        filename = self.attachment2_filename or ''
        file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Create the action based on file type
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            # Image preview
            return {
                'name': _('Ek2 Önizleme: %s') % self.attachment2_filename,
                'type': 'ir.actions.act_window',
                'res_model': 'ak.tender.line',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'flags': {'mode': 'readonly'},
                'views': [(self.env.ref('ak_tender.ak_tender_line_attachment_preview_form').id, 'form')],
                'context': {
                    'form_view_initial_mode': 'view',
                    'force_detailed_view': True,
                    'preview_attachment': 'attachment2',
                }
            }
        elif file_extension == 'pdf':
            # PDF preview using the form view with improved height
            return {
                'name': _('Ek2 Önizleme: %s') % self.attachment2_filename,
                'type': 'ir.actions.act_window',
                'res_model': 'ak.tender.line',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'flags': {'mode': 'readonly'},
                'views': [(self.env.ref('ak_tender.ak_tender_line_attachment_preview_form').id, 'form')],
                'context': {
                    'form_view_initial_mode': 'view',
                    'force_detailed_view': True,
                    'preview_attachment': 'attachment2',
                }
            }
        else:
            # For other file types, just return to form view
            return {'type': 'ir.actions.act_window_close'}
            
    def action_download_attachment1(self):
        """
        Generate a download URL for attachment1
        """
        self.ensure_one()
        if not self.attachment1 or not self.attachment1_filename:
            raise UserError(_("Dosya bulunamadı."))
            
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        attachment_url = f"{base_url}/web/content?model=ak.tender.line&id={self.id}&field=attachment1&filename={self.attachment1_filename}"
        return {
            'type': 'ir.actions.act_url',
            'url': attachment_url,
            'target': 'new',
        }
        
    def action_download_attachment2(self):
        """
        Generate a download URL for attachment2
        """
        self.ensure_one()
        if not self.attachment2 or not self.attachment2_filename:
            raise UserError(_("Dosya bulunamadı."))
            
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        attachment_url = f"{base_url}/web/content?model=ak.tender.line&id={self.id}&field=attachment2&filename={self.attachment2_filename}"
        return {
            'type': 'ir.actions.act_url',
            'url': attachment_url,
            'target': 'new',
        }

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
    buyer_id = fields.Many2one('res.users', string=_('Satın Alma Uzmanı'),
                              default=lambda self: self.env.user,
                              tracking=True,
                              help=_("Bu ihaleden sorumlu satın alma uzmanı."))

    delay_days = fields.Integer(string=_('Gecikme Günü'), compute='_compute_delay_days', store=False)
    workflow_step_deadline = fields.Datetime(string=_('Adım Bitiş Tarihi'), compute='_compute_workflow_step_deadline', store=False,
                                            help=_("Mevcut iş akışı adımının bitmesi gereken tarih ve saat."))

    @api.depends('workflow_current_state_id', 'transition_history_ids.create_date')
    def _compute_delay_days(self):
        for record in self:
            delay = 0
            if record.workflow_current_state_id:
                # Get expected duration from workflow state (default 7 days if not set)
                expected_duration = record.workflow_current_state_id.default_duration_days or 2
                
                # Find the latest transition to the current state
                latest_transition = self.env['ak.workflow.transition.history'].search([
                    ('res_model', '=', record._name),
                    ('res_id', '=', record.id),
                    ('to_state_id', '=', record.workflow_current_state_id.id),
                ], order='create_date desc', limit=1)

                if latest_transition and latest_transition.create_date:
                    # Calculate the difference in days
                    time_diff = fields.Datetime.now() - latest_transition.create_date
                    actual_days = time_diff.days

                    if actual_days > expected_duration:
                        delay = actual_days - expected_duration

            record.delay_days = delay
    
    @api.depends('workflow_current_state_id', 'transition_history_ids.create_date')
    def _compute_workflow_step_deadline(self):
        """Mevcut iş akışı adımının bitiş tarihini hesapla ve yarım saatlere yuvarla"""
        for record in self:
            deadline = False
            if record.workflow_current_state_id:
                # Get expected duration from workflow state (default 1 days if not set)
                expected_duration = record.workflow_current_state_id.default_duration_days or 1
                
                # Find the latest transition to the current state
                latest_transition = self.env['ak.workflow.transition.history'].search([
                    ('res_model', '=', record._name),
                    ('res_id', '=', record.id),
                    ('to_state_id', '=', record.workflow_current_state_id.id),
                ], order='create_date desc', limit=1)
                
                if latest_transition and latest_transition.create_date:
                    # Calculate deadline: transition date + expected duration
                    deadline = latest_transition.create_date + timedelta(days=expected_duration)
                    
                    # Round to nearest half hour (00 or 30 minutes)
                    minute = deadline.minute
                    if minute < 15:
                        # Round down to :00
                        deadline = deadline.replace(minute=0, second=0, microsecond=0)
                    elif minute < 45:
                        # Round to :30
                        deadline = deadline.replace(minute=30, second=0, microsecond=0)
                    else:
                        # Round up to next hour :00
                        deadline = deadline.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            record.workflow_step_deadline = deadline
            

            
    total_new_message_count = fields.Integer(
        string=_('Toplam Yeni Mesaj'),
        compute='_compute_total_new_message_count',
        store=False,
        help=_("Bu ihaleye bağlı tekliflerdeki toplam yeni mesaj sayısı.")
    )

    @api.depends('purchase_order_ids.new_message_count')
    def _compute_total_new_message_count(self):
        for record in self:
            record.total_new_message_count = sum(po.new_message_count for po in record.purchase_order_ids)
            
    # ERP Entegrasyon Alanları (Simülasyon)
    erp_pr_id = fields.Char(string=_('ERP SAT No'), copy=False,
                             help=_("İlgili ERP Satın Alma Talebi Numarası (entegrasyon ile gelecek)."))
    erp_company_code = fields.Char(string=_('ERP Şirket Kodu'), help=_("İlgili ERP Şirket Kodu (entegrasyon ile gelecek)."))
    erp_plant_code = fields.Char(string=_('ERP Tesis Kodu'), help=_("İlgili ERP Tesis Kodu (entegrasyon ile gelecek)."))
    erp_requester = fields.Char(string=_('SAT Talep Eden'), copy=False,
                                help=_("SAP'ta SAT'ı açan kullanıcı bilgisi (entegrasyon ile gelecek)."))
    
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
   
    location_dest_id = fields.Many2one(
       comodel_name="stock.location",
       string=_("Teslim Yeri"),
       domain=[("usage", "in", ["internal", "transit"])],
       help=_("İhale için varsayılan teslim yeri.")
   )
    
    # TEKLİF DOKÜMANINA GÖRE REVİZE EDİLEN DURUM ALANI

    tender_type = fields.Selection([
        ('direct', _('Direkt Satınalma')),
        ('indirect', _('Endirekt Satınalma')),
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
    request_date = fields.Date(string=_('Talep Tarihi'), help=_("SAT'ın talep edildiği tarih."))
    tender_round = fields.Integer(string=_('Teklif Turu'), default=1, help=_("Bu ihalenin hangi turda olduğu (1, 2, 3...)."))
    required_delivery_date = fields.Date(string=_('Gerekli Teslim Tarihi'),
                               help=_("Satın alma siparişlerinde kullanılacak gerekli teslim tarihi."))
    description = fields.Html(string=_('İhale Açıklaması'),
                              help=_("İhale ile ilgili detaylı bilgiler ve şartnameler."))
    
    # İhale Kalemleri (One2many ilişki) - İhalenin temelini oluşturur
    
    # Product Matrix fields for variant selection
    grid_product_tmpl_id = fields.Many2one('product.template', store=False, help="Technical field for product_matrix functionalities.")
    grid_update = fields.Boolean(default=False, store=False, help="Whether the grid field contains a new matrix to apply or not.")
    grid = fields.Char(store=False, help="Technical storage of grid. \nIf grid_update, will be loaded on the tender. \nIf not, represents the matrix to open.")
    report_grids = fields.Boolean(string="Print Variant Grids", default=True, help="If set, the matrix of configurable products will be shown on the report of this tender.")
    tender_lines = fields.One2many('ak.tender.line', 'tender_id', string=_('İhale Kalemleri'), required=True)

    # Davetli Tedarikçiler (Many2many ilişki)
    invited_partners = fields.Many2many('res.partner', string=_('Davetli Tedarikçiler'),
                                       domain="[('supplier_rank', '>=', 0), '|', ('id', 'in', allowed_supplier_ids), ('id', 'not in', allowed_supplier_ids if allowed_supplier_ids else [])]",
                                       help=_("Bu ihaleye davet edilecek tedarikçiler. Tek ürünlü ihalelerde, ürünün tanımlı tedarikçileri varsa sadece onlar gösterilir."))
    allowed_supplier_ids = fields.Many2many('res.partner', string='İzin Verilen Tedarikçiler',
                                           compute='_compute_allowed_supplier_ids', store=False,
                                           help="Tek ürünlü ihalelerde ürünün tedarikçileri, çok ürünlü ihalelerde tüm tedarikçiler")

    @api.depends('tender_lines.product_id')
    def _compute_allowed_supplier_ids(self):
        """
        Tek ürünlü ihalelerde ürünün tedarikçilerini hesapla.
        Çok ürünlü ihalelerde veya ürünün tedarikçisi yoksa tüm tedarikçilere izin ver.
        """
        for record in self:
            allowed_suppliers = self.env['res.partner']
            
            # Sadece ürün satırlarını al (section ve note hariç)
            product_lines = record.tender_lines.filtered(lambda l: l.display_type == 'product' and l.product_id)
            
            # Tek ürünlü ihale kontrolü
            if len(product_lines) == 1:
                product = product_lines[0].product_id
                # Ürünün tedarikçilerini al (seller_ids)
                if product.seller_ids:
                    # seller_ids'den partner'ları al
                    allowed_suppliers = product.seller_ids.mapped('partner_id')
                    _logger.info(f"Tek ürünlü ihale: {record.name}, Ürün: {product.name}, Tedarikçi sayısı: {len(allowed_suppliers)}")
            
            # Eğer allowed_suppliers boşsa, tüm tedarikçilere izin ver (domain'de zaten supplier_rank kontrolü var)
            record.allowed_supplier_ids = allowed_suppliers
    
    # Kazanan Teklifler (SAS)
    winning_order_ids = fields.Many2many('purchase.order', string=_('Kazanan Teklifler (SAS)'), compute='_compute_winning_orders', store=True, readonly=True)
    
    @api.depends('purchase_order_ids.state', 'purchase_order_ids.tender_round', 'tender_round')
    def _compute_winning_orders(self):
        for record in self:
            winning_orders = self.env['purchase.order']
            if record.purchase_order_ids:
                # Get the latest tender round
                last_tender_round = max(record.purchase_order_ids.mapped('tender_round')) if record.purchase_order_ids.mapped('tender_round') else 0

                # Filter purchase orders from the last tender round that are in 'purchase' or 'to approve' state
                winning_orders = record.purchase_order_ids.filtered(lambda po:
                    po.tender_round == last_tender_round and
                    po.state in ('to approve', 'purchase', 'done') 
                )
            record.winning_order_ids = winning_orders
        
    winning_supplier_ids = fields.Many2many(
        'res.partner',
        string=_('Kazanan Tedarikçiler'),
        compute='_compute_winning_supplier_ids',
        store=False, # This is a dynamic list based on current state
        help=_("Son teklif turunda Satınalma Siparişi veya Onaylanacak statüsündeki tedarikçiler.")
    )

    @api.depends('winning_order_ids')
    def _compute_winning_supplier_ids(self):
        for record in self:
            winning_partners = self.env['res.partner']
            if record.winning_order_ids:
                winning_partners |= record.winning_order_ids.mapped('partner_id')
            record.winning_supplier_ids = winning_partners

    # İhale Sonuçları (One2many ilişki)
    purchase_order_ids = fields.One2many('purchase.order', 'tender_id', string=_('Teklifler (SAT)'))
        
    # TEKLİF DOKÜMANINA GÖRE KRİTİK ALAN: HEDEF FİYAT
    currency_id = fields.Many2one('res.currency', string=_('Para Birimi'), default=lambda self: self.env.company.currency_id)
    target_price = fields.Monetary(string=_('Hedef Fiyat'), currency_field='currency_id',
                                help=_("Satın Alma Direktörü tarafından belirlenen hedef fiyat."))
    
    def _convert_currency_two_stage(self, amount, from_currency, to_currency, company=None, date=None):
        """
        İki aşamalı para birimi dönüşümü: kaynak -> şirket -> hedef
        
        Args:
            amount: Dönüştürülecek tutar
            from_currency: Kaynak para birimi
            to_currency: Hedef para birimi
            company: Şirket (varsayılan: self.company_id)
            date: Dönüşüm tarihi (varsayılan: bugün)
            
        Returns:
            float: Dönüştürülmüş tutar
        """
        if not date:
            date = fields.Date.today()
            
        if not company:
            company = self.company_id
            
        if from_currency == to_currency:
            return amount
            
        try:
            # 1. Aşama: Kaynak para biriminden şirket para birimine
            company_amount = from_currency._convert(
                amount,
                company.currency_id,
                company,
                date
            )
            
            # 2. Aşama: Şirket para biriminden hedef para birimine
            converted_amount = company.currency_id._convert(
                company_amount,
                to_currency,
                company,
                date
            )
            return converted_amount
        except Exception:
            # Dönüşüm başarısız olursa orijinal değeri döndür
            return amount
    
    def calculate_total_target_price(self):
        """
        Tüm ihale kalemlerinin toplam hedef fiyatını hesapla ve tender'ın hedef fiyatını güncelle
        Para birimi dönüşümü ile birlikte
        """
        self.ensure_one()
        
        total = 0.0
        tender_currency = self.currency_id
        
        for line in self.tender_lines:
            if line.display_type == 'product' and line.target_price and line.quantity:
                line_total = line.target_price * line.quantity
                
                # Para birimi dönüşümü yap - iki aşamalı
                if line.currency_id and line.currency_id != tender_currency:
                    converted_amount = self._convert_currency_two_stage(
                        line_total,
                        line.currency_id,
                        tender_currency
                    )
                    total += converted_amount
                else:
                    total += line_total
        
        self.target_price = total
        return total
    
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
    
    def get_workflow_duration_days(self):
        """
        Dinamik parametre sisteminden workflow duration'ını al
        """
        if not self.workflow_current_state_id:
            return 1
            
        # Dinamik parametreden değeri al
        duration = self.env['ak.workflow.dynamic.parameter'].get_workflow_parameter_value(
            model_name='ak.tender',
            record=self,
            model_field='default_duration_days'
        )
        
        return duration if duration is not None else self.workflow_current_state_id.default_duration_days or 1
            
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

    @api.depends('purchase_order_ids', 'tender_round', 'workflow_current_state_id')
    def _compute_offer_count(self):
        for tender in self:
            # state_code = tender.workflow_current_state_id.code if tender.workflow_current_state_id else None
            tender.offer_count = len(tender.purchase_order_ids.filtered(lambda o: o.tender_round == tender.tender_round))
    
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

    @api.onchange('grid_product_tmpl_id')
    def _set_grid_up(self):
        """Set up the grid when a product template is selected"""
        if self.grid_product_tmpl_id:
            self.grid_update = False
            self.grid = json.dumps(self._get_matrix(self.grid_product_tmpl_id))

    @api.onchange('grid')
    def _apply_grid(self):
        """Apply the grid changes to tender lines"""
        if self.grid and self.grid_update:
            grid = json.loads(self.grid)
            product_template = self.env['product.template'].browse(grid['product_template_id'])
            product_ids = set()
            dirty_cells = grid['changes']
            Attrib = self.env['product.template.attribute.value']
            default_line_vals = {}
            new_lines = []
            
            for cell in dirty_cells:
                combination = Attrib.browse(cell['ptav_ids'])
                no_variant_attribute_values = combination - combination._without_no_variant_attributes()

                # create or find product variant from combination
                product = product_template._create_product_variant(combination)
                
                # Find existing tender lines with this product
                tender_lines = self.tender_lines.filtered(
                    lambda line: (line._origin or line).product_id == product and 
                    (line._origin or line).product_no_variant_attribute_value_ids == no_variant_attribute_values
                )

                # Calculate quantity difference
                old_qty = sum(tender_lines.mapped('quantity'))
                qty = cell['qty']
                diff = qty - old_qty

                if not diff:
                    continue

                product_ids.add(product.id)

                if tender_lines:
                    if qty == 0:
                        # Remove lines if qty was set to 0 in matrix
                        self.tender_lines -= tender_lines
                    else:
                        if len(tender_lines) > 1:
                            raise ValidationError(_("You cannot change the quantity of a product present in multiple tender lines."))
                        else:
                            tender_lines[0].quantity = qty
                else:
                    if not default_line_vals:
                        TenderLine = self.env['ak.tender.line']
                        default_line_vals = TenderLine.default_get(TenderLine._fields.keys())
                    
                    last_sequence = self.tender_lines[-1:].sequence
                    if last_sequence:
                        default_line_vals['sequence'] = last_sequence
                    
                    # Prepare product description with variant attributes
                    product_name = product.display_name
                    for no_variant_attribute_value in no_variant_attribute_values:
                        product_name += "\n" + no_variant_attribute_value.attribute_id.name + ': ' + no_variant_attribute_value.name
                    
                    new_lines.append((0, 0, dict(
                        default_line_vals,
                        product_id=product.id,
                        name=product_name,
                        quantity=qty,
                        product_no_variant_attribute_value_ids=no_variant_attribute_values.ids)
                    ))
            
            if product_ids:
                if new_lines:
                    # Add new tender lines
                    self.update(dict(tender_lines=new_lines))

    def _get_matrix(self, product_template):
        """Get the matrix for a product template"""
        def has_ptavs(line, sorted_attr_ids):
            ptav = line.product_template_attribute_value_ids.ids
            pnav = line.product_no_variant_attribute_value_ids.ids
            pav = pnav + ptav
            pav.sort()
            return pav == sorted_attr_ids
        
        matrix = product_template._get_template_matrix(
            company_id=self.company_id,
            currency_id=self.currency_id)
        
        if self.tender_lines:
            lines = matrix['matrix']
            tender_lines = self.tender_lines.filtered(lambda line: line.product_template_id == product_template)
            for line in lines:
                for cell in line:
                    if not cell.get('name', False):
                        line = tender_lines.filtered(lambda line: has_ptavs(line, cell['ptav_ids']))
                        if line:
                            cell.update({
                                'qty': sum(line.mapped('quantity'))
                            })
        return matrix
        
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
        
        # Comprehensive cache invalidation
        self._invalidate_cache()
        self.env.invalidate_all()
        
        # Force refresh of all related data from database
        self.env.cr.execute("SELECT 1")  # Force database sync
        
        # Re-read the tender record from database to get fresh data
        fresh_tender = self.env['ak.tender'].browse(self.id)
        
        # Get fresh purchase orders directly from database
        self.env.cr.execute("""
            SELECT id FROM purchase_order 
            WHERE tender_id = %s AND tender_round = %s AND state != 'cancel'
            ORDER BY id
        """, (self.id, self.tender_round))
        
        po_ids = [row[0] for row in self.env.cr.fetchall()]
        tender_pos = self.env['purchase.order'].sudo().browse(po_ids)
        
        
        # Build vendors list
        vendors = []
        for po in tender_pos:
            vendors.append({
                'id': po.id,
                'partner_id': po.partner_id.id,
                'partner_name': po.partner_id.name,
            })
        
        # Get tender lines with vendor data
        tender_lines = []
        for line in fresh_tender.sudo().tender_lines:
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
            for po in tender_pos:
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
        
    def action_view_purchase_order(self, purchase_order_id=None):
        """
        Open a specific purchase order form view.
        This method is used by the notification system to open a specific purchase order.
        """
        self.ensure_one()
        if not purchase_order_id:
            # If no specific purchase order is provided, find the most recent one
            purchase_order = self.env['purchase.order'].search([
                ('tender_id', '=', self.id)
            ], order='create_date desc', limit=1)
            if not purchase_order:
                # If no purchase order found, show all purchase orders
                return self.action_view_purchase_orders()
            purchase_order_id = purchase_order.id
            
        # Open the specific purchase order
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['res_id'] = purchase_order_id
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
        Tender para birimi değiştiğinde hedef fiyatı yeniden hesapla
        Tender line para birimlerini zorla değiştirmez
        """
        if self.currency_id:
            self.calculate_total_target_price()
    
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
        
    def action_set_target_price(self):
        """
        Open the Set Target Price wizard.
        This method is called from the server action.
        """
        self.ensure_one()
        
        return {
            'name': _('Hedef Fiyat Belirleme'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.set.target.price.wizard',
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
        # and exclude cancelled purchase orders
        valid_previous_pos = previous_pos.filtered(lambda po: po.amount_total > 0 and po.state != 'cancel')
        
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
            'location_dest_id': self.location_dest_id.id if self.location_dest_id else False, # Transfer delivery location
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
                'line_currency_id': prev_line.line_currency_id.id,
                'line_price_unit': prev_line.line_price_unit,
                'discount': prev_line.discount if hasattr(prev_line, 'discount') else 0.0,
                'date_planned': date_planned,
                'taxes_id': [(6, 0, prev_line.taxes_id.ids)],
                'tender_line_id': prev_line.tender_line_id.id if prev_line.tender_line_id else False,
                'sequence': prev_line.sequence,
                'display_type': prev_line.display_type,
                'alt_materials': prev_line.alt_materials if hasattr(prev_line, 'alt_materials') else False,
                
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
                'price_unit': 0.0,
                'line_currency_id': tender_line.currency_id.id,
                'line_price_unit': tender_line.target_price or 0.0,
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
            # Use our custom template with the tender number
            template_id = self.env.ref('ak_tender.email_template_edi_purchase_custom').id
        except ValueError:
            # Fall back to the standard template if our custom one is not found
            try:
                template_id = self.env.ref('purchase.email_template_edi_purchase').id
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
                pass
        
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
        
    def create_orders_from_total_selection(self, po_ids, use_npv=False):
        """
        Create purchase orders from the selected purchase orders based on total amount or NPV.
        
        Args:
            po_ids (list): List of purchase order IDs to create orders from
            use_npv (bool): Whether to use NPV for selection instead of total amount
            
        Returns:
            dict: Action to reload the page
        """
        self.ensure_one()
        if not po_ids:
            return {'type': 'ir.actions.act_window_close'}
            
        # Convert string IDs to integers if needed
        if isinstance(po_ids[0], str):
            po_ids = [int(po_id) for po_id in po_ids]
            
        # Get the selected purchase orders
        selected_pos = self.env['purchase.order'].browse(po_ids)

        if not selected_pos:
            return {'type': 'ir.actions.act_window_close'}
            
        # Confirm the selected purchase orders
        confirmed_orders = self.env['purchase.order']
        
        try:
            for po in selected_pos:
                
                # Update selection fields
                po.write({'user_selection': True})
                
                # Update lines
                for line in po.order_line:
                    line.write({'user_selection': True})
                
                # Confirm if not already confirmed
                if po.state in ['draft', 'sent']:
                    po.button_confirm()
                    po.write({
                        'date_approve': fields.Datetime.now(),
                        'state': 'purchase'
                    })
                
                confirmed_orders += po
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
        if confirmed_orders:
            # Log the creation
            self.message_post(
                body=_("%s sipariş(ler) onaylandı: %s") % (
                    len(confirmed_orders), ", ".join(confirmed_orders.mapped('name'))
                ),
                subtype_xmlid='mail.mt_note'
            )
            
            return {
                'success': True,
                'message': f'{len(confirmed_orders)} sipariş başarıyla onaylandı',
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            return {'success': False, 'error': 'Hiç sipariş oluşturulamadı'}
        
    def save_user_selection(self, selections):
        """
        Save user selections to the database.
        
        Args:
            selections: Dictionary containing selection data
            
        Returns:
            dict: Result of the operation
        """
        self.ensure_one()
        
        
        # List all purchase orders for this tender
        all_pos = self.purchase_order_ids
        
        try:
            # Process each selection
            for i, selection in enumerate(selections):
                vendor_id = selection.get('vendor_id')
                tender_line_id = selection.get('tender_line_id')
                is_checked = selection.get('is_checked', False)
                
                
                # Find the purchase order by ID (vendor_id is actually PO ID)
                po = self.purchase_order_ids.filtered(
                    lambda p: p.id == vendor_id and p.tender_round == self.tender_round
                )
                
                if not po:
                    continue
                    
                po = po[0]
                
                if tender_line_id:
                    # Product selection - update purchase order line
                    po_lines = po.order_line.filtered(lambda l: l.tender_line_id and l.tender_line_id.id == tender_line_id)
                    
                    if po_lines:
                        po_line = po_lines[0]
                        
                        # Use SQL to ensure the write happens
                        self.env.cr.execute(
                            "UPDATE purchase_order_line SET user_selection = %s WHERE id = %s",
                            (is_checked, po_line.id)
                        )
                    else:
                        pass  # No PO line found, do nothing
                else:
                    # Total selection - update purchase order
                    self.env.cr.execute(
                        "UPDATE purchase_order SET user_selection = %s WHERE id = %s",
                        (is_checked, po.id)
                    )
                    
            
            # Commit changes
            self.env.cr.commit()
            
            # Force cache invalidation to ensure fresh data on next read
            self.env.invalidate_all()
            self._invalidate_cache()
            
            # Also invalidate related models
            self.env['purchase.order'].invalidate_cache()
            self.env['purchase.order.line'].invalidate_cache()
            
            
            return {'success': True, 'message': 'Selection saved successfully'}
            
        except Exception as e:
            self.env.cr.rollback()
            return {'success': False, 'error': str(e)}
    
    def _save_system_selection_line(self, po_line_id, is_selected):
        """
        Save system selection for a purchase order line.
        Called from template during rendering.
        """
        try:
            self.env.cr.execute(
                "UPDATE purchase_order_line SET system_selection = %s WHERE id = %s",
                (is_selected, po_line_id)
            )
            return True
        except Exception as e:
            return False
    
    def _save_system_selection_po(self, po_id, is_selected):
        """
        Save system selection for a purchase order.
        Called from template during rendering.
        """
        try:
            self.env.cr.execute(
                "UPDATE purchase_order SET system_selection = %s WHERE id = %s",
                (is_selected, po_id)
            )
            return True
        except Exception as e:
            return False
    
    def calculate_and_save_system_selections(self):
        """
        Calculate system selections based on NPV and save to database.
        Called when report is opened.
        """
        self.ensure_one()
        
        try:
            # Get current round purchase orders
            current_pos = self.purchase_order_ids.filtered(lambda p: p.tender_round == self.tender_round)
            
            # Calculate product-level system selections
            for tender_line in self.tender_lines.filtered(lambda l: l.display_type == 'product'):
                # Get all vendor lines for this product
                vendor_lines = []
                for po in current_pos:
                    po_line = po.order_line.filtered(lambda l: l.tender_line_id.id == tender_line.id)
                    if po_line:
                        vendor_lines.append(po_line[0])
                
                # Find minimum NPV/price for this product
                min_value = None
                selected_line = None
                
                for line in vendor_lines:
                    # Use NPV if available, otherwise use price_subtotal
                    value = getattr(line, 'npv_value', 0) if hasattr(line, 'npv_value') and line.npv_value > 0 else line.price_subtotal
                    if value > 0 and (min_value is None or value < min_value):
                        min_value = value
                        selected_line = line
                
                # Update system selections for this product
                for line in vendor_lines:
                    is_selected = (line == selected_line)
                    self.env.cr.execute(
                        "UPDATE purchase_order_line SET system_selection = %s WHERE id = %s",
                        (is_selected, line.id)
                    )
            
            # Calculate total-level system selections
            vendor_totals = []
            excluded_pos_info = []
            
            for po in current_pos:
                total_npv = 0
                total_amount = 0
                has_npv = False
                has_incomplete_offer = False
                
                # Check if PO has lines for all tender products
                tender_product_count = len(self.tender_lines.filtered(lambda l: l.display_type == 'product'))
                po_product_count = len(po.order_line.filtered(lambda l: l.tender_line_id and not l.display_type))
                
                if po_product_count < tender_product_count:
                    has_incomplete_offer = True
                
                for line in po.order_line.filtered(lambda l: l.tender_line_id and not l.display_type):
                    total_amount += line.price_subtotal
                    if line.price_subtotal <= 0.01:
                        has_incomplete_offer = True
                    if hasattr(line, 'npv_value') and line.npv_value > 0:
                        total_npv += line.npv_value
                        has_npv = True
                
                # Skip POs that have incomplete offers
                if has_incomplete_offer:
                    excluded_pos_info.append((po.id, po.partner_id.name, "incomplete_offer"))
                    continue
                    
                # Use NPV if available, otherwise use total amount
                value = total_npv if has_npv and total_npv > 0 else total_amount
                if value > 0:
                    vendor_totals.append((po, value))
                else:
                    excluded_pos_info.append((po.id, po.partner_id.name, "zero_value"))
            
            
            # Find minimum total
            if vendor_totals:
                min_total = min(vendor_totals, key=lambda x: x[1])
                selected_po = min_total[0]
                
                # Update system selections for totals - only for POs in vendor_totals
                for po, value in vendor_totals:
                    is_selected = (po == selected_po)
                    self.env.cr.execute(
                        "UPDATE purchase_order SET system_selection = %s WHERE id = %s",
                        (is_selected, po.id)
                    )
                
                # Clear system selection for POs not in vendor_totals (incomplete offers)
                excluded_pos = current_pos.filtered(lambda p: p not in [po for po, _ in vendor_totals])
                for po in excluded_pos:
                    self.env.cr.execute(
                        "UPDATE purchase_order SET system_selection = %s WHERE id = %s",
                        (False, po.id)
                    )
            
            # Commit changes
            self.env.cr.commit()
            
        except Exception as e:
            self.env.cr.rollback()
        
    def save_all_selections(self, tender_id, selections):
        """
        Save all user selections at once.
        
        Args:
            tender_id: The ID of the tender
            selections: Dictionary with product and total selections
            
        Returns:
            dict: Result of the operation
        """
        # Find the tender record
        tender = self.browse(tender_id)
        if not tender.exists():
            return {'success': False, 'error': 'Tender not found'}
        
        # Log the input parameters
        
        try:
            # First, clear all user selections for this tender round
            all_po_lines = tender.purchase_order_ids.filtered(
                lambda p: p.tender_round == tender.tender_round
            ).mapped('order_line')
            all_po_lines.write({'user_selection': False})
            
            # Process product selections
            if 'product' in selections:
                for selection in selections['product']:
                    value = selection.get('value')
                    is_checked = selection.get('isChecked')
                    
                    if value and is_checked:  # Only process checked selections
                        parts = value.split('_')
                        if len(parts) >= 2:
                            vendor_id = int(parts[0])
                            tender_line_id = int(parts[1])
                            
                            # Find the purchase order for this vendor in the current round
                            po = tender.purchase_order_ids.filtered(lambda p: p.partner_id.id == vendor_id and p.tender_round == tender.tender_round)
                            if po:
                                # Find the purchase order line for this tender line
                                po_line = po[0].order_line.filtered(lambda l: l.tender_line_id.id == tender_line_id)
                                if po_line:
                                    # Set this line as user selected
                                    po_line.write({'user_selection': True})
            
            # Clear all PO user selections for this tender round
            all_pos = tender.purchase_order_ids.filtered(
                lambda p: p.tender_round == tender.tender_round
            )
            all_pos.write({'user_selection': False})
            
            # Process total selections
            if 'total' in selections:
                for selection in selections['total']:
                    value = selection.get('value')
                    is_checked = selection.get('isChecked')
                    
                    if value and is_checked:  # Only process checked selections
                        vendor_id = int(value)
                        
                        # Find the purchase order for this vendor in the current round
                        po = tender.purchase_order_ids.filtered(lambda p: p.partner_id.id == vendor_id and p.tender_round == tender.tender_round)
                        if po:
                            # Set this PO as user selected
                            po[0].write({'user_selection': True})
            
            # Force commit to ensure changes are saved
            self.env.cr.commit()
            
            return {'success': True, 'message': 'All selections saved successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_purchase_order(self, po_id):
        """
        Delete a user-created purchase order after cancelling it.
        Only works for orders created from tender selections.
        
        Args:
            po_id (int): The ID of the purchase order to delete
            
        Returns:
            dict: Result of the operation
        """
        self.ensure_one()
        
        try:
            # Find the purchase order
            po = self.env['purchase.order'].browse(po_id)
            if not po.exists():
                return {'success': False, 'error': 'Satınalma siparişi bulunamadı'}
            
            # Check if it belongs to this tender
            if po.tender_id.id != self.id:
                return {'success': False, 'error': 'Bu sipariş bu ihaleye ait değil'}
            
            # Only allow deletion of user-created orders (purchase/done state)
            if po.state not in ['purchase', 'done']:
                return {'success': False, 'error': 'Sadece oluşturulmuş siparişler silinebilir'}
            
            partner_name = po.partner_id.name
            po_name = po.name
            
            # Cancel and delete the order
            po.button_cancel()
            po.unlink()
            
            return {
                'success': True, 
                'message': f'{partner_name} tedarikçisinin siparişi ({po_name}) iptal edilip silindi'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_orders_from_selections(self, selections):
        """
        Create purchase orders from the selected product-vendor combinations.
        
        Args:
            selections (list): List of strings in format "po_id_tender_line_id"
            
        Returns:
            dict: Action to reload the page
        """
        self.ensure_one()

        if not selections:
            return {'type': 'ir.actions.act_window_close'}
            
        # Parse the selection values (format: "po_id_tender_line_id")
        po_products = {}
        for selection in selections:
            parts = selection.split('_')
            if len(parts) >= 2:
                try:
                    po_id = int(parts[0])
                    tender_line_id = int(parts[1])
                    
                    if po_id not in po_products:
                        po_products[po_id] = []
                    po_products[po_id].append(tender_line_id)
                except ValueError as e:
                    continue
        
        if not po_products:
            return {'type': 'ir.actions.act_window_close'}
            
        # Get existing user-selected orders for this tender
        existing_orders = self.env['purchase.order'].search([
            ('tender_id', '=', self.id),
            ('state', 'in', ['purchase', 'done']),
            ('user_selection', '=', True)
        ])
        
        updated_orders = self.env['purchase.order']
        created_orders = self.env['purchase.order']
        
        # Process each PO selection
        for po_id, tender_line_ids in po_products.items():
            # Find the source purchase order by ID
            source_po = self.purchase_order_ids.filtered(lambda po: po.id == po_id and po.tender_round == self.tender_round)
            
            if not source_po:
                continue
                
            source_po = source_po[0]
            
            # Check if there's an existing order for this partner
            existing_order = existing_orders.filtered(lambda o: o.partner_id.id == source_po.partner_id.id)
            
            if existing_order:
                # Update existing order
                
                # Get current lines in the existing order
                current_line_ids = existing_order[0].order_line.filtered(lambda l: l.tender_line_id).mapped('tender_line_id.id')
                new_line_ids = set(tender_line_ids)
                current_line_ids_set = set(current_line_ids)
                
                if new_line_ids == current_line_ids_set:
                    updated_orders += existing_order[0]
                    continue
                
                # Lines are different, need to update
                
                # Cancel existing order and create new one
                existing_order[0].button_cancel()
            
            # Create new order (either first time or replacement)
            
            try:
                # Get selected lines from source PO
                selected_lines = source_po.order_line.filtered(
                    lambda l: l.tender_line_id and l.tender_line_id.id in tender_line_ids
                )
                
                if not selected_lines:
                    continue
                
                # Create new PO without lines first
                new_po_vals = {
                    'partner_id': source_po.partner_id.id,
                    'state': 'draft',
                    'tender_id': self.id,
                    'origin': f"{self.code} - {source_po.name}",
                    'tender_round': self.tender_round,
                    'user_selection': True,
                    'system_selection': False,
                    'selection_note': _("Ürün bazlı kullanıcı seçimi"),
                    'company_id': source_po.company_id.id,
                    'currency_id': source_po.currency_id.id,
                    'date_order': source_po.date_order,
                    'payment_term_id': source_po.payment_term_id.id if source_po.payment_term_id else False,
                }
                
                new_po = self.env['purchase.order'].with_context(from_tender=True).create(new_po_vals)
                
                # Clear any auto-created lines first
                if new_po.order_line:
                    new_po.order_line.unlink()
                
                # Copy selected lines with all their values
                for original_line in selected_lines:
                    # Check if this line was also selected by system
                    was_system_selected = original_line.system_selection
                    
                    # Copy line with all values
                    line_vals = {
                        'order_id': new_po.id,
                        'product_id': original_line.product_id.id,
                        'name': original_line.name,
                        'product_qty': original_line.product_qty,
                        'product_uom': original_line.product_uom.id,
                        'price_unit': original_line.price_unit,
                        'line_currency_id': original_line.line_currency_id.id,
                        'line_price_unit': original_line.line_price_unit,
                        'discount': getattr(original_line, 'discount', 0.0),
                        'date_planned': original_line.date_planned,
                        'taxes_id': [(6, 0, original_line.taxes_id.ids)],
                        'tender_line_id': original_line.tender_line_id.id,
                        'sequence': original_line.sequence,
                        'display_type': original_line.display_type,
                        'user_selection': True,
                        'system_selection': was_system_selected,
                    }
                    
                    # Copy custom fields if they exist
                    if hasattr(original_line, 'alt_materials'):
                        line_vals['alt_materials'] = original_line.alt_materials
                    if hasattr(original_line, 'npv_value'):
                        line_vals['npv_value'] = original_line.npv_value
                    if hasattr(original_line, 'warranty_period'):
                        line_vals['warranty_period'] = original_line.warranty_period
                    
                    # Set appropriate note
                    if was_system_selected:
                        line_vals['selection_note'] = _("Ürün bazlı kullanıcı ve sistem seçimi")
                    else:
                        line_vals['selection_note'] = _("Ürün bazlı kullanıcı seçimi")
                    
                    self.env['purchase.order.line'].create(line_vals)
                
                # Now confirm the purchase order
                new_po.button_confirm()
                new_po.write({
                    'date_approve': fields.Datetime.now(),
                    'state': 'purchase'
                })
                created_orders += new_po
                    
            except Exception as e:
                continue
            
        
        # Log the results
        all_processed_orders = created_orders + updated_orders
        
        if all_processed_orders:
            created_names = created_orders.mapped('name') if created_orders else []
            updated_names = updated_orders.mapped('name') if updated_orders else []
            
            
            message_parts = []
            if created_orders:
                message_parts.append(_("%s yeni sipariş oluşturuldu: %s") % (len(created_orders), ", ".join(created_names)))
            if updated_orders:
                message_parts.append(_("%s sipariş güncellendi: %s") % (len(updated_orders), ", ".join(updated_names)))
            
            self.message_post(
                body="<br/>".join(message_parts),
                subtype_xmlid='mail.mt_note'
            )
        else:
            pass
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def export_comparison_report_to_excel(self, tender_id, table_html):
        """
        Exports the given HTML table content to an Excel file.
        """
        self = self.sudo()
        tender = self.browse(tender_id)
        if not tender:
            raise UserError(_("İhale bulunamadı."))

        # Parse HTML table using BeautifulSoup
        soup = BeautifulSoup(table_html, 'html.parser')
        table = soup.find('table', class_='comparison-table')

        if not table:
            raise UserError(_("HTML içeriğinde karşılaştırma tablosu bulunamadı."))

        # Extract table headers - handle colspan
        headers = []
        thead = table.find('thead')
        if thead:
            header_rows = thead.find_all('tr')
            for header_row in header_rows:
                for th in header_row.find_all('th'):
                    colspan_attr = th.get('colspan')
                    colspan_value = int(colspan_attr or 1)
                    
                    header_text = th.get_text(strip=True)
                    if header_text:  # Only add non-empty headers
                        for i in range(colspan_value): # Changed _ to i
                            headers.append(header_text)

        # If no headers found, create default ones
        if not headers:
            headers = ['Ürün', 'Alan']  # Default headers

        # Extract table rows
        data = []
        rows = table.find('tbody').find_all('tr')
        
        # Keep track of rowspan cells
        rowspan_tracker = {}

        for r_idx, row in enumerate(rows):
            cols = row.find_all(['td', 'th'])
            row_data = []
            col_position = 0
            
            for col in cols:
                # Skip positions occupied by rowspan from previous rows
                while rowspan_tracker.get((r_idx, col_position)):
                    row_data.append(rowspan_tracker[(r_idx, col_position)])
                    col_position += 1
                
                # Get colspan safely
                colspan_attr = col.get('colspan')
                colspan_value = int(colspan_attr or 1)
                
                # Get rowspan safely
                rowspan_attr = col.get('rowspan')
                rowspan_value = int(rowspan_attr or 1)
                    
                cell_text = col.get_text(strip=True)
                
                # Add cell value for each colspan
                for i in range(colspan_value): # Changed _ to i
                    row_data.append(cell_text)
                    col_position += 1
                
                # Track rowspan cells for future rows
                if rowspan_value > 1:
                    for i in range(1, rowspan_value):
                        for j in range(colspan_value):
                            rowspan_tracker[(r_idx + i, col_position - colspan_value + j)] = cell_text

            data.append(row_data)

        # Determine the maximum number of columns
        if data:
            max_cols = max([len(row) for row in data])
        else:
            max_cols = len(headers) if headers else 0
        
        # Pad rows to have the same number of columns
        for row in data:
            while len(row) < max_cols:
                row.append('')

        # Ensure headers match the number of columns
        while len(headers) < max_cols:
            headers.append(f'Column {len(headers) + 1}')
        
        # Truncate headers if they exceed max_cols
        headers = headers[:max_cols]

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Remove rows that are entirely empty (e.g., due to rowspan handling)
        df = df.loc[(df != '').any(axis=1)]

        # Generate Excel file
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Tedarikçi Karşılaştırma', index=False)
        writer.close()
        output.seek(0)
        excel_file = base64.b64encode(output.read())

        # Create an attachment and return its download action
        attachment = self.env['ir.attachment'].create({
            'name': f"Tedarikci_Karsilastirma_{tender.code}.xlsx",
            'type': 'binary',
            'datas': excel_file,
            'res_model': 'ak.tender',
            'res_id': tender.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'action': {
                'id': attachment.id,
                'name': _('Tedarikçi Karşılaştırma Raporu'),
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
        }
