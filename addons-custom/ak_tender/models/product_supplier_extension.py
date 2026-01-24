# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    x_synonym_name = fields.Char(
        string='Sinonim İsim',
        help='Ürünün alternatif/sinonim ismi',
        translate=True
    )


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    partner_type = fields.Selection([
        ('supplier', 'Tedarikçi'),
        ('manufacturer', 'Üretici')
    ], string='Partner Tipi', default='supplier', required=True,
       help='Bu kaydın tedarikçi mi yoksa üretici mi olduğunu belirtir')
    
    is_approved = fields.Boolean(
        string='Onaylı',
        default=False,
        help='Onaylı mı?'
    )

