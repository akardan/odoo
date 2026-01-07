from odoo import http
from odoo.http import request
from odoo.addons.survey.controllers.main import Survey
import logging

class SurveyExtension(Survey):

    @http.route('/survey/submit/<string:survey_token>/<string:access_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, access_token, **post):
        user_input = request.env['survey.user_input'].sudo().search([('access_token', '=', access_token)], limit=1)
        survey = user_input.survey_id if user_input else None

        if survey and user_input and user_input.start_datetime:
            from datetime import datetime
            import pytz
            
            # Check if time limit exceeded
            if survey.is_time_limited and survey.time_limit > 0:
                time_elapsed = (datetime.now() - user_input.start_datetime).total_seconds() / 60
                
                # Also check end_date if set
                if survey.end_date:
                    now_utc = datetime.now(pytz.UTC)
                    end_date_utc = pytz.UTC.localize(survey.end_date) if survey.end_date.tzinfo is None else survey.end_date
                    time_remaining_minutes = (end_date_utc - now_utc).total_seconds() / 60
                    
                    # Use the shorter of the two limits
                    effective_limit = min(survey.time_limit, time_remaining_minutes) if time_remaining_minutes > 0 else survey.time_limit
                else:
                    effective_limit = survey.time_limit
                
                if time_elapsed > effective_limit:
                    # Time limit exceeded - mark survey as done
                    user_input.sudo().write({'state': 'done'})
                    return {
                        'error': 'time_expired',
                        'error_message': 'Süreniz doldu. Sınav otomatik olarak sonlandırıldı.'
                    }
            
            # Check if end_date passed
            if survey.end_date:
                now_utc = datetime.now(pytz.UTC)
                end_date_utc = pytz.UTC.localize(survey.end_date) if survey.end_date.tzinfo is None else survey.end_date
                
                if now_utc > end_date_utc:
                    # Survey end date passed - mark as done
                    user_input.sudo().write({'state': 'done'})
                    return {
                        'error': 'exam_closed',
                        'error_message': 'Sınav süresi sona erdi. Sınav otomatik olarak sonlandırıldı.'
                    }

        # Session Timeout Logic for Certification Surveys
        if survey and survey.session_timeout_minutes > 0:
            if user_input.start_datetime:
                from datetime import datetime, timedelta
                time_elapsed = (datetime.now() - user_input.start_datetime).total_seconds() / 60
                if time_elapsed > survey.session_timeout_minutes:
                    user_input.sudo().write({'state': 'done'})
                    return {
                        'error': 'session_timeout',
                        'error_message': 'Oturum zaman aşımına uğradı.'
                    }

        # Capture IP address and save it to survey.user_input
        if request.httprequest.remote_addr and user_input:
            user_input.sudo().write({'ip_address': request.httprequest.remote_addr})

        # Call the original method to handle survey submission logic
        res = super(SurveyExtension, self).survey_submit(survey_token, access_token, **post)
        return res

    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, **post):
        # Get survey to check date/time restrictions
        survey_sudo = request.env['survey.survey'].sudo().search([('access_token', '=', survey_token)], limit=1)
        
        if survey_sudo and (survey_sudo.start_date or survey_sudo.end_date):
            from datetime import datetime
            import pytz
            
            # Get current time in company timezone
            company_tz = survey_sudo.company_id.resource_calendar_id.tz or survey_sudo.company_id.partner_id.tz or 'UTC'
            tz = pytz.timezone(company_tz)
            now_utc = datetime.now(pytz.UTC)
            now_company = now_utc.astimezone(tz)
            
            # Convert start_date and end_date to company timezone for comparison
            if survey_sudo.start_date:
                start_date_utc = pytz.UTC.localize(survey_sudo.start_date) if survey_sudo.start_date.tzinfo is None else survey_sudo.start_date
                start_date_company = start_date_utc.astimezone(tz)
                
                if now_company < start_date_company:
                    # Survey hasn't started yet
                    return request.render('ak_exams.survey_date_error', {
                        'survey': survey_sudo,
                        'error_message': 'Bu sınav henüz başlamamıştır. Başlama tarihi: %s' % start_date_company.strftime('%d-%m-%Y %H:%M')
                    })
            
            if survey_sudo.end_date:
                end_date_utc = pytz.UTC.localize(survey_sudo.end_date) if survey_sudo.end_date.tzinfo is None else survey_sudo.end_date
                end_date_company = end_date_utc.astimezone(tz)
                
                if now_company > end_date_company:
                    # Survey has ended
                    return request.render('ak_exams.survey_date_error', {
                        'survey': survey_sudo,
                        'error_message': 'Bu sınav sona ermiştir. Bitiş tarihi: %s' % end_date_company.strftime('%d-%m-%Y %H:%M')
                    })
        
        # Call the original method
        res = super(SurveyExtension, self).survey_start(survey_token, **post)

        # No need to modify the context as we're directly adding data attributes in the template
        return res
    
    def _prepare_survey_data(self, survey_sudo, answer_sudo, **post):
        """Override to adjust time_limit based on end_date and inject user_input_id in context for answer randomization"""
        # Set user_input_id in context for answer randomization
        if answer_sudo and survey_sudo.randomize_answer_order:
            survey_sudo = survey_sudo.with_context(user_input_id=answer_sudo.id)
        
        # Call parent method to get the base survey data
        data = super(SurveyExtension, self)._prepare_survey_data(survey_sudo, answer_sudo, **post)

        # Custom logic for answer randomization to prevent re-shuffling
        if answer_sudo and survey_sudo.randomize_answer_order:
            import json
            import random

            if not answer_sudo.randomized_question_ids:
                randomized_data = {}
                questions = survey_sudo.question_ids.filtered(lambda q: q.question_type in ['simple_choice', 'multiple_choice'])
                for question in questions:
                    answer_ids = question.suggested_answer_ids.ids
                    random.shuffle(answer_ids)
                    randomized_data[str(question.id)] = answer_ids
                answer_sudo.randomized_question_ids = json.dumps(randomized_data)

        # Check if survey has end_date and is time limited
        if survey_sudo.end_date and survey_sudo.is_time_limited and answer_sudo.state == 'in_progress':
            from datetime import datetime
            import pytz
            
            # Get current time
            now_utc = datetime.now(pytz.UTC)
            
            # Convert end_date to timezone-aware if needed
            end_date_utc = pytz.UTC.localize(survey_sudo.end_date) if survey_sudo.end_date.tzinfo is None else survey_sudo.end_date
            
            # Calculate time remaining until end_date (in minutes)
            time_remaining_seconds = (end_date_utc - now_utc).total_seconds()
            time_remaining_minutes = time_remaining_seconds / 60
            
            # If time remaining is less than the configured time_limit, use the remaining time
            if time_remaining_minutes > 0 and time_remaining_minutes < survey_sudo.time_limit:
                data['time_limit_minutes'] = time_remaining_minutes
        
        # Set randomized answers directly in data for template
        if answer_sudo and survey_sudo.randomize_answer_order and 'question' in data:
            question = data['question']
            if question.question_type == 'simple_choice':
                randomized_answers = survey_sudo._get_randomized_suggested_answers(question, answer_sudo.id)
                data['randomized_suggested_answer_ids'] = randomized_answers
        
        # OVERRIDE survey_last for randomized sequences - this controls submit button
        if 'question' in data and survey_sudo.questions_layout == 'page_per_question':
            question = data['question']
            if survey_sudo.enable_question_randomization and answer_sudo.randomized_question_sequence:
                # Use randomized sequence to determine if this is the last question
                randomized_ids = [int(qid) for qid in answer_sudo.randomized_question_sequence.split(',') if qid.strip()]
                if question.id in randomized_ids:
                    current_position = randomized_ids.index(question.id)
                    data['survey_last'] = current_position == len(randomized_ids) - 1
                else:
                    data['survey_last'] = False
            elif survey_sudo.enable_question_randomization and answer_sudo.predefined_question_ids:
                # Use predefined questions for last question check
                predefined_ids = answer_sudo.predefined_question_ids.ids
                if question.id in predefined_ids:
                    current_position = predefined_ids.index(question.id)
                    data['survey_last'] = current_position == len(predefined_ids) - 1
                else:
                    data['survey_last'] = False
        
        # CRITICAL FIX: Ensure can_go_back is always set when question is present
        # This fixes the issue where back button stays disabled until F5 refresh
        if 'question' in data and 'can_go_back' not in data:
            question = data['question']
            data['can_go_back'] = survey_sudo._can_go_back(answer_sudo, question)
        
        return data
    
    def _prepare_question_html(self, survey_sudo, answer_sudo, **post):
        """Override to handle randomized questions and fix progress calculation"""
        # Call parent to get survey_data
        survey_data = self._prepare_survey_data(survey_sudo, answer_sudo, **post)

        if answer_sudo.state == 'done':
            survey_content = request.env['ir.qweb']._render('survey.survey_fill_form_done', survey_data)
        else:
            survey_content = request.env['ir.qweb']._render('survey.survey_fill_form_in_progress', survey_data)

        survey_progress = False
        if answer_sudo.state == 'in_progress' and not survey_data.get('question', request.env['survey.question']).is_page:
            if survey_sudo.questions_layout == 'page_per_section':
                page_ids = survey_sudo.page_ids.ids
                survey_progress = request.env['ir.qweb']._render('survey.survey_progression', {
                    'survey': survey_sudo,
                    'page_ids': page_ids,
                    'page_number': page_ids.index(survey_data['page'].id) + (1 if survey_sudo.progression_mode == 'number' else 0)
                })
            elif survey_sudo.questions_layout == 'page_per_question':
                # Check for custom randomization first, then standard randomization
                if survey_sudo.enable_question_randomization and answer_sudo.randomized_question_sequence:
                    # Custom randomization - use randomized sequence
                    page_ids = [int(qid) for qid in answer_sudo.randomized_question_sequence.split(',') if qid.strip()]
                elif survey_sudo.enable_question_randomization and answer_sudo.predefined_question_ids:
                    # Custom randomization - use predefined questions
                    page_ids = answer_sudo.predefined_question_ids.ids
                elif not answer_sudo.is_session_answer and survey_sudo.questions_selection == 'random':
                    # Standard Odoo randomization
                    page_ids = answer_sudo.predefined_question_ids.ids
                else:
                    # No randomization
                    page_ids = survey_sudo.question_ids.ids
                
                # Only render progress if current question is in the page_ids
                if survey_data.get('question') and survey_data['question'].id in page_ids:
                    # Use 0-based index like Odoo's original template
                    page_number = page_ids.index(survey_data['question'].id)
                    
                    survey_progress = request.env['ir.qweb']._render('survey.survey_progression', {
                        'survey': survey_sudo,
                        'page_ids': page_ids,
                        'page_number': page_number
                    })

        background_image_url = survey_sudo.background_image_url
        if 'question' in survey_data:
            background_image_url = survey_data['question'].background_image_url
        elif 'page' in survey_data:
            background_image_url = survey_data['page'].background_image_url

        return {
            'has_skipped_questions': any(answer_sudo._get_skipped_questions()),
            'survey_content': survey_content,
            'survey_progress': survey_progress,
            'survey_navigation': request.env['ir.qweb']._render('survey.survey_navigation', survey_data),
            'background_image_url': background_image_url,
        }