from odoo import models, fields, _


class PaymentProviderPaytr(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('paytr', "PayTR")], ondelete={'paytr': 'set default'}
    )
    paytr_merchant_id = fields.Char(string=_('Merchant ID'))
    paytr_merchant_key = fields.Char(string=_('Merchant Key'))
    paytr_merchant_salt = fields.Char(string=_('Merchant Salt'))
    paytr_test_mode = fields.Boolean(string=_('Test Mode', default=True))


    def _paytr_get_urls(self):
        """Return PayTR URL based on the provider state."""
        if self.state == 'test':
            return 'https://www.paytr.com/odeme/guvenli-test/'
        return 'https://www.paytr.com/odeme/guvenli/'
    
