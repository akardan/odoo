# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductAttributeCustomValue(models.Model):
    _inherit = "product.attribute.custom.value"

    tender_line_id = fields.Many2one('ak.tender.line', string=_("Tender Line"), ondelete='cascade')

    _sql_constraints = [
        ('tender_line_custom_value_unique', 'unique(custom_product_template_attribute_value_id, tender_line_id)',
         _("Only one Custom Value is allowed per Attribute Value per Tender Line."))
    ]

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_hotel_accommodation = fields.Boolean(string=_("Otel Konaklaması"))
    manufacturer_id = fields.Many2one('res.partner', string=_("Manufacturer"), help=_("Manufacturer of the product"))
    material_group = fields.Char(
        string=_("Malzeme Grubu"),
        index=True,
        help=_("SAP Malzeme Grubu Kodu (ör: 1000, 6000)")
    )

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    material_group = fields.Char(
        related='product_tmpl_id.material_group',
        string=_("Malzeme Grubu"),
        store=True,
        readonly=False,
        index=True,
        help=_("SAP Malzeme Grubu Kodu (ör: 10000, 6000)")
    )