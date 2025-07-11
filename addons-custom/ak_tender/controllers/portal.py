# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

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
                ('state', 'in', ['first_tender_round', 'second_tender_round', 'target_price_set']) # Active bidding states
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
            ('state', 'in', ['first_tender_round', 'second_tender_round', 'target_price_set']) # Active bidding states
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
        return request.render("ak_tender.portal_my_tenders_list", values)

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
        if tender.state not in ['first_tender_round', 'second_tender_round', 'target_price_set']:
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
        
        return request.render("ak_tender.portal_tender_bid_form", values)

    # Placeholder for bid submission POST handler
    @http.route(['/my/tenders/<int:tender_id>/submit'], type='http', auth="user", website=True, methods=['POST'], csrf=True)
    def portal_tender_form_submit(self, tender_id, **post):
        tender = request.env['ak.tender'].browse(tender_id)
        partner = request.env.user.partner_id

        if not tender.exists() or partner not in tender.invited_partners:
            return request.redirect('/my')

        if tender.state not in ['first_tender_round', 'second_tender_round', 'target_price_set']:
            # Handle case where tender is not open for bidding
            # You might want to redirect with an error message
            return request.redirect('/my/tenders/%s' % tender_id) 

        # Extract data from post
        # Example: post.get('delivery_date'), post.get('payment_terms_id'), etc.
        # For lines, they might come as post['price_unit_for_line_X']
        
        order_vals = {
            'tender_id': tender.id,
            'partner_id': partner.commercial_partner_id.id,
            'date_order': fields.Datetime.now(),
            'currency_id': tender.currency_id.id,
            'delivery_date': post.get('delivery_date') or None,
            'payment_term_id': int(post.get('payment_terms')) if post.get('payment_terms') else None,
            'notes': post.get('notes') or None,
            'tender_round': 1, # Default to 1, can be adjusted based on tender state
            'state': 'draft', # Start as a draft RFQ
        }
        
        order_lines_vals = []
        for tender_line in tender.tender_lines:
            price_unit_str = post.get(f'price_unit_line_{tender_line.id}')
            if price_unit_str:
                try:
                    price_unit = float(price_unit_str)
                    order_lines_vals.append((0, 0, {
                        'tender_line_id': tender_line.id,
                        'product_id': tender_line.product_id.id,
                        'name': tender_line.name,
                        'product_qty': tender_line.quantity,
                        'product_uom': tender_line.uom_id.id,
                        'price_unit': price_unit,
                        'date_planned': fields.Date.today(),
                    }))
                except ValueError:
                    pass

        if not order_lines_vals and tender.tender_lines:
            return request.redirect('/my/tenders/%s?error=no_prices' % tender_id)

        # Check if an order already exists for this partner and tender
        existing_order = request.env['purchase.order'].search([
            ('tender_id', '=', tender.id),
            ('partner_id', '=', partner.commercial_partner_id.id)
        ], limit=1)

        try:
            if existing_order:
                # Update existing order
                existing_order.order_line.unlink()
                order_vals['order_line'] = order_lines_vals
                existing_order.write(order_vals)
            else:
                # Create new order
                order_vals['order_line'] = order_lines_vals
                request.env['purchase.order'].create(order_vals)
            
            return request.redirect(f'/my/tenders/{tender_id}?bid_submitted=1')
            
        except Exception as e:
            # Log error e
            # Redirect back to form with an error message
            return request.redirect('/my/tenders/%s?error=submission_failed' % tender_id)

        # This is a basic structure. You'll need to add QWeb templates
        # (portal_my_tenders_list.xml, portal_tender_bid_form.xml)
        # and refine the logic, validation, and error handling.