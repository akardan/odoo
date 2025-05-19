from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectSprint(models.Model):
    _name = 'project.sprint'
    _description = _('Project Sprints')
    _order = 'sequence, name'
    _rec_name = "display_name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=0)
    start_date = fields.Date(string=_('Start Date'))
    end_date = fields.Date(string=_('End Date'))
    state = fields.Selection([('planned', _('Planned')), ('active', _('Active')), ('closed', _('Closed'))],
                             string=_('Status'),
                             default='planned')
    team_id = fields.Many2one('crm.team', string=_('Team'))
    board_id = fields.Many2one('project.board', string=_('Board'))
    task_ids = fields.One2many('project.task', inverse_name='sprint_id', string=_('Sprint Tasks'))
    is_active = fields.Boolean(string="Is Active?", compute='_compute_is_active')
    display_name = fields.Char(string="Display Name", compute='_compute_display_name')

    @api.constrains('state')
    def _check_backlog_sprint(self):
        for sprint in self:
            if sprint.sequence == 0 and sprint.state != 'planned':
                raise ValidationError(_("Backlog sprint should be Planned Status."))

    @api.depends('state')
    def _compute_is_active(self):
        for record in self:
            record.is_active = True if record.state == 'active' else False

    @api.depends('name', 'start_date', 'end_date')
    def _compute_display_name(self):
        for record in self:
            display_name = '%s' % (record.name)
            if record.start_date and record.end_date:
                display_name += ' (%s-%s / %s-%s)' % (
                                record.start_date.day, record.start_date.month,
                                record.end_date.day, record.end_date.month )
            record.display_name = display_name
