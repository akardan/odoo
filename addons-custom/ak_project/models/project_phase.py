from odoo import fields, models


class ProjectPhase(models.Model):
    _name = 'project.phase'
    _description = "Project Phase"

    name = fields.Char(string="Name", required=True)
    project_id = fields.Many2one('project.project', "Project")
    sequence = fields.Integer(string="Sequence")
    internal_notes = fields.Html()

    task_count = fields.Integer(compute="_compute_task_count")

    def _compute_task_count(self):
        for rec in self:
            rec.task_count = self.env['project.task'].search_count([('phase_id', '=', rec.id)])
            


    def get_project_tasks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('phase_id', '=', self.id)],
        }






