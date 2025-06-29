# -*- coding: utf-8 -*-
from odoo import models, fields, tools

class WorkflowAnalytics(models.Model):
    _name = 'ak.workflow.analytics'
    _description = 'Workflow Analytics and Reporting'
    _auto = False
    _rec_name = 'workflow_name'

    # Dimensions
    workflow_id = fields.Many2one('tier.definition', 'Workflow', readonly=True)
    workflow_name = fields.Char('Workflow Name', readonly=True)
    state_id = fields.Many2one('ak.workflow.state', 'State', readonly=True)
    state_name = fields.Char('State Name', readonly=True)
    model_name = fields.Char('Model', readonly=True)
    
    # Measures
    instance_count = fields.Integer('Instance Count', readonly=True)
    active_instances = fields.Integer('Active Instances', readonly=True)
    completed_count = fields.Integer('Completed Instances', readonly=True)
    avg_duration_days = fields.Float('Avg. Completion (Days)', readonly=True, group_operator="avg")

    def init(self):
        """Create the database view"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ws.id as id,
                    wd.id AS workflow_id,
                    wd.name AS workflow_name,
                    ws.id AS state_id,
                    ws.name AS state_name,
                    wd.model_name,
                    0 AS instance_count,
                    0 AS active_instances,
                    0 AS completed_count,
                    0.0 AS avg_duration_days
                FROM
                    ak_workflow_state ws
                JOIN
                    tier_definition wd ON ws.workflow_id = wd.id
                WHERE
                    wd.is_workflow = true
            )
        """)