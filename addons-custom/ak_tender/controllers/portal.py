# -*- coding: utf-8 -*-
import logging
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import formatLang

_logger = logging.getLogger(__name__)

class TenderPortal(CustomerPortal): # Inherit from CustomerPortal for standard layout and access control

    def _prepare_home_portal_values(self, counters):
        """ Add tender counts to the home portal /my values """
        values = super()._prepare_home_portal_values(counters)
        
        if 'tender_count' in counters:
            partner = request.env.user.partner_id
            partner_ids_to_check = [partner.id]
            if partner.commercial_partner_id and partner.commercial_partner_id.id != partner.id:
                partner_ids_to_check.append(partner.commercial_partner_id.id)

            AkTender = request.env['ak.tender']
            values['tender_count'] = AkTender.search_count([
                ('invited_partners', 'in', partner_ids_to_check),
                ('state', 'in', ['first_tender_round', 'new_tender_round', 'target_price_set']) # Active bidding states
            ]) if AkTender.has_access('read') else 0
            
        return values

    @http.route(['/my/tenders', '/my/tenders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_tenders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', groupby=None, **kw):
        AkTender = request.env['ak.tender']
        partner = request.env.user.partner_id
        # Portal user might be a contact of the invited partner (company)
        # So we check against the user's direct partner_id and their commercial_partner_id
        partner_ids_to_check = [partner.id]
        if partner.commercial_partner_id and partner.commercial_partner_id.id != partner.id:
            partner_ids_to_check.append(partner.commercial_partner_id.id)

        domain = [
            ('invited_partners', 'in', partner_ids_to_check),
            ('state', 'in', ['first_tender_round', 'new_tender_round', 'target_price_set']) # Active bidding states
        ]

        # TODO: Implement search, sortby, filterby, groupby if needed later
        # For now, a simple list
        
        tender_count = AkTender.search_count(domain)

        # Pager
        url = "/my/tenders"
        pager_values = portal_pager(
            url=url,
            total=tender_count,
            page=page,
            step=self._items_per_page
        )

        tenders = AkTender.search(domain, limit=self._items_per_page, offset=pager_values['offset'])

        values = self._prepare_portal_layout_values()
        values.update({
            'tenders': tenders,
            'page_name': 'tenders',
            'pager': pager_values,
            'default_url': url,
            # Add other necessary values for the template
        })
        # Redirect to portal home as the tenders list template has been removed
        return request.redirect('/my')

    # Placeholder for bid submission form route
    @http.route(['/my/tenders/<int:tender_id>'], type='http', auth="user", website=True)
    def portal_tender_form(self, tender_id, **kw):
        tender = request.env['ak.tender'].browse(tender_id)
        partner = request.env.user.partner_id

        is_invited = False
        if tender.exists():
            partner_ids_to_check = [partner.id]
            if partner.commercial_partner_id and partner.commercial_partner_id.id != partner.id:
                partner_ids_to_check.append(partner.commercial_partner_id.id)
            
            # Check if any of the user's relevant partner IDs are in the tender's invited_partners
            if any(pid in tender.invited_partners.ids for pid in partner_ids_to_check):
                is_invited = True
        
        if not tender.exists() or not is_invited:
            # You might want to redirect to an access error page or show a message
            # For now, redirecting to portal home
            return request.redirect('/my')

        # Check if tender is in a state that allows bidding
        if tender.state not in ['first_tender_round', 'new_tender_round', 'target_price_set']:
            # Maybe show a message or redirect
            # For now, still show the form but could be read-only or show status
            pass

        # Try to find an existing bid by this partner for this tender
        existing_order = request.env['purchase.order'].search([
            ('tender_id', '=', tender.id),
            ('partner_id', '=', request.env.user.partner_id.commercial_partner_id.id)
        ], limit=1)
        
        # Fetch available payment terms
        payment_terms = request.env['account.payment.term'].sudo().search([])
        
        # Prepare values for the form, including tender lines and existing bid data if any
        form_values = {
            'tender': tender,
            'tender_lines': tender.tender_lines,
            'existing_order': existing_order, # This will be a purchase.order recordset
            'page_name': 'tender_form',
            'user': request.env.user,
            'payment_terms': payment_terms,
            # Add other necessary values
        }
        # Add existing bid line data if an existing bid is found
        if existing_order:
            # Create a dictionary with tender_line_id as key for easier lookup in the template
            order_lines_data = {}
            for line in existing_order.order_line:
                # Make sure we have the tender line ID as the key
                tender_line_id = line.tender_line_id.id
                if tender_line_id:
                    order_lines_data[tender_line_id] = {
                        'price_unit': line.price_unit,
                        # any other fields from purchase.order.line you want to prefill
                    }
            form_values['order_lines_data'] = order_lines_data


        values = self._prepare_portal_layout_values()
        values.update(form_values)
        values.update(kw) # Pass URL parameters to the template
        
        # Redirect to tenders list as the bid form template has been removed
        return request.redirect('/my/tenders')

    # This method has been removed as the related template has been removed

        # This is a basic structure. The referenced templates have been removed.
    
    # Notification functionality moved to purchase_order model
        
    @http.route(['/my/purchase/update_supplier_order'], type='json', auth="public", website=True)
    def portal_update_supplier_order(self, order_id, access_token=None, lines=None, line_id=None, payment_term_id=None, **kw):
        """
        Update the supplier's purchase order from the portal.
        This method allows suppliers to update various fields of their purchase order:
        - price_unit: Unit price
        - date_planned: Delivery date
        - warranty_period: Warranty period in months
        - supplier_ref: Supplier reference
        - alt_materials: Alternative materials
        - payment_term_id: Payment terms
        
        Can handle both single line updates and multiple line updates:
        - Single line: line_id, price_unit, etc. are passed directly
        - Multiple lines: lines parameter contains a list of line data
        """
        try:
            # Log the request parameters for debugging
            _logger = logging.getLogger(__name__)
            _logger.info(f"Update supplier order request: order_id={order_id}, access_token={access_token}, lines={lines}, line_id={line_id}, payment_term_id={payment_term_id}, kw={kw}")
            
            # Check access to the order
            order_sudo = self._document_check_access('purchase.order', order_id, access_token)
            if not order_sudo:
                _logger.warning(f"Invalid order access: order_id={order_id}")
                return {'error': 'Invalid Order'}
                
            # Check if the order is in a state that allows editing (draft or sent)
            if order_sudo.state not in ['draft', 'sent']:
                _logger.warning(f"Order in non-editable state: {order_sudo.state}")
                return {'error': 'This order cannot be edited anymore.'}
            
            # Handle multiple lines update
            if lines:
                _logger.info(f"Processing multiple lines: {len(lines)}")
                results = []
                
                for line_data in lines:
                    line_id = line_data.get('line_id')
                    if not line_id:
                        continue
                    
                    # Find the line
                    line = request.env['purchase.order.line'].sudo().browse(int(line_id))
                    if not line:
                        _logger.warning(f"Line not found: line_id={line_id}")
                        continue
                        
                    if line.order_id.id != order_sudo.id:
                        _logger.warning(f"Line belongs to different order: line.order_id.id={line.order_id.id}, order_sudo.id={order_sudo.id}")
                        continue
                    
                    # Prepare values to update
                    vals = {}
                    
                    # Handle price_unit update
                    if 'price_unit' in line_data:
                        try:
                            price_unit = float(line_data.get('price_unit'))
                            _logger.info(f"Updating price: old={line.price_unit}, new={price_unit}")
                            vals['price_unit'] = price_unit
                        except (ValueError, TypeError) as e:
                            _logger.warning(f"Invalid price_unit value: {line_data.get('price_unit')}, error: {str(e)}")
                            continue
                    
                    # Handle discount update
                    if 'discount' in line_data:
                        try:
                            discount = float(line_data.get('discount'))
                            if discount < 0 or discount > 100:
                                _logger.warning(f"Invalid discount value (must be between 0-100): {discount}")
                                continue
                            _logger.info(f"Updating discount: old={line.discount}, new={discount}")
                            vals['discount'] = discount
                        except (ValueError, TypeError) as e:
                            _logger.warning(f"Invalid discount value: {line_data.get('discount')}, error: {str(e)}")
                            continue
                    
                    # Handle date_planned update
                    if 'date_planned' in line_data:
                        try:
                            date_planned = line_data.get('date_planned')
                            _logger.info(f"Updating delivery date: old={line.date_planned}, new={date_planned}")
                            vals['date_planned'] = date_planned
                        except Exception as e:
                            _logger.warning(f"Invalid date_planned value: {line_data.get('date_planned')}, error: {str(e)}")
                            continue
                    
                    # Handle warranty_period update
                    if 'warranty_period' in line_data:
                        try:
                            warranty_period = int(line_data.get('warranty_period'))
                            _logger.info(f"Updating warranty period: old={line.warranty_period if hasattr(line, 'warranty_period') else 'N/A'}, new={warranty_period}")
                            vals['warranty_period'] = warranty_period
                        except (ValueError, TypeError) as e:
                            _logger.warning(f"Invalid warranty_period value: {line_data.get('warranty_period')}, error: {str(e)}")
                            continue
                    
                    # Handle supplier_ref update
                    if 'supplier_ref' in line_data:
                        supplier_ref = line_data.get('supplier_ref')
                        _logger.info(f"Updating supplier reference: old={line.supplier_ref if hasattr(line, 'supplier_ref') else 'N/A'}, new={supplier_ref}")
                        vals['supplier_ref'] = supplier_ref
                    
                    # Handle alt_materials update
                    if 'alt_materials' in line_data:
                        alt_materials = line_data.get('alt_materials')
                        _logger.info(f"Updating alternative materials: old={line.alt_materials if hasattr(line, 'alt_materials') else 'N/A'}, new={alt_materials}")
                        vals['alt_materials'] = alt_materials
                    
                    # Handle name update
                    if 'name' in line_data:
                        name = line_data.get('name')
                        _logger.info(f"Updating purchase description: old={line.name}, new={name}")
                        vals['name'] = name
                    
                    # Handle taxes_id update
                    if 'taxes_id' in line_data:
                        taxes_id = line_data.get('taxes_id')
                        _logger.info(f"Updating taxes: old={line.taxes_id}, new={taxes_id}")
                        vals['taxes_id'] = taxes_id
                    
                    # Update the line with all the values
                    if vals:
                        _logger.info(f"Writing values to line: {vals}")
                        line.write(vals)
                        results.append({
                            'line_id': line_id,
                            'success': True
                        })
                
                # Update payment term if provided
                if payment_term_id:
                    try:
                        _logger.info(f"Updating payment term: {payment_term_id}")
                        # Handle special case for 'cash' value
                        if payment_term_id == 'cash':
                            # Find or create the cash payment term
                            cash_term = request.env['account.payment.term'].sudo().search([('name', '=', 'Peşin Ödeme')], limit=1)
                            if cash_term:
                                order_sudo.payment_term_id = cash_term.id
                            else:
                                _logger.warning("Cash payment term not found")
                        else:
                            # Try to convert to integer for regular payment term IDs
                            try:
                                payment_term_id_int = int(payment_term_id)
                                order_sudo.payment_term_id = payment_term_id_int
                            except (ValueError, TypeError) as e:
                                _logger.warning(f"Invalid payment_term_id value: {payment_term_id}, error: {str(e)}")
                    except Exception as e:
                        _logger.exception(f"Error updating payment term: {str(e)}")
                
                # Recompute the order totals
                order_sudo._amount_all()
                
                # Return updated values
                return {
                    'success': True,
                    'lines_updated': len(results),
                    'payment_term_updated': bool(payment_term_id),
                    'amount_total': request.env['ir.qweb.field.monetary'].value_to_html(
                        order_sudo.amount_total, {'display_currency': order_sudo.currency_id}),
                }
            
            # Handle single line update (backward compatibility)
            elif line_id:
                # Find the line
                line = request.env['purchase.order.line'].sudo().browse(int(line_id))
                if not line:
                    _logger.warning(f"Line not found: line_id={line_id}")
                    return {'error': 'Invalid Order Line - Not found'}
                    
                if line.order_id.id != order_sudo.id:
                    _logger.warning(f"Line belongs to different order: line.order_id.id={line.order_id.id}, order_sudo.id={order_sudo.id}")
                    return {'error': 'Invalid Order Line - Wrong order'}
                
                # Prepare values to update
                vals = {}
                
                # Handle price_unit update
                if 'price_unit' in kw:
                    try:
                        price_unit = float(kw.get('price_unit'))
                        _logger.info(f"Updating price: old={line.price_unit}, new={price_unit}")
                        vals['price_unit'] = price_unit
                    except (ValueError, TypeError) as e:
                        _logger.warning(f"Invalid price_unit value: {kw.get('price_unit')}, error: {str(e)}")
                        return {'error': 'Invalid price value'}
                
                # Handle discount update
                if 'discount' in kw:
                    try:
                        discount = float(kw.get('discount'))
                        if discount < 0 or discount > 100:
                            _logger.warning(f"Invalid discount value (must be between 0-100): {discount}")
                            return {'error': 'Invalid discount value (must be between 0-100)'}
                        _logger.info(f"Updating discount: old={line.discount}, new={discount}")
                        vals['discount'] = discount
                    except (ValueError, TypeError) as e:
                        _logger.warning(f"Invalid discount value: {kw.get('discount')}, error: {str(e)}")
                        return {'error': 'Invalid discount value'}
                
                # Handle date_planned update
                if 'date_planned' in kw:
                    try:
                        date_planned = kw.get('date_planned')
                        _logger.info(f"Updating delivery date: old={line.date_planned}, new={date_planned}")
                        vals['date_planned'] = date_planned
                    except Exception as e:
                        _logger.warning(f"Invalid date_planned value: {kw.get('date_planned')}, error: {str(e)}")
                        return {'error': 'Invalid delivery date value'}
                
                # Handle warranty_period update
                if 'warranty_period' in kw:
                    try:
                        warranty_period = int(kw.get('warranty_period'))
                        _logger.info(f"Updating warranty period: old={line.warranty_period if hasattr(line, 'warranty_period') else 'N/A'}, new={warranty_period}")
                        vals['warranty_period'] = warranty_period
                    except (ValueError, TypeError) as e:
                        _logger.warning(f"Invalid warranty_period value: {kw.get('warranty_period')}, error: {str(e)}")
                        return {'error': 'Invalid warranty period value'}
                
                # Handle supplier_ref update
                if 'supplier_ref' in kw:
                    supplier_ref = kw.get('supplier_ref')
                    _logger.info(f"Updating supplier reference: old={line.supplier_ref if hasattr(line, 'supplier_ref') else 'N/A'}, new={supplier_ref}")
                    vals['supplier_ref'] = supplier_ref
                
                # Handle alt_materials update
                if 'alt_materials' in kw:
                    alt_materials = kw.get('alt_materials')
                    _logger.info(f"Updating alternative materials: old={line.alt_materials if hasattr(line, 'alt_materials') else 'N/A'}, new={alt_materials}")
                    vals['alt_materials'] = alt_materials
                
                # Handle name update
                if 'name' in kw:
                    name = kw.get('name')
                    _logger.info(f"Updating purchase description: old={line.name}, new={name}")
                    vals['name'] = name
                
                # Handle taxes_id update
                if 'taxes_id' in kw:
                    taxes_id = kw.get('taxes_id')
                    _logger.info(f"Updating taxes: old={line.taxes_id}, new={taxes_id}")
                    vals['taxes_id'] = taxes_id
                
                # Update the line with all the values
                if vals:
                    _logger.info(f"Writing values to line: {vals}")
                    line.write(vals)
                    
                    # Recompute the order if price or discount was updated
                    if 'price_unit' in vals or 'discount' in vals:
                        order_sudo._amount_all()
                
                # Update payment term if provided
                if payment_term_id:
                    try:
                        _logger.info(f"Updating payment term: {payment_term_id}")
                        # Handle special case for 'cash' value
                        if payment_term_id == 'cash':
                            # Find or create the cash payment term
                            cash_term = request.env['account.payment.term'].sudo().search([('name', '=', 'Peşin Ödeme')], limit=1)
                            if cash_term:
                                order_sudo.payment_term_id = cash_term.id
                            else:
                                _logger.warning("Cash payment term not found")
                        else:
                            # Try to convert to integer for regular payment term IDs
                            try:
                                payment_term_id_int = int(payment_term_id)
                                order_sudo.payment_term_id = payment_term_id_int
                            except (ValueError, TypeError) as e:
                                _logger.warning(f"Invalid payment_term_id value: {payment_term_id}, error: {str(e)}")
                    except Exception as e:
                        _logger.exception(f"Error updating payment term: {str(e)}")
                
                # Return updated values
                result = {
                    'success': True,
                    'payment_term_updated': bool(payment_term_id)
                }
                
                # Add price-related values if price or discount was updated
                if 'price_unit' in vals or 'discount' in vals:
                    result.update({
                        'price_subtotal': request.env['ir.qweb.field.monetary'].value_to_html(
                            line.price_subtotal, {'display_currency': order_sudo.currency_id}),
                        'price_total': request.env['ir.qweb.field.monetary'].value_to_html(
                            line.price_total, {'display_currency': order_sudo.currency_id}),
                        'amount_untaxed': request.env['ir.qweb.field.monetary'].value_to_html(
                            order_sudo.amount_untaxed, {'display_currency': order_sudo.currency_id}),
                        'amount_tax': request.env['ir.qweb.field.monetary'].value_to_html(
                            order_sudo.amount_tax, {'display_currency': order_sudo.currency_id}),
                        'amount_total': request.env['ir.qweb.field.monetary'].value_to_html(
                            order_sudo.amount_total, {'display_currency': order_sudo.currency_id}),
                    })
                
                return result
            
            return {'error': 'No line_id or lines provided'}
            
        except Exception as e:
            _logger.exception(f"Error in portal_update_supplier_order: {str(e)}")
            return {'error': str(e)}