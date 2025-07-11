# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WorkflowDesignerWizard(models.TransientModel):
    _name = 'ak.workflow.designer.wizard'
    _description = 'Workflow Designer Wizard'

    workflow_id = fields.Many2one(
        'ak.workflow.definition',
        string='Workflow',
        required=True,
        readonly=True
    )
    
    # The actual designer will be implemented using a JS widget.
    # This wizard is mainly a container to launch it.
    
    def action_save_workflow(self):
        """
        This method will be called from the JS designer to save the layout
        and potentially create/update states and transitions.
        """
        # The data will be passed in the context from the JS widget
        return {'type': 'ir.actions.act_window_close'}