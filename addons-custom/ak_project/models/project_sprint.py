from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectSprint(models.Model):
    _name = 'project.sprint'
    _description = _('Project Sprints')
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=0)
    start_date = fields.Date(string=_('Start Date'))
    end_date = fields.Date(string=_('End Date'))
    state = fields.Selection([
        ('planned', _('Planned')),
        ('active', _('Active')),
        ('closed', _('Closed'))
    ], string=_('Status'), default='planned')
    is_active = fields.Boolean(string=_('Active'), default=False)
    team_id = fields.Many2one('crm.team', string=_('Team'))
    board_id = fields.Many2one('project.board', string=_('Board'))
    task_ids = fields.One2many('project.task', 'sprint_id', string=_('Sprint Tasks'))
    
    @api.constrains('state')
    def _check_backlog_sprint(self):
        for sprint in self:
            if sprint.sequence == 0 and sprint.state != 'planned':
                raise ValidationError(_("Backlog sprint should be Planned Status."))
    
    @api.onchange('is_active')
    def _onchange_is_active(self):
        for sprint in self:
            if sprint.is_active and sprint.state == 'planned':
                sprint.state = 'active'
            elif not sprint.is_active and sprint.state == 'active':
                sprint.state = 'planned'
    
    @api.onchange('state')
    def _onchange_state(self):
        for sprint in self:
            if sprint.state == 'active':
                sprint.is_active = True
            else:
                sprint.is_active = False
    
    @api.onchange('is_backlog')
    def _onchange_is_backlog(self):
        for sprint in self:
            if sprint.is_backlog:
                sprint.state = 'planned'
                sprint.is_active = False
                sprint.sequence = 1  # Ensure backlog is at the beginning
    
    @api.model
    def create_team_backlog(self, team_id):
        """Create a backlog sprint for a team if it doesn't exist"""
        if not team_id:
            return False
            
        # Check if backlog already exists for this team
        existing_backlog = self.search([
            ('is_backlog', '=', True),
            ('team_id', '=', team_id)
        ], limit=1)
        
        if existing_backlog:
            return existing_backlog
            
        # Get team name for the backlog name
        team_name = self.env['crm.team'].browse(team_id).name
        
        # Create new backlog
        return self.create({
            'name': team_name + " Backlog",
            'is_backlog': True,
            'state': 'planned',
            'sequence': 1,
            'team_id': team_id,
        })
