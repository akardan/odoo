# -*- coding: utf-8 -*-
import base64
import json
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, AccessError
import logging

_logger = logging.getLogger(__name__)


class SupplierApplicationController(http.Controller):
    
    @http.route(['/supplier/register'], type='http', auth='public', website=True, sitemap=True)
    def supplier_register(self, **kwargs):
        """Show supplier registration form"""
        values = self._prepare_form_values()
        return request.render('ak_tender.supplier_registration_form', values)
    
    @http.route(['/supplier/application/<string:token>'], type='http', auth='public', website=True)
    def supplier_application(self, token, **kwargs):
        """Resume existing application via token"""
        application = request.env['supplier.application'].sudo().search([
            ('access_token', '=', token)
        ], limit=1)
        
        if not application:
            return request.render('ak_tender.supplier_application_not_found', {})
        
        # Check if already submitted
        if application.state != 'draft':
            return request.render('ak_tender.supplier_application_already_submitted', {
                'application': application
            })
        
        values = self._prepare_form_values(application=application)
        return request.render('ak_tender.supplier_registration_form', values)
    
    @http.route(['/supplier/application/save'], type='http', auth='public', website=True, methods=['POST'])
    def supplier_application_save(self, **post):
        """Save or update application (draft state)"""
        try:
            # Get or create application
            token = post.get('access_token')
            
            if token:
                application = request.env['supplier.application'].sudo().search([
                    ('access_token', '=', token),
                    ('state', '=', 'draft')
                ], limit=1)
            else:
                application = False
            
            # Prepare values
            vals = self._prepare_application_values(post)
            
            if application:
                # Update existing draft
                application.sudo().write(vals)
            else:
                # Create new application
                application = request.env['supplier.application'].sudo().create(vals)
                # Send draft link email
                application._send_draft_link_email()
            
            # Handle success response
            if post.get('action') == 'submit':
                # Submit the application
                try:
                    application.action_submit()
                    return request.render('ak_tender.supplier_application_success', {
                        'application': application
                    })
                except Exception as e:
                    _logger.error("Error submitting application: %s", str(e))
                    return request.render('ak_tender.supplier_application_error', {
                        'error': str(e),
                        'application': application
                    })
            else:
                # Just save as draft
                return request.render('ak_tender.supplier_application_saved', {
                    'application': application
                })
                
        except Exception as e:
            _logger.error("Error saving supplier application: %s", str(e))
            return request.render('ak_tender.supplier_application_error', {
                'error': str(e)
            })
    
    @http.route(['/supplier/application/upload'], type='json', auth='public', methods=['POST'], csrf=False)
    def supplier_application_upload(self, **post):
        """Handle file uploads via AJAX"""
        try:
            token = post.get('token')
            field_name = post.get('field')
            file_data = post.get('file')
            filename = post.get('filename')
            
            if not all([token, field_name, file_data]):
                return {'error': _('Missing required parameters')}
            
            application = request.env['supplier.application'].sudo().search([
                ('access_token', '=', token),
                ('state', '=', 'draft')
            ], limit=1)
            
            if not application:
                return {'error': _('Application not found or already submitted')}
            
            # Validate field name
            valid_fields = [
                'document_tax_certificate',
                'document_signature_circular', 
                'document_trade_registry',
                'document_bank_info'
            ]
            
            if field_name not in valid_fields:
                return {'error': _('Invalid field name')}
            
            # Save file
            application.sudo().write({
                field_name: file_data,
                f'{field_name}_filename': filename
            })
            
            return {'success': True, 'filename': filename}
            
        except Exception as e:
            _logger.error("Error uploading file: %s", str(e))
            return {'error': str(e)}
    
    def _prepare_form_values(self, application=None):
        """Prepare values for the form template"""
        values = {
            'application': application,
            'countries': request.env['res.country'].sudo().search([]),
            'page_name': 'supplier_registration',
        }
        
        if application:
            values['access_token'] = application.access_token
        
        return values
    
    def _prepare_application_values(self, post):
        """Prepare values from form data"""
        vals = {
            'company_name': post.get('company_name'),
            'vat_number': post.get('vat_number'),
            'tax_office': post.get('tax_office'),
            'tc_number': post.get('tc_number'),
            'company_address': post.get('company_address'),
            'company_phone': post.get('company_phone'),
            'kep_address': post.get('kep_address'),
            'mersis_number': post.get('mersis_number'),
            'product_service_group': post.get('product_service_group'),
            'contact_name': post.get('contact_name'),
            'contact_email': post.get('contact_email'),
            'payment_term': post.get('payment_term'),
            'payment_method': post.get('payment_method'),
            'bank_name': post.get('bank_name'),
            'iban_try': post.get('iban_try'),
            'iban_usd': post.get('iban_usd'),
            'iban_eur': post.get('iban_eur'),
            'swift_code': post.get('swift_code'),
        }
        
        # Handle file uploads
        for field in ['document_tax_certificate', 'document_signature_circular', 
                     'document_trade_registry', 'document_bank_info']:
            file = post.get(field)
            if file:
                try:
                    vals[field] = base64.b64encode(file.read())
                    vals[f'{field}_filename'] = file.filename
                except Exception as e:
                    _logger.warning("Error processing file %s: %s", field, str(e))
        
        # Remove only None and False values, keep empty strings for required fields
        vals = {k: v for k, v in vals.items() if v is not None and v is not False}
        
        return vals