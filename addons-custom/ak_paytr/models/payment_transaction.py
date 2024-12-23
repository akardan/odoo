import hashlib
import hmac
import base64
import logging
import requests
import json
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from odoo.http import request  # request modülünü içe aktar

_logger = logging.getLogger(__name__)


class PaymentTransactionPaytr(models.Model):
    _inherit = 'payment.transaction'

    paytr_form_data = fields.Text(string="PayTR Form Data")  # paytr_form_data alanını ekle

    def paytr_payment_request(self, transaction):
        # PayTR ödeme isteği oluşturma ve iframe_token alma
        _logger.info("Creating payment request for PayTR transaction: %s", transaction.reference)
        
        # API Entegrasyon Bilgileri
        merchant_id = transaction.provider_id.paytr_merchant_id
        merchant_key = transaction.provider_id.paytr_merchant_key.encode()  
        merchant_salt = str(transaction.provider_id.paytr_merchant_salt)
        
        base_url = self._get_base_url()

        # Base URL Kontrolü
        if not base_url:
            _logger.error("Base URL could not be determined. Aborting PayTR payment request.")
            raise ValidationError("Base URL could not be determined. Please check your configuration.")

        # PayTR Form URL
        paytr_form_url = self._get_paytr_form_url(transaction.provider_id.state)
        if not paytr_form_url:
            _logger.error("PayTR Form URL could not be determined. Aborting payment request.")
            raise ValidationError("PayTR Form URL could not be determined. Please check your configuration.")
        
        # Müşteri bilgileri (Gerekli olanlar)
        email = transaction.partner_id.email
        payment_amount = str(int(transaction.amount * 100)) # Kuruşa çevir
        
        # merchant_oid alfanumerik olmalı ve özel karakter içermemeli
        merchant_oid = transaction.reference.replace('-', 'T')

        # Müşteri Ad-Soyad
        user_name = transaction.partner_id.name

        # Müşteri adres (Gerekli ise)
        user_address = (transaction.partner_id.street or '') + ' ' + (transaction.partner_id.street2 or '') if transaction.partner_id.street or transaction.partner_id.street2 else ''

        # Müşteri telefon (Gerekli ise)
        user_phone = transaction.partner_id.phone if transaction.partner_id.phone else ''

        # Sepet Listesi
        basket_list = [f"{line.product_id.name}, {str(int(line.price_unit * 100))},{int(line.product_uom_qty)}" for order in transaction.sale_order_ids for line in order.order_line if not line.display_type]
        user_basket = base64.b64encode(json.dumps(basket_list).encode())

        # Diğer parametreler
        user_ip = request.httprequest.remote_addr
        timeout_limit = '30'
        debug_on = '1'
        test_mode = '1'
        no_installment = '0'
        max_installment = '0'
        currency = 'TL'
        merchant_ok_url = base_url + '/payment/paytr/return'
        merchant_fail_url = base_url + '/payment/paytr/cancel'

        # Hash hesaplama
        # Bu kısımda herhangi bir değişiklik yapmanıza gerek yoktur.
        hash_str = merchant_id + user_ip + merchant_oid + email + payment_amount + user_basket.decode() + no_installment + max_installment + currency + test_mode
        hash_salt = hash_str + merchant_salt
        paytr_token = base64.b64encode(hmac.new(merchant_key, hash_salt.encode(), hashlib.sha256).digest())

        params = {
            'merchant_id': merchant_id,
            'user_ip': user_ip,
            'merchant_oid': merchant_oid,
            'email': email,
            'payment_amount': payment_amount,
            'paytr_token': paytr_token.decode(),
            'user_basket': user_basket.decode(),
            'debug_on': debug_on,
            'no_installment': no_installment,
            'max_installment': max_installment,
            'user_name': user_name,
            'user_address': user_address,
            'user_phone': user_phone,
            'merchant_ok_url': merchant_ok_url,
            'merchant_fail_url': merchant_fail_url,
            'timeout_limit': timeout_limit,
            'currency': currency,
            'test_mode': test_mode
        }
        
        # PayTR API'sine istek gönder
        try:
            result = requests.post('https://www.paytr.com/odeme/api/get-token', data=params)
            res = json.loads(result.text)
        
            if res['status'] == 'success':
                _logger.info("PayTR iframe token successfully received for transaction %s: %s", transaction.reference, res['token'])
                return {
                    'paytr_url': paytr_form_url + res['token'],
                }
            else:
                _logger.error("PayTR API error for transaction %s: %s", transaction.reference, result.text)
                raise ValidationError(f"PayTR API error: {result.text}")
        except requests.exceptions.RequestException as e:
            _logger.error("Error communicating with PayTR API: %s", e)
            raise ValidationError(f"Error communicating with PayTR API: {e}")
        
    def _get_base_url(self):
        # Base URL'i döndüren yardımcı metot
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url')        
    
    def _get_paytr_form_url(self, state):
        # Test veya canlı ortam için PayTR form URL'sini döndür
        if state == 'enabled':
            return 'https://www.paytr.com/odeme/guvenli/'
        else:
            return 'https://www.paytr.com/odeme/guvenli-test/'

    def _get_specific_create_values(self, provider_code, values):
        if provider_code == 'paytr':
            return {
                'operation': 'online_redirect',
                'tokenize': False,
            }
        return super()._get_specific_create_values(provider_code, values)

    def _get_specific_processing_values(self, processing_values):
        _logger.debug("Getting specific processing values for transaction with reference %s", self.reference)
        if self.provider_code == 'paytr':
            provider = self.env['payment.provider'].browse(processing_values['provider_id'])
            if not provider.exists():
                _logger.error("Payment provider with ID %s does not exist.", processing_values['provider_id'])
                raise ValidationError("The specified payment provider does not exist. Please check your configuration.")
            form_data = self.paytr_payment_request(self)
            self.paytr_form_data = json.dumps(form_data)  # Form verilerini sakla
            return form_data
        return super()._get_specific_processing_values(processing_values)

    def _get_specific_rendering_values(self, processing_values):
        _logger.debug("Getting specific rendering values for transaction with reference %s", self.reference)
        if self.provider_code == 'paytr':
            if not self.paytr_form_data:
                _logger.error("Failed to retrieve form data for rendering.")
                raise ValidationError("Form data could not be generated for PayTR payment. Please check your configuration.")
            _logger.debug("Form data for rendering: %s", self.paytr_form_data)
            return {'form_data': json.loads(self.paytr_form_data)}  # Token'i template'e gönder
        return super()._get_specific_rendering_values(processing_values)

    def _send_payment_request(self):
        _logger.info("Sending payment request for transaction reference %s", self.reference)
        if self.provider_code == 'paytr':
            if self.paytr_form_data:
                self._set_pending("The payment request has been sent.")  # Sadece form_data başarılı geldiğinde pending yap
            else:
                _logger.error("Payment request could not be generated.")
        else:
            super()._send_payment_request()

