from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    project_team_ids = fields.One2many('crm.team', 'user_id', readonly=True)

