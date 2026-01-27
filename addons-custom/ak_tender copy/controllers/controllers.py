# -*- coding: utf-8 -*-
# from odoo import http


# class AkTender(http.Controller):
#     @http.route('/ak_tender/ak_tender', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ak_tender/ak_tender/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ak_tender.listing', {
#             'root': '/ak_tender/ak_tender',
#             'objects': http.request.env['ak_tender.ak_tender'].search([]),
#         })

#     @http.route('/ak_tender/ak_tender/objects/<model("ak_tender.ak_tender"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ak_tender.object', {
#             'object': obj
#         })

