# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class AkWorkflowTransitionHistory(models.Model):
    _name = 'ak.workflow.transition.history'
    _description = 'Workflow Transition History'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    res_model = fields.Char('Related Document Model', readonly=True, required=True)
    res_id = fields.Many2oneReference('Related Document ID', model_field='res_model', readonly=True, required=True)
    from_state_id = fields.Many2one('ak.workflow.state', string='From State', required=True)
    to_state_id = fields.Many2one('ak.workflow.state', string='To State', required=True)
    transition_id = fields.Many2one('ak.workflow.transition', string='Transition', required=True)
    stage_id = fields.Many2one('ak.workflow.transition.stage', string='Aşama',
                               help="Geçiş aşaması, eğer varsa")
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string='Status', default='completed', required=True, index=True,
       help="Status of the transition execution")
    comment = fields.Text(string='Comment')
    elapsed_time = fields.Float(
        string='Elapsed Time (Hours)',
        compute='_compute_elapsed_time',
        store=True,
        help="Time elapsed in this state/stage in hours. Calculated when transitioning to next state or as current time if still active."
    )
    elapsed_time_display = fields.Char(
        string='Geçen Süre',
        compute='_compute_elapsed_time_display',
        store=True,
        help="Geçen süre dd:hh:mm formatında"
    )
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    @api.depends('create_date', 'res_model', 'res_id')
    def _compute_elapsed_time(self):
        """
        Calculate elapsed time for each history record.
        If there's a next transition, use that time. Otherwise, use current time.
        """
        for history in self:
            if not history.create_date:
                history.elapsed_time = 0.0
                continue
            
            # Find the next transition for the same record
            next_history = self.search([
                ('res_model', '=', history.res_model),
                ('res_id', '=', history.res_id),
                ('create_date', '>', history.create_date),
            ], order='create_date asc', limit=1)
            
            if next_history:
                # Calculate time until next transition
                end_time = next_history.create_date
            else:
                # No next transition, use current time
                end_time = fields.Datetime.now()
            
            # Calculate elapsed time in hours
            time_diff = end_time - history.create_date
            history.elapsed_time = time_diff.total_seconds() / 3600.0
    
    @api.depends('elapsed_time')
    def _compute_elapsed_time_display(self):
        """
        Format elapsed time as dd:hh:mm
        """
        for history in self:
            if not history.elapsed_time:
                history.elapsed_time_display = "00:00:00"
                continue
            
            total_hours = history.elapsed_time
            days = int(total_hours // 24)
            hours = int(total_hours % 24)
            minutes = int((total_hours * 60) % 60)
            
            history.elapsed_time_display = f"{days:02d}:{hours:02d}:{minutes:02d}"
    
    @api.depends('transition_id.name', 'stage_id.name', 'status', 'create_date')
    def _compute_display_name(self):
        for history in self:
            status_icon = {'pending': '⏳', 'completed': '✅', 'failed': '❌'}.get(history.status, '')
            if history.stage_id:
                history.display_name = f"{status_icon} {history.transition_id.name} - {history.stage_id.name}"
            else:
                history.display_name = f"{status_icon} {history.transition_id.name}"