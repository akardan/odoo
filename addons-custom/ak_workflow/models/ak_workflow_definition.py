# -*- coding: utf-8 -*-
from odoo import models, fields, api

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
