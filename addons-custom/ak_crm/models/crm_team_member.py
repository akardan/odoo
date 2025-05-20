from odoo import fields, models

class CrmTeamMember(models.Model):
    _inherit = 'crm.team.member'

    brick_ids = fields.One2many('crm.brick', 'territory_id', string='Bricks')