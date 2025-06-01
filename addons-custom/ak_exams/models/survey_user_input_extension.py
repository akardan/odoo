from odoo import fields, models

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    ip_address = fields.Char(string='IP Address', readonly=True)