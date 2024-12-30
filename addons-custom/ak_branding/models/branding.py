from odoo import models, fields

class BrandingSettings(models.Model):
    _name = 'ak.branding'
    _description = 'Branding Settings'

    name = fields.Char(string="Name", default="Default Branding")
    footer_text = fields.Char(string="Footer Text", default="Powered by Kardan.Digital")
    footer_url = fields.Char(string="Footer URL", default="https://kardan.digital")
    logo = fields.Binary(string="Logo", attachment=True)
    favicon = fields.Binary(string="Favicon", attachment=True)

