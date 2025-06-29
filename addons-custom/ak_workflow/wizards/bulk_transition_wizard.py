# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BulkTransitionWizard(models.TransientModel):
    _name = 'ak.workflow.bulk.transition.wizard'
    _description = 'Bulk Workflow Transition Wizard'

    transition_id = fields.Many2one(
        'ak.workflow.transition',
        string='Transition',
        required=True
    )
    record_ids = fields.Many2many(
        comodel_name='ak.workflow.mixin', # This is a placeholder, will be set from context
        string='Records'
    )
    comment = fields.Text(string='Comment')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') and self.env.context.get('active_ids'):
            model_name = self.env.context['active_model']
            active_ids = self.env.context['active_ids']
            records = self.env[model_name].browse(active_ids)
            
            # Check if all records share a common available transition
            common_transitions = records[0].workflow_available_transition_ids
            for rec in records[1:]:
                common_transitions &= rec.workflow_available_transition_ids
            
            if not common_transitions:
                raise UserError(_("The selected records do not have any common available transitions."))
            
            # For simplicity, we can pre-select the first common transition
            if 'transition_id' in fields_list and common_transitions:
                res['transition_id'] = common_transitions[0].id

        return res

    def action_apply_transition(self):
        self.ensure_one()
        model_name = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids')
        records = self.env[model_name].browse(active_ids)

        for record in records:
            if self.transition_id in record.workflow_available_transition_ids:
                try:
                    # We can't easily pass comments to the execute_transition method as designed
                    # This would require a modification to the mixin or a different approach
                    record.execute_transition(self.transition_id.id)
                except Exception as e:
                    _logger.error(f"Error during bulk transition for record {record.id}: {e}")
        
        return {'type': 'ir.actions.act_window_close'}