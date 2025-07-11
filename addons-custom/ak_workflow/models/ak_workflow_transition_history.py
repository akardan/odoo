# -*- coding: utf-8 -*-
from odoo import models, fields

class AkWorkflowTransitionHistory(models.Model):
    _name = 'ak.workflow.transition.history'
    _description = 'Workflow Transition History'
    _order = 'create_date desc'

    res_model = fields.Char('Related Document Model', readonly=True, required=True)
    res_id = fields.Many2oneReference('Related Document ID', model_field='res_model', readonly=True, required=True)
    from_state_id = fields.Many2one('ak.workflow.state', string='From State', required=True)
    to_state_id = fields.Many2one('ak.workflow.state', string='To State', required=True)
    transition_id = fields.Many2one('ak.workflow.transition', string='Transition', required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    comment = fields.Text(string='Comment')