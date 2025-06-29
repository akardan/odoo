# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class TierDefinition(models.Model):
    _inherit = 'tier.definition'
    
    # --- AK Workflow Fields ---
    is_workflow = fields.Boolean(
        'Is a Full Workflow?',
        default=False,
        help="Check this to enable states, transitions, and advanced workflow features."
    )
    code = fields.Char('Workflow Code', help="Unique technical identifier for the workflow")
    category = fields.Selection([
        ('approval', 'Approval Process'),
        ('procurement', 'Procurement Process'),
        ('tender', 'Tender Process'),
        ('validation', 'Validation Process'),
        ('business_process', 'Business Process'),
        ('custom', 'Custom Workflow')
    ], string='Category', default='business_process')

    # Workflow Structure
    state_ids = fields.One2many('ak.workflow.state', 'workflow_id', string='Workflow States')
    transition_ids = fields.One2many('ak.workflow.transition', 'workflow_id', string='Workflow Transitions')
    initial_state_id = fields.Many2one(
        'ak.workflow.state', 'Initial State',
        domain="[('workflow_id', '=', id), ('is_initial', '=', True)]"
    )

    # Enhanced Conditions for Tier Rules
    workflow_condition_type = fields.Selection([
        ('none', 'No Condition'),
        ('state', 'Current State'),
        ('field_value', 'Field Value'),
        ('python_expression', 'Python Expression'),
    ], string='Workflow Condition', default='none', help="Apply this tier rule only if this condition is met.")
    
    workflow_condition_state_id = fields.Many2one('ak.workflow.state', 'Required State', domain="[('workflow_id.model_id', '=', model_id)]")
    workflow_condition_field_id = fields.Many2one('ir.model.fields', 'Field', domain="[('model_id', '=', model_id)]")
    workflow_condition_operator = fields.Selection([
        ('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')
    ], string='Operator', default='=')
    workflow_condition_value = fields.Char('Value')
    workflow_condition_expression = fields.Text('Python Expression')

    # Notification Enhancements
    custom_notification_template_id = fields.Many2one('mail.template', 'Custom Notification Template')
    
    # Timing
    approval_timeout_days = fields.Integer('Approval Timeout (Days)', default=7)
    
    @api.model
    def _get_tier_validation_model_names(self):
        """Extend to include all models that have the workflow mixin."""
        res = super()._get_tier_validation_model_names()
        workflow_models = []
        for model_name, model in self.env.items():
            if isinstance(model, self.pool['ak.workflow.mixin']):
                workflow_models.append(model_name)
        
        for model_name in workflow_models:
            if model_name not in res:
                res.append(model_name)
        return res

    def _evaluate_tier(self, record):
        """Enhanced tier evaluation with workflow conditions."""
        res = super()._evaluate_tier(record)
        if not res:
            return False
        
        return self._check_workflow_conditions(record)

    def _check_workflow_conditions(self, record):
        """Check workflow-specific conditions for applying a tier rule."""
        self.ensure_one()
        if self.workflow_condition_type == 'none':
            return True
        
        elif self.workflow_condition_type == 'state':
            if hasattr(record, 'workflow_current_state_id'):
                return record.workflow_current_state_id == self.workflow_condition_state_id
        
        elif self.workflow_condition_type == 'field_value':
            if self.workflow_condition_field_id and hasattr(record, self.workflow_condition_field_id.name):
                field_value = record[self.workflow_condition_field_id.name]
                expected_value = self.workflow_condition_value
                op = self.workflow_condition_operator
                
                # Basic type casting for comparison
                try:
                    if self.workflow_condition_field_id.ttype in ['integer', 'float', 'monetary']:
                        expected_value = float(expected_value)
                except (ValueError, TypeError):
                    return False

                if op == '=': return field_value == expected_value
                if op == '!=': return field_value != expected_value
                if op == '>': return field_value > expected_value
                if op == '>=': return field_value >= expected_value
                if op == '<': return field_value < expected_value
                if op == '<=': return field_value <= expected_value
        
        elif self.workflow_condition_type == 'python_expression':
            if self.workflow_condition_expression:
                try:
                    eval_context = {'record': record, 'env': self.env, 'user': self.env.user}
                    return bool(eval(self.workflow_condition_expression, eval_context))
                except Exception as e:
                    _logger.error(f"Tier condition evaluation failed for '{self.name}': {e}")
                    return False
        
        return True
    def action_validate_workflow(self):
        """
        Placeholder method for the 'Validate Workflow' button.
        This method can be implemented to check the consistency and
        correctness of the defined workflow states and transitions.
        """
        self.ensure_one()
        _logger.info(f"Workflow validation called for '{self.name}'.")
        # TODO: Implement workflow validation logic here.
        # e.g., check for unique initial state, reachable final states, etc.
        return True