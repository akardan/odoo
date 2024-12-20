from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class QNBPaymentController(http.Controller):
    
    @http.route('/payment/qnb/return', type='http', auth='public', csrf=False)
    def qnb_payment_return(self, **post):
        """Handle the successful payment response from QNB."""
        _logger.info("Handling QNB payment return: %s", post)
        # Add logic to handle the response, find the transaction and confirm payment
        reference = post.get('OrderId')
        if reference:
            transaction = request.env['payment.transaction'].sudo().search([('reference', '=', reference)], limit=1)
            if transaction:
                transaction._set_done("Payment successful.")
                return request.render('payment.payment_success', {'transaction': transaction})
        return request.render('payment.payment_failed')

    @http.route('/payment/qnb/cancel', type='http', auth='public', csrf=False)
    def qnb_payment_cancel(self, **post):
        """Handle the failed payment response from QNB."""
        _logger.info("Handling QNB payment cancellation: %s", post)
        # Add logic to handle the cancellation response and update transaction status
        reference = post.get('OrderId')
        if reference:
            transaction = request.env['payment.transaction'].sudo().search([('reference', '=', reference)], limit=1)
            if transaction:
                transaction._set_canceled("Payment canceled by user.")
                return request.render('payment.payment_failed', {'transaction': transaction})
        return request.render('payment.payment_failed')
        

    # @http.route(['/payment/qnb/return', '/payment/qnb/cancel'], type='http', auth='public', csrf=False)
    # def qnb_payment_return(self, **kwargs):
    #     # QNB ödeme dönüş verilerini işleme
    #     _logger.info("Handling QNB payment return with data: %s", kwargs)
        
    #     # Log CSRF token
    #     # csrf_token = request.session.csrf_token
    #     # _logger.info("CSRF Token: %s", csrf_token)
        
    #     # Log session validity
    #     _logger.info("Session valid: %s", request.session.sid)
        
    #     try:
    #         provider = request.env['payment.provider'].sudo().search([('provider', '=', 'qnb')], limit=1)
    #         provider._process_feedback_data(kwargs)
    #         order_id = kwargs.get('OrderId')
    #         sale_order = request.env['sale.order'].sudo().search([('name', '=', order_id)], limit=1)
    #         if sale_order:
    #             _logger.info("Order found: %s. Confirming order.", sale_order)
    #             sale_order.action_confirm()
    #             return request.redirect('/payment/status?status=success')
    #         else:
    #             _logger.warning("Order not found for ID: %s", order_id)
    #             _logger.info("Redirecting to cancel URL for failed order ID: %s", order_id)
    #             return request.redirect('/payment/status?status=cancel&message=Order not found')
    #     except ValidationError as e:
    #         _logger.error("Validation error occurred: %s", str(e))
    #         _logger.info("Redirecting to cancel URL due to validation error: %s", str(e))
    #         return request.redirect('/payment/status?status=cancel&message=%s' % str(e))
