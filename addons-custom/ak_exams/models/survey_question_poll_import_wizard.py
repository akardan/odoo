# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

class SurveyQuestionPollImportWizard(models.TransientModel):
    _name = 'survey.question.poll.import.wizard'
    _description = 'Import Survey Question Polls from Excel'

    excel_file = fields.Binary(string=_('Excel File'), required=True, 
                              help=_("Upload an Excel file to import poll questions, options, and categories."))
    excel_file_name = fields.Char(string=_('Excel File Name'))
    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        default=lambda self: self.env.company,
        help=_("Company to associate with imported polls. Leave empty for current company.")
    )
    team_id = fields.Many2one(
        'crm.team',
        string=_('Sales Team'),
        groups='sales_team.group_sale_manager',
        domain="[('team_type', '=', 'G')]"
    )
    job_position_ids = fields.Many2many(
        'hr.job',
        string=_('Role'),
        help=_('Roles to assign to question categories')
    )

    def action_import(self):
        """
        Import poll questions from the uploaded Excel file
        """
        self.ensure_one()
        if not self.excel_file:
            raise UserError(_("Please upload an Excel file first."))

        # Create a temporary poll record to use for import
        Poll = self.env['survey.question.poll']
        temp_poll = Poll.create({
            'name': 'Temp Import Poll',
            'excel_file': self.excel_file,
            'excel_file_name': self.excel_file_name,
            'company_id': self.company_id.id or self.env.company.id,
            'team_id': self.team_id.id,
        })
        
        # Store job_position_ids in context for import method
        if self.job_position_ids:
            temp_poll = temp_poll.with_context(default_job_position_ids=self.job_position_ids.ids)
        
        try:
            # Call the import method on the poll record
            result = temp_poll.import_from_excel()
            # Delete the temporary record after import
            temp_poll.unlink()
            return result
        except Exception as e:
            # Delete the temporary record if there's an error
            # (rollback inside import_from_excel may have already removed it)
            if temp_poll.exists():
                temp_poll.unlink()
            raise