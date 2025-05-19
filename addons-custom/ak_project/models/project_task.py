from odoo import api, fields, models, _, exceptions


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_department_id = fields.Many2one(
        related="project_id.department_id",
        string="Project Department",
        store=True,
        readonly=True,
    )

    project_team_id = fields.Many2one(
        related="project_id.team_id",
        string="Project Team",
        store=True,
        readonly=True,
    )
    
    allowed_assigned_user_ids = fields.Many2many(
        comodel_name="res.users",
        string="Allowed users",
        compute="_compute_allowed_assigned_user_ids",
        help="Technical field for computing allowed users according project team.",
    )
    
    document_count = fields.Integer(string='Documents',
                                    compute='_compute_document_count',
                                    help="For getting document count")

    issue_type = fields.Selection([('story', 'Story'), ('task', 'Task'), ('bug', 'Bug')], default='task', string='Issue Type', required=True)
    board_type = fields.Char(compute='_compute_board_type')

    @api.depends("project_id", "project_id.board_id")
    def _compute_board_type(self):
        for record in self:
            if not record.project_id or not record.project_id.board_id:
                record.board_type = 'kanban'
            else:
                record.board_type = record.project_id.board_id.type


    version_id = fields.Many2one(comodel_name="project.version", string="Version")            

    sprint_id = fields.Many2one('project.sprint', string=_('Sprint'), group_expand='_read_group_sprint_id')
    sprint_history_ids = fields.One2many('project.task.sprint.history', 'task_id', string=_('Sprint History'))
    
    phase_id = fields.Many2one('project.phase', "Project Phase")    

    def write(self, vals):
        # Eğer sprint_id değeri değişirse, geçmişe yeni bir kayıt ekle
        if 'sprint_id' in vals:
            new_sprint = self.env['project.sprint'].browse(vals['sprint_id'])

            # Yeni sprint "active" durumdaysa ya da task zaten "active" bir sprintten çıkıyorsa
            if new_sprint.state == 'active' or (self.sprint_id and self.sprint_id.state == 'active'):
                for task in self:
                    self.env['project.task.sprint.history'].create({
                        'task_id': task.id,
                        'sprint_id': vals['sprint_id'],
                        'date_added': fields.Datetime.now()
                    })

        # görevin aşaması değişiyorsa
        if 'stage_id' in vals:
            new_stage = self.env['project.task.type'].browse(vals['stage_id'])
            if new_stage.authorised_group:
                user_groups = self.env.user.groups_id
                required_group = self.env['res.groups'].search([('name', '=', new_stage.authorised_group)], limit=1)
                if required_group not in user_groups:
                    raise exceptions.AccessError('You do not have the required authorisation to move the task to this stage.')        
                
        return super(ProjectTask, self).write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # projedeki en yüksek sequence değeri bulunarak yeni kayıtta 1 fazlası set ediliyor
            project_id = vals.get('project_id') or self.env.context.get('default_project_id')
            if project_id:
                last_task_by_sequence = self.env['project.task'].search([('project_id', '=', project_id)], order='sequence desc', limit=1)
                vals["sequence"] = last_task_by_sequence.sequence + 1

        return super(ProjectTask, self).create(vals_list)

    @api.model
    def _read_group_sprint_id(self, sprints, domain, order):
        # sprint_ids = self.env['project.sprint'].search([('state', '!=', 'closed')], order='sequence').ids
        sprint_ids = self.env['project.sprint'].search([
            ('state', '!=', 'closed'),
            '|',
            ('team_id', '=', False),
            ('team_id.team_members_ids', 'in', [self.env.user.id])
        ], order='sequence').ids
        return sprints.browse(sprint_ids)
    
    def _compute_document_count(self):
        """ Compute document count and return """
        for rec in self:
            attachment_ids = self.env['ir.attachment'].search(
                [('res_model', '=', 'project.task'), ('res_id', '=', rec.id)])
            rec.document_count = len(attachment_ids)

    def button_task_document(self):
        """ Return document kanban for the task"""
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,form',
            'res_id': self._origin.id,
            'domain': [
                ('res_id', '=', self._origin.id),
                ('res_model', '=', 'project.task')],
        }    
    
    @api.depends("project_id", "project_id.team_id", "project_id.members_ids")
    def _compute_allowed_assigned_user_ids(self):      
        user_obj = self.env["res.users"]
        for task in self:
            domain = []
            if task.project_id and task.project_id.team_id and self.project_id.only_team_members_can_be_assigned: #self.env['ir.config_parameter'].sudo().get_param('project_team.only_team_members_can_be_assigned'):         
                domain = [
                ("user_ids", "in", task.project_id.members_ids.ids),          
                ]
            task.allowed_assigned_user_ids = user_obj.search(domain)  

    def action_duplicate_subtasks(self):
        action = self.env.ref("project.action_view_task")
        result = action.read()[0]
        task_created = self.env["project.task"]
        for task in self:
            new_task = task.copy()
            task_created |= new_task
            if task.child_ids:

                def duplicate_childs(task, new_task):
                    if task.child_ids:
                        for child in task.child_ids:
                            new_subtask = child.copy()
                            new_subtask.write({"parent_id": new_task.id})
                            duplicate_childs(child, new_subtask)

                duplicate_childs(task, new_task)

        if len(task_created) == 1:
            res = self.env.ref("project.view_task_form2")
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = new_task.id
            action["context"] = {
                "form_view_initial_mode": "edit",
                "force_detailed_view": "true",
            }

        else:
            result["domain"] = "[('id', 'in', " + str(task_created.ids) + ")]"
        return result            
      
class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'      

    authorised_group = fields.Selection(selection=lambda self: self._get_project_groups(), 
                                        string="Groups Authorised To Change Stage")

    def _get_project_groups(self):
        groups = self.env['res.groups'].search([('category_id', '=', self.env.ref('base.module_category_services_project').id)])
        return [(group.name, group.name) for group in groups]    
    
