# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class AkWorkflowTransition(models.Model):
    _name = 'ak.workflow.transition'
    _description = 'Workflow Transition Definition'
    _order = 'workflow_id, from_state_id, sequence'
    _rec_name = 'display_name'

    # Basic Info
    name = fields.Char('Transition Name', required=True, translate=True)
    code = fields.Char('Transition Code', help="Technical identifier")
    description = fields.Text('Description', translate=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    # Workflow and States
    workflow_id = fields.Many2one(
        'tier.definition', 'Workflow',
        required=True, ondelete='cascade',
        domain="[('is_workflow', '=', True)]"
    )
    from_state_id = fields.Many2one(
        'ak.workflow.state', 'From State',
        required=True, ondelete='cascade',
        domain="[('workflow_id', '=', workflow_id)]"
    )
    to_state_id = fields.Many2one(
        'ak.workflow.state', 'To State',
        required=True, ondelete='cascade',
        domain="[('workflow_id', '=', workflow_id)]"
    )
    
    # UI Configuration
    sequence = fields.Integer('Sequence', default=10)
    button_label = fields.Char('Button Label', translate=True,
                               help="Label shown on transition button")
    button_class = fields.Selection([
        ('btn-primary', 'Primary (Blue)'),
        ('btn-success', 'Success (Green)'),
        ('btn-warning', 'Warning (Yellow)'),
        ('btn-danger', 'Danger (Red)'),
        ('btn-info', 'Info (Cyan)'),
        ('btn-secondary', 'Secondary (Gray)')
    ], string='Button Style', default='btn-primary')
    icon = fields.Char('Icon', help="FontAwesome icon class", default="fa-arrow-right")
    
    # Security and Authorization
    group_ids = fields.Many2many(
        'res.groups', 'transition_groups_rel',
        string='Required Groups',
        help="Groups required to execute this transition"
    )
    
    # Conditions
    condition_type = fields.Selection([
        ('none', 'No Condition'),
        ('python', 'Python Expression'),
        ('field', 'Field Condition'),
        ('method', 'Model Method'),
        ('amount', 'Amount Threshold'),
    ], string='Condition Type', default='none')
    
    condition_expression = fields.Text('Python Expression',
                                       help="Python expression that must return True")
    condition_field_id = fields.Many2one(
        'ir.model.fields', 'Field',
        domain="[('model_id', '=', parent.workflow_id.model_id)]"
    )
    condition_operator = fields.Selection([
        ('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<='),
        ('in', 'in'), ('not in', 'not in'), ('set', 'is set'), ('not set', 'is not set')
    ], string='Operator', default='=')
    condition_value = fields.Text('Value')
    condition_method = fields.Char('Method Name')
    
    amount_threshold = fields.Float('Amount Threshold')
    amount_currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Tier Validation Integration
    require_tier_validation = fields.Boolean(
        'Require Tier Validation',
        help="Use OCA tier validation for this transition"
    )
    
    # Actions
    action_ids = fields.One2many('ak.workflow.action', 'transition_id',
                                 string='Transition Actions')
    
    # Notifications
    send_notification = fields.Boolean('Send Notification', default=True)
    notification_template_id = fields.Many2one(
        'mail.template', 'Notification Template',
        domain="[('model_id', '=', parent.workflow_id.model_id)]"
    )
    
    active = fields.Boolean('Active', default=True)
    
    @api.depends('name', 'from_state_id.name', 'to_state_id.name')
    def _compute_display_name(self):
        for transition in self:
            if transition.from_state_id and transition.to_state_id:
                transition.display_name = f"{transition.from_state_id.name} → {transition.to_state_id.name}"
            else:
                transition.display_name = transition.name or 'New Transition'
    
    @api.constrains('from_state_id', 'to_state_id')
    def _check_states_same_workflow(self):
        for transition in self:
            if (transition.from_state_id.workflow_id != transition.workflow_id or
                transition.to_state_id.workflow_id != transition.workflow_id):
                raise ValidationError(_(
                    'All states in transition must belong to the same workflow'
                ))

    def check_transition_conditions(self, record):
        # This method is now on the mixin for easier access
        return True