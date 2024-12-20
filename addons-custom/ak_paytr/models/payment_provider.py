from odoo import models, fields, api
import hmac
import hashlib
import base64
import requests
import json

class PaymentProviderPaytr(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('paytr', "PayTR")], ondelete={'paytr': 'set default'}
    )
    paytr_merchant_id = fields.Char(string='Merchant ID')
    paytr_merchant_key = fields.Char(string='Merchant Key')
    paytr_merchant_salt = fields.Char(string='Merchant Salt')
    paytr_test_mode = fields.Boolean(string='Test Mode', default=True)

    def _paytr_generate_token(self, values):
        """Generate PayTR iframe token for secure payment."""
        user_basket = base64.b64encode(json.dumps([
            [values['description'], str(values['amount']), 1]
        ]).encode()).decode()

        hash_str = (
            f"{self.paytr_merchant_id}{values['user_ip']}{values['merchant_oid']}"
            f"{values['email']}{values['amount']}{user_basket}{0}{0}TL{int(self.paytr_test_mode)}"
        )
        paytr_token = base64.b64encode(
            hmac.new(self.paytr_merchant_key.encode(), hash_str.encode() + self.paytr_merchant_salt.encode(), hashlib.sha256).digest()
        )

        payload = {
            'merchant_id': self.paytr_merchant_id,
            'user_ip': values['user_ip'],           # En fazla 39 karakter (ipv4)
            'merchant_oid': values['merchant_oid'], # En fazla 64 karakter,Alfa numerik
            'email': values['email'],               # En fazla 100 karakter
            'payment_amount': values['amount'],     # Örn: 34.56 için 3456 gönderilmelidir.(34.56 * 100 = 3456)
            'currency': values['currency'],         # TL(veya TRY), EUR, USD, GBP, RUB (Boş ise TL kabul edilir)
            'user_basket': user_basket,             # Nasıl bir yapıda olacağı ile ilgili olarak örnek kodlara bakmalısınız
            'no_installment': 0,                    # 0 veya 1.  Eğer 1 olarak gönderilirse taksit seçenekleri gösterilmez
            'max_installment': 0,                   # 0,2..12 Sıfır (0) gönderilmesi durumunda yürürlükteki en fazla izin verilen taksit geçerli olur
            'paytr_token': paytr_token,
            'user_name': values['user_name'],
            'user_address': values['user_address'],
            'user_phone': values['user_phone'],
            'merchant_ok_url': values['ok_url'],
            'merchant_fail_url': values['fail_url'],
            'test_mode': int(self.paytr_test_mode), # 0: Canlı, 1: Test  Mağaza canlı modda iken test işlem yapmak için 1 olarak gönderilebilir
            'debug_on': 1,                          # 0: Hata mesajlarını gösterme, 1: Hata mesajlarını göster
            'timeout_limit': 30,                    # PayTR tarafında işlem yapılma süresi dakika cinsinden
            'lang': 'tr'                            # Sayfa dil seçeneği tr, en. Boş gönderilirse tr kabul edilir.
        }
        response = requests.post('https://www.paytr.com/odeme/api/get-token', data=payload)
        return response.json()
    
class PaymentTransactionPaytr(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _handle_notification(self, data):
        """Handle PayTR notification for payment status."""
        merchant_oid = data.get('merchant_oid')
        status = data.get('status')
        payment_transaction = self.search([('reference', '=', merchant_oid)], limit=1)

        if not payment_transaction:
            return 'Transaction not found'

        if status == 'success':
            payment_transaction._set_transaction_done()
        else:
            payment_transaction._set_transaction_cancel()

        return 'OK'