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
        })
        
        try:
            # Call the import method on the poll record
            result = temp_poll.import_from_excel()
            # Delete the temporary record after import
            temp_poll.unlink()
            return result
        except Exception as e:
            # Delete the temporary record if there's an error
            temp_poll.unlink()
            raise