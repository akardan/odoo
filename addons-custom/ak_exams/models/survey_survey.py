from odoo import api, fields, models, _
from odoo.exceptions import UserError
# import re # No longer needed for this simplified approach

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        default=lambda self: self.env.company
    )
    
    excel_file = fields.Binary(string=_('Excel File'), help=_("Upload an Excel file to import questions."))
    excel_file_name = fields.Char(string=_('Excel File Name'))
    
    def action_import_from_excel(self):
        """
        Import questions, participants, and their answers from Excel file.
        Expected Excel structure:
        - "Soru" sheet: Contains questions and answer options
          - ID: Question ID (optional)
          - Soru: Question text
          - A, B, C, D: Answer options
          - Kategori: Question category
        - "Yanıt" sheet: Contains participant responses and correct answers
          - Katılımcı: Participant name
          - Takım: Team name
          - Kategori: Category
          - Soru: Question text
          - Yanıt: Answer (a, b, c, d)
          - Doğru mu: Whether the answer is correct (1 = correct)
        - "Katılımcı" sheet: Contains participant information
          - Katılımcı: Participant name
          - Takım: Team name
          - Başlama Zamanı: Start time
          - Bitirme Zamanı: End time
        - "TEAM" sheet: Contains brick/territory information
          - BRICK: Brick name
          - BRICK CODE: Brick code
          - İL: City
          - BÖLGE: Region
          - PAYLAŞIM: Sharing percentage
          - REP 1: Representative 1
          - REP 2: Representative 2
          - REP 3: Representative 3
        
        This method will:
        1. Import questions from the "Soru" sheet
        2. Import participants from the "Katılımcı" sheet
        3. Import participant answers from the "Yanıt" sheet
        4. Import team data from the "TEAM" sheet
        """
        self.ensure_one()
        if not self.excel_file:
            raise UserError(_("Please upload an Excel file first."))

        try:
            import base64
            import io
            from openpyxl import load_workbook
        except ImportError:
            raise UserError(_("The 'openpyxl' library is required to import Excel files. Please install it (pip install openpyxl)."))

        try:
            # Decode and load the Excel file
            decoded_file = base64.b64decode(self.excel_file)
            workbook = load_workbook(filename=io.BytesIO(decoded_file))
            
            # Check if required sheets exist
            required_sheets = ["Soru", "Yanıt"]
            for sheet_name in required_sheets:
                if sheet_name not in workbook.sheetnames:
                    raise UserError(_("The Excel file must contain a sheet named '%s'.") % sheet_name)
            
            # Check if "Katılımcı" sheet exists
            has_participant_sheet = "Katılımcı" in workbook.sheetnames
            
            # Check if "TEAM" sheet exists
            has_team_sheet = "TEAM" in workbook.sheetnames
            
            # First, process the "Yanıt" sheet to get correct answers for each question
            yanit_sheet = workbook["Yanıt"]
            
            # Get headers for Yanıt sheet
            yanit_headers = [cell.value for cell in yanit_sheet[1]]
            
            # Check required headers for Yanıt sheet
            required_yanit_headers = ["Soru", "Yanıt", "Doğru mu"]
            if not all(header in yanit_headers for header in required_yanit_headers):
                raise UserError(_("The 'Yanıt' sheet must contain the following headers: Soru, Yanıt, Doğru mu."))
            
            # Map headers to indices for Yanıt sheet
            yanit_header_indices = {header: idx for idx, header in enumerate(yanit_headers, 1)}
            
            # Create a dictionary to store correct answers for each question
            correct_answers = {}
            
            # Create a set to store unique questions from the Yanıt sheet
            unique_questions = set()
            
            # Process rows in Yanıt sheet
            for row in yanit_sheet.iter_rows(min_row=2, values_only=True):
                # Skip empty rows
                if not any(row):
                    continue
                
                # Get question text
                question_text = row[yanit_header_indices["Soru"] - 1]
                if not question_text:
                    continue
                
                # Ensure question_text is a string
                question_text = str(question_text) if question_text is not None else ""
                if not question_text.strip():
                    continue
                
                # Add to unique questions set
                unique_questions.add(question_text)
                
                # Get answer and whether it's correct
                answer = row[yanit_header_indices["Yanıt"] - 1]
                is_correct = row[yanit_header_indices["Doğru mu"] - 1]
                
                # If the answer is correct, store it in a list of correct answers
                if is_correct == 1:
                    answer_str = str(answer).strip().lower()
                    if question_text not in correct_answers:
                        correct_answers[question_text] = []
                    if answer_str not in correct_answers[question_text]:
                        correct_answers[question_text].append(answer_str)
            
            # Now process the "Soru" sheet
            soru_sheet = workbook["Soru"]
            
            # Get headers for Soru sheet
            soru_headers = [cell.value for cell in soru_sheet[1]]
            
            # Check required headers for Soru sheet
            required_soru_headers = ["Soru", "A", "B", "C", "D"]
            if not all(header in soru_headers for header in required_soru_headers):
                raise UserError(_("The 'Soru' sheet must contain the following headers: Soru, A, B, C, D."))
            
            # Map headers to indices for Soru sheet
            soru_header_indices = {header: idx for idx, header in enumerate(soru_headers, 1)}
            
            # Get category model
            category_model = self.env['survey.question.poll.category']
            
            # Dictionary to map question text to question ID
            question_map = {}
            
            # Get existing questions to avoid duplicates
            existing_questions = {}
            for question in self.question_ids:
                existing_questions[question.title] = question.id
            
            # Fixed score calculation: 25 questions per participant, 4 points per question
            total_questions = 25  # Fixed number of questions per participant
            score_per_question = 4.0  # Fixed score per question (100/25 = 4)
            
            # Process rows in Soru sheet
            questions_created = 0
            questions_updated = 0
            for row_idx, row in enumerate(soru_sheet.iter_rows(min_row=2, values_only=True), 2):
                # Skip empty rows
                if not any(row):
                    continue
                
                # Get question text
                question_text = row[soru_header_indices["Soru"] - 1]
                if not question_text:
                    continue
                
                # Ensure question_text is a string
                question_text = str(question_text) if question_text is not None else ""
                if not question_text.strip():
                    continue
                
                # Get category
                category_id = False
                if "Kategori" in soru_header_indices and row[soru_header_indices["Kategori"] - 1]:
                    category_name = row[soru_header_indices["Kategori"] - 1]
                    category = category_model.search([
                        '|',
                        '&', ('name', '=', category_name), ('company_id', '=', self.company_id.id),
                        '&', ('name', '=', category_name), ('company_id', '=', False)
                    ], limit=1)
                    
                    if category:
                        category_id = category.id
                    else:
                        # Create new category
                        category = category_model.create({
                            'name': category_name,
                            'company_id': self.company_id.id
                        })
                        category_id = category.id
                
                # Create question
                question_vals = {
                    'title': question_text,
                    'survey_id': self.id,
                    'question_type': 'simple_choice',
                    'category_id': category_id,
                    'suggested_answer_ids': []
                }
                
                # Get correct answers for this question (now a list)
                correct_answer_list = correct_answers.get(question_text, [])
                
                # Add options
                for option_letter in ["A", "B", "C", "D"]:
                    if option_letter in soru_header_indices:
                        option_text = row[soru_header_indices[option_letter] - 1]
                        if option_text:
                            # Check if this option letter is in the list of correct answers
                            is_correct = option_letter.lower() in correct_answer_list
                            
                            question_vals['suggested_answer_ids'].append((0, 0, {
                                'value': option_text,
                                'is_correct': is_correct,
                                'answer_score': score_per_question if is_correct else 0.0
                            }))
                
                # Check if question already exists
                if question_text in existing_questions:
                    # Update existing question
                    question_id = existing_questions[question_text]
                    question = self.env['survey.question'].browse(question_id)
                    
                    # Prepare update values
                    update_vals = {}
                    
                    # Update category if needed
                    if category_id and question.category_id.id != category_id:
                        update_vals['category_id'] = category_id
                    
                    # Update question type if needed
                    if question.question_type != 'simple_choice':
                        update_vals['question_type'] = 'simple_choice'
                    
                    # Update suggested answers if needed
                    suggested_answers = []
                    
                    # Get correct answers for this question (now a list)
                    correct_answer_list = correct_answers.get(question_text, [])
                    
                    for option_letter in ["A", "B", "C", "D"]:
                        if option_letter in soru_header_indices:
                            option_text = row[soru_header_indices[option_letter] - 1]
                            if option_text:
                                # Check if this option letter is in the list of correct answers
                                is_correct = option_letter.lower() in correct_answer_list
                                
                                # Find existing suggested answer
                                existing_answer = False
                                for suggested_answer in question.suggested_answer_ids:
                                    if suggested_answer.value == option_text:
                                        existing_answer = suggested_answer
                                        break
                                
                                if existing_answer:
                                    # Update existing answer
                                    if existing_answer.is_correct != is_correct or existing_answer.answer_score != (score_per_question if is_correct else 0.0):
                                        suggested_answers.append((1, existing_answer.id, {
                                            'is_correct': is_correct,
                                            'answer_score': score_per_question if is_correct else 0.0
                                        }))
                                else:
                                    # Create new answer
                                    suggested_answers.append((0, 0, {
                                        'value': option_text,
                                        'is_correct': is_correct,
                                        'answer_score': score_per_question if is_correct else 0.0
                                    }))
                    
                    if suggested_answers:
                        update_vals['suggested_answer_ids'] = suggested_answers
                    
                    # Update question if needed
                    if update_vals:
                        question.write(update_vals)
                    
                    # Store the question ID with its text for later use
                    question_map[question_text] = question.id
                    questions_updated += 1
                else:
                    # Create new question
                    if question_vals['suggested_answer_ids']:
                        question = self.env['survey.question'].create(question_vals)
                        questions_created += 1
                        
                        # Store the question ID with its text for later use
                        question_map[question_text] = question.id
            
            # Read participant information from "Katılımcı" sheet if it exists
            participant_info = {}
            if has_participant_sheet:
                participant_sheet = workbook["Katılımcı"]
                
                # Get headers for Katılımcı sheet
                participant_headers = [cell.value for cell in participant_sheet[1]]
                
                # Check required headers for Katılımcı sheet
                required_participant_headers = ["Katılımcı", "Takım"]
                if not all(header in participant_headers for header in required_participant_headers):
                    raise UserError(_("The 'Katılımcı' sheet must contain the following headers: Katılımcı, Takım."))
                
                # Map headers to indices for Katılımcı sheet
                participant_header_indices = {header: idx for idx, header in enumerate(participant_headers, 1)}
                
                # Process rows in Katılımcı sheet
                for row in participant_sheet.iter_rows(min_row=2, values_only=True):
                    # Skip empty rows
                    if not any(row):
                        continue
                    
                    participant_name = row[participant_header_indices["Katılımcı"] - 1]
                    if not participant_name:
                        continue
                    
                    # Ensure participant_name is a string
                    participant_name = str(participant_name) if participant_name is not None else ""
                    if not participant_name.strip():
                        continue
                    
                    team_name = row[participant_header_indices["Takım"] - 1] if "Takım" in participant_header_indices else ""
                    
                    # Get score if available
                    score = None
                    if "Puan" in participant_header_indices:
                        score_value = row[participant_header_indices["Puan"] - 1]
                        if score_value is not None:
                            try:
                                score = float(score_value)
                            except (ValueError, TypeError):
                                score = None
                    
                    # Get start and end times if available
                    start_time = None
                    end_time = None
                    
                    if "Başlama Zamanı" in participant_header_indices:
                        start_time_value = row[participant_header_indices["Başlama Zamanı"] - 1]
                        if start_time_value:
                            # Convert to datetime if it's a string
                            if isinstance(start_time_value, str):
                                try:
                                    from datetime import datetime
                                    start_time = datetime.strptime(start_time_value, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    start_time = None
                            else:
                                start_time = start_time_value
                    
                    if "Bitirme Zamanı" in participant_header_indices:
                        end_time_value = row[participant_header_indices["Bitirme Zamanı"] - 1]
                        if end_time_value:
                            # Convert to datetime if it's a string
                            if isinstance(end_time_value, str):
                                try:
                                    from datetime import datetime
                                    end_time = datetime.strptime(end_time_value, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    end_time = None
                            else:
                                end_time = end_time_value
                    
                    participant_info[participant_name] = {
                        'team': team_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'score': score
                    }
            
            # Now import participants and their answers from the "Yanıt" sheet
            participants_data = {}
            
            # Group data by participant
            for row in yanit_sheet.iter_rows(min_row=2, values_only=True):
                # Skip empty rows
                if not any(row):
                    continue
                
                participant_name = row[yanit_header_indices["Katılımcı"] - 1]
                if not participant_name:
                    continue
                
                # Ensure participant_name is a string
                participant_name = str(participant_name) if participant_name is not None else ""
                if not participant_name.strip():
                    continue
                
                team_name = row[yanit_header_indices["Takım"] - 1] if "Takım" in yanit_header_indices else ""
                question_text = row[yanit_header_indices["Soru"] - 1]
                answer = row[yanit_header_indices["Yanıt"] - 1]
                
                if participant_name not in participants_data:
                    participants_data[participant_name] = {
                        'team': team_name,
                        'answers': []
                    }
                
                participants_data[participant_name]['answers'].append({
                    'question_text': question_text,
                    'answer': answer
                })
            
            # Get existing participants to avoid duplicates
            existing_participants = {}
            for user_input in self.env['survey.user_input'].search([('survey_id', '=', self.id)]):
                # Use email as the key for existing participants
                if user_input.email:
                    existing_participants[user_input.email] = user_input.id
            
            # Create user inputs and answers
            participants_created = 0
            participants_updated = 0
            answers_created = 0
            
            # Find or create department based on team_name
            department = self.env['hr.department'].search([
                ('name', '=', team_name),
                '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)
            ], limit=1)
            
            if not department:
                department = self.env['hr.department'].create({
                    'name': team_name,
                    'company_id': self.company_id.id,
                })
            
            # Find or create job position "Rep"
            job_position = self.env['hr.job'].search([
                ('name', '=', 'Rep'),
                '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)
            ], limit=1)
            
            if not job_position:
                job_position = self.env['hr.job'].create({
                    'name': 'Rep',
                    'company_id': self.company_id.id,
                    'department_id': department.id,
                })
            
            # Counter for created and updated employees and users
            employees_created = 0
            employees_updated = 0
            users_created = 0
            users_updated = 0
            
            for participant_name, data in participants_data.items():
                # Get participant info from Katılımcı sheet if available
                info = participant_info.get(participant_name, {})
                team_name = info.get('team', data.get('team', ''))
                start_time = info.get('start_time')
                end_time = info.get('end_time')
                score = info.get('score')
                
                # Format participant name as email address
                # Convert "First Last" to "first.last@nutricia.com"
                if participant_name:
                    # Replace Turkish characters with their English equivalents
                    email_name = participant_name.lower().replace(' ', '.')
                    email_name = email_name.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u')
                    email_name = email_name.replace('ğ', 'g').replace('ş', 's').replace('ç', 'c')
                    email = email_name + '@nutricia.com'
                else:
                    # Handle None or empty participant name
                    email = f"unknown.participant.{participants_created + 1}@nutricia.com"
                
                # Create or find contact (res.partner) for this participant
                partner = self.env['res.partner'].search([
                    ('email', '=', email),
                    '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)
                ], limit=1)
                
                if not partner:
                    # Create new contact
                    partner = self.env['res.partner'].create({
                        'name': participant_name,
                        'email': email,
                        'company_id': self.company_id.id,
                    })
                
                # Create or find user for this participant
                user = self.env['res.users'].search([
                    ('login', '=', email),
                    '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)
                ], limit=1)
                
                if not user:
                    # Check if a user with this partner_id already exists
                    user = self.env['res.users'].search([
                        ('partner_id', '=', partner.id),
                        '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)
                    ], limit=1)
                
                if user:
                    # Update existing user
                    update_vals = {}
                    
                    if user.login != email:
                        update_vals['login'] = email
                    
                    if user.name != participant_name:
                        update_vals['name'] = participant_name
                    
                    if user.partner_id.id != partner.id:
                        update_vals['partner_id'] = partner.id
                    
                    if update_vals:
                        user.write(update_vals)
                        users_updated += 1
                else:
                    try:
                        # Create new user
                        user = self.env['res.users'].create({
                            'name': participant_name,
                            'login': email,
                            'partner_id': partner.id,
                            'company_id': self.company_id.id,
                            'company_ids': [(4, self.company_id.id)],
                            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],  # Internal User group
                        })
                        users_created += 1
                    except Exception as e:
                        # If user creation fails, log the error but continue
                        _logger.error(f"Failed to create user for {participant_name}: {str(e)}")
                        user = None
                
                # Create or find employee for this participant
                employee = self.env['hr.employee'].search([
                    '|', ('work_email', '=', email), ('name', '=', participant_name),
                    '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)
                ], limit=1)
                
                if employee:
                    # Update existing employee
                    update_vals = {}
                    
                    if employee.department_id.id != department.id:
                        update_vals['department_id'] = department.id
                    
                    if employee.job_id.id != job_position.id:
                        update_vals['job_id'] = job_position.id
                    
                    if employee.work_email != email:
                        update_vals['work_email'] = email
                    
                    if employee.name != participant_name:
                        update_vals['name'] = participant_name
                    
                    # Link employee to user if user exists
                    if user and (not employee.user_id or employee.user_id.id != user.id):
                        update_vals['user_id'] = user.id
                    
                    if update_vals:
                        employee.write(update_vals)
                        employees_updated += 1
                else:
                    # Create new employee
                    employee_vals = {
                        'name': participant_name,
                        'work_email': email,
                        'department_id': department.id,
                        'job_id': job_position.id,
                        'company_id': self.company_id.id,
                    }
                    
                    # Link employee to user if user exists
                    if user:
                        employee_vals['user_id'] = user.id
                    
                    employee = self.env['hr.employee'].create(employee_vals)
                    employees_created += 1
                
                # Create the user input (participant)
                user_input_vals = {
                    'survey_id': self.id,
                    'partner_id': partner.id,  # Link to the contact
                    'email': email,  # Also store the email
                    'state': 'done',  # Mark as completed
                    'nickname': participant_name,  # Set nickname to participant name
                }
                
                # Add start and end times if available
                if start_time:
                    user_input_vals['start_datetime'] = start_time
                if end_time:
                    user_input_vals['end_datetime'] = end_time
                
                # Add score if available
                if score is not None:
                    user_input_vals['scoring_percentage'] = score
                
                # Check if participant already exists using email field
                if email in existing_participants:
                    # Update existing participant
                    user_input_id = existing_participants[email]
                    user_input = self.env['survey.user_input'].browse(user_input_id)
                    
                    # Update partner_id, start and end times, and score if needed
                    update_vals = {}
                    
                    # Always update partner_id to ensure it's linked to the contact
                    if user_input.partner_id.id != partner.id:
                        update_vals['partner_id'] = partner.id
                    
                    # Always update nickname to ensure it's set to participant name
                    if user_input.nickname != participant_name:
                        update_vals['nickname'] = participant_name
                    
                    if start_time and not user_input.start_datetime:
                        update_vals['start_datetime'] = start_time
                    if end_time and not user_input.end_datetime:
                        update_vals['end_datetime'] = end_time
                    
                    # Update score if available
                    if score is not None:
                        update_vals['scoring_percentage'] = score
                    
                    if update_vals:
                        user_input.write(update_vals)
                    
                    participants_updated += 1
                else:
                    # Create new participant
                    user_input = self.env['survey.user_input'].create(user_input_vals)
                    participants_created += 1
                
                # Create answers for this participant
                for answer_data in data['answers']:
                    question_text = answer_data['question_text']
                    answer_letter = answer_data['answer']
                    
                    # Skip if question not found
                    if question_text not in question_map:
                        continue
                    
                    question_id = question_map[question_text]
                    question = self.env['survey.question'].browse(question_id)
                    
                    # Find the suggested answer ID based on the letter
                    if not answer_letter:
                        continue  # Skip if answer_letter is None or empty
                        
                    answer_index = ord(answer_letter.lower()) - ord('a')
                    if answer_index < 0 or answer_index >= len(question.suggested_answer_ids):
                        continue
                    
                    suggested_answer = question.suggested_answer_ids[answer_index]
                    
                    # Check if answer already exists
                    existing_answer = self.env['survey.user_input.line'].search([
                        ('user_input_id', '=', user_input.id),
                        ('question_id', '=', question_id)
                    ], limit=1)
                    
                    if existing_answer:
                        # Update existing answer if different
                        if existing_answer.suggested_answer_id.id != suggested_answer.id:
                            existing_answer.write({
                                'suggested_answer_id': suggested_answer.id
                            })
                    else:
                        # Create new answer
                        answer_vals = {
                            'user_input_id': user_input.id,
                            'question_id': question_id,
                            'answer_type': 'suggestion',
                            'suggested_answer_id': suggested_answer.id,
                            # Removed 'value_suggested_row' field as it doesn't exist
                        }
                        
                        self.env['survey.user_input.line'].create(answer_vals)
                        answers_created += 1
            
            # Process TEAM sheet if it exists
            teams_created = 0
            teams_updated = 0
            bricks_created = 0
            bricks_updated = 0
            team_members_created = 0
            team_members_updated = 0
            
            if has_team_sheet:
                # Get the main team name from the Katılımcı sheet
                # Use the first non-empty team name from participant_info
                main_team_name = ""
                for p_info in participant_info.values():
                    if p_info.get('team'):
                        main_team_name = p_info.get('team')
                        break
                
                if not main_team_name:
                    raise UserError(_("No team name found in the Katılımcı sheet. Please ensure the 'Takım' column is filled."))
                
                # Find or create team based on main_team_name
                group_team = self.env['crm.team'].search([('name', '=', main_team_name)], limit=1)
                if not group_team:
                    group_team = self.env['crm.team'].create({
                        'name': main_team_name,
                        'team_type': 'G',  # Group type
                    })
                    teams_created += 1
                else:
                    # Update team_type if needed
                    if group_team.team_type != 'G':
                        group_team.write({'team_type': 'G'})
                    teams_updated += 1
                
                # Dictionary to store regions and their teams
                region_teams = {}
                
                # Dictionary to store representatives and their user IDs
                rep_users = {}
                
                # Get TEAM sheet
                team_sheet = workbook["TEAM"]
                
                # Get headers for TEAM sheet
                team_headers = [cell.value for cell in team_sheet[1]]
                
                # Check required headers for TEAM sheet
                required_team_headers = ["BRICK", "BRICK CODE", "İL", "BÖLGE", "PAYLAŞIM", "REP 1", "REP 2", "REP 3"]
                if not all(header in team_headers for header in required_team_headers):
                    raise UserError(_("The 'TEAM' sheet must contain the following headers: " + ", ".join(required_team_headers)))
                
                # Map headers to indices for TEAM sheet
                team_header_indices = {header: idx for idx, header in enumerate(team_headers, 1)}
                
                # Process rows in TEAM sheet
                for row in team_sheet.iter_rows(min_row=2, values_only=True):
                    # Skip empty rows
                    if not any(row):
                        continue
                    
                    # Get values (safely handle missing columns)
                    brick_name = row[team_header_indices.get("BRICK", 0) - 1] if "BRICK" in team_header_indices else ""
                    brick_code = row[team_header_indices.get("BRICK CODE", 0) - 1] if "BRICK CODE" in team_header_indices else ""
                    city = row[team_header_indices.get("İL", 0) - 1] if "İL" in team_header_indices else ""
                    region = row[team_header_indices["BÖLGE"] - 1]  # BÖLGE is required
                    sharing = row[team_header_indices.get("PAYLAŞIM", 0) - 1] if "PAYLAŞIM" in team_header_indices else ""
                    rep1 = row[team_header_indices["REP 1"] - 1]  # REP 1 is required
                    rep2 = row[team_header_indices.get("REP 2", 0) - 1] if "REP 2" in team_header_indices else ""
                    rep3 = row[team_header_indices.get("REP 3", 0) - 1] if "REP 3" in team_header_indices else ""
                    
                    # Skip if region is empty (only check required fields)
                    if not region:
                        continue
                    
                    # Convert sharing percentage to float
                    if sharing and isinstance(sharing, str):
                        sharing = sharing.replace('%', '').strip()
                        try:
                            sharing = float(sharing)
                        except ValueError:
                            sharing = 100.0
                    else:
                        sharing = 100.0
                    
                    # Find or create region team
                    if region not in region_teams:
                        region_team = self.env['crm.team'].search([
                            ('name', '=', region),
                            ('parent_id', '=', group_team.id)
                        ], limit=1)
                        
                        if not region_team:
                            region_team = self.env['crm.team'].create({
                                'name': region,
                                'parent_id': group_team.id,
                                'team_type': 'R',  # Region type
                            })
                            teams_created += 1
                        else:
                            # Update team_type and parent_id if needed
                            update_vals = {}
                            if region_team.team_type != 'R':
                                update_vals['team_type'] = 'R'
                            if region_team.parent_id.id != group_team.id:
                                update_vals['parent_id'] = group_team.id
                            
                            if update_vals:
                                region_team.write(update_vals)
                            
                            teams_updated += 1
                        
                        region_teams[region] = region_team
                    
                    region_team = region_teams[region]
                    
                    # Process brick information if available
                    brick = None
                    if brick_code:
                        # Ensure brick_code is a string and pad to 7 digits with leading zeros
                        # Convert to string if it's not already
                        if not isinstance(brick_code, str):
                            brick_code = str(int(brick_code))  # Convert to int first to remove any decimal part
                        # Pad with leading zeros to make it 7 digits
                        brick_code = brick_code.zfill(7)
                       
                        # Find or create brick
                        brick = self.env['crm.brick'].search([('code', '=', brick_code)], limit=1)

                        # Find state by name or code
                        state = False
                        if city:
                            # Try to find state by exact name
                            state = self.env['res.country.state'].search([
                                ('name', '=', city),
                                ('country_id', '=', self.env.ref('base.tr').id)  # Turkey
                            ], limit=1)
                            
                            if not state:
                                # Try to find state by name containing the city
                                state = self.env['res.country.state'].search([
                                    ('name', 'ilike', city),
                                    ('country_id', '=', self.env.ref('base.tr').id)  # Turkey
                                ], limit=1)
                                
                            if not state:
                                # Try to find state by code
                                state = self.env['res.country.state'].search([
                                    ('code', 'ilike', city[:3]),  # First 3 characters of city
                                    ('country_id', '=', self.env.ref('base.tr').id)  # Turkey
                                ], limit=1)
                        
                        state_id = state.id if state else False
                        
                        if not brick:
                            brick = self.env['crm.brick'].create({
                                'name': brick_name or brick_code,  # Use code as name if name is empty
                                'code': brick_code,
                                'state_id': state_id,
                                'country_id': self.env.ref('base.tr').id,  # Turkey
                                'active': True,
                            })
                            bricks_created += 1
                        else:
                            # Update brick with missing information
                            update_vals = {}
                            
                            # Update name if different and not empty
                            if brick_name and brick.name != brick_name:
                                update_vals['name'] = brick_name
                            
                            # Update state_id if it's not set or different
                            if state_id and (not brick.state_id or brick.state_id.id != state_id):
                                update_vals['state_id'] = state_id
                        
                        # Update country_id if it's not set
                        if not brick.country_id:
                            update_vals['country_id'] = self.env.ref('base.tr').id
                        
                        if update_vals:
                            brick.write(update_vals)
                        
                        bricks_updated += 1
                    
                    # Process representatives
                    for rep_idx, rep_name in enumerate([rep1, rep2, rep3], 1):
                        if not rep_name or rep_name == '0':
                            continue
                        
                        # Find or create user for representative
                        if rep_name not in rep_users:
                            user = self.env['res.users'].search([('name', '=', rep_name)], limit=1)
                            if not user:
                                # Create partner
                                email_name = rep_name.lower().replace(' ', '.')
                                email_name = email_name.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u')
                                email_name = email_name.replace('ğ', 'g').replace('ş', 's').replace('ç', 'c')
                                email = email_name + '@nutricia.com'
                                
                                # Check if a user with this login already exists
                                existing_user = self.env['res.users'].search([('login', '=', email)], limit=1)
                                if existing_user:
                                    # Use the existing user
                                    user = existing_user
                                else:
                                    # Find or create partner
                                    partner = self.env['res.partner'].search([('email', '=', email)], limit=1)
                                    if not partner:
                                        partner = self.env['res.partner'].create({
                                            'name': rep_name,
                                            'email': email,
                                        })
                                    
                                    # Create user
                                    try:
                                        user = self.env['res.users'].create({
                                            'name': rep_name,
                                            'login': email,
                                            'partner_id': partner.id,
                                            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
                                        })
                                    except Exception as e:
                                        # If user creation fails, use the partner's user if it exists
                                        if partner.user_ids:
                                            user = partner.user_ids[0]
                                        else:
                                            # Try with a unique login
                                            try:
                                                unique_login = email_name + '.' + str(rep_idx) + '@nutricia.com'
                                                user = self.env['res.users'].create({
                                                    'name': rep_name,
                                                    'login': unique_login,
                                                    'partner_id': partner.id,
                                                    'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
                                                })
                                            except Exception as e2:
                                                # Skip this representative
                                                continue
                            
                            rep_users[rep_name] = user
                        
                        user = rep_users[rep_name]
                        
                        # Find or create team member
                        team_member = self.env['crm.team.member'].search([
                            ('user_id', '=', user.id),
                            ('crm_team_id', '=', region_team.id),
                        ], limit=1)
                        
                        if not team_member:
                            team_member = self.env['crm.team.member'].create({
                                'user_id': user.id,
                                'crm_team_id': region_team.id,
                            })
                            team_members_created += 1
                        else:
                            # Update team_id if needed
                            if team_member.crm_team_id.id != region_team.id:
                                team_member.write({'crm_team_id': region_team.id})
                            team_members_updated += 1
                        
                        # Link brick to team member if brick exists
                        if brick:
                            brick.territory_id = team_member.id
            
            # Clear the file after import
            self.excel_file = False
            self.excel_file_name = False
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Successful'),
                    'message': _('Created: %s questions, %s participants, %s answers, %s contacts, %s employees, %s users, %s teams, %s bricks, %s team members\nUpdated: %s questions, %s participants, %s employees, %s users, %s teams, %s bricks, %s team members\nFixed score: 25 questions, 4 points per question\nNote: All questions from Soru sheet are imported, but each participant only has answers for their 25 assigned questions\nParticipant scores are imported from the "Puan" column in the Katılımcı sheet\nEmployees created with Department based on team name and Job Position "Rep"\nEmployees linked to users and contacts for full integration\nTeam data imported from TEAM sheet with regions\nReimporting updates existing records instead of creating duplicates') % (
                        questions_created, participants_created, answers_created, len(participants_data) - participants_updated,
                        employees_created, users_created, teams_created, bricks_created, team_members_created,
                        questions_updated, participants_updated, employees_updated, users_updated, teams_updated, bricks_updated, team_members_updated
                    ),
                    'sticky': False,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            # Clear the file after import
            self.excel_file = False
            self.excel_file_name = False
            
            # Re-raise the exception with a user-friendly message
            raise UserError(_("Error processing Excel file: %s") % str(e))
            raise UserError(_("Error processing Excel file: %s") % str(e))

    session_timeout_minutes = fields.Integer(
        string=_('Session Timeout (minutes)'),
        help=_("Automatically end the survey session after this many minutes of inactivity. Set to 0 for no timeout."),
        default=0
    )
    

    full_screen_mode = fields.Boolean(
        string=_('Full Screen Mode'),
        help=_("If enabled, the survey will attempt to run in full screen mode, preventing users from switching to other applications during the exam."),
        default=False
    )

    disable_copy_paste = fields.Boolean(
        string=_('Disable Copy/Paste'),
        help=_("If enabled, right-click and copy/cut/paste operations will be disabled during the exam."),
        default=False
    )

    disable_dev_tools = fields.Boolean(
        string=_('Disable Developer Tools'),
        help=_("If enabled, F12 and other developer tools access will be restricted during the exam."),
        default=False
    )

    disable_print_screen = fields.Boolean(
        string=_('Disable Print Screen'),
        help=_("If enabled, attempts to take screenshots using the Print Screen key will be restricted during the exam."),
        default=False
    )

    detect_tab_switching = fields.Boolean(
        string=_('Detect Tab Switching'),
        help=_("If enabled, the system will detect when the user switches to another browser tab or application during the exam."),
        default=False
    )

    # Penalty and Limit Settings
    penalty_fullscreen_exit = fields.Integer(string=_("Penalty for Fullscreen Exit"), default=0, help=_("Points deducted each time user exits fullscreen."))
    penalty_tab_switch = fields.Integer(string=_("Penalty for Tab Switch"), default=0, help=_("Points deducted each time user switches tab/focus."))
    penalty_devtools_attempt = fields.Integer(string=_("Penalty for Dev Tools Attempt"), default=0, help=_("Points deducted for attempting to use developer tools."))
    penalty_print_screen_attempt = fields.Integer(string=_("Penalty for Print Screen Attempt"), default=0, help=_("Points deducted for attempting to use print screen."))
    # Note: Copy/Paste is preventative, so direct penalty per attempt is harder. Could be a fixed penalty if any circumvention is detected server-side later.

    max_total_violations_allowed = fields.Integer(
        string=_("Max Allowed Violations"),
        default=0,
        help=_("Maximum number of cumulative security violations allowed before the survey is automatically submitted. 0 means no limit.")
    )
    max_total_penalty_points = fields.Integer(
        string=_("Max Total Penalty Points"),
        default=0,
        help=_("Maximum total penalty points that can be accumulated. If 0, no limit to penalty points, but survey might end due to violation count.")
    )

    @api.onchange('full_screen_mode', 'disable_copy_paste', 'disable_dev_tools', 'detect_tab_switching', 'disable_print_screen')
    def _onchange_update_security_description(self):
        """
        Updates the survey description with security rules based on enabled security features.
        Uses plain text formatting in Turkish language.
        """
        # Build list of security messages based on enabled features
        messages = []
        
        if self.full_screen_mode:
            if self.penalty_fullscreen_exit > 0:
                messages.append(f"Tam Ekran Modu: Bu sınav tam ekran modunda alınmalıdır. Tam ekrandan çıkış ihlali, her seferinde {self.penalty_fullscreen_exit} ceza puanına neden olur.")
            else:
                messages.append("Tam Ekran Modu: Bu sınav tam ekran modunda alınmalıdır. Tam ekrandan çıkış ceza puanlarına neden olabilir.")
                
        if self.detect_tab_switching:
            if self.penalty_tab_switch > 0:
                messages.append(f"Sekme Değiştirme Tespiti: Sınav penceresinden uzaklaşmak veya sekme değiştirmek tespit edilmektedir ve ihlali, her seferinde {self.penalty_tab_switch} ceza puanına neden olacaktır.")
            else:
                messages.append("Sekme Değiştirme Tespiti: Sınav penceresinden uzaklaşmak veya sekme değiştirmek tespit edilmektedir ve ceza puanlarına neden olabilir.")
                
        if self.disable_copy_paste:
            messages.append("Kopyala/Yapıştır Devre Dışı: İçeriği kopyalama, kesme veya yapıştırma işlemleri yasaktır.")
            
        if self.disable_print_screen:
            if self.penalty_print_screen_attempt > 0:
                messages.append(f"Ekran Görüntüsü Devre Dışı: Print Screen tuşunu kullanarak ekran görüntüsü alma girişimleri yasaktır. İhlali, her seferinde {self.penalty_print_screen_attempt} ceza puanına neden olacaktır.")
            else:
                messages.append("Ekran Görüntüsü Devre Dışı: Print Screen tuşunu kullanarak ekran görüntüsü alma girişimleri yasaktır.")
                
        if self.disable_dev_tools:
            if self.penalty_devtools_attempt > 0:
                messages.append(f"Geliştirici Araçları Devre Dışı: Tarayıcı geliştirici araçlarına erişim yasaktır. İhlali {self.penalty_devtools_attempt} ceza puanına neden olacaktır.")
            else:
                messages.append("Geliştirici Araçları Devre Dışı: Tarayıcı geliştirici araçlarına erişim yasaktır.")

        # Create a plain text security section if there are messages
        if messages:
            # Create a plain text security section in Turkish
            security_text = "ÖNEMLİ GÜVENLİK UYARILARI:\n\n"
            
            for msg in messages:
                security_text += "• " + msg + "\n"
            
            # Set the description directly
            self.description = security_text
        else:
            # No security features enabled, clear the description
            self.description = ""


    def _can_go_back(self, answer, page_or_question):
        self.ensure_one()
        if self.questions_layout == "one_page" or not self.users_can_go_back:
            return False
        if answer.state != 'in_progress' or answer.is_session_answer:
            return False

        # Determine the list of questions/pages relevant for navigation
        if self.questions_layout == 'page_per_section':
            # For 'page_per_section', navigation is based on survey.page_ids
            if self.page_ids and page_or_question == self.page_ids[0]:
                return False
            return True # Can go back if not first page
        else: # 'page_per_question'
            # For 'page_per_question', navigation is based on question_ids
            # Use predefined_question_ids if random, otherwise survey.question_ids
            if not answer.is_session_answer and self.questions_selection == 'random':
                relevant_questions = answer.predefined_question_ids
            else:
                relevant_questions = self.question_ids

            if relevant_questions and page_or_question == relevant_questions[0]:
                return False
            return True # Can go back if not first question in the relevant list

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        related='survey_id.company_id',
        store=True,
        readonly=True
    )
    
    is_terminated = fields.Boolean(
        string=_('Terminated Due to Security Violation'),
        help=_("Indicates if this survey session was terminated due to a security violation."),
        default=False
    )
    
    # Violation Counters per type
    fullscreen_violation_count = fields.Integer(string=_("Fullscreen Exit Count"), default=0, readonly=True)
    tab_switch_violation_count = fields.Integer(string=_("Tab Switch/Focus Loss Count"), default=0, readonly=True)
    devtools_attempt_count = fields.Integer(string=_("Dev Tools Attempt Count"), default=0, readonly=True)
    print_screen_attempt_count = fields.Integer(string=_("Print Screen Attempt Count"), default=0, readonly=True)
    # copy_paste_attempt_count - Harder to track distinct "attempts" if successfully blocked.
    
    exclude_from_statistics = fields.Boolean(
        string=_('Exclude from Statistics'),
        help=_("If checked, this participant will be excluded from region average calculations"),
        default=False
    )

    total_security_violations = fields.Integer(
        string=_('Total Security Violations'),
        compute='_compute_total_security_violations',
        store=True,
        help=_("Total number of all types of security violations detected during this survey session.")
    )
    
    accumulated_penalty_points = fields.Integer(string=_("Accumulated Penalty Points"), default=0, readonly=True)

    @api.depends('fullscreen_violation_count', 'tab_switch_violation_count', 'devtools_attempt_count', 'print_screen_attempt_count')
    def _compute_total_security_violations(self):
        for record in self:
            record.total_security_violations = (
                record.fullscreen_violation_count +
                record.tab_switch_violation_count +
                record.devtools_attempt_count +
                record.print_screen_attempt_count
            )

    def _get_penalty_for_violation(self, violation_type):
        self.ensure_one()
        survey_sudo = self.survey_id.sudo()
        if violation_type == 'fullscreen_exit':
            return survey_sudo.penalty_fullscreen_exit
        elif violation_type == 'tab_switch':
            return survey_sudo.penalty_tab_switch
        elif violation_type == 'devtools_attempt':
            return survey_sudo.penalty_devtools_attempt
        elif violation_type == 'print_screen_attempt':
            return survey_sudo.penalty_print_screen_attempt
        return 0

    def log_security_violation(self, violation_type):
        """
        Log a security violation, increment its counter, apply penalty, and check limits.
        Returns True if the survey was terminated as a result, False otherwise.
        """
        self.ensure_one()
        if self.state != 'in_progress':
            return False # Cannot log violations for already completed/terminated surveys

        vals_to_write = {}
        current_penalty = self._get_penalty_for_violation(violation_type)
        new_accumulated_penalty = self.accumulated_penalty_points + current_penalty

        if violation_type == 'fullscreen_exit':
            vals_to_write['fullscreen_violation_count'] = self.fullscreen_violation_count + 1
        elif violation_type == 'tab_switch':
            vals_to_write['tab_switch_violation_count'] = self.tab_switch_violation_count + 1
        elif violation_type == 'devtools_attempt':
            vals_to_write['devtools_attempt_count'] = self.devtools_attempt_count + 1
        elif violation_type == 'print_screen_attempt':
            vals_to_write['print_screen_attempt_count'] = self.print_screen_attempt_count + 1
        else:
            # For unknown types, or generic violations if you keep the old field
            # self.security_violations += 1 # This field is now computed
            pass
        
        if current_penalty > 0:
            max_penalty = self.survey_id.sudo().max_total_penalty_points
            if max_penalty > 0 and new_accumulated_penalty > max_penalty:
                new_accumulated_penalty = max_penalty
            vals_to_write['accumulated_penalty_points'] = new_accumulated_penalty
        
        # Note: The 'note' field was removed as it doesn't exist on the base survey.user_input model.
        # If detailed textual logging per violation on the user_input record is needed,
        # a 'note' or similar Text field should be added to the SurveyUserInput model extension.
        # For now, we rely on the specific violation counters and accumulated penalty points.
        
        self.write(vals_to_write) # Write accumulated changes

        # Recompute total violations after individual counts are updated
        # The @api.depends should handle this if store=True, but explicit recompute can be safer if called within same transaction.
        # self._compute_total_security_violations() # Not strictly needed if store=True and ORM handles it.

        # Check if the overall violation limit is reached
        # Need to access the recomputed total_security_violations or sum them manually here for the check
        current_total_violations = (
            self.fullscreen_violation_count +
            self.tab_switch_violation_count +
            self.devtools_attempt_count +
            self.print_screen_attempt_count
        ) # This uses values before potential write if not re-read.
        # It's better to sum the new values based on vals_to_write
        
        updated_total_violations = sum([
            vals_to_write.get('fullscreen_violation_count', self.fullscreen_violation_count),
            vals_to_write.get('tab_switch_violation_count', self.tab_switch_violation_count),
            vals_to_write.get('devtools_attempt_count', self.devtools_attempt_count),
            vals_to_write.get('print_screen_attempt_count', self.print_screen_attempt_count),
        ])

        max_allowed = self.survey_id.sudo().max_total_violations_allowed
        if max_allowed > 0 and updated_total_violations >= max_allowed:
            if self.state == 'in_progress': # Double check state before terminating
                self.write({
                    'state': 'done',
                    'is_terminated': True
                    # Note: Removed note update here as well.
                    # A custom message could be logged to server logs if needed:
                    # _logger.info(f"Survey (User Input ID: {self.id}) auto-submitted. Exceeded max violations ({updated_total_violations}/{max_allowed}).")
                })
                return True # Survey terminated
        
        return False # Survey not terminated by this violation