# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AkWorkflowMixin(models.AbstractModel):
    _name = 'ak.workflow.mixin'
    _description = 'Workflow Integration Mixin'

    # Workflow Definition
    workflow_definition_id = fields.Many2one(
        'ak.workflow.definition',
        string='Workflow',
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

    transition_history_ids = fields.One2many(
        'ak.workflow.transition.history',
        'res_id',
        string='Transition History',
        compute='_compute_transition_history_ids',
        readonly=True
    )

    def _compute_transition_history_ids(self):
        for record in self:
            record.transition_history_ids = self.env['ak.workflow.transition.history'].search([
                ('res_model', '=', record._name),
                ('res_id', '=', record.id)
            ])

    @api.depends('workflow_current_state_id')
    def _compute_available_transitions(self):
        _logger.info("--- Starting _compute_available_transitions ---")
        for record in self:
            _logger.info(f"Processing record: {record.display_name} (ID: {record.id})")
            if not record.workflow_current_state_id:
                _logger.warning(f"Record {record.id} has no current workflow state. Setting transitions to empty.")
                record.workflow_available_transition_ids = []
                continue
            
            _logger.info(f"Current state for record {record.id} is: '{record.workflow_current_state_id.name}' (ID: {record.workflow_current_state_id.id})")
            
            all_transitions = record.workflow_current_state_id.outgoing_transition_ids
            _logger.info(f"Found {len(all_transitions)} outgoing transitions from this state: {[t.name for t in all_transitions]}")

            available_transitions = self.env['ak.workflow.transition']
            
            for transition in all_transitions.filtered('active'):
                _logger.debug(f"Checking transition '{transition.name}' (ID: {transition.id})")
                
                # Check user groups
                if transition.group_ids and not any(group in self.env.user.groups_id for group in transition.group_ids):
                    _logger.debug(f"Skipping transition '{transition.name}' due to group restrictions. User groups: {[g.name for g in self.env.user.groups_id]}")
                    continue
                
                # Check custom conditions
                if transition.check_transition_conditions(record):
                    _logger.info(f"Transition '{transition.name}' is available for record {record.id}.")
                    available_transitions |= transition
                else:
                    _logger.debug(f"Skipping transition '{transition.name}' because its conditions are not met.")
            
            _logger.info(f"Final available transitions for record {record.id}: {[t.name for t in available_transitions]}")
            record.workflow_available_transition_ids = available_transitions
        _logger.info("--- Finished _compute_available_transitions ---")

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
        domain = [('model_name', '=', self._name), ('active', '=', True)]
        return self.env['ak.workflow.definition'].search(domain, limit=1)

    def execute_transition(self, transition_id, comment=None):
        self.ensure_one()
        transition = self.env['ak.workflow.transition'].browse(transition_id)

        if transition not in self.workflow_available_transition_ids:
            raise UserError(_("This transition is not available for the current state or user."))

        self._perform_transition(transition, comment)
        return True

    def _perform_transition(self, transition, comment=None):
        self.ensure_one()
        if not transition:
            raise UserError(_("Cannot perform transition: No transition provided"))
        
        if not transition.to_state_id:
            raise UserError(_("Cannot perform transition: Destination state is not defined"))
        
        old_state = self.workflow_current_state_id
        if not old_state:
            raise UserError(_("Cannot perform transition: Record has no current state"))
        
        # Log the transition start
        _logger.info(f"Starting transition '{transition.name}' for {self._name} (ID: {self.id})")
        _logger.info(f"From state: {old_state.name} ({old_state.code}) to {transition.to_state_id.name} ({transition.to_state_id.code})")
        
        try:
            # Execute exit actions for the old state
            self._execute_state_actions('exit', state=old_state)
            
            # Update the state
            self.workflow_current_state_id = transition.to_state_id
            
            # Log the transition
            self._log_transition(transition, old_state, 'completed', comment)
            
            # Execute entry actions for the new state
            self._execute_state_actions('entry')
            
            # Execute transition actions
            for action in transition.action_ids:
                try:
                    action.execute_action(self)
                except Exception as e:
                    _logger.error(f"Error executing action {action.name} during transition: {str(e)}")
                    # Continue with other actions even if one fails
            
            _logger.info(f"Transition '{transition.name}' completed successfully")
            
        except Exception as e:
            _logger.error(f"Error during transition '{transition.name}': {str(e)}")
            # Log the failed transition
            self._log_transition(transition, old_state, 'failed', f"Error: {str(e)}")
            # Re-raise the exception
            raise UserError(_("Error during workflow transition: %s") % str(e))

    def _execute_state_actions(self, trigger_event, state=None):
        state_to_process = state or self.workflow_current_state_id
        if not state_to_process:
            return
        
        actions = state_to_process.entry_action_ids if trigger_event == 'entry' else state_to_process.exit_action_ids
        for action in actions.filtered(lambda a: a.trigger_event == trigger_event):
            action.execute_action(self)

    def _log_transition(self, transition, old_state, status, comment=None):
        # Create transition history record
        history = self.env['ak.workflow.transition.history'].sudo().create({
            'res_model': self._name,
            'res_id': self.id,
            'from_state_id': old_state.id,
            'to_state_id': transition.to_state_id.id,
            'transition_id': transition.id,
            'status': status,  # Add status field to track success/failure
            'comment': comment,
        })
        
        # Post message in chatter
        message = ""
        if status == 'completed':
            message = _("Workflow transition: %s → %s") % (old_state.name, transition.to_state_id.name)
        elif status == 'failed':
            message = _("Failed workflow transition: %s → %s") % (old_state.name, transition.to_state_id.name)
        
        if comment:
            message += "<br/>" + comment
            
        if message:
            self.message_post(body=message, subtype_xmlid='mail.mt_note')
            
        return history

    def get_available_transitions(self):
        if not self:
            return []
        self.ensure_one()
        self._compute_available_transitions()
        transitions = []
        for transition in self.workflow_available_transition_ids:
            transitions.append({
                'id': transition.id,
                'name': transition.button_label or transition.name,
                'button_class': transition.button_class,
            })
        return transitions


