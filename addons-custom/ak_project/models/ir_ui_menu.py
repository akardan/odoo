from odoo import models, fields, api, tools

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    # gizlemek istenen menüler menü blackliste ekleniyor
    def _load_menus_blacklist(self):
        res = super()._load_menus_blacklist()

        # kullanıcının tipi scrum olan bir boarda girmeye yetkisi var mı?
        board_ids = self.env['project.board'].search(['|', '|', '|',
                                                        ('workspace_id.department_id', 'child_of', self.env.user.department_id.id),
                                                        ('project_ids.message_partner_ids', 'in', [self.env.user.partner_id.id]),
                                                        ('message_partner_ids', 'in', [self.env.user.partner_id.id]),
                                                        ('project_ids.privacy_visibility', '!=', 'followers'),
                                                     ]).search([('type', '=', 'scrum')])        

        if len(board_ids) == 0 and not self.env.user.has_group('base.group_erp_manager'):
            res.append(self.env.ref('ak_project.menu_project_scrum').id)

        if self.env.user.has_group('project.group_project_user') and not self.env.user.has_group('project.group_project_manager'):
            res.append(self.env.ref('ak_project.menu_project_sprint').id)

        return res
