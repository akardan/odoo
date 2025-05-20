from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    MEDICAL_TYPE_SELECTION = [
        ('D', 'Doktor'),
        ('P', 'Eczane'),
    ]

    medical_type = fields.Selection(MEDICAL_TYPE_SELECTION, string='Partner Type')
    specialization_ids = fields.Many2many('crm.medical.specialization', string='İhtisas Alanları',
                                          help="Doktorların birden fazla ihtisas alanı olabilir.")
    # brick_id = fields.Many2one('crm.brick', string='Brick')
    segmentation_ids = fields.One2many('crm.segmentation', 'partner_id', string='Segments By Groups')
    unit_id = fields.Many2one('crm.unit', string='Unit')
    brick_id = fields.Many2one('crm.brick', string='Brick', related='unit_id.brick_id', readonly=True)
