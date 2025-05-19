from odoo import models, fields, _

class ProjectTaskSprintHistory(models.Model):
    _name = 'project.task.sprint.history'
    _description = _('Task Sprint History')
    _rec_name = 'sprint_id'

    task_id = fields.Many2one('project.task', string=_('Task'), required=True, ondelete='cascade')
    sprint_id = fields.Many2one('project.sprint', string=_('Sprint'), required=True, ondelete='cascade')
    date_added = fields.Datetime(string=_('Date Added'), default=fields.Datetime.now)
