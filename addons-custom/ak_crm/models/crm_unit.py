from odoo import models, fields, _

class CrmUnit(models.Model):
    _name = 'crm.unit'
    _description = 'Crm Unit'

    name = fields.Char(string='Name', required=True)
    brick_id = fields.Many2one('crm.brick', string='Brick')
    type_id = fields.Many2one('crm.unit.type', string='Type')
    code_id = fields.Many2one('crm.unit.code', string='Code')
    is_large_unit = fields.Boolean(string='Is Large Unit?', default=False)
    active = fields.Boolean(string='Active', default=True)
    external_id = fields.Char(string='External ID')
    partner_ids = fields.One2many('res.partner', 'unit_id', string='Partners')

    def open_unit_form(self):
        self.ensure_one()
        return {
            'name': _('Unit Form'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.unit',
            'res_id': self.id,
            'target': 'new',
        }