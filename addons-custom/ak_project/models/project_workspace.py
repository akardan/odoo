from ast import literal_eval
from odoo import api, fields, models


class ProjectWorkspace(models.Model):    
    _name = "project.workspace"
    _description = 'Project workspace'
    _order = "name, id"

    name = fields.Char(string="Name", required=True, translate=True)
    department_id = fields.Many2one(comodel_name="hr.department", string="Workspace Department", required=True)    
    active = fields.Boolean(default=True)
    board_ids = fields.Many2many("project.board", "project_workspace_board_rel", "workspace_id", "board_id", "Boards")
    
  

class ProjectBoard(models.Model):
    _name = "project.board"
    _description = 'Project board'
    _inherit = 'mail.thread'
    _order = "name, id"

    name = fields.Char(string="Name", required=True, translate=True, tracking=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string="Description", translate=True)
    color = fields.Integer('Color')
    workspace_id = fields.Many2one(comodel_name="project.workspace", string="Workspace", required=True, tracking=True)
    stage_ids = fields.Many2many("project.project.stage", "project_board_stage_rel", "board_id", "stage_id", string="Stages", required=True)
    team_ids = fields.Many2many("crm.team", "project_board_team_rel", "board_id", "team_id", "Teams")
    members_ids = fields.Many2many('res.users', 'project_board_user_rel', 'board_id', 'user_id', 'Board Members')    

    project_ids = fields.One2many('project.project', 'board_id', string='Projects')

    type = fields.Selection([('kanban', 'Kanban'), ('scrum', 'Scrum')], default='kanban', string='Board Type', required=True)


    project_count = fields.Integer(compute='_compute_project_count')
    department_desc = fields.Char(compute='_compute_department_desc')
                    
    # board oluşturma adımında kullanıcının yetkili olduğu workspaceler gelmesi için
    allowed_workspace_ids = fields.Many2many("project.workspace", compute="_compute_allowed_workspace_ids")

    def _compute_allowed_workspace_ids(self):
        workspace = self.env["project.workspace"]
        for record in self:
            domain = []
            if self.env.user.has_group('base.group_erp_manager') == False:
                domain = [('department_id', 'child_of', self.env.user.department_id.id)]
            else:
                domain = [(1, '=', 1)]
            record.allowed_workspace_ids = workspace.search(domain)              
    
    @api.onchange('team_ids')
    def _get_team_members(self):
        ids = []
        for record in self:
            for team_id in record.team_ids:
                for id in team_id.team_members_ids.ids:
                    ids.append(id)
            record.update({"members_ids": [(6, 0, ids)]})

    def action_open_board(self):
        return {
            'view_mode': 'form',
            'res_model': 'project.board',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }        
    
    def _compute_project_count(self):
        for record in self:
            
            if self.env.user.partner_id.user_has_groups('base.group_erp_manager'):
                domain = [('board_id', '=', record.id)]
            else:
                domain = ['&', ('board_id', '=', record.id), '|', ('message_partner_ids', 'in', [self.env.user.partner_id.id]), ('privacy_visibility', '!=', 'followers')]
            record.project_count = record.project_count + len(record.sudo().project_ids.search(domain))

    def _compute_department_desc(self):
        for record in self:
            record.department_desc = record.sudo().workspace_id.department_id.name + ' (' + record.sudo().workspace_id.name + ')'

    def _get_action(self, action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        if self:
            action['display_name'] = self.display_name

        context = {
            'search_default_groupby_stage': 1,
            'search_default_board_id': [self.id],
            'default_board_id': self.id,
        }

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action
        
    def get_project_board_action(self):
        return self._get_action('project.open_view_project_all')    

    # def _get_default_workspace_id(self):
    #     default_workspace_id = self.env.context.get('default_workspace_id')
    #     return [default_workspace_id] if default_workspace_id else None
    
    @api.model
    def default_get(self, fields):
        res = super(ProjectBoard, self).default_get(fields)
        
        # yeni kayıt ekranında compute fonksiyonu çalışmıyor bu yüzden buraya da eklendi
        workspace = self.env["project.workspace"]
        domain = []
        if self.env.user.has_group('base.group_erp_manager') == False:
            domain = [('department_id', 'child_of', self.env.user.department_id.id)]
        else:
            domain = [(1, '=', 1)]
        res['allowed_workspace_ids'] = workspace.search(domain)  

        return res

