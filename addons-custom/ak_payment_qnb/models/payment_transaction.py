# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from datetime import datetime
import hashlib
from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransactionQNB(models.Model):
    _inherit = 'payment.transaction'

    def qnb_payment_request(self, transaction):
        # Create a payment request for QNB 3D Host method
        _logger.info("Creating payment request for transaction: %s", transaction.reference)
        rnd = str(datetime.now().timestamp())  # Generate a random value based on the current timestamp
        base_url = self._get_base_url()
        # Check if base URL is available
        if not base_url:
            _logger.error("Base URL could not be determined. Aborting payment request.")
            raise ValidationError("Base URL could not be determined. Please check your configuration.")

        # Determine the correct URL based on provider state
        qnb_form_url = self._get_qnb_form_url(transaction.provider_id.state)
        if not qnb_form_url:
            _logger.error("QNB Form URL could not be determined. Aborting payment request.")
            raise ValidationError("QNB Form URL could not be determined. Please check your configuration.")

        # Prepare data to be sent in the payment request
        data = {
            'MbrId': '5',
            'MerchantId': transaction.provider_id.qnb_merchant_id,
            'UserCode': transaction.provider_id.qnb_user_code,
            'UserPass': transaction.provider_id.qnb_user_pass,
            'OrderId': transaction.reference,
            'TxnType': 'Auth',  # Transaction type is authorization
            'PurchAmount': str(int(transaction.amount * 100)),  # Convert the amount to the smallest unit (cents)
            'Currency': '949',  # Currency code for Turkish Lira (TRY)
            'SecureType': '3DHost',  # Use 3D Secure Host method
            'InstallmentCount': '0',  # No installment
            'OkUrl': f"{base_url}/shop/payment/qnb/return",  # URL for successful payment
            'FailUrl': f"{base_url}/shop/payment/qnb/cancel",  # URL for failed payment
            'Lang': 'TR',  # Language set to Turkish
            'Rnd': rnd,
            'qnb_form_url': qnb_form_url  # Test or Live URL for QNB payment
        }
        _logger.debug("Payment request data: %s", data)
        # Generate hash for the payment request and add it to the data dictionary
        data['Hash'] = self._generate_qnb_hash(data)
        _logger.debug("Payment request hash: %s", data['Hash'])
        return data

    def _generate_qnb_hash(self, params):
        # Generate hash value for QNB payment, following the order specified in the QNB documentation
        _logger.debug("Generating hash with parameters: %s", params)
        # Concatenate all required parameters and merchant password to form the string to hash
        str_to_hash = (
            params.get('MbrId') +
            params.get('OrderId') +
            params.get('PurchAmount') +
            params.get('OkUrl') +
            params.get('FailUrl') +
            params.get('TxnType') +
            params.get('InstallmentCount') +
            params.get('Rnd') +
            self.provider_id.qnb_merchant_pass
        )
        # Use SHA1 to create the hash and then encode it in Base64
        hash_object = hashlib.sha1(str_to_hash.encode('utf-8'))
        hash_result = base64.b64encode(hash_object.digest()).decode('utf-8')
        _logger.debug("Generated hash: %s", hash_result)
        return hash_result

    def _get_qnb_form_url(self, state):
        # Return the appropriate form URL based on provider state
        if state == 'test':
            return 'https://vpostest.qnb.com.tr/Gateway/3DHost.aspx'
        return 'https://vpostest.qnb.com.tr/Gateway/3DHost.aspx'

    def _get_specific_create_values(self, provider_code, values):
        # Add specific create values for QNB transactions
        if provider_code == 'qnb':
            return {
                'operation': 'online_redirect',  # Indicate that the operation is an online redirect
                'tokenize': False,  # No tokenization for QNB payments
            }
        return super()._get_specific_create_values(provider_code, values)

    def _get_specific_processing_values(self, processing_values):
        _logger.debug("Getting specific processing values for transaction with reference %s", self.reference)
        # Get provider-specific processing values for QNB
        if self.provider_code == 'qnb':
            provider = self.env['payment.provider'].browse(processing_values['provider_id'])
            # Check if the provider exists
            if not provider.exists():
                _logger.error("Payment provider with ID %s does not exist.", processing_values['provider_id'])
                raise ValidationError("The specified payment provider does not exist. Please check your configuration.")
            return self.qnb_payment_request(self)
        return super()._get_specific_processing_values(processing_values)

    def _get_specific_rendering_values(self, processing_values):
        _logger.debug("Getting specific rendering values for transaction with reference %s", self.reference)
        # Get provider-specific rendering values for QNB
        if self.provider_code == 'qnb':
            provider = self.env['payment.provider'].browse(processing_values['provider_id'])
            # Check if the provider exists
            if not provider.exists():
                _logger.error("Payment provider with ID %s does not exist.", processing_values['provider_id'])
                raise ValidationError("The specified payment provider does not exist. Please check your configuration.")
            form_data = self.qnb_payment_request(self)
            _logger.debug("Form data for rendering: %s", form_data)
            return form_data
        return super()._get_specific_rendering_values(processing_values)

    def _get_specific_rendering_values(self, processing_values):
        _logger.debug("Getting specific rendering values for transaction with reference %s", self.reference)
        # Get provider-specific rendering values for QNB
        if self.provider_code == 'qnb':
            form_data = self.qnb_payment_request(self)
            if not form_data:
                _logger.error("Failed to retrieve form data for rendering.")
                raise ValidationError("Form data could not be generated for QNB payment. Please check your configuration.")
            _logger.debug("Form data for rendering: %s", form_data)
            return {'form_data': form_data}  # Bu satırla `form_data` template'e gönderilir
        return super()._get_specific_rendering_values(processing_values)

    def _send_payment_request(self):
        _logger.info("Sending payment request for transaction reference %s", self.reference)
        # Send payment request specifically for QNB transactions
        if self.provider_code == 'qnb':
            form_data = self.qnb_payment_request(self)
            _logger.info("Form data generated for QNB payment request: %s", form_data)
            # Set the transaction state to pending after sending the request
            self._set_pending("The payment request has been sent.")
        else:
            super()._send_payment_request()

    def _set_pending(self, state_message=None):
        _logger.info("Setting transaction %s to pending state.", self.reference)
        # Safely update the state of the transaction to 'pending'
        self.write({'state': 'pending', 'state_message': state_message or "The payment is pending."})

    def _set_done(self, state_message=None):
        _logger.info("Setting transaction %s to done state.", self.reference)
        # Safely update the state of the transaction to 'done'
        self.write({'state': 'done', 'state_message': state_message or "The payment has been successfully completed."})

    def _set_canceled(self, state_message=None):
        _logger.info("Setting transaction %s to canceled state.", self.reference)
        # Safely update the state of the transaction to 'canceled'
        self.write({'state': 'cancel', 'state_message': state_message or "The payment was canceled by the user."})

    def _get_base_url(self):
        # Retrieve the base URL from the system parameters or configuration
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not base_url:
            _logger.error("Base URL is not configured in the system parameters.")
            raise ValidationError("Base URL is not configured. Please check your system settings.")
        return base_url
    
    
    
#         """
#         Extract necessary values from the post data to generate QNB transaction values.
#         This function is used in the controller when redirecting the user to QNB's 3D Host payment page.
#         """
#         _logger.debug("Extracting QNB transaction values from post data: %s", post)
#         # Get the payment transaction reference
#         reference = post.get('reference') or post.get('OrderId')
#         # Find the corresponding transaction in Odoo using the reference
#         transaction = self.search([('reference', '=', reference)], limit=1)
#         if not transaction:
#             _logger.error("No transaction found for reference %s", reference)
#             raise ValueError("Transaction not found")

#         # Prepare transaction values to be sent to QNB
#         values = {
#             'reference': transaction.reference,
#             'amount': transaction.amount,
#             'currency_id': transaction.currency_id,
#             'partner_id': transaction.partner_id,
#             'partner_email': transaction.partner_email,
#         }
#         _logger.debug("Prepared transaction values for QNB: %s", values)
#         return transaction.acquirer_id.qnb_form_generate_values(values)

#     def _handle_feedback_data(self, provider, data):
#         """
#         Handle feedback data coming from QNB.
#         This function processes the data QNB sends after payment is processed (success or failure).
#         """
#         _logger.debug("Handling feedback data for provider %s: %s", provider, data)
#         if provider != 'qnb':
#             # If the feedback is not for QNB, fall back to the original method
#             return super()._handle_feedback_data(provider, data)

#         # Extract the necessary details from the data provided by QNB
#         reference = data.get('OrderId')
#         transaction = self.search([('reference', '=', reference)], limit=1)
#         if not transaction:
#             _logger.error("Transaction with reference %s not found", reference)
#             return False

#         # Check if the return code indicates success
#         if data.get('ProcReturnCode') == '00':
#             # Mark the transaction as done if payment is successful
#             transaction.write({
#                 'state': 'done',
#                 'acquirer_reference': reference,
#                 'date': fields.Datetime.now(),
#             })
#             _logger.info("QNB payment for transaction %s was successful.", reference)
#         else:
#             # Mark the transaction as failed if there's an error
#             error_message = data.get('ErrorMessage', 'Unknown error')
#             transaction.write({
#                 'state': 'error',
#                 'state_message': error_message,
#             })
#             _logger.warning("QNB payment for transaction %s failed with error: %s", reference, error_message)
#         return True

#     @api.model
#     def create(self, values):
#         """
#         Override create method to ensure QNB-specific initialization is done if required.
#         """
#         _logger.debug("Creating a payment transaction with values: %s", values)
#         # If the transaction is for QNB, we may initialize some specific values.
#         if values.get('acquirer_id'):
#             acquirer = self.env['payment.provider'].browse(values['acquirer_id'])
#             if acquirer.provider == 'qnb':
#                 _logger.info("Creating a transaction for QNB with reference: %s", values.get('reference'))
#                 # Any QNB-specific initialization can go here.
#                 values['reference'] = values.get('reference') or self.env['ir.sequence'].next_by_code('payment.qnb')
#         return super(PaymentTransactionQNB, self).create(values)

#     def _log_qnb_transaction(self, reference, state):
#         """
#         Log transaction status for QNB payments.
#         Useful for auditing and debugging purposes.
#         """
#         _logger.info("QNB transaction %s has reached state: %s", reference, state)

#     def _qnb_form_validate(self, data):
#         """
#         Validate the incoming data from QNB to ensure the integrity of the transaction.
#         This validation can help prevent fraud or issues during the payment process.
#         """
#         _logger.debug("Validating QNB transaction data: %s", data)
#         reference = data.get('OrderId')
#         transaction = self.search([('reference', '=', reference)], limit=1)
#         if not transaction:
#             _logger.error("Transaction with reference %s not found during validation", reference)
#             return False

#         # Validation: Ensure the transaction reference and amount match
#         if transaction.amount != float(data.get('amount', 0)) / 100:
#             _logger.error("Transaction amount mismatch for reference %s", reference)
#             transaction.write({
#                 'state': 'error',
#                 'state_message': "Amount mismatch during validation",
#             })
#             return False

#         # Additional validation checks can go here, such as verifying the hash value

#         _logger.info("QNB transaction %s validated successfully.", reference)
#         return True
