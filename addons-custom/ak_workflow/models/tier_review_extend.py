# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TierReview(models.Model):
    _inherit = 'tier.review'

    # Workflow Context
    workflow_state_id = fields.Many2one(
        'ak.workflow.state', 
        string='Workflow State at Review',
        readonly=True
    )
    workflow_transition_id = fields.Many2one(
        'ak.workflow.transition', 
        string='Triggered Transition',
        readonly=True
    )

    # Enhanced Review Data
    review_comment = fields.Text('Review Comment')
    review_duration = fields.Float(
        'Review Duration (Hours)',
        compute='_compute_review_duration', 
        store=True,
        help="Time taken from creation to review."
    )
    attachment_ids = fields.Many2many(
        'ir.attachment', 
        'tier_review_attachment_rel',
        'tier_review_id', 'attachment_id',
        string='Review Attachments'
    )

    @api.depends('create_date', 'reviewed_date')
    def _compute_review_duration(self):
        """Compute review duration in hours."""
        for review in self:
            if review.create_date and review.reviewed_date:
                delta = review.reviewed_date - review.create_date
                review.review_duration = delta.total_seconds() / 3600
            else:
                review.review_duration = 0

    def _prepare_review_vals(self, record):
        """Inject workflow context when creating a review."""
        vals = super()._prepare_review_vals(record)
        if hasattr(record, 'workflow_current_state_id'):
            vals['workflow_state_id'] = record.workflow_current_state_id.id
        if hasattr(record, 'workflow_pending_transition_id'):
            vals['workflow_transition_id'] = record.workflow_pending_transition_id.id
        return vals

    def _log_activity(self, approved=True):
        """Override to add more context to the log message."""
        super()._log_activity(approved)
        for review in self:
            if review.review_comment:
                record = self.env[review.model].browse(review.res_id)
                body = _("Review Comment: %s") % review.review_comment
                record.message_post(body=body, author_id=review.reviewed_by.partner_id.id)