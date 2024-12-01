from odoo import models, fields, api, _


class ResCountry(models.Model):
    _inherit = 'res.country'

    titck_country_code = fields.Char(string=_("TİTCK Country Code"), help=_("Enter the TİTCK country code"))

    def action_open_country_import_wizard(self):
        return {
            'name': _('Import Country Codes Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'country.import.wizard',
            'view_mode': 'form',
            'target': 'new',
        }