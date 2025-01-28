from odoo import models, fields, api, _

class BadgeAlignment(models.Model):
    _name = 'badge.alignment'
    _description = _('Badge Alignment to External Standards')

    badge_class_id = fields.Many2one('badge.class', string=_('Badge Class'), required=True)
    target_name = fields.Char(string=_('Target Name'), required=True)
    target_url = fields.Char(string=_('Target URL'), required=True)
    target_description = fields.Text(string=_('Target Description'))
    target_framework = fields.Char(string=_('Target Framework'))
    target_code = fields.Char(string=_('Target Code'))

    def get_json_ld(self):
        return {
            "targetName": self.target_name,
            "targetUrl": self.target_url,
            "targetDescription": self.target_description,
            "targetFramework": self.target_framework,
            "targetCode": self.target_code,
        }
