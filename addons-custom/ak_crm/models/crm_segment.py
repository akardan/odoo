from odoo import models, fields, api

class CrmSegment(models.Model):
    _name = 'crm.segment'
    _description = 'CRM Segment'
    _check_company_auto = True

    name = fields.Char(string='Segment', required=True)
    score_min = fields.Float(string='Min. Score')
    score_max = fields.Float(string='Max. Score')
    frequency_min = fields.Integer(string='Minimum Frequency')
    frequency_max = fields.Integer(string='Max Frequency')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)

