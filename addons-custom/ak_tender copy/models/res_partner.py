# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_hotel = fields.Boolean(string=_("Otel"))
    hotel_star_rating = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string=_("Yıldız"), help=_("Otelin yıldız sayısı"))