# -*- coding: utf-8 -*-
# from odoo import http


# class AkExams(http.Controller):
#     @http.route('/ak_exams/ak_exams', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ak_exams/ak_exams/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ak_exams.listing', {
#             'root': '/ak_exams/ak_exams',
#             'objects': http.request.env['ak_exams.ak_exams'].search([]),
#         })

#     @http.route('/ak_exams/ak_exams/objects/<model("ak_exams.ak_exams"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ak_exams.object', {
#             'object': obj
#         })

