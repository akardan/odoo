from odoo import http
from odoo.http import request
from odoo.addons.survey.controllers.main import Survey

class SurveyExtension(Survey):

    @http.route('/survey/submit/<string:survey_token>/<string:access_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, access_token, **post):
        user_input = request.env['survey.user_input'].sudo().search([('access_token', '=', access_token)], limit=1)
        survey = user_input.survey_id if user_input else None

        # Session Timeout Logic for Certification Surveys
        if survey and survey.certification and survey.session_timeout_minutes > 0:
            if user_input.start_datetime:
                from datetime import datetime, timedelta
                time_elapsed = (datetime.now() - user_input.start_datetime).total_seconds() / 60
                if time_elapsed > survey.session_timeout_minutes:
                    user_input.sudo().write({'state': 'done'})
                    # Redirect to a timeout page or survey done page
                    return request.redirect(survey.get_print_url()) # Or a custom timeout URL

        # Capture IP address and save it to survey.user_input
        if request.httprequest.remote_addr and user_input:
            user_input.sudo().write({'ip_address': request.httprequest.remote_addr})

        # Call the original method to handle survey submission logic
        res = super(SurveyExtension, self).survey_submit(survey_token, access_token, **post)
        return res

    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, **post):
        # Call the original method
        res = super(SurveyExtension, self).survey_start(survey_token, **post)

        # No need to modify the context as we're directly adding data attributes in the template
        return res
    
    def _prepare_question_html(self, survey, user_input, **kwargs):
        """Override to use randomized answers"""
        result = super()._prepare_question_html(survey, user_input, **kwargs)
        
        # If randomization is enabled, use randomized suggested answers
        if survey.enable_question_randomization and survey.randomize_answer_order:
            # Get the current question from the result context
            if hasattr(result, 'qcontext') and 'question' in result.qcontext:
                question = result.qcontext['question']
                if question.question_type == 'simple_choice':
                    randomized_answers = question.get_randomized_suggested_answers(user_input.id)
                    result.qcontext['question'].suggested_answer_ids = randomized_answers
        
        return result
    
    def _get_survey_questions(self, survey, user_input, page_or_question_key=None):
        """Override to use randomized questions"""
        if survey.enable_question_randomization and user_input.predefined_question_ids:
            # Use randomized questions for this participant
            return user_input.predefined_question_ids.filtered(lambda q: not q.is_page)
        
        return super()._get_survey_questions(survey, user_input, page_or_question_key)