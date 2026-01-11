import logging
from odoo import models, api, _, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def _check_active_exams(env):
    """
    Checks for active exams and raises a UserError if any are found.
    This function is intended to be called from model write/unlink/install methods.
    """
    query = """
        SELECT COUNT(sui.id)
        FROM survey_user_input AS sui
        JOIN survey_survey AS ss ON sui.survey_id = ss.id
        WHERE sui.state = 'in_progress'
          AND ss.survey_type = 'assessment'
          AND ss.start_date <= NOW() AT TIME ZONE 'UTC'
          AND (ss.end_date IS NULL OR ss.end_date >= NOW() AT TIME ZONE 'UTC');
    """
    env.cr.execute(query)
    active_exam_count = env.cr.fetchone()[0]
    
    if active_exam_count > 0:
        raise UserError(_(
            'UYARI: Bu işlem aktif sınav sırasında yapılamaz!\n\n'
            'Şu anda %s öğrenci sınav yapıyor.\n'
            'Lütfen tüm sınavlar bittikten sonra devam edin.') % active_exam_count)

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'
    
    def write(self, vals):
        _check_active_exams(self.env)
        return super(IrUiView, self).write(vals)

class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def button_immediate_install(self):
        _check_active_exams(self.env)
        return super(IrModuleModule, self).button_immediate_install()

    def button_immediate_upgrade(self):
        _check_active_exams(self.env)
        return super(IrModuleModule, self).button_immediate_upgrade()

    def button_immediate_uninstall(self):
        _check_active_exams(self.env)
        return super(IrModuleModule, self).button_immediate_uninstall()
