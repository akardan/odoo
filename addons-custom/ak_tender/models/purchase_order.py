# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Fields from ak.tender.result
    tender_id = fields.Many2one('ak.tender', string='İhale', ondelete='restrict')
    
    # The domain for partner_id will be handled in the view to ensure correctness.

    offer_date = fields.Datetime(string='Teklif Tarihi', default=fields.Datetime.now, readonly=True)
    tender_round = fields.Integer(string='Teklif Turu', default=1, help="Bu teklifin hangi turda sunulduğu (1, 2, 3...).")
    
    # currency_id is already in purchase.order
    
    # total_price is amount_total in purchase.order

    # payment_terms_id is already in purchase.order
    guarantee_period = fields.Char(string='Garanti Süresi', help="Tedarikçinin sunduğu garanti süresi (örn: 2 Yıl).")
    # notes is notes in purchase.order
    
    # status is state in purchase.order

    # purchase_order_id is self.id now.
    
    # NPV calculation fields
    total_npv = fields.Monetary(string='Toplam NPV Değeri', currency_field='currency_id',
                               help="Tüm satırların NPV değerlerinin toplamı.", readonly=True)
    
    is_readonly = fields.Boolean(compute='_compute_is_readonly', store=False)

    @api.depends('tender_id.workflow_current_state_id', 'tender_round')
    def _compute_is_readonly(self):
        for record in self:
            record.is_readonly = False
            if not record.tender_id:
                continue
            state_code = record.tender_id.workflow_current_state_id.code if record.tender_id.workflow_current_state_id else None
            if state_code == 'second_tender_round' and record.tender_round == 1:
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
        """
        for order in self:
            # Calculate NPV for each line
            for line in order.order_line:
                line.calculate_npv()
            
            # Sum up the NPV values of all lines
            total_npv = sum(line.npv_value for line in order.order_line)
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
        """Override to recalculate NPV when payment term changes and send notifications"""
        # Check if this is a price update
        price_update = any(field in vals for field in ['order_line', 'amount_untaxed', 'amount_total'])
        
        result = super(PurchaseOrder, self).write(vals)
        
        if 'payment_term_id' in vals:
            self.calculate_total_npv()
            
        # Send notification if this is a price update and has a tender
        if price_update:
            for record in self:
                if record.tender_id:
                    self._send_bid_notification(record)
                    
        return result
        
    @api.model
    def create(self, vals):
        """Override to send notification when a purchase order is created"""
        record = super(PurchaseOrder, self).create(vals)
        
        # Send notification if this has a tender
        if record.tender_id:
            self._send_bid_notification(record)
            
        return record
        
    def _send_bid_notification(self, order):
        """Send notification to tender managers when a supplier submits a bid"""
        if not order.tender_id or not order.partner_id:
            return
            
        # Find users who should be notified (tender creator and followers)
        users_to_notify = self.env['res.users'].sudo()
        
        # Add the tender creator
        if order.tender_id.create_uid:
            users_to_notify |= order.tender_id.create_uid
        
        # Add followers with write access (typically purchasers)
        for follower in order.tender_id.message_follower_ids:
            if follower.partner_id.user_ids:
                users_to_notify |= follower.partner_id.user_ids
        
        if not users_to_notify:
            return
            
        # Format the bid amount
        bid_amount = f"{order.amount_untaxed} {order.currency_id.symbol}"
        
        # Create the message body
        message_body = f"""
        <p>Yeni bir teklif alındı:</p>
        <ul>
            <li><strong>Tedarikçi:</strong> {order.partner_id.name}</li>
            <li><strong>Teklif Tutarı:</strong> {bid_amount}</li>
            <li><strong>Teklif Tarihi:</strong> {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}</li>
        </ul>
        <p>Detayları görmek için <a href="/web#id={order.id}&model=purchase.order&view_type=form">tıklayın</a>.</p>
        """
        
        _logger.info(f"Sending bid notifications to {len(users_to_notify)} users for tender {order.tender_id.name}")
        
        # Create a notification for each user
        for user in users_to_notify:
            try:
                _logger.info(f"Creating notification for user {user.name} (ID: {user.id})")
                
                # Create a mail.message record
                message = self.env['mail.message'].sudo().create({
                    'model': 'ak.tender',
                    'res_id': order.tender_id.id,
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_note').id,
                    'subject': f"Yeni Teklif: {order.partner_id.name} - {bid_amount}",
                    'body': message_body,
                    'author_id': self.env.user.partner_id.id,
                    'email_from': self.env.user.email_formatted,
                    'notification_ids': [(0, 0, {
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox',
                        'notification_status': 'sent',
                    })],
                })
                
                _logger.info(f"Created message ID: {message.id}")
                
                # Create a bus notification to update the UI
                self.env['bus.bus']._sendone(
                    user.partner_id,
                    'mail.message/inbox',
                    {
                        'type': 'activity_updated',
                        'message_id': message.id,
                    }
                )
                
                _logger.info(f"Sent bus notification for message ID: {message.id}")
                
                # Also create a mail.notification record to ensure it appears in the inbox
                self.env['mail.notification'].sudo().create({
                    'mail_message_id': message.id,
                    'notification_type': 'inbox',
                    'res_partner_id': user.partner_id.id,
                    'notification_status': 'sent',
                })
                
                _logger.info(f"Created mail.notification for message ID: {message.id}")
                
            except Exception as e:
                _logger.error(f"Error creating notification for user {user.name}: {str(e)}")
            
        try:
            # Also post a message to the tender's chatter for record keeping
            # Use notification_ids to ensure it appears in the inbox
            partner_ids = users_to_notify.mapped('partner_id').ids
            _logger.info(f"Posting message to tender chatter with partners: {partner_ids}")
            
            message = order.tender_id.sudo().message_post(
                body=message_body,
                message_type='notification',
                subtype_id=self.env.ref('mail.mt_comment').id,
                subject=f"Yeni Teklif: {order.partner_id.name} - {bid_amount}",
                partner_ids=partner_ids,
                notification_type='inbox'
            )
            
            _logger.info(f"Posted message to tender chatter: {message}")
            
            # Force a notification update
            self.env.cr.commit()
            
        except Exception as e:
            _logger.error(f"Error posting message to tender chatter: {str(e)}")