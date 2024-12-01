# -*- coding: utf-8 -*-
# from odoo import http


# class AkRpt(http.Controller):
#     @http.route('/ak_rpt/ak_rpt', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ak_rpt/ak_rpt/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ak_rpt.listing', {
#             'root': '/ak_rpt/ak_rpt',
#             'objects': http.request.env['ak_rpt.ak_rpt'].search([]),
#         })

#     @http.route('/ak_rpt/ak_rpt/objects/<model("ak_rpt.ak_rpt"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ak_rpt.object', {
#             'object': obj
#         })

