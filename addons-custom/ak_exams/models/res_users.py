# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    external_id = fields.Char('Harici ID', help='Entegrasyon için harici kimlik')
    
    _sql_constraints = [
        ('external_id_uniq', 'unique (external_id)', 
         'Harici ID benzersiz olmalıdır!'),
    ]