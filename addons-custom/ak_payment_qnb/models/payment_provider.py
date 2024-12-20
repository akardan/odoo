# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
import logging
import hashlib
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo import http

_logger = logging.getLogger(__name__)

class PaymentProviderQNB(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('qnb', 'QNB VPOS')], ondelete={'qnb': 'set default'})
 
    # QNB Specific Configuration Fields
    qnb_merchant_id = fields.Char(string="Merchant ID", required_if_provider='qnb')  # QNB Merchant ID, required for QNB transactions
    qnb_user_code = fields.Char(string="User Code", required_if_provider='qnb')  # QNB User Code, needed to authenticate
    qnb_user_pass = fields.Char(string="User Password", required_if_provider='qnb')  # QNB User Password, used for secure transactions
    qnb_merchant_pass = fields.Char(string="Merchant Password", required_if_provider='qnb')  # QNB Merchant Password, used to create hash for security

