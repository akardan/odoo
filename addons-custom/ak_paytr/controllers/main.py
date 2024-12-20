import hashlib
import hmac
import base64
from odoo import http
from odoo.http import request

class PaytrController(http.Controller):

    @http.route('/payment/paytr/notification', type='http', auth='public', methods=['POST'], csrf=False)
    def paytr_notification(self, **post):
        provider = request.env['payment.provider'].sudo().search([('code', '=', 'paytr')], limit=1)
        merchant_key = provider.paytr_merchant_key
        merchant_salt = provider.paytr_merchant_salt

        hash_str = f"{post['merchant_oid']}{merchant_salt}{post['status']}{post['total_amount']}"
        calculated_hash = base64.b64encode(hmac.new(merchant_key.encode(), hash_str.encode(), hashlib.sha256).digest())

        if calculated_hash.decode() != post['hash']:
            return "PAYTR notification failed: bad hash"

        if post['status'] == 'success':
            order = request.env['sale.order'].sudo().search([('name', '=', post['merchant_oid'].replace('T', '-'))], limit=1)
            if order:
                order.action_confirm()
        return "OK"

    @http.route('/payment/paytr/payment', type='http', auth='public', methods=['GET'], csrf=False)
    def paytr_payment(self, **kwargs):
        transaction = request.env['payment.transaction'].sudo().search([('reference', '=', kwargs.get('reference'))], limit=1)
        if not transaction:
            return "Transaction not found"

        paytr_data = transaction.paytr_payment_request(transaction)
        return request.render('ak_paytr.paytr_payment_form', paytr_data)
    
    @http.route('/payment/paytr/return', type='http', auth='public', methods=['GET'], csrf=False)
    def paytr_return(self, **kwargs):
        # Ödeme başarılı olduğunda yönlendirilecek sayfa
        return request.render('ak_paytr.payment_success')

    @http.route('/payment/paytr/cancel', type='http', auth='public', methods=['GET'], csrf=False)
    def paytr_cancel(self, **kwargs):
        # Ödeme başarısız olduğunda yönlendirilecek sayfa
        return request.render('ak_paytr.payment_failure')    