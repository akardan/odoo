# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class AkWorkflowState(models.Model):
    _name = 'ak.workflow.state'
    _description = 'Workflow State Definition'
    _order = 'workflow_id, sequence, name'
    _rec_name = 'name'

    # Basic Info
    name = fields.Char('State Name', required=True, translate=True)
    code = fields.Char('State Code', required=True, 
                       help="Technical identifier unique within workflow")
    description = fields.Text('Description', translate=True)
    display_name = fields.Char(compute='_compute_display_name')
    
    # Workflow Relation
    workflow_id = fields.Many2one('ak.workflow.definition', 'Workflow',
                                  required=True, ondelete='cascade')
    
    # State Properties
    sequence = fields.Integer('Sequence', default=10)
    is_initial = fields.Boolean('Initial State',
                                help="Workflow starts from this state")
    is_final = fields.Boolean('Final State',
                              help="Workflow ends at this state")
    
    # Behavior Configuration
    allow_edit = fields.Boolean('Allow Edit', default=True,
                                help="Records can be edited in this state")
    
    # UI Configuration
    color = fields.Integer('Color Index', default=0,
                           help="Color for kanban/calendar views (0-11)")
    icon = fields.Char('Icon', help="FontAwesome icon class",
                       default="fa-circle-o")
    
    # Security and Permissions
    edit_group_ids = fields.Many2many('res.groups', 'state_edit_groups_rel',
                                      string='Edit Groups',
                                      help="Groups that can edit records in this state")
    
    
    # Transitions
    outgoing_transition_ids = fields.One2many('ak.workflow.transition',
                                              'from_state_id',
                                              string='Outgoing Transitions')
    incoming_transition_ids = fields.One2many('ak.workflow.transition',
                                              'to_state_id',
                                              string='Incoming Transitions')
    
    # Actions
    entry_action_ids = fields.One2many('ak.workflow.action', 'trigger_state_id',
                                       string='Entry Actions',
                                       domain=[('trigger_event', '=', 'state_entry')])
    exit_action_ids = fields.One2many('ak.workflow.action', 'trigger_state_id',
                                      string='Exit Actions',
                                      domain=[('trigger_event', '=', 'state_exit')])
    
    def _compute_display_name(self):
        for state in self:
            state.display_name = state.name
    
    def name_get(self):
        return [(state.id, state.name) for state in self]
    @api.constrains('workflow_id', 'code')
    def _check_unique_code(self):
        """Ensure state code is unique within workflow"""
        for state in self:
            if state.code:
                domain = [
                    ('workflow_id', '=', state.workflow_id.id),
                    ('code', '=', state.code),
                    ('id', '!=', state.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_(
                        'State code "%s" already exists in workflow "%s"'
                    ) % (state.code, state.workflow_id.name))
    
    @api.constrains('workflow_id', 'is_initial')
    def _check_single_initial_state(self):
        """Ensure only one initial state per workflow"""
        for state in self:
            if state.is_initial:
                other_initials = self.search([
                    ('workflow_id', '=', state.workflow_id.id),
                    ('is_initial', '=', True),
                    ('id', '!=', state.id)
                ])
                if other_initials:
                    raise ValidationError(_(
                        'Workflow "%s" can have only one initial state'
                    ) % state.workflow_id.name)