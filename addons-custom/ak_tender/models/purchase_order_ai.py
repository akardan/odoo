# -*- coding: utf-8 -*-

from odoo import models

class PurchaseOrderAI(models.Model):
    """Extend purchase.order with AI mixin"""
    _inherit = ['purchase.order', 'ak_ai.mixin']
    _name = 'purchase.order'
