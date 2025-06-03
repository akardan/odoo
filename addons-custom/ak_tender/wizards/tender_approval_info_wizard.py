# -*- coding: utf-8 -*-

from odoo import models, fields

class TenderApprovalInfoWizard(models.TransientModel):
    _name = 'tender.approval.info.wizard'
    _description = 'Tender Approval Information Wizard'

    tender_id = fields.Many2one('ak.tender', string='Tender', readonly=True)
    approval_user_id = fields.Many2one(
        related='tender_id.approval_user_id',
        string='Approved By',
        readonly=True
    )
    approval_date = fields.Datetime(
        related='tender_id.approval_date',
        string='Approval Date',
        readonly=True
    )

    # No action buttons needed on the wizard, it's just for display.
    # A default "Close" button will be provided by Odoo.