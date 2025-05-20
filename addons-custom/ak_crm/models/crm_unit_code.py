from odoo import models, fields

class CrmUnitCode(models.Model):
    _name = 'crm.unit.code'
    _description = 'CRM Unit Code'

    name = fields.Char(string='Name', required=True)
    ref_code = fields.Char(string='Reference Code', required=True)
