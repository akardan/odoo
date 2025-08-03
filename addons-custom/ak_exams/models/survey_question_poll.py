# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError

class SurveyQuestionPoll(models.Model):
    _name = 'survey.question.poll'
    _description = 'Survey Question Poll Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    sequence = fields.Integer(string=_('Sequence'), default=10)
    name = fields.Text(string=_('Title'), required=True, translate=True, tracking=True)
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

    def import_from_excel(self):
        """
        Import poll questions, options, and categories from an Excel file.
        Checks for existing records to prevent duplication.
        
        Returns:
            Action dict with import results
        """
        self.ensure_one()  # Ensure we are working on a single record where the file is attached
        if not self.excel_file:
            raise UserError(_("Please upload an Excel file first on this record."))
        file_content = self.excel_file

        try:
            import base64
            import io
            from openpyxl import load_workbook
        except ImportError:
            raise UserError(_("The 'openpyxl' library is required to import Excel files. Please install it (pip install openpyxl)."))

        try:
            decoded_file = base64.b64decode(file_content)
            workbook = load_workbook(filename=io.BytesIO(decoded_file))
            sheet = workbook.active

            # Headers: KATEGORİ, ID, SORU, A, B, C, D, CEVAP
            # We assume headers are in the first row and skip them.
            header = [str(cell.value).upper() if cell.value else '' for cell in sheet[1]]
            
            # Map common header variations
            header_mapping = {
                'KATEGORI': 'KATEGORİ',
                'KATEGOR': 'KATEGORİ',
                'CATEGORY': 'KATEGORİ',
                'QUESTION': 'SORU',
                'ANSWER': 'CEVAP',
                'CORRECT': 'CEVAP'
            }
            
            # Normalize headers
            normalized_header = []
            for h in header:
                if h in header_mapping:
                    normalized_header.append(header_mapping[h])
                else:
                    normalized_header.append(h)
            
            # Basic header check - can be made more robust
            required_headers = ['KATEGORİ', 'SORU', 'A', 'CEVAP']
            missing_headers = [h for h in required_headers if h not in normalized_header]
            if missing_headers:
                raise UserError(_("Excel file is missing required headers: %s") % ', '.join(missing_headers))

            # Map headers to indices
            col_map = {name: idx for idx, name in enumerate(normalized_header)}
            
            # Find all option columns (A, B, C, D, etc.)
            option_cols = []
            for key in col_map:
                if key.isalpha() and len(key) == 1 and key >= 'A' and key <= 'Z':
                    option_cols.append((key, col_map[key]))
            
            # Sort option columns by letter
            option_cols.sort(key=lambda x: x[0])

            PollCategory = self.env['survey.question.poll.category']
            Poll = self.env['survey.question.poll']
            PollOption = self.env['survey.question.poll.option']

            stats = {
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'categories_created': 0,
                'categories_existing': 0,
                'roles_assigned': 0,
            }
            
            current_poll_company_id = self.env.company.id
            if hasattr(self, 'company_id') and self.company_id:
                current_poll_company_id = self.company_id.id

            # Process each row
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if row_idx % 50 == 0:
                    self.env.cr.commit()  # Commit every 50 rows to avoid long transactions
                
                # Skip empty rows
                if not any(row):
                    stats['skipped'] += 1
                    continue
                
                # Extract data from row
                category_name = row[col_map.get('KATEGORİ', 0)] if 'KATEGORİ' in col_map else None
                role_name = row[0] if len(row) > 0 else None  # First column is ROLE
                question_id = row[col_map.get('ID', 1)] if 'ID' in col_map else None
                question_text = row[col_map.get('SORU', 2)] if 'SORU' in col_map else None
                correct_answer_letter = str(row[col_map.get('CEVAP', -1)]).strip().upper() if 'CEVAP' in col_map and row[col_map['CEVAP']] else None

                if not question_text:  # Skip row if question is empty
                    stats['skipped'] += 1
                    continue

                # Find or create category
                category = False
                if category_name:
                    # Search for category specific to the company or a global one
                    domain = [('name', '=ilike', category_name)]
                    company_specific_domain = ['&'] + domain + [('company_id', '=', current_poll_company_id)]
                    global_domain = ['&'] + domain + [('company_id', '=', False)]
                    
                    category = PollCategory.search(company_specific_domain, limit=1)
                    if not category:
                        category = PollCategory.search(global_domain, limit=1)
                    
                    if category:
                        # Update existing category with role if specified
                        if role_name:
                            job_position = self.env['hr.job'].search([('name', '=ilike', role_name)], limit=1)
                            if job_position and job_position.id not in category.job_position_ids.ids:
                                category.write({'job_position_ids': [(4, job_position.id)]})
                                stats['roles_assigned'] += 1
                        
                        stats['categories_existing'] += 1
                    else:
                        # Find job position based on role name
                        job_position = False
                        if role_name:
                            job_position = self.env['hr.job'].search([('name', '=ilike', role_name)], limit=1)
                        
                        category_vals = {
                            'name': category_name,
                            'company_id': current_poll_company_id  # Create new categories under the poll's company
                        }
                        
                        # Add job position if found
                        if job_position:
                            category_vals['job_position_ids'] = [(4, job_position.id)]
                            stats['roles_assigned'] += 1
                        
                        category = PollCategory.create(category_vals)
                        stats['categories_created'] += 1

                # Check if poll already exists to prevent duplication
                existing_poll = False
                if category:
                    existing_poll = Poll.search([
                        ('name', '=', question_text),
                        ('category_id', '=', category.id),
                        ('company_id', '=', current_poll_company_id)
                    ], limit=1)
                else:
                    existing_poll = Poll.search([
                        ('name', '=', question_text),
                        ('company_id', '=', current_poll_company_id)
                    ], limit=1)

                # Collect option data
                options_data = []
                for i, (option_letter, opt_col_idx) in enumerate(option_cols):
                    if opt_col_idx < len(row):
                        option_text = row[opt_col_idx]
                        if option_text:  # Only add option if text exists
                            is_correct = option_letter == correct_answer_letter
                            options_data.append({
                                'name': str(option_text),
                                'sequence': i + 1,
                                'is_correct': is_correct,
                                'answer_score': 1.0 if is_correct else 0.0,  # Default score
                            })

                if not options_data:  # Skip if no options found
                    stats['skipped'] += 1
                    continue

                # Create or update poll
                if existing_poll:
                    # Update existing poll
                    # First, remove existing options
                    existing_poll.option_ids.unlink()
                    
                    # Then add new options
                    for opt_data in options_data:
                        PollOption.create(dict(poll_id=existing_poll.id, **opt_data))
                    
                    stats['updated'] += 1
                else:
                    # Create new poll
                    poll_vals = {
                        'name': question_text,
                        'category_id': category.id if category else False,
                        'company_id': current_poll_company_id,
                        'option_ids': [(0, 0, opt_data) for opt_data in options_data],
                    }
                    Poll.create(poll_vals)
                    stats['created'] += 1

            # Clear the file after import
            self.excel_file = False
            self.excel_file_name = False

            # Prepare result message
            message = _(
                "Import results:\n"
                "- Created: %(created)s\n"
                "- Updated: %(updated)s\n"
                "- Skipped: %(skipped)s\n"
                "- Categories created: %(categories_created)s\n"
                "- Existing categories used: %(categories_existing)s\n"
                "- Roles assigned: %(roles_assigned)s"
            ) % stats

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Successful'),
                    'message': message,
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            self.env.cr.rollback()
            raise UserError(_("Error processing Excel file: %s") % str(e))

    @api.model
    def create_poll_from_template(self, poll_template_id, survey_id, sequence):
        """
        Creates a survey.question (as a poll) from this poll template.
        """
        _logger = logging.getLogger(__name__)
        _logger.info("create_poll_from_template called with poll_template_id=%s, survey_id=%s, sequence=%s",
                    poll_template_id, survey_id, sequence)
        
        try:
            template = self.browse(poll_template_id)
            if not template.exists():
                _logger.error("Poll template with ID %s does not exist", poll_template_id)
                raise UserError(_("The selected poll template does not exist."))

            _logger.info("Poll template found: %s", template.name)
            
            # Get the category_id from the template
            category_id = template.category_id.id if template.category_id else False
            
            _logger.info("Setting category_id: %s from template category: %s",
                        category_id,
                        template.category_id.name if template.category_id else 'None')
            
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
                'category_id': category_id,
                'suggested_answer_ids': []
            }

            _logger.info("Option count: %s", len(template.option_ids))
            for option_template in template.option_ids:
                _logger.info("Adding option: %s", option_template.name)
                question_vals['suggested_answer_ids'].append((0, 0, {
                    'value': option_template.name,
                    'sequence': option_template.sequence,
                    'is_correct': option_template.is_correct,
                    'answer_score': option_template.answer_score,
                    'value_image': option_template.value_image,
                    # 'value_image_filename': option_template.value_image_filename, # filename is often set automatically
                }))
            
            _logger.info("Creating survey question with values: %s", question_vals)
            question = self.env['survey.question'].create(question_vals)
            _logger.info("Survey question created with ID: %s", question.id)
            return question.id
        except Exception as e:
            _logger.error("Error in create_poll_from_template: %s", e)
            raise