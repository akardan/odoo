# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class WorkflowTransitionWizard(models.TransientModel):
    _name = 'ak.workflow.transition.wizard'
    _description = 'Workflow Transition Execution Wizard'

    # Bu sihirbazın hangi kaydı etkileyeceğini bilmesi gerekiyor.
    res_model = fields.Char('Model', readonly=True, required=True)
    res_id = fields.Integer('Record ID', readonly=True, required=True)
    
    # Hangi geçişin çalıştırılacağını tutar.
    transition_id = fields.Many2one('ak.workflow.transition', string='Transition', readonly=True, required=True)
    comment = fields.Text(string='Comment')
    transition_display_info = fields.Char(string="Transition Info", compute='_compute_transition_display_info')

    @api.depends('transition_id')
    def _compute_transition_display_info(self):
        for wizard in self:
            if wizard.transition_id:
                wizard.transition_display_info = f"{wizard.transition_id.from_state_id.name} → {wizard.transition_id.to_state_id.name}"
            else:
                wizard.transition_display_info = ''

    @api.model
    def default_get(self, fields_list):
        # Butona tıklandığında context'ten gelen bilgileri alır.
        res = super(WorkflowTransitionWizard, self).default_get(fields_list)
        active_model = self.env.context.get('active_model') or self.env.context.get('default_active_model')
        active_id = self.env.context.get('active_id') or self.env.context.get('default_active_id')
        if active_model and active_id:
            res.update({
                'res_model': active_model,
                'res_id': active_id,
            })
        if self.env.context.get('default_transition_id'):
            res['transition_id'] = self.env.context['default_transition_id']
        return res

    def execute_transition(self):
        # Asıl işi yapan metod.
        self.ensure_one()
        # İlgili kaydı model ve ID'sinden bulur.
        record = self.env[self.res_model].browse(self.res_id)
        # Kaydın kendi üzerindeki execute_transition metodunu çağırır.
        record.execute_transition(self.transition_id.id, self.comment)
        return {'type': 'ir.actions.act_window_close'}