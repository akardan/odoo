from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tcmb_url = fields.Char(
        string="TCMB Exchange Rate URL",
        config_parameter="ak_currency_rate_tcmb.tcmb_url",
        help="URL to fetch exchange rates from TCMB (e.g., https://www.tcmb.gov.tr/kurlar/today.xml)",
    )