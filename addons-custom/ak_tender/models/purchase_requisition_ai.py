# -*- coding: utf-8 -*-

from odoo import models

class PurchaseRequisitionAI(models.Model):
    """Extend purchase.requisition with AI mixin"""
    _inherit = ['purchase.requisition', 'ak_ai.mixin']
    _name = 'purchase.requisition'
