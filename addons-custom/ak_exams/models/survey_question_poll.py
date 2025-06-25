# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

class SurveyQuestionPoll(models.Model):
    _name = 'survey.question.poll'
    _description = 'Survey Question Poll Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    sequence = fields.Integer(string=_('Sequence'), default=10)
    name = fields.Char(string=_('Title'), required=True, translate=True, tracking=True)
    description = fields.Html(string=_('Description'), translate=True)
    option_ids = fields.One2many(
        'survey.question.poll.option',
        'poll_id',
        string=_('Options'),
        copy=True
    )
    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        default=lambda self: self.env.company
    )
    category_id = fields.Many2one(
        'survey.question.poll.category',
        string=_('Category'),
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    active = fields.Boolean(default=True, tracking=True)

    excel_file = fields.Binary(string=_('Excel File'), help_=_("Upload an Excel file to import poll templates."))
    excel_file_name = fields.Char(string=_('Excel File Name'))

    # Placeholder for Excel import method
    def import_from_excel(self):
        self.ensure_one() # Ensure we are working on a single record where the file is attached
        if not self.excel_file:
            raise UserError(_("Please upload an Excel file first on this record."))

        try:
            import base64
            import io
            from openpyxl import load_workbook
        except ImportError:
            raise UserError(_("The 'openpyxl' library is required to import Excel files. Please install it (pip install openpyxl)."))

        try:
            decoded_file = base64.b64decode(self.excel_file)
            workbook = load_workbook(filename=io.BytesIO(decoded_file))
            sheet = workbook.active

            # Headers: KATEGORİ, ID, SORU, A, B, C, D, CEVAP
            # We assume headers are in the first row and skip them.
            # Adjust if your Excel has no headers or they are different.
            header = [cell.value for cell in sheet[1]]
            expected_headers = ['KATEGORİ', 'ID', 'SORU', 'A', 'B', 'C', 'D', 'CEVAP'] # Extend if more options like E, F etc.
            
            # Basic header check - can be made more robust
            if not all(h in header for h in ['KATEGORİ', 'SORU', 'A', 'CEVAP']):
                 raise UserError(_("Excel file is missing one of the required headers: KATEGORİ, SORU, A, CEVAP."))

            # Map headers to indices
            col_map = {name: idx for idx, name in enumerate(header)}
            option_cols = sorted([col_map[key] for key in col_map if key.isalpha() and len(key) == 1 and key >= 'A' and key <= 'Z'])


            PollCategory = self.env['survey.question.poll.category']
            PollOption = self.env['survey.question.poll.option']

            polls_created_count = 0
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                category_name = row[col_map['KATEGORİ']]
                question_text = row[col_map['SORU']]
                correct_answer_letter = str(row[col_map['CEVAP']]).strip().upper() if row[col_map['CEVAP']] else None

                if not question_text: # Skip row if question is empty
                    continue
                
                current_poll_company_id = self.company_id.id or self.env.company.id

                category = False
                if category_name:
                    # Search for category specific to the company or a global one
                    domain = [('name', '=ilike', category_name)]
                    company_specific_domain = ['&'] + domain + [('company_id', '=', current_poll_company_id)]
                    global_domain = ['&'] + domain + [('company_id', '=', False)]
                    
                    category = PollCategory.search(company_specific_domain, limit=1)
                    if not category:
                        category = PollCategory.search(global_domain, limit=1)
                    
                    if not category:
                        category = PollCategory.create({
                            'name': category_name,
                            'company_id': current_poll_company_id # Create new categories under the poll's company
                        })
                
                options_data = []
                for i, opt_col_idx in enumerate(option_cols):
                    option_text = row[opt_col_idx]
                    if option_text: # Only add option if text exists
                        is_correct = chr(65 + i) == correct_answer_letter # A=0, B=1, ...
                        options_data.append({
                            'name': str(option_text),
                            'sequence': i + 1,
                            'is_correct': is_correct,
                            'answer_score': 1.0 if is_correct else 0.0, # Default score
                        })
                
                if not options_data: # Skip if no options found
                    continue

                poll_vals = {
                    'name': question_text,
                    'category_id': category.id if category else False,
                    'company_id': current_poll_company_id,
                    'option_ids': [(0, 0, opt_data) for opt_data in options_data],
                }
                self.env['survey.question.poll'].create(poll_vals)
                polls_created_count += 1
            
            # Clear the file after import to prevent re-importing accidentally
            self.excel_file = False
            self.excel_file_name = False

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Successful'),
                    'message': _('%s poll templates have been successfully imported.') % polls_created_count,
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            raise UserError(_("Error processing Excel file: %s") % str(e))

    @api.model
    def create_poll_from_template(self, poll_template_id, survey_id, sequence):
        """
        Creates a survey.question (as a poll) from this poll template.
        """
        template = self.browse(poll_template_id)
        if not template.exists():
            raise UserError(_("The selected poll template does not exist."))

        question_vals = {
            'title': template.name,
            'description': template.description,
            'survey_id': survey_id,
            'sequence': sequence,
            'question_type': 'simple_choice', # Assuming polls are simple choice
            'constr_mandatory': True, # Or based on a template field
            'comment_count_as_answer': False,
            'is_time_limited': False,
            'time_limit': 0,
            'suggested_answer_ids': []
        }

        for option_template in template.option_ids:
            question_vals['suggested_answer_ids'].append((0, 0, {
                'value': option_template.name,
                'sequence': option_template.sequence,
                'is_correct': option_template.is_correct,
                'answer_score': option_template.answer_score,
                'value_image': option_template.value_image,
                # 'value_image_filename': option_template.value_image_filename, # filename is often set automatically
            }))
        
        question = self.env['survey.question'].create(question_vals)
        return question.id