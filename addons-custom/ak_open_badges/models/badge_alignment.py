from odoo import models, fields, api, _

class BadgeAlignment(models.Model):
    _name = 'badge.alignment'
    _description = _('Badge Alignment to External Standards')

    # Çevrilmesi gereken alanlar
    target_name = fields.Char(string=_('Target Name'), required=True, translate=True)
    target_description = fields.Text(string=_('Target Description'), translate=True)
    target_framework = fields.Char(string=_('Target Framework'), translate=True)

    badge_class_id = fields.Many2one('badge.class', string=_('Badge Class'), required=True)
    target_url = fields.Char(string=_('Target URL'))
    target_code = fields.Char(string=_('Target Code'))

    def get_json_ld(self):
        """JSON-LD formatında alignment verisi"""
        # Varsayılan dili kullan
        default_lang = 'en_US'
        self = self.with_context(lang=default_lang)

        return {
            "targetName": self.target_name,
            "targetUrl": self.target_url,
            "targetDescription": self.target_description,
            "targetFramework": self.target_framework,
            "targetCode": self.target_code,
        }
