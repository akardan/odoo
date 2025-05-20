from odoo import models, fields

class CrmUnitType(models.Model):
    _name = 'crm.unit.type'
    _description = 'CRM Unit Type'

    name = fields.Char(string='Name', required=True)
    ref_code = fields.Char(string='Reference Code', required=True)
