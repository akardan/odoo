from odoo import http
from odoo.http import request
import hmac
import hashlib
import base64
import logging
import json

_logger = logging.getLogger(__name__)

class PaytrController(http.Controller):

    @http.route('/payment/paytr/notification', type='http', auth='public', methods=['POST'], csrf=False)
    def paytr_notification(self, **post):
        """Handle PayTR notifications."""
        _logger.info("Received PayTR notification: %s", post)

        # Gerekli Parametreler (PayTR'den gelen)
        merchant_oid = post.get('merchant_oid')
        hash_value = post.get('hash')
        status = post.get('status')
        payment_type = post.get('payment_type', '')

        # Odoo'da İşlem Bul ......... # Özel karakter için 'T' -> '-' çevirimi
        transaction = request.env['payment.transaction'].sudo().search([('reference', '=', merchant_oid.replace('T', '-'))], limit=1)
        if not transaction:
            _logger.error("Transaction not found for merchant_oid: %s", merchant_oid)
            return "ERROR"

        # İşlemin Bağlı Olduğu Ödeme Sağlayıcıyı Bul
        provider = transaction.provider_id
        if not provider or provider.code != 'paytr':
            _logger.error("PayTR provider not configured correctly.")
            return "ERROR"

        # API Entegrasyon Bilgileri
        merchant_id = provider.paytr_merchant_id
        merchant_key = provider.paytr_merchant_key.encode()
        merchant_salt = str(provider.paytr_merchant_salt)

        # Müşteri bilgileri (Gerekli olanlar)
        email = transaction.partner_id.email
        payment_amount = str(int(transaction.amount * 100)) # Kuruşa çevir


        # Dinamik Sepet İçeriği
        basket_list = [f"{line.product_id.name}, {str(int(line.price_unit * 100))},{int(line.product_uom_qty)}" for order in transaction.sale_order_ids for line in order.order_line if not line.display_type]
        user_basket = base64.b64encode(json.dumps(basket_list).encode())

        # Dokümantasyona Uygun Hash Oluşturma
        user_ip = request.httprequest.remote_addr
        no_installment = '0'
        max_installment = '0'
        currency = 'TL'
        test_mode = '1' if provider.paytr_test_mode else '0'
        
        # Hash hesaplama
        # Bu kısımda herhangi bir değişiklik yapmanıza gerek yoktur.
        # POST değerleri ile hash oluştur.
        hash_str = merchant_oid + merchant_salt + status + payment_amount
        generated_hash = base64.b64encode(hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()).decode()

        # Gelen Hash ile Karşılaştır
        if hash_value != generated_hash:
            _logger.error("Hash verification failed for PayTR notification. Expected %s, got %s", generated_hash, hash_value)
            return "ERROR"

        # İşlem Güncelleme
        if status == 'success':
            transaction._set_done()
        else:
            transaction._set_cancel()
            
        _logger.info("OK will be sent to PayTR")
        return "OK"
    

    @http.route('/payment/paytr/return', type='http', auth='public', methods=['GET'], csrf=False)
    def paytr_return(self, **kwargs):
        # Ödeme başarılı olduğunda yönlendirilecek sayfa
        _logger.info("Received PayTR return: %s", kwargs)

        # merchant_oid = kwargs.get('merchant_oid')
        # status = kwargs.get('status')

        # transaction = request.env['payment.transaction'].sudo().search([('reference', '=', merchant_oid)], limit=1)
        # if not transaction:
        #     _logger.error("Transaction not found for PayTR return: %s", kwargs)
        #     return request.render('website.404')

        # transaction._set_done()
        
        return request.redirect('/payment/status')    
    
    @http.route('/payment/paytr/cancel', type='http', auth='public', methods=['GET'], csrf=False)
    def paytr_cancel(self, **kwargs):
        # Ödeme başarısız olduğunda yönlendirilecek sayfa
        _logger.info("Received PayTR cancel: %s", kwargs)

        # merchant_oid = kwargs.get('merchant_oid')

        # transaction = request.env['payment.transaction'].sudo().search([('reference', '=', merchant_oid)], limit=1)
        # if not transaction:
        #     _logger.error("Transaction not found for PayTR cancel: %s", kwargs)
        #     return request.render('website.404')

        # transaction._set_transaction_cancel()

        return request.redirect('/payment/status')    
