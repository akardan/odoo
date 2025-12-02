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
    
    # Stored time fields for reporting performance
    end_time = fields.Datetime(
        string='End Time',
        help="The time when this state/stage ended (next transition time or current time if still active)",
        store=True,
        compute='_compute_end_time',
        readonly=True
    )
    expected_duration = fields.Float(
        string='Expected Duration (Hours)',
        help="Expected duration for this state/stage in hours (from state/stage definition)",
        compute='_compute_expected_duration',
        store=True,
        readonly=True
    )
    
    @api.depends('to_state_id', 'to_state_id.default_duration_days')
    def _compute_expected_duration(self):
        """
        Compute expected duration from state definition.
        Converts days to hours for consistency.
        """
        for history in self:
            if history.to_state_id and history.to_state_id.default_duration_days:
                # Convert days to hours
                history.expected_duration = history.to_state_id.default_duration_days * 24.0
            else:
                history.expected_duration = 0.0
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
    def _compute_end_time(self):
        """
        Calculate end time for each history record.
        End time is only set when there's a next transition.
        If still in the same state, end_time remains empty.
        """
        for history in self:
            if not history.create_date:
                history.end_time = False
                continue
            
            # Find the next transition for the same record
            next_history = self.search([
                ('res_model', '=', history.res_model),
                ('res_id', '=', history.res_id),
                ('create_date', '>', history.create_date),
            ], order='create_date asc', limit=1)
            
            if next_history:
                # Use next transition time as end time
                history.end_time = next_history.create_date
            else:
                # No next transition yet, end_time stays empty
                history.end_time = False
    
    @api.depends('create_date', 'end_time')
    def _compute_elapsed_time(self):
        """
        Calculate elapsed time for each history record.
        Uses stored end_time if available, otherwise uses current time for active states.
        """
        for history in self:
            if not history.create_date:
                history.elapsed_time = 0.0
                continue
            
            # Use end_time if set, otherwise use current time for active states
            end_time = history.end_time or fields.Datetime.now()
            
            # Calculate elapsed time in hours, ensure it's not negative
            time_diff = end_time - history.create_date
            elapsed_seconds = time_diff.total_seconds()
            history.elapsed_time = max(0.0, elapsed_seconds / 3600.0)
    
    @api.depends('elapsed_time')
    def _compute_elapsed_time_display(self):
        """
        Format elapsed time as dd:hh:mm
        """
        for history in self:
            if not history.elapsed_time or history.elapsed_time < 0:
                history.elapsed_time_display = "00:00:00"
                continue
            
            # Use absolute value to prevent negative display
            total_hours = abs(history.elapsed_time)
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