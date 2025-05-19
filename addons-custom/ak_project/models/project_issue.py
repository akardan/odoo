from odoo import api, fields, models


class ProjectIssue(models.Model):    
    _name = "project.issue"
    _description = 'Project issue'

    user_id = fields.Many2one("res.users", string="Assigned to",
                              help="The person who is responsible to solve "
                                   "the issue")
    summary = fields.Text(string='Issue summary', help="Adding project issue", required=True, translate=True)    
    project_id = fields.Many2one('project.project', string="Project",
                                 help="To know issue noticed in which project", required=True)
    task_id = fields.Many2one('project.task', string="Task",
                              help="To know issue noticed in which task",
                              domain="[('project_id', '=', project_id)]")
    priority = fields.Selection([('0', 'Low'), ('1', 'High')], default='0',
                                string="Priority")
    tag_ids = fields.Many2many('project.tags', string='Tags',
                               help='Set the tags')
    number = fields.Char(string='Number', default='New',
                       help='To track the issue reference')
    description = fields.Text(string='Description',
                              help="To add the issue in detail", translate=True)
    extra_info = fields.Text(string="Extra Info",
                             help="To add some extra information", translate=True)
    state = fields.Selection([('new', 'New'), ('progress', 'In Progress'),
                              ('done', 'Done'), ('cancel', 'Cancel')],
                             default='new', string='State',
                             help='Project issue pipeline stages')
    create_date = fields.Datetime(string="Create Date",
                                  help='For tracking the record creation date',
                                  default=fields.Datetime.now())
    name = fields.Char(string="Name", compute='_compute_name')    

    def _compute_name(self):
        self.name = self.number
        
    # @api.onchange('project_id')
    # def _onchange_project_id(self):
    #     if self.project_id:
    #         return {'domain': {'task_id': [('project_id', '=', self.project_id.id)]}}
    #     else:
    #         return {'domain': {'task_id': []}}
                
    @api.model_create_multi
    def create(self, vals_list):
        """ Added reference number"""
        for vals in vals_list:
            if vals.get('number', 'New'):
                vals['number'] = self.env['ir.sequence'].next_by_code(
                    'project.issue')
        res = super(ProjectIssue, self).create(vals_list)
        return res
