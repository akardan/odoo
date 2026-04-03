from odoo import http, fields
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

        VALID_MODEL_VIOLATION_TYPES = {
            'fullscreen_exit',
            'tab_switch',
            'devtools_attempt',
            'print_screen_attempt',
            'copy_paste_attempt',
        }

        if event_type not in VALID_MODEL_VIOLATION_TYPES:
            _logger.warning(
                "Invalid or unknown security event_type '%s' received for User Input ID: %s.",
                event_type, user_input.id,
            )
            return {'success': False, 'error': f'Invalid event_type: {event_type}'}

        # Ayrı bir cursor kullan: survey submit ile aynı transaction'ı paylaşmadığı için
        # REPEATABLE READ snapshot çakışması (could not serialize access due to concurrent update)
        # yaşanmaz. Her violation write kendi fresh transaction'ında commit edilir.
        user_input_id = user_input.id
        try:
            with request.env.registry.cursor() as new_cr:
                # READ COMMITTED: eş zamanlı iki UPDATE birbirini bekler, çakışmaz.
                # Odoo varsayılanı REPEATABLE READ olduğundan burada açıkça set ediyoruz.
                new_cr.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
                new_env = request.env(cr=new_cr)
                ui = new_env['survey.user_input'].sudo().browse(user_input_id)
                result = ui.log_security_violation(violation_type=event_type)
                new_cr.commit()
        except Exception as e:
            _logger.error(
                "Error processing security event for User Input ID %s: %s",
                user_input_id, str(e), exc_info=True,
            )
            return {'success': False, 'error': 'Internal server error while processing event.'}

        _logger.info(
            "Violation log result for User Input ID %s (True if terminated, False otherwise): %s",
            user_input_id, result,
        )

        if result is True:
            return {
                'success': True,
                'action': 'terminate',
                'message': 'Survey has been terminated due to security violations.',
            }
        return {
            'success': True,
            'action': 'logged',
            'message': 'Security violation logged.',
        }

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
    
    @http.route('/survey/security/screenshot', type='json', auth='public', website=True)
    def save_security_screenshot(self):
        """
        Endpoint to save screenshot captured during security violation
        """
        try:
            raw_body = request.httprequest.data.decode('utf-8')
            payload = json.loads(raw_body)
            _logger.info("Screenshot upload request received")
        except Exception as e:
            _logger.error("Error decoding/parsing screenshot payload: %s", e)
            return {'success': False, 'error': 'Invalid JSON payload'}
        
        access_token = payload.get('access_token')
        screenshot_data = payload.get('screenshot_data')
        violation_type = payload.get('violation_type', 'unknown')
        
        if not access_token or not screenshot_data:
            _logger.warning("Screenshot upload missing required parameters")
            return {'success': False, 'error': 'Missing required parameters'}
        
        user_input = request.env['survey.user_input'].sudo().search([
            ('access_token', '=', access_token)
        ], limit=1)
        
        if not user_input:
            _logger.warning("Screenshot upload with invalid access_token: %s", access_token)
            return {'success': False, 'error': 'Invalid access token'}
        
        try:
            # Remove data URL prefix if present
            if ',' in screenshot_data:
                screenshot_data = screenshot_data.split(',')[1]
            
            # Create attachment for the screenshot
            attachment = request.env['ir.attachment'].sudo().create({
                'name': f'security_screenshot_{violation_type}_{user_input.id}_{fields.Datetime.now().strftime("%Y%m%d_%H%M%S")}.png',
                'type': 'binary',
                'datas': screenshot_data,
                'res_model': 'survey.user_input',
                'res_id': user_input.id,
                'description': f'Security violation screenshot - Type: {violation_type}',
            })
            
            _logger.info(
                'Security screenshot saved for User Input ID: %s, Violation: %s, Attachment ID: %s',
                user_input.id, violation_type, attachment.id
            )
            
            return {
                'success': True,
                'message': 'Screenshot saved successfully',
                'attachment_id': attachment.id
            }
            
        except Exception as e:
            _logger.error(
                "Error saving security screenshot for User Input ID %s: %s",
                user_input.id, str(e), exc_info=True
            )
            return {'success': False, 'error': 'Failed to save screenshot'}