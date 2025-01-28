from odoo import models, fields, api, _

class BadgeType(models.Model):
    _name = 'badge.type'
    _description = _('Badge Type')

    name = fields.Char(string=_('Name'), required=True)
    code = fields.Char(string=_('Code'), required=True)
    description = fields.Text(string=_('Description'))
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Badge Type Code must be unique!')
    ]