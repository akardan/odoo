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
    actions_info = fields.Html(string="Actions to Execute", compute='_compute_actions_info')

    @api.depends('transition_id')
    def _compute_transition_display_info(self):
        for wizard in self:
            if wizard.transition_id:
                wizard.transition_display_info = f"{wizard.transition_id.from_state_id.name} → {wizard.transition_id.to_state_id.name}"
            else:
                wizard.transition_display_info = ''
    
    @api.depends('transition_id', 'res_model', 'res_id')
    def _compute_actions_info(self):
        for wizard in self:
            html_parts = []
            
            # Stage bilgisi
            if wizard.transition_id and wizard.transition_id.has_stages:
                record = self.env[wizard.res_model].browse(wizard.res_id) if wizard.res_model and wizard.res_id else None
                if record:
                    next_stage = wizard.transition_id.get_next_pending_stage(record)
                    if next_stage:
                        # Mevcut stage'in sırasını bul (kaçıncı stage)
                        all_stages = wizard.transition_id.stage_ids.sorted('sequence')
                        current_stage_index = 0
                        for idx, stage in enumerate(all_stages, 1):
                            if stage.id == next_stage.id:
                                current_stage_index = idx
                                break
                        
                        # Bir sonraki stage'i bul (varsa)
                        next_stage_info = ""
                        if current_stage_index < len(all_stages):
                            next_stage_obj = all_stages[current_stage_index]  # Index 0-based, current_stage_index 1-based
                            next_stage_info = f"<br/>Next Stage: <strong>{next_stage_obj.name}</strong>"
                        
                        html_parts.append(f'''
                            <div class="alert alert-info">
                                <strong>📋 Multi-Stage Approval</strong><br/>
                                Stage: <strong>{current_stage_index}/{len(all_stages)}</strong><br/>
                                Current Stage: <strong>{next_stage.name}</strong>
                                {next_stage_info}
                            </div>
                        ''')
                        
                        # Stage aksiyonları
                        if next_stage.action_ids:
                            html_parts.append('<p><strong>Stage Actions:</strong></p>')
                            html_parts.append('<ol class="list-group list-group-numbered">')
                            for action in next_stage.action_ids.sorted(key=lambda r: (r.sequence, r.name)):
                                html_parts.append(f'<li class="list-group-item">{action.name}</li>')
                            html_parts.append('</ol>')
                    else:
                        html_parts.append('<div class="alert alert-warning">All stages completed. State will change.</div>')
            
            # Ana transition aksiyonları
            if wizard.transition_id and wizard.transition_id.action_ids:
                if html_parts:  # Eğer stage bilgisi varsa
                    html_parts.append('<p><strong>Final Transition Actions:</strong></p>')
                html_parts.append('<ol class="list-group list-group-numbered">')
                for action in wizard.transition_id.action_ids.sorted(key=lambda r: (r.sequence, r.name)):
                    html_parts.append(f'<li class="list-group-item">{action.name}</li>')
                html_parts.append('</ol>')
            
            if not html_parts:
                wizard.actions_info = '<p>No actions will be executed.</p>'
            else:
                wizard.actions_info = ''.join(html_parts)

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