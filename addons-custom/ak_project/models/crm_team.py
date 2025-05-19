from odoo import api, fields, models

class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    type_team = fields.Selection([('sale', 'Sale'), ('project', 'Project')],
                                 string="Team Type", default="sale")
    team_members_ids = fields.Many2many('res.users', 'project_team_user_rel',
                                        'team_id', 'user_id', 'Project Members',
                                        help="""Project's members are users who
                                     can have an access to the tasks related
                                     to this project.""")
    board_ids = fields.Many2many("project.board", "project_board_team_rel", "team_id", "board_id", "Boards")


class CrmTeamMemberInherit(models.Model):
    _inherit = 'crm.team.member'

    crm_sales_team_id = fields.Many2one('crm.team', compute="_compute_crm_sales_team_id", store=True)

    @api.depends('crm_team_id')                    
    def _compute_crm_sales_team_id(self):
        for member in self:
          domain = []
          if member.crm_team_id:
              domain = [
              ("type_team", "=", "sale"),          
              ]
          member.crm_sales_team_id = member.crm_team_id.search(domain, limit=1)