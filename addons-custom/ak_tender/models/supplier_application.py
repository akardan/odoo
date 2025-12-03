# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class SupplierApplication(models.Model):
    _name = 'supplier.application'
    _description = 'Supplier Registration Application'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information & Control
    name = fields.Char('Application Number', required=True, copy=False, readonly=True,
                       default='New', tracking=True)
    access_token = fields.Char('Access Token', default=lambda self: str(uuid.uuid4()),
                               copy=False, readonly=True, index=True)
    lang = fields.Selection(
        string='Language',
        selection=lambda self: self.env['res.lang'].get_installed(),
        default=lambda self: self.env.lang or 'tr_TR',
        help='Language for email communications'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    partner_id = fields.Many2one('res.partner', string='Partner', 
                                  readonly=True, tracking=True,
                                  help='Created partner after approval')
    partner_created = fields.Boolean('Partner Created', default=False, copy=False)
    
    # Company Information (Turkish Form Fields)
    application_date = fields.Date('Application Date', default=fields.Date.today, 
                                    required=True, tracking=True)
    company_name = fields.Char('Company Name', required=True, tracking=True, 
                                translate=False)
    vat_number = fields.Char('VAT Number', tracking=True)
    tax_office = fields.Char('Tax Office', tracking=True)
    tc_number = fields.Char('T.C. ID Number (For Individual Companies)', tracking=True,
                             help='For individual/sole proprietor companies only')
    company_address = fields.Text('Company Address', required=True, tracking=True)
    company_phone = fields.Char('Company Phone', required=True, tracking=True)
    kep_address = fields.Char('KEP Address', tracking=True,
                               help='Registered Electronic Mail address')
    mersis_number = fields.Char('MERSIS Number', tracking=True,
                                 help='Central Registry System Number')
    
    # Product/Service Information
    product_service_group = fields.Text('Goods (Group)/Service (Group)', 
                                         required=True, tracking=True,
                                         help='Description of goods or services provided')
    
    # Contact Person Information
    contact_name = fields.Char('Contact Person Name', required=True, tracking=True,
                                help='Accounting / Finance / Authorized Signature Person')
    contact_email = fields.Char('Contact Email', required=True, tracking=True,
                                 help='Email for accounting/finance contact')
    
    # Payment Information
    payment_term = fields.Char('Payment Term', tracking=True,
                                help='e.g., 30 days, 60 days, etc.')
    payment_method = fields.Char('Payment Method', tracking=True,
                                  help='e.g., Bank Transfer, Check, etc.')
    
    # Bank Information
    bank_name = fields.Char('Bank Name', tracking=True)
    iban_try = fields.Char('IBAN (TRY)', tracking=True)
    iban_usd = fields.Char('IBAN (USD)', tracking=True)
    iban_eur = fields.Char('IBAN (EUR)', tracking=True)
    swift_code = fields.Char('SWIFT Code', tracking=True,
                              help='For international transfers')
    
    # Required Documents
    document_tax_certificate = fields.Binary('Tax Certificate',
                                              attachment=True)
    document_tax_certificate_filename = fields.Char('Tax Certificate Filename')
    
    document_signature_circular = fields.Binary('Signature Circular',
                                                 attachment=True)
    document_signature_circular_filename = fields.Char('Signature Circular Filename')
    
    document_trade_registry = fields.Binary('Trade Registry Gazette',
                                             attachment=True)
    document_trade_registry_filename = fields.Char('Trade Registry Filename')
    
    document_bank_info = fields.Binary('Bank Information (Stamped)',
                                        attachment=True,
                                        help='Bank information on stamped letterhead')
    document_bank_info_filename = fields.Char('Bank Info Filename')
    
    # Additional Fields
    notes = fields.Text('Internal Notes', tracking=True,
                         help='Internal notes for review team')
    rejection_reason = fields.Text('Rejection Reason', tracking=True)
    
    # Computed Fields
    website_url = fields.Char('Application URL', compute='_compute_website_url')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('supplier.application') or 'New'
        return super(SupplierApplication, self).create(vals)
    
    @api.depends('access_token')
    def _compute_website_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for application in self:
            if application.access_token:
                application.website_url = f"{base_url}/supplier/application/{application.access_token}"
            else:
                application.website_url = False
    
    @api.constrains('contact_email')
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.contact_email:
                # Basic email validation
                if '@' not in record.contact_email or '.' not in record.contact_email:
                    raise ValidationError(_('Please enter a valid email address.'))
    
    @api.constrains('iban_try', 'iban_usd', 'iban_eur', 'state')
    def _check_iban_required(self):
        """Check that at least one IBAN is provided when submitting"""
        for record in self:
            if record.state in ['submitted', 'under_review', 'approved']:
                if not record.iban_try and not record.iban_usd and not record.iban_eur:
                    raise ValidationError(_(
                        'En az bir IBAN bilgisi (TRY, USD veya EUR) girilmelidir.'
                    ))
    
    @api.constrains('vat_number')
    def _check_vat_unique(self):
        """Check if VAT number is already registered"""
        for record in self:
            if record.vat_number and record.state in ['submitted', 'under_review', 'approved']:
                # Check in approved applications
                existing = self.search([
                    ('id', '!=', record.id),
                    ('vat_number', '=', record.vat_number),
                    ('state', '=', 'approved'),
                ], limit=1)
                if existing:
                    raise ValidationError(_(
                        'A supplier with this VAT number (%s) is already registered in the system.'
                    ) % record.vat_number)
                
                # Check in res.partner
                partner = self.env['res.partner'].search([
                    ('vat', '=', record.vat_number),
                    ('supplier_rank', '>', 0),
                ], limit=1)
                if partner:
                    raise ValidationError(_(
                        'A supplier with this VAT number (%s) already exists in the system.'
                    ) % record.vat_number)
    
    def action_submit(self):
        """Submit application for review"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft applications can be submitted.'))
        
        # Validate required fields
        required_fields = ['company_name', 'company_address', 'company_phone',
                          'contact_email', 'product_service_group']
        missing_fields = []
        for field in required_fields:
            if not self[field]:
                field_desc = self._fields[field].string
                missing_fields.append(field_desc)
        
        if missing_fields:
            raise ValidationError(_(
                'Please fill in all required fields: %s'
            ) % ', '.join(missing_fields))
        
        # Validate required documents
        required_documents = {
            'document_tax_certificate': 'Vergi Levhası',
            'document_signature_circular': 'İmza Sirküleri',
            'document_trade_registry': 'Ticaret Sicil Gazetesi',
            'document_bank_info': 'Banka Bilgileri (Kaşeli)',
        }
        missing_docs = []
        for doc_field, doc_name in required_documents.items():
            if not self[doc_field]:
                missing_docs.append(doc_name)
        
        if missing_docs:
            raise ValidationError(
                'Lütfen tüm gerekli belgeleri yükleyin:\n\n%s' % '\n'.join(['• ' + doc for doc in missing_docs])
            )
        
        self.write({'state': 'submitted'})
        
        # Send notification to procurement team
        self._send_submission_notification()
        
        # Send confirmation to supplier
        self._send_supplier_confirmation()
        
        return True
    
    def action_review(self):
        """Start review process"""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Only submitted applications can be reviewed.'))
        
        self.write({'state': 'under_review'})
        return True
    
    def action_approve(self):
        """Approve application and create/update partner"""
        self.ensure_one()
        
        if self.state not in ['submitted', 'under_review']:
            raise UserError(_('Only submitted or under review applications can be approved.'))
        
        if self.partner_created:
            raise UserError(_('Partner has already been created for this application.'))
        
        # Check if partner exists with same VAT number
        partner = False
        partner_action = 'created'
        if self.vat_number:
            partner = self.env['res.partner'].sudo().search([
                ('vat', '=', self.vat_number),
                ('is_company', '=', True)
            ], limit=1)
        
        # Prepare partner values
        partner_vals = self._prepare_partner_values()
        
        if partner:
            # Update existing partner
            partner.sudo().write(partner_vals)
            partner_action = 'updated'
        else:
            # Create new partner
            partner = self.env['res.partner'].sudo().create(partner_vals)
            partner_action = 'created'
        
        # Ensure supplier rank is set
        if partner.supplier_rank == 0:
            partner.sudo().write({'supplier_rank': 1})
        
        # Find or create contact person partner
        contact_partner = self.env['res.partner'].sudo().search([
            ('parent_id', '=', partner.id),
            ('email', '=', self.contact_email),
        ], limit=1)
        
        if not contact_partner:
            # Find by name if email search failed
            contact_partner = self.env['res.partner'].sudo().search([
                ('parent_id', '=', partner.id),
                ('name', '=', self.contact_name),
            ], limit=1)
        
        # Create portal user for contact person
        user = self._create_portal_user(contact_partner) if contact_partner else None
        
        # Update application
        self.write({
            'state': 'approved',
            'partner_id': partner.id,
            'partner_created': True,
        })
        
        # Send welcome email to supplier
        if user:
            self._send_approval_email(partner, user)
        
        # Log message
        action_text = _('updated') if partner_action == 'updated' else _('created')
        self.message_post(
            body=_('Application approved. Partner %s %s and portal access granted.') % (partner.name, action_text),
            subject=_('Application Approved'),
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Supplier'),
            'res_model': 'res.partner',
            'res_id': partner.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_reject(self):
        """Reject application"""
        self.ensure_one()
        
        if self.state not in ['submitted', 'under_review']:
            raise UserError(_('Only submitted or under review applications can be rejected.'))
        
        # Open wizard for rejection reason
        return {
            'name': _('Reject Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.application.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_application_id': self.id},
        }
    
    def action_set_to_draft(self):
        """Reset to draft"""
        self.ensure_one()
        if self.partner_created:
            raise UserError(_('Cannot reset to draft after partner creation.'))
        
        self.write({'state': 'draft'})
        return True
    
    def _prepare_partner_values(self):
        """Prepare values for partner creation"""
        self.ensure_one()
        
        # Prepare bank account values
        bank_vals = []
        if self.iban_try:
            bank_vals.append((0, 0, {
                'acc_number': self.iban_try,
                'currency_id': self.env.ref('base.TRY').id,
            }))
        if self.iban_usd:
            bank_vals.append((0, 0, {
                'acc_number': self.iban_usd,
                'currency_id': self.env.ref('base.USD').id,
            }))
        if self.iban_eur:
            bank_vals.append((0, 0, {
                'acc_number': self.iban_eur,
                'currency_id': self.env.ref('base.EUR').id,
            }))
        
        # Prepare contact person as child contact
        child_vals = []
        if self.contact_name and self.contact_email:
            child_vals.append((0, 0, {
                'name': self.contact_name,
                'email': self.contact_email,
                'type': 'contact',
                'function': _('Sales / Marketing Contact'),
            }))
        
        vals = {
            'name': self.company_name,
            'is_company': True,
            'supplier_rank': 1,
            'customer_rank': 0,
            'street': self.company_address,
            'phone': self.company_phone,
            'vat': self.vat_number,
            'comment': self.product_service_group,
        }
        
        # Add bank accounts if any
        if bank_vals:
            vals['bank_ids'] = bank_vals
        
        # Add contact person as child
        if child_vals:
            vals['child_ids'] = child_vals
        
        return vals
    
    def _create_portal_user(self, contact_partner):
        """Create portal user for the contact person"""
        if not contact_partner:
            return None
            
        # Check if user already exists for this contact
        user = self.env['res.users'].sudo().search([
            ('partner_id', '=', contact_partner.id)
        ], limit=1)
        
        if user:
            return user
        
        # Check if email is already taken by another user
        existing_user = self.env['res.users'].sudo().search([
            ('login', '=', self.contact_email)
        ], limit=1)
        
        if existing_user:
            # Email already used, don't create new user
            _logger.warning(
                'Cannot create portal user: email %s already in use by user %s',
                self.contact_email, existing_user.name
            )
            return None
        
        # Create portal user
        portal_group = self.env.ref('base.group_portal')
        
        user_vals = {
            'login': self.contact_email,
            'email': self.contact_email,
            'partner_id': contact_partner.id,
            'groups_id': [(6, 0, [portal_group.id])],
            'company_id': self.env.company.id,
        }
        
        user = self.env['res.users'].sudo().with_context(no_reset_password=True).create(user_vals)
        
        return user
    
    def _send_submission_notification(self):
        """Send email notification to procurement team"""
        self.ensure_one()
        
        template = self.env.ref('ak_tender.email_template_supplier_application_submitted', 
                                raise_if_not_found=False)
        if template:
            # Get procurement team emails
            procurement_group = self.env.ref('ak_tender.group_tender_manager', 
                                             raise_if_not_found=False)
            if procurement_group:
                users = procurement_group.users
                for user in users:
                    if user.email:
                        template.send_mail(self.id, email_values={'email_to': user.email})
    
    def _send_supplier_confirmation(self):
        """Send confirmation email to supplier"""
        self.ensure_one()
        
        template = self.env.ref('ak_tender.email_template_supplier_application_confirmation',
                                raise_if_not_found=False)
        if template:
            template.send_mail(self.id, email_values={'email_to': self.contact_email})
    
    def _send_approval_email(self, partner, user):
        """Send approval and welcome email"""
        self.ensure_one()
        
        # Send portal invitation
        if user:
            template = self.env.ref('portal.mail_template_data_portal_welcome',
                                   raise_if_not_found=False)
            if template:
                user.action_reset_password()
    
    def _send_draft_link_email(self):
        """Send draft link to supplier's email"""
        self.ensure_one()
        
        template = self.env.ref('ak_tender.email_template_supplier_application_draft_link',
                                raise_if_not_found=False)
        if template:
            template.send_mail(self.id, email_values={'email_to': self.contact_email})
    
    def action_send_draft_link(self):
        """Manually send draft link"""
        self.ensure_one()
        self._send_draft_link_email()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Draft Link Sent'),
                'message': _('Application link has been sent to %s') % self.contact_email,
                'type': 'success',
                'sticky': False,
            }
        }