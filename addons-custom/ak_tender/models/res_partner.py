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
    
    # Supplier Application
    supplier_application_id = fields.Many2one(
        'supplier.application',
        string='Supplier Application',
        readonly=True,
        help='Original supplier registration application'
    )
    supplier_application_date = fields.Date(
        related='supplier_application_id.application_date',
        string='Application Date',
        readonly=True,
        store=True
    )