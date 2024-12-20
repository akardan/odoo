# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nh_oem_activate = fields.Boolean(string='Activate OEM Branding', config_parameter='nh_oem.active')
    nh_oem_level = fields.Selection([('back', 'Backend'), ('front', 'Frontend'), ('full', 'Complete OEM')],
                                    default='front', string='OEM Level', config_parameter='nh_oem.level')

    def set_values(self):
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        return res





