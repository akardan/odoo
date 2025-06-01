from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class SurveySecurityController(http.Controller):
    
    @http.route('/survey/security/log', type='json', auth='public', website=True)
    def log_security_event(self): # Changed signature
        """
        Endpoint to log security-related events from the client side.
        This method calls the log_security_violation method on the survey.user_input model.
        """
        try:
            raw_body = request.httprequest.data.decode('utf-8')
            payload = json.loads(raw_body)
            _logger.info("Raw request body for /survey/security/log: %s", raw_body)
            _logger.info("Parsed payload for /survey/security/log: %s", payload)
        except Exception as e:
            _logger.error("Error decoding/parsing JSON payload: %s. Raw body: %s", e, request.httprequest.data)
            return {'success': False, 'error': 'Invalid JSON payload'}

        access_token = payload.get('access_token')
        event_type = payload.get('event_type')
        event_data = payload.get('event_data', {})

        if not event_type or not access_token:
            _logger.warning("Security log attempt with missing event_type or access_token. Event: %s, Token: %s, Parsed Payload: %s", event_type, access_token, payload)
            return {'success': False, 'error': 'Missing required parameters (event_type, access_token)'}

        user_input = request.env['survey.user_input'].sudo().search([
            ('access_token', '=', access_token)
        ], limit=1)

        if not user_input:
            _logger.warning("Security log attempt with invalid access_token: %s", access_token)
            return {'success': False, 'error': 'Invalid access token'}

        if user_input.state != 'in_progress':
            _logger.info("Security log attempt for non-active survey (User Input ID: %s, State: %s)", user_input.id, user_input.state)
            return {'success': False, 'error': 'Survey is not in progress.', 'survey_state': user_input.state}

        _logger.info(
            'Security event received for survey %s (User Input ID: %s, Access Token: %s): Type: %s, Data: %s',
            user_input.survey_id.title, user_input.id, access_token, event_type, json.dumps(event_data or {})
        )

        try:
            # JavaScript sends event_types that should directly match model violation_types
            # Define valid model violation types to check against
            VALID_MODEL_VIOLATION_TYPES = {
                'fullscreen_exit',
                'tab_switch',
                'devtools_attempt',
                'print_screen_attempt',
                'copy_paste_attempt'
                # Add any other distinct violation types the model's log_security_violation handles
            }

            model_violation_type = event_type # Directly use event_type from JS

            if model_violation_type not in VALID_MODEL_VIOLATION_TYPES:
                _logger.warning(
                    "Invalid or unknown security event_type '%s' received for User Input ID: %s. Expected one of %s.",
                    event_type, user_input.id, VALID_MODEL_VIOLATION_TYPES
                )
                return {'success': False, 'error': f'Invalid event_type: {event_type}'}

            result = user_input.log_security_violation(violation_type=model_violation_type)
            
            _logger.info("Violation log result for User Input ID %s (True if terminated, False otherwise): %s", user_input.id, result)

            if result is True: # Survey was terminated by the model
                return {
                    'success': True,
                    'action': 'terminate',
                    'message': 'Survey has been terminated due to security violations.'
                }
            else: # Violation logged, survey not terminated
                return {
                    'success': True,
                    'action': 'logged',
                    'message': 'Security violation logged.'
                }

        except Exception as e:
            _logger.error(
                "Error processing security event for User Input ID %s: %s",
                user_input.id, str(e), exc_info=True
            )
            return {'success': False, 'error': 'Internal server error while processing event.'}

    @http.route('/survey/security/check', type='json', auth='public', website=True)
    def check_security_requirements(self, **post):
        """
        Endpoint to check if the client meets all security requirements
        Returns the security settings that should be enforced
        """
        access_token = post.get('access_token')
        
        if not access_token:
            return {'success': False, 'error': 'Missing access token'}
        
        # Find the user input (survey session) based on access token
        user_input = request.env['survey.user_input'].sudo().search([
            ('access_token', '=', access_token)
        ], limit=1)
        
        if not user_input:
            return {'success': False, 'error': 'Invalid access token'}
        
        survey = user_input.survey_id
        
        # Return the security settings for this survey
        return {
            'success': True,
            'security_settings': {
                'full_screen_mode': survey.full_screen_mode,
                'disable_copy_paste': survey.disable_copy_paste,
                'disable_dev_tools': survey.disable_dev_tools,
                'disable_print_screen': survey.disable_print_screen,
                'detect_tab_switching': survey.detect_tab_switching,
            }
        }