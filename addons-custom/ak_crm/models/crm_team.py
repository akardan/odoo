from odoo import _, fields, models, api
from odoo.exceptions import ValidationError

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    parent_id = fields.Many2one('crm.team', string=_('Parent Team'), index=True, ondelete='cascade')
    child_ids = fields.One2many('crm.team', 'parent_id', string=_('Child Teams'))
    # is_sales_group = fields.Boolean(string='Is Sales Group?', default=False)
    team_type = fields.Selection([('G', _('Group')), ('H', _('Head Office')), ('R', _('Region')), ('U', _('Unit'))],
                                 string=_('Team Type'), default='U', required=True, index=True)
    product_ids = fields.Many2many('product.product', string=_('Marketing Products'))
    group_id = fields.Many2one('crm.team', string=_('Marketing Group'), compute='_compute_group_id', readonly=True)

    @api.depends('parent_id', 'parent_id.team_type')
    def _compute_group_id(self):
        for team in self:
            current_team = team
            while current_team.parent_id:
                if current_team.parent_id.team_type == 'G':
                    team.group_id = current_team.parent_id
                    break
                current_team = current_team.parent_id
            else:
                team.group_id = False

    @api.constrains('team_type', 'product_ids')
    def _check_product_ids(self):
        for record in self:
            if record.team_type != 'G' and record.product_ids:
                raise ValidationError(_("Only teams with type 'G' can select 'Marketing Products'."))