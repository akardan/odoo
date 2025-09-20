from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError

class ProspectusPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        
        if 'prospectus_count' in counters:
            prospectus_count = request.env['digital.prospectus'].search_count([
                ('partner_id', '=', request.env.user.partner_id.commercial_partner_id.id)
            ]) if request.env.user.partner_id else 0
            values['prospectus_count'] = prospectus_count
        
        return values

    @http.route(['/my/prospectus', '/my/prospectus/page/<int:page>'], 
                type='http', auth="user", website=True)
    def portal_my_prospectus(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        
        # Mevcut kullanıcının prospektüslerini al
        domain = [
            ('partner_id', '=', request.env.user.partner_id.commercial_partner_id.id)
        ]
        
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # Sıralama
        sortby_options = {
            'date': {'label': _('Tarih'), 'order': 'create_date desc'},
            'name': {'label': _('İsim'), 'order': 'name'},
            'state': {'label': _('Durum'), 'order': 'state'},
        }
        
        if not sortby:
            sortby = 'date'
        order = sortby_options[sortby]['order']

        # Prospektüsleri getir
        prospectus_count = request.env['digital.prospectus'].search_count(domain)
        
        pager = portal_pager(
            url="/my/prospectus",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=prospectus_count,
            page=page,
            step=self._items_per_page
        )

        prospectus_list = request.env['digital.prospectus'].search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset']
        )

        # Abonelik bilgisi
        subscription = request.env['digital.customer.subscription'].search([
            ('partner_id', '=', request.env.user.partner_id.commercial_partner_id.id),
            ('state', '=', 'active')
        ], limit=1)

        values.update({
            'date': date_begin,
            'prospectus_list': prospectus_list,
            'page_name': 'prospectus',
            'pager': pager,
            'default_url': '/my/prospectus',
            'sortby': sortby,
            'sortby_options': sortby_options,
            'subscription': subscription,
        })
        
        return request.render("ak_eKT.portal_my_prospectus", values)

    @http.route(['/my/prospectus/<int:prospectus_id>'], 
                type='http', auth="user", website=True)
    def portal_prospectus_detail(self, prospectus_id, **kw):
        try:
            prospectus = self._get_prospectus(prospectus_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'prospectus': prospectus,
            'page_name': 'prospectus_detail',
        }
        
        return request.render("ak_eKT.portal_prospectus_detail", values)

    @http.route(['/my/prospectus/<int:prospectus_id>/qr'], 
                type='http', auth="user", website=True)
    def portal_prospectus_qr(self, prospectus_id, **kw):
        try:
            prospectus = self._get_prospectus(prospectus_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'prospectus': prospectus,
            'page_name': 'prospectus_qr',
        }
        
        return request.render("ak_eKT.qr_code_page", values)

    def _get_prospectus(self, prospectus_id):
        return request.env['digital.prospectus'].browse(prospectus_id).sudo().exists()