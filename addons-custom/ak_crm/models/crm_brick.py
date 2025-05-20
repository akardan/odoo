from odoo import models, fields, api

class Brick(models.Model):
    _name = 'crm.brick'
    _description = "Brick"
    _check_company_auto = True


    name = fields.Char(string='Brick', required=True)
    code = fields.Char(string='Brick Code', required=True)
    state_id = fields.Many2one('res.country.state', 'State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', groups="hr.group_hr_user")
    active = fields.Boolean(default=True)
    territory_id = fields.Many2one('crm.team.member', string='Territory', ondelete='set null')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    unit_ids = fields.One2many('crm.unit', 'brick_id', string='Units')
