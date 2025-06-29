# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64
import json
from odoo.exceptions import UserError

class WorkflowImportWizard(models.TransientModel):
    _name = 'ak.workflow.import.wizard'
    _description = 'Workflow Import/Export Wizard'

    workflow_data = fields.Binary(string='Workflow File', required=True)
    file_name = fields.Char(string='File Name')

    def action_import_workflow(self):
        self.ensure_one()
        if not self.workflow_data:
            raise UserError(_("Please upload a file."))
        
        try:
            data = json.loads(base64.b64decode(self.workflow_data).decode('utf-8'))
        except Exception as e:
            raise UserError(_("Invalid file format. Please upload a valid JSON file. Error: %s") % e)

        workflow_vals = data.get('workflow', {})
        if not workflow_vals:
            raise UserError(_("The JSON file does not contain workflow data."))

        model_name = workflow_vals.get('model_name')
        model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            raise UserError(_("The target model '%s' does not exist in this database.") % model_name)

        workflow_vals['model_id'] = model.id
        
        # Create workflow
        workflow = self.env['tier.definition'].create(workflow_vals)
        
        # Create states
        state_mapping = {}
        for state_val in data.get('states', []):
            state_val['workflow_id'] = workflow.id
            state = self.env['ak.workflow.state'].create(state_val)
            state_mapping[state.code] = state.id
            if state.is_initial:
                workflow.initial_state_id = state.id

        # Create transitions
        for trans_val in data.get('transitions', []):
            trans_val['workflow_id'] = workflow.id
            from_state_code = trans_val.pop('from_state_code', None)
            to_state_code = trans_val.pop('to_state_code', None)
            trans_val['from_state_id'] = state_mapping.get(from_state_code)
            trans_val['to_state_id'] = state_mapping.get(to_state_code)
            self.env['ak.workflow.transition'].create(trans_val)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tier.definition',
            'view_mode': 'form',
            'res_id': workflow.id,
            'target': 'current',
        }