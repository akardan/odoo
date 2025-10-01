
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    tender_id = fields.Many2one('ak.tender', string='İhale', ondelete='restrict')
    offer_date = fields.Datetime(string='Teklif Tarihi', default=fields.Datetime.now, readonly=True)
    tender_round = fields.Integer(string='Teklif Turu', default=1, help="Bu teklifin hangi turda sunulduğu (1, 2, 3...).")
    guarantee_period = fields.Char(string='Garanti Süresi', help="Tedarikçinin sunduğu garanti süresi (örn: 2 Yıl).")
    # NPV calculation fields
    total_npv = fields.Monetary(string='Toplam NPV Değeri', currency_field='currency_id',
                               help="Tüm satırların NPV değerlerinin toplamı.", readonly=True)
    is_readonly = fields.Boolean(compute='_compute_is_readonly', store=False)
    # Selection fields
    system_selection = fields.Boolean(
        string='Sistem Seçimi',
        default=False,
        help="Bu sipariş sistem tarafından otomatik olarak seçildi (NPV veya diğer kriterlere göre)"
    )
    user_selection = fields.Boolean(
        string='Kullanıcı Seçimi',
        default=False,
        help="Bu sipariş kullanıcı tarafından karşılaştırma ekranında manuel olarak seçildi"
    )
    selection_note = fields.Text(
        string='Seçim Notu',
        help="Sistem Seçiminden farklı ise, ilgili notlar (neden seçildi, hangi kriterlere göre seçildi, vb.)"
    )

    new_message_count = fields.Integer(
        string=_('Mesajlar'),
        compute='_compute_new_message_count',
        store=False,
        help=_("Bu teklife ait yeni mesajların sayısı.")
    )

    @api.depends('message_ids')
    def _compute_new_message_count(self):
        for record in self:
            record.new_message_count = len(record.message_ids.filtered(
                lambda msg: msg.message_type in ['comment', 'email'] and 
                        msg.author_id == record.partner_id
            ))
    
    # def _compute_new_message_count(self):
    #     for record in self:
    #         # Assuming 'message_unread' is not directly available or causing issues,
    #         # we count all messages for now. If a specific "unread" logic is needed,
    #         # it would require a custom tracking mechanism (e.g., a custom message_read_date per user).
    #         record.new_message_count = self.env['mail.message'].sudo().search_count([
    #             ('res_id', '=', record.id),
    #             ('model', '=', 'purchase.order'),
    #             ('message_type', 'in', ['comment', 'email'])
    #         ])

    
    @api.depends('tender_id.workflow_current_state_id', 'tender_round')
    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = False
            if not record.tender_id:
                continue
            state_code = record.tender_id.workflow_current_state_id.code if record.tender_id.workflow_current_state_id else None
            if state_code == 'completed' or state_code == 'cancelled':
                record.is_readonly = True
    
    @api.constrains('tender_id', 'order_line')
    def _check_alternative_products(self):
        """
        İhale tipine göre muadil ürün kontrolü yapar.
        Direkt ihale tipinde muadil ürün kabul edilmez.
        Endirekt ihale tipinde ise konfigürasyon ayarına göre kabul edilir veya edilmez.
        """
        for record in self:
            if not record.tender_id:
                continue
                
            # Direkt ihale tipinde muadil ürün kabul edilmez
            if record.tender_id.tender_type == 'direct':
                alternative_lines = record.order_line.filtered(lambda l: l.alt_materials)
                if alternative_lines:
                    raise ValidationError(_(
                        "Direkt ihale tipinde muadil ürün kabul edilmez. "
                        "Lütfen orijinal ürünleri kullanın."
                    ))
            
            # Endirekt ihale tipinde konfigürasyon ayarına göre kontrol et
            elif record.tender_id.tender_type == 'indirect':
                # Ayarlardan alternatif ürünlere izin verilip verilmediğini kontrol et
                allow_alternative = self.env['ir.config_parameter'].sudo().get_param(
                    'ak_tender_allow_alternative_products', 'True').lower() in ('true', '1', 't')
                
                if not allow_alternative:
                    alternative_lines = record.order_line.filtered(lambda l: l.alt_materials)
                    if alternative_lines:
                        raise ValidationError(_(
                            "Endirekt ihale tipinde muadil ürün kabul edilmemektedir. "
                            "Lütfen orijinal ürünleri kullanın."
                        ))

    # The logic for creating lines needs to be adapted.
    # The original logic was creating 'ak.tender.result.line' for each 'ak.tender.line'.
    # Now we need to create 'purchase.order.line' for each 'ak.tender.line'.
    def create_lines_from_tender(self):
        """Create purchase order lines from tender lines"""
        self.ensure_one()
        if not self.tender_id or not self.tender_id.tender_lines:
            return

        # Clear existing lines to avoid duplicates if re-run
        self.order_line = [(5, 0, 0)]
        
        lines_to_create = []
        for tender_line in self.tender_id.tender_lines:
            # Skip lines without product for product type lines
            if tender_line.display_type == 'product' and not tender_line.product_id:
                continue
                
            # Create line based on type
            if tender_line.display_type == 'line_section':
                # Section line
                line_vals = {
                    'display_type': 'line_section',
                    'name': tender_line.name or '',
                    'tender_line_id': tender_line.id,
                    'product_qty': 0.0,  # Set a default quantity for section lines
                }
            elif tender_line.display_type == 'line_note':
                # Note line
                line_vals = {
                    'display_type': 'line_note',
                    'name': tender_line.name or '',
                    'tender_line_id': tender_line.id,
                    'product_qty': 0.0,  # Set a default quantity for note lines
                }
            else:
                # Product line
                # Use product's purchase description if available
                description = tender_line.name
                if not description and tender_line.product_id and tender_line.product_id.description_purchase:
                    description = tender_line.product_id.description_purchase
                elif not description and tender_line.product_id:
                    description = tender_line.product_id.name
                
                line_vals = {
                    'product_id': tender_line.product_id.id,
                    'name': description or '',
                    'product_qty': tender_line.quantity or 1.0,
                    'product_uom': tender_line.uom_id.id or tender_line.product_id.uom_id.id,
                    'price_unit': 0,  # Price will be filled by the supplier
                    'date_planned': tender_line.required_delivery_date or self.tender_id.required_delivery_date or fields.Date.today(),
                    'tender_line_id': tender_line.id,
                }
            
            lines_to_create.append((0, 0, line_vals))
        
        # Create all lines at once
        if lines_to_create:
            self.order_line = lines_to_create

    @api.model
    def create(self, vals):
        # Create the order first
        order = super(PurchaseOrder, self).create(vals)
        
        # If a tender_id is provided and skip_create_lines is not in context, auto-create lines
        # We're now handling line creation in create_purchase_orders_for_suppliers
        # so we'll skip the automatic creation here
        if order.tender_id and not self.env.context.get('skip_create_lines') and not self.env.context.get('from_tender'):
            order.create_lines_from_tender()
        
        return order
    
    def calculate_total_npv(self):
        """
        Calculate the total NPV value for the order based on the NPV values of its lines.
        Convert each line's NPV to PO currency before summing.
        """
        for order in self:
            # Calculate NPV for each line
            for line in order.order_line:
                line.calculate_npv()
            
            # Sum up the NPV values with currency conversion to PO currency
            total_npv = 0.0
            order_currency = order.currency_id
            
            for line in order.order_line:
                if line.npv_value and line.tender_line_currency_id:
                    if line.tender_line_currency_id == order_currency:
                        # Same currency, add directly
                        total_npv += line.npv_value
                    else:
                        # Convert from tender line currency to PO currency
                        converted_npv = line._convert_currency_two_stage(
                            line.npv_value,
                            line.tender_line_currency_id,
                            order_currency
                        )
                        total_npv += converted_npv
                elif line.npv_value:
                    # No tender line currency, assume PO currency
                    total_npv += line.npv_value
            
            order.total_npv = total_npv
        
        return True
    
    def button_confirm(self):
        """Override to calculate NPV before confirming the order"""
        for order in self:
            order.calculate_total_npv()
        return super(PurchaseOrder, self).button_confirm()
        
    @api.onchange('payment_term_id')
    def _onchange_payment_term_id(self):
        """Recalculate NPV when payment term changes"""
        if self.order_line:
            self.calculate_total_npv()
            
    def write(self, vals):
        """Override to recalculate NPV when payment term changes"""
        result = super(PurchaseOrder, self).write(vals)
        
    def write(self, vals):
        """Override to recalculate NPV when payment term changes"""
        result = super(PurchaseOrder, self).write(vals)
        
        if 'payment_term_id' in vals:
            self.calculate_total_npv()
            
        return result
        
    def button_to_approve(self):
        """
        Set the purchase order state to 'to approve' directly.
        This is used in the tender process to set RFQs to approval state.
        """
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def _send_supplier_tender_update_email(self):
        """
        Sends an email notification to the purchaser (user_id) when a supplier updates their tender.
        """
        self.ensure_one()
        if self.user_id and self.user_id.email_formatted:
            template = self.env.ref('ak_tender.email_template_supplier_tender_update', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True, email_values={'email_to': self.user_id.email_formatted})
                _logger.info(f"Email notification sent to purchaser {self.user_id.email_formatted} for tender update on {self.name}")
            else:
                _logger.warning("Mail template 'email_template_supplier_tender_update' not found.")
        else:
            _logger.warning(f"Purchaser (user_id) or their email not found for order {self.name}. Email notification skipped.")

