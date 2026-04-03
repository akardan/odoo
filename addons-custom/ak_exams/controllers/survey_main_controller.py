from odoo import http
from odoo.http import request
from odoo.addons.survey.controllers.main import Survey
import logging

class SurveyExtension(Survey):

    @http.route('/survey/submit/<string:survey_token>/<string:access_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, access_token, **post):
        user_input = request.env['survey.user_input'].sudo().search([('access_token', '=', access_token)], limit=1)
        survey = user_input.survey_id if user_input else None

        # Check time limits BEFORE calling parent
        if survey and user_input and user_input.state == 'in_progress' and user_input.start_datetime:
            from datetime import datetime
            import pytz
            
            # Get current time
            now_utc = datetime.now(pytz.UTC)
            
            # Ensure start_datetime is timezone-aware
            start_dt = user_input.start_datetime
            if start_dt.tzinfo is None:
                start_dt = pytz.UTC.localize(start_dt)
            
            # Calculate elapsed time since participant started
            time_elapsed_minutes = (now_utc - start_dt).total_seconds() / 60
            
            # CHECK 1: Individual time limit (from participant's start time)
            if survey.is_time_limited and survey.time_limit > 0:
                if time_elapsed_minutes > survey.time_limit:
                    logging.getLogger(__name__).warning(
                        f"TIME LIMIT EXCEEDED! User {user_input.id} exceeded {survey.time_limit} min limit - marking as done"
                    )
                    # Mark as done
                    user_input.sudo().write({'state': 'done'})
                    # Return as tuple: (correct_answers, question_html) - same format as Odoo
                    return {}, self._prepare_question_html(survey, user_input, **post)
            
            # CHECK 2: Global end date (survey closes for everyone)
            if survey.end_date:
                end_date_utc = pytz.UTC.localize(survey.end_date) if survey.end_date.tzinfo is None else survey.end_date
                
                if now_utc > end_date_utc:
                    logging.getLogger(__name__).warning(
                        f"EXAM END DATE PASSED! User {user_input.id} - Survey closed at {end_date_utc} - marking as done"
                    )
                    # Mark as done
                    user_input.sudo().write({'state': 'done'})
                    # Return as tuple: (correct_answers, question_html) - same format as Odoo
                    return {}, self._prepare_question_html(survey, user_input, **post)

        # REMOVED: Session Timeout Logic - This was causing premature exam closure
        # The session_timeout_minutes field is kept for potential future use, but the check is disabled
        # Use time_limit (is_time_limited) for exam duration control instead
        #
        # Issue: session_timeout_minutes was being treated as total elapsed time instead of inactivity timeout,
        # and when set lower than time_limit (e.g., 5 min vs 25 min), it would close exams prematurely.
        #
        # if survey and survey.session_timeout_minutes > 0:
        #     ...session timeout logic removed...

        # Capture IP address and save it to survey.user_input
        if request.httprequest.remote_addr and user_input:
            user_input.sudo().write({'ip_address': request.httprequest.remote_addr})

        # Call the original method to handle survey submission logic
        res = super(SurveyExtension, self).survey_submit(survey_token, access_token, **post)
        
        # DISABLED: Rollback logic has been temporarily disabled for testing
        # This was preventing surveys from being marked as 'done' properly
        
        # OLD CODE (COMMENTED OUT FOR TESTING):
        # if user_input and user_input.state == 'done' and not post.get('button_submit'):
        #     if isinstance(res, dict) and res.get('survey_content') and 'survey_fill_form_done' in str(res.get('survey_content', '')):
        #         pass
        #     else:
        #         answered_question_ids = user_input.user_input_line_ids.mapped('question_id').ids
        #         required_question_ids = survey.question_ids.filtered(lambda q: q.constr_mandatory).ids
        #         if required_question_ids and not all(qid in answered_question_ids for qid in required_question_ids):
        #             user_input.sudo().write({'state': 'in_progress'})
        
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
                    # Katılımcının tamamlanmış cevabı varsa ve scoring_type sonuç göstermeye izin veriyorsa
                    # direkt review sayfasına yönlendir
                    answer_token = post.get('answer_token')
                    if answer_token:
                        answer_sudo = request.env['survey.user_input'].sudo().search([
                            ('access_token', '=', answer_token),
                            ('survey_id', '=', survey_sudo.id),
                            ('state', '=', 'done'),
                        ], limit=1)
                        if answer_sudo and survey_sudo.scoring_type in ['scoring_with_answers', 'scoring_with_answers_after_page']:
                            return request.redirect('/survey/print/%s?answer_token=%s&review=True' % (
                                survey_sudo.access_token, answer_sudo.access_token))
                    # Sonuç gösterimi yoksa veya cevap bulunamadıysa hata sayfası göster
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

        # Check if survey has end_date and is time limited for JS timer - calculate remaining time and pass to template
        if (survey_sudo.end_date or survey_sudo.is_time_limited) and answer_sudo.state == 'in_progress':
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