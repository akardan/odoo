# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AkWorkflowDefinition(models.Model):
    _name = 'ak.workflow.definition'
    _description = 'Workflow Definition'

    name = fields.Char(string='Name', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', string='Model Name', store=True)
    active = fields.Boolean(string='Active', default=True)
    initial_state_id = fields.Many2one('ak.workflow.state', string='Initial State',
                                       domain="[('workflow_id', '=', id)]")
    state_ids = fields.One2many('ak.workflow.state', 'workflow_id', string='States')
    transition_ids = fields.One2many('ak.workflow.transition', 'workflow_id', string='Transitions')
    dynamic_parameter_ids = fields.Many2many('ak.workflow.dynamic.parameter', 'ak_workflow_definition_dynamic_parameter_rel',
                                             'workflow_definition_id', 'dynamic_parameter_id', string='Dynamic Parameters')

    def copy(self, default=None):
        """Override copy to duplicate all child records (states, transitions, actions, etc.)"""
        self.ensure_one()
        
        if default is None:
            default = {}
        
        # Set new name for the copy
        if 'name' not in default:
            default['name'] = _("%s (Copy)", self.name)
        
        # Create the new workflow definition without states and transitions
        new_workflow = super(AkWorkflowDefinition, self).copy(default)
        
        # Map old state IDs to new state IDs
        state_mapping = {}
        
        # Copy all states
        for old_state in self.state_ids:
            # Prepare state copy data
            state_default = {
                'workflow_id': new_workflow.id,
            }
            
            # Copy the state
            new_state = old_state.copy(state_default)
            state_mapping[old_state.id] = new_state.id
            
            # Copy entry actions for this state
            for action in old_state.entry_action_ids:
                action.copy({
                    'trigger_state_id': new_state.id,
                    'workflow_id': new_workflow.id,
                })
            
            # Copy exit actions for this state
            for action in old_state.exit_action_ids:
                action.copy({
                    'trigger_state_id': new_state.id,
                    'workflow_id': new_workflow.id,
                })
        
        # Map old transition IDs to new transition IDs (needed for stages)
        transition_mapping = {}
        
        # Copy all transitions with updated state references
        for old_transition in self.transition_ids:
            # Get new from_state and to_state IDs
            new_from_state_id = state_mapping.get(old_transition.from_state_id.id)
            new_to_state_id = state_mapping.get(old_transition.to_state_id.id)
            
            if not new_from_state_id or not new_to_state_id:
                continue  # Skip if states weren't copied
            
            # Prepare transition copy data
            transition_default = {
                'workflow_id': new_workflow.id,
                'from_state_id': new_from_state_id,
                'to_state_id': new_to_state_id,
            }
            
            # Copy the transition (without stages and actions)
            new_transition = old_transition.copy(transition_default)
            transition_mapping[old_transition.id] = new_transition.id
            
            # Copy stages for this transition
            for old_stage in old_transition.stage_ids:
                new_stage = old_stage.copy({
                    'transition_id': new_transition.id,
                })
                
                # Copy stage-specific actions
                for action in old_stage.action_ids:
                    action.copy({
                        'transition_id': new_transition.id,
                        'stage_id': new_stage.id,
                        'workflow_id': new_workflow.id,
                    })
            
            # Copy transition actions (not stage-specific)
            for action in old_transition.action_ids.filtered(lambda a: not a.stage_id):
                action.copy({
                    'transition_id': new_transition.id,
                    'workflow_id': new_workflow.id,
                })
        
        # Update initial_state_id to point to the new state
        if self.initial_state_id and self.initial_state_id.id in state_mapping:
            new_workflow.write({
                'initial_state_id': state_mapping[self.initial_state_id.id]
            })
        
        # Many2many fields (dynamic_parameter_ids) are automatically copied by default copy behavior
        
        return new_workflow
