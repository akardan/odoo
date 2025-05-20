from odoo import models, fields, api

class Territory(models.Model):
    _name = 'crm.territory'
    _description = "Territory"

    name = fields.Char(string='Territory')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    brick_ids = fields.One2many('crm.brick', 'territory_id', string='Bricks')
