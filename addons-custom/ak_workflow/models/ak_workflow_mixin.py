# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AkWorkflowMixin(models.AbstractModel):
    _name = 'ak.workflow.mixin'
    _inherit = 'tier.validation'
    _description = 'Workflow Integration Mixin'

    # Workflow Definition
    workflow_definition_id = fields.Many2one(
        'tier.definition',
        string='Workflow',
        domain="[('model_name', '=', _name), ('is_workflow', '=', True)]",
        copy=False,
        help="The active workflow definition for this record."
    )

    # Current State
    workflow_current_state_id = fields.Many2one(
        'ak.workflow.state',
        string='Current State',
        domain="[('workflow_id', '=', workflow_definition_id)]",
        tracking=True,
        copy=False,
        help="Current state of the record in the workflow."
    )
    workflow_state = fields.Char(
        related='workflow_current_state_id.code',
        string='Workflow State Code',
        store=True
    )

    # Available Transitions
    workflow_available_transition_ids = fields.Many2many(
        'ak.workflow.transition',
        compute='_compute_available_transitions',
        string='Available Transitions'
    )

    # Workflow Dates
    workflow_start_date = fields.Datetime('Workflow Start Date', readonly=True, copy=False)
    workflow_end_date = fields.Datetime('Workflow End Date', readonly=True, copy=False)

    # Tier Validation Integration
    workflow_pending_transition_id = fields.Many2one(
        'ak.workflow.transition',
        string='Pending Transition',
        copy=False,
        help="The transition that is waiting for tier validation approval."
    )

    @api.depends('workflow_current_state_id', 'review_ids', 'review_ids.status')
    def _compute_available_transitions(self):
        for record in self:
            if not record.workflow_current_state_id:
                record.workflow_available_transition_ids = []
                continue
            
            all_transitions = record.workflow_current_state_id.outgoing_transition_ids
            available_transitions = self.env['ak.workflow.transition']
            
            for transition in all_transitions.filtered('active'):
                if transition.group_ids and not any(group in self.env.user.groups_id for group in transition.group_ids):
                    continue
                
                if transition.check_transition_conditions(record):
                    available_transitions |= transition
            
            record.workflow_available_transition_ids = available_transitions

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda r: not r.workflow_definition_id):
            record.workflow_definition_id = record._get_default_workflow()
            if record.workflow_definition_id and not record.workflow_current_state_id:
                initial_state = record.workflow_definition_id.initial_state_id
                if initial_state:
                    record.workflow_current_state_id = initial_state
                    record.workflow_start_date = fields.Datetime.now()
                    record._execute_state_actions('entry')
        return records

    def write(self, vals):
        old_states = {rec.id: rec.workflow_current_state_id for rec in self}
        res = super().write(vals)
        for record in self:
            if 'workflow_current_state_id' in vals and record.workflow_current_state_id != old_states[record.id]:
                if old_states[record.id]:
                    record._execute_state_actions('exit', state=old_states[record.id])
                record._execute_state_actions('entry')

                if record.workflow_current_state_id.is_final and not record.workflow_end_date:
                    record.workflow_end_date = fields.Datetime.now()
        return res

    def _get_default_workflow(self):
        domain = [('model_name', '=', self._name), ('active', '=', True), ('is_workflow', '=', True)]
        return self.env['tier.definition'].search(domain, limit=1)

    def execute_transition(self, transition_id, comment=None):
        self.ensure_one()
        transition = self.env['ak.workflow.transition'].browse(transition_id)

        if transition not in self.workflow_available_transition_ids:
            raise UserError(_("This transition is not available for the current state or user."))

        if transition.require_tier_validation:
            self.workflow_pending_transition_id = transition
            self.request_validation()
            self._log_transition(transition, self.workflow_current_state_id, 'pending_approval', comment)
        else:
            self._perform_transition(transition, comment)
        return True

    def _perform_transition(self, transition, comment=None):
        old_state = self.workflow_current_state_id
        self.workflow_current_state_id = transition.to_state_id
        self._log_transition(transition, old_state, 'completed', comment)
        
        for action in transition.action_ids:
            action.execute_action(self)

    def _execute_state_actions(self, trigger_event, state=None):
        state_to_process = state or self.workflow_current_state_id
        if not state_to_process:
            return
        
        actions = state_to_process.entry_action_ids if trigger_event == 'entry' else state_to_process.exit_action_ids
        for action in actions.filtered(lambda a: a.trigger_event == trigger_event):
            action.execute_action(self)

    def _log_transition(self, transition, old_state, status, comment=None):
        status_map = {'completed': '✅', 'pending_approval': '⏳', 'rejected': '❌'}
        body = _(
            "<strong>%(icon)s Workflow Transition</strong><br/>"
            "From: <strong>%(from)s</strong> → To: <strong>%(to)s</strong><br/>"
            "Transition: %(trans)s"
        ) % {
            'icon': status_map.get(status, ''),
            'from': old_state.name,
            'to': transition.to_state_id.name,
            'trans': transition.name
        }
        if comment:
            body += _("<br/>Comment: %s") % comment
        self.message_post(body=body)

    def _validate_tier(self, tiers):
        res = super()._validate_tier(tiers)
        for record in self.filtered(lambda r: r.workflow_pending_transition_id and r.validated):
            transition = record.workflow_pending_transition_id
            record.workflow_pending_transition_id = False
            record._perform_transition(transition, _("Approved via tier validation"))
        return res

    def _rejected_tier(self, tier_review):
        super()._rejected_tier(tier_review)
        for record in self.filtered('workflow_pending_transition_id'):
            transition = record.workflow_pending_transition_id
            record.workflow_pending_transition_id = False
            record._log_transition(transition, record.workflow_current_state_id, 'rejected', tier_review.review_comment)