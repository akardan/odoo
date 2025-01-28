from odoo import models, fields, api, _

class BadgeIssuer(models.Model):
    _name = 'badge.issuer'
    _description = _('Badge Issuer Profile')
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_('Name'), required=True)
    url = fields.Char(string=_('URL'), required=True)
    email = fields.Char(string=_('Email'), required=True)
    description = fields.Text(string=_('Description'))
    image = fields.Binary(string=_("Issuer Logo"))
    public_key = fields.Text(string=_("Public Key for Verification"))

    def get_json_ld(self):
        return {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Issuer",
            "id": self.url,
            "name": self.name,
            "url": self.url,
            "email": self.email,
            "description": self.description or "",
        }
