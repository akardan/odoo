from odoo import fields, models, api


class CrmSegmentation(models.Model):
    _name = 'crm.segmentation'
    _description = 'CRM Segmentation'
    _rec_name = 'partner_id'
    _check_company_auto = True

    sales_team_id = fields.Many2one('crm.team', string='Sales Team', required=True, domain="[('team_type', '=', 'G')]")
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    segment_id = fields.Many2one('crm.segment', string='Segment', required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company,
                                 check_company=True)
