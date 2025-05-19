from odoo import api, fields, models
from datetime import date
from odoo.exceptions import ValidationError

class ProjectVersion(models.Model):    
    _name = "project.version"
    _description = 'Project version'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, id"

    name = fields.Char(string="Name", required=True, tracking=True, size=30)
    description = fields.Text(string="Description")
    start_date = fields.Date(string="Start Date", tracking=True)
    release_date = fields.Date(string="Release Date", tracking=True)
    is_released = fields.Boolean(compute="_compute_is_released", store=True)
    project_id = fields.Many2one(comodel_name="project.project", string="Project")
    active = fields.Boolean(default=True)

    task_ids = fields.One2many("project.task", "version_id", string="Tasks")
    task_count = fields.Integer(compute="_compute_task_count")

    is_released_text = fields.Char(compute="_compute_is_release_text")

    checklist_progress = fields.Float(store=True, compute="_compute_checklist_progress")

    @api.depends("release_date")
    def _compute_is_released(self):
        for record in self:            
            record.is_released = True if record.release_date else False

    @api.depends("release_date")
    def _compute_is_release_text(self):
        for record in self:            
            record.is_released_text = 'Released' if record.release_date else ''

    @api.depends("task_ids")
    def _compute_task_count(self):
        for record in self:
            record.task_count = len(record.task_ids)            

    def action_version_release(self):
        for record in self:
            if len(record.task_ids) > 0 and len(record.task_ids.search([('stage_id.name', '=', 'Done')])) > 0:
                record.release_date = date.today()      
            else:    
                raise ValidationError("At least one task has to be completed")

    @api.depends("task_ids.stage_id", "task_ids")
    def _compute_checklist_progress(self):        
        for task in self:
            total_items = len(task.task_ids)
            if total_items > 0:
                completed_items = task.task_ids.filtered(
                    lambda item: item.stage_id.name.lower() == "done"
                )
                progress = (len(completed_items) / total_items) * 100
                task.checklist_progress = progress
            else:
                task.checklist_progress = 0.0

    def action_unrelease(self):
        for record in self:
            record.release_date = False