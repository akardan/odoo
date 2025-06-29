# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json
import requests
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AkWorkflowAction(models.Model):
    _name = 'ak.workflow.action'
    _description = 'Workflow Action Definition'
    _order = 'sequence, name'

    # Basic Info
    name = fields.Char('Action Name', required=True, translate=True)
    description = fields.Text('Description', translate=True)
    
    # Trigger Configuration
    trigger_event = fields.Selection([
        ('state_entry', 'State Entry'),
        ('state_exit', 'State Exit'),
        ('transition', 'Transition'),
    ], string='Trigger Event', required=True)
    
    # Relations
    workflow_id = fields.Many2one(
        'tier.definition', 'Workflow',
        domain="[('is_workflow', '=', True)]"
    )
    trigger_state_id = fields.Many2one('ak.workflow.state', 'Trigger State')
    transition_id = fields.Many2one('ak.workflow.transition', 'Transition')
    
    # Action Configuration
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    
    action_type = fields.Selection([
        ('email', 'Send Email'),
        ('method', 'Execute Method'),
        ('field_update', 'Update Field'),
        ('create_record', 'Create Record'),
        ('webhook', 'Call Webhook'),
        ('notification', 'Send Notification'),
        ('activity', 'Create Activity'),
        ('server_action', 'Server Action'),
    ], string='Action Type', required=True)
    
    # Type-specific fields
    email_template_id = fields.Many2one('mail.template', 'Email Template')
    method_name = fields.Char('Method Name')
    field_id = fields.Many2one('ir.model.fields', 'Field to Update')
    field_value = fields.Text('Value (Python Expression)')
    create_model_id = fields.Many2one('ir.model', 'Model to Create')
    create_values = fields.Text('Values (Python Dictionary)')
    webhook_url = fields.Char('Webhook URL')
    webhook_method = fields.Selection([
        ('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH')
    ], default='POST')
    webhook_data_expression = fields.Text('Webhook Data (Python Expression)')
    notification_title = fields.Char('Notification Title')
    notification_message = fields.Text('Notification Message')
    notification_type = fields.Selection([
        ('info', 'Info'), ('success', 'Success'), ('warning', 'Warning'), ('danger', 'Error')
    ], default='info')
    activity_type_id = fields.Many2one('mail.activity.type', 'Activity Type')
    activity_summary = fields.Char('Activity Summary')
    activity_note = fields.Text('Activity Note')
    activity_user_id = fields.Many2one('res.users', 'Assign to User')
    server_action_id = fields.Many2one('ir.actions.server', 'Server Action')
    
    condition_expression = fields.Text('Condition (Python)',
                                       help="Python expression that must return True")
    
    continue_on_error = fields.Boolean('Continue on Error', default=True)

    def execute_action(self, record):
        self.ensure_one()
        
        if self.condition_expression and not self._check_condition(record):
            return False
        
        try:
            action_method = getattr(self, f'_execute_{self.action_type}_action', None)
            if action_method:
                return action_method(record)
        except Exception as e:
            _logger.error(f"Workflow action execution failed: {str(e)}")
            if not self.continue_on_error:
                raise UserError(_('Action "%s" failed: %s') % (self.name, str(e)))
            return False
        return True
    
    def _check_condition(self, record):
        if not self.condition_expression:
            return True
        try:
            eval_context = {'record': record, 'env': self.env, 'user': self.env.user}
            return bool(eval(self.condition_expression, eval_context))
        except Exception as e:
            _logger.error(f"Action condition evaluation failed: {str(e)}")
            return False

    def _get_eval_context(self, record):
        return {'record': record, 'env': self.env, 'user': self.env.user, 'datetime': datetime, 'timedelta': timedelta}

    def _execute_email_action(self, record):
        if self.email_template_id:
            self.email_template_id.send_mail(record.id, force_send=True)
        return True

    def _execute_method_action(self, record):
        if self.method_name and hasattr(record, self.method_name):
            getattr(record, self.method_name)()
        return True

    def _execute_field_update_action(self, record):
        if self.field_id and self.field_value:
            value = eval(self.field_value, self._get_eval_context(record))
            record.write({self.field_id.name: value})
        return True

    def _execute_create_record_action(self, record):
        if self.create_model_id and self.create_values:
            values = eval(self.create_values, self._get_eval_context(record))
            self.env[self.create_model_id.model].create(values)
        return True

    def _execute_webhook_action(self, record):
        if not self.webhook_url:
            return False
        data = eval(self.webhook_data_expression, self._get_eval_context(record)) if self.webhook_data_expression else {}
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.request(
                self.webhook_method, self.webhook_url,
                json=data, headers=headers, timeout=15
            )
            response.raise_for_status()
        except requests.RequestException as e:
            _logger.error(f"Webhook action failed: {str(e)}")
            return False
        return True

    def _execute_notification_action(self, record):
        record.message_post(
            body=self.notification_message or self.name,
            subject=self.notification_title or _("Workflow Notification"),
            message_type='notification'
        )
        return True

    def _execute_activity_action(self, record):
        if self.activity_type_id:
            assign_user = self.activity_user_id or self.env.user
            record.activity_schedule(
                activity_type_id=self.activity_type_id.id,
                summary=self.activity_summary or self.name,
                note=self.activity_note or '',
                user_id=assign_user.id
            )
        return True

    def _execute_server_action(self, record):
        if self.server_action_id:
            self.server_action_id.with_context(active_id=record.id, active_model=record._name).run()
        return True