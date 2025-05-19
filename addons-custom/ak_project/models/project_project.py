from odoo import api, fields, models, _, SUPERUSER_ID


class ProjectProjectStage(models.Model):
    _inherit = "project.project.stage"

    board_ids = fields.Many2many("project.board", "project_board_stage_rel", "stage_id", "board_id")

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):        
        project_stage = super(ProjectProjectStage, self).copy(default)    
        project_stage.board_ids = False

        return project_stage    
    
    def duplicate_project_stage(self):
        for record in self:
            record.copy();      

class ProjectProject(models.Model):
    _inherit = 'project.project'

    department_id = fields.Many2one(comodel_name="hr.department", string="Project Department")
    
    board_id = fields.Many2one('project.board', 'Board')
    board_desc = fields.Char(string="Board (Workspace)", compute="_compute_board_desc")

    document_count = fields.Integer(string='Documents',
                                    compute='_compute_document_count',
                                    help="For getting the document count")
    issue_count = fields.Integer(string="Project issues",
                                 help="For getting project issue count",
                                 compute="_compute_issue_count")
        
    members_ids = fields.Many2many('res.users', 'project_user_rel', 'project_id',
                                   'user_id', 'Project Members', help="""Project's
                               members are users who can have an access to
                               the tasks related to this project."""
                                   )
    team_id = fields.Many2one('crm.team', "Project Team", 
                              domain=[('type_team', '=', 'project')])
    
    added_followers = fields.Many2many('res.users', 'project_follower_rel', 'project_id', 'user_id', 'Auto Added Followers')
    
    only_team_members_can_be_assigned = fields.Boolean(string='Only Team Members Can Be Assigned')
    add_the_team_members_to_the_followers = fields.Boolean(string='Add The Team Members To The Followers')

    send_mail_when_the_task_is_ready = fields.Boolean("Task Reminder")

    task_count = fields.Integer("Task Count", compute="_compute_task_count")
    phase_count = fields.Integer("Phases Count", compute="_compute_phase_count")

    # ar-ge projeleri için
    project_group = fields.Char("Project Group", size=50)
    project_code = fields.Char("Project Code", size=20)
    project_forms = fields.Char("Project Forms", size=100)
    is_rd_board = fields.Boolean(compute="_compute_is_rd_board")

    @api.depends('board_id', 'board_id.is_rd_board')
    def _compute_is_rd_board(self):
        for record in self:
            record.is_rd_board = record.board_id.is_rd_board

    def _compute_board_desc(self):
        for record in self:
            if record.board_id:
                record.board_desc = record.board_id.name + " (" + record.board_id.workspace_id.name + ")"
            else:
                record.board_desc = ""                
    
    # board açıldığında board için tanımlanan stagelerin gelmesi için 
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        if 'default_board_id' in self.env.context:
            search_domain = ['|', ('board_ids', '=', self.env.context['default_board_id'])] + search_domain
        else: 
            search_domain = []

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)                

    def _default_stage_id(self):
        board_id = self.env.context.get('default_board_id')
        return self.env['project.project.stage'].search([('board_ids', '=', board_id)], limit=1) 
            
    stage_id = fields.Many2one('project.project.stage', string='Stage', ondelete='restrict', groups="project.group_project_stages",
        tracking=True, index=True, copy=False, default=_default_stage_id, group_expand='_read_group_stage_ids', domain="[('board_ids', '=', board_id)]")

    def button_document(self):
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,form',
            'res_id': self._origin.id,
            'domain': [
                ('res_id', '=', self._origin.id),
                ('res_model', '=', 'project.project')
            ],
        }

    def _compute_document_count(self):
        for rec in self:
            attachment_ids = self.env['ir.attachment'].search(
                [('res_model', '=', 'project.project'),
                 ('res_id', '=', rec.id)])
            rec.document_count = len(attachment_ids)    

    def button_issue(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Issues',
            'view_mode': 'list,form',
            'res_model': 'project.issue',
            'domain': [('project_id', '=', self.id)]
        }            
    
    def _compute_issue_count(self):
        for rec in self:
            issue_id = self.env['project.issue'].search(
                [('project_id', '=', rec.id)])
            rec.issue_count = len(issue_id)    

    def button_task(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Tasks',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.task',
            'domain': [('project_id', '=', self.id)]
        }            
            
    def _compute_task_count(self):
        for rec in self:
            task_id = self.env['project.task'].search(
                [('project_id', '=', rec.id)])
            rec.task_count = len(task_id)  

    def button_phase(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Phases',
            'view_mode': 'kanban,list,form',
            'res_model': 'project.phase',
            'domain': [('project_id', '=', self.id)],
        }

    def _compute_phase_count(self):
        for rec in self:
            rec.phase_count = self.env['project.phase'].search_count([('project_id', '=', rec.id)])
            


    @api.onchange('team_id')
    def _get_team_members(self):
        self.update({"members_ids": [(6, 0, self.team_id.team_members_ids.ids)]})
    
    # takım seçilince takımdaki tüm kişiler takip listesine ekleniyor. takımdan çıkartılan kişiler de takip listesinden otomatik çıkartılıyor    
    @api.onchange('members_ids')
    def _change_members(self):
        if self.add_the_team_members_to_the_followers: #self.env['ir.config_parameter'].sudo().get_param('project_team.add_the_team_members_to_the_followers'): 
            for record in self:
                if record.privacy_visibility == 'followers':
                    new_members = record.members_ids
                    previous_members = record.added_followers
                    removed_members = previous_members - new_members
                    added_members = new_members - previous_members
                    if added_members:
                        record.message_subscribe(added_members.user_ids.partner_id.ids)
                    if removed_members:
                        # bu kod ile takip listesinden çıkartılıyor ancak members_ids listesi eski haline geliyor nedense. bu yüzden 2. satırdaki kodu ekledim
                        record.message_unsubscribe(removed_members.user_ids.partner_id.ids)
                        record.members_ids = new_members

                    record.added_followers = [(6, 0, new_members.ids)]      

    def _get_manager(self):
        return self.user_id.partner_id;                             

    def get_project(self):
        project = self
        return {
            'type': 'ir.actions.act_window',  
            'name': 'Project',                      
            'view_mode': 'form',
            'views': [[False, 'form']],
            'res_model': 'project.project',
            'target': 'current',
            'res_id': self.id,
        }                
    
