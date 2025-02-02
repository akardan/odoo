# models/badge_tag.py
from odoo import models, fields, api, _

class BadgeTag(models.Model):
    _name = 'badge.tag'
    _description = _('Badge Tag')

    name = fields.Char(string=_('Name'), required=True, translate=True)
    color = fields.Integer(string=_('Color Index'))
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', _('Tag name must be unique!')),
    ]