# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)


class SurveyPhotoController(http.Controller):
    
    @http.route('/survey/photo/capture', type='json', auth='public', website=True, csrf=False)
    def capture_photo(self, access_token, photo_data, capture_type='random', **kwargs):
        """
        Capture and store exam photo
        
        Args:
            access_token: Survey user input access token
            photo_data: Base64 encoded photo data
            capture_type: Type of capture (initial/random/manual)
            
        Returns:
            dict: Success status and photo ID
        """
        try:
            # Find user input
            user_input = request.env['survey.user_input'].sudo().search([
                ('access_token', '=', access_token)
            ], limit=1)
            
            if not user_input:
                return {
                    'success': False,
                    'error': 'Invalid access token'
                }
            
            # Check if photo capture is enabled
            if user_input.survey_id.photo_capture_mode == 'disabled':
                return {
                    'success': False,
                    'error': 'Photo capture not enabled for this exam'
                }
            
            # Validate photo data
            if not photo_data or not photo_data.startswith('data:image'):
                return {
                    'success': False,
                    'error': 'Invalid photo data'
                }
            
            # Extract base64 data (remove data:image/jpeg;base64, prefix)
            photo_base64 = photo_data.split(',')[1] if ',' in photo_data else photo_data
            
            # Get request metadata
            browser_info = request.httprequest.headers.get('User-Agent', '')
            ip_address = request.httprequest.remote_addr
            
            # Create photo record
            photo = request.env['survey.user_input.photo'].sudo().create({
                'user_input_id': user_input.id,
                'photo': photo_base64,
                'capture_type': capture_type,
                'browser_info': browser_info,
                'ip_address': ip_address,
                'capture_success': True
            })
            
            _logger.info(f"Photo captured for user_input {user_input.id}, photo_id: {photo.id}, type: {capture_type}")
            
            return {
                'success': True,
                'photo_id': photo.id,
                'message': 'Photo captured successfully'
            }
            
        except Exception as e:
            _logger.error(f"Error capturing photo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/survey/photo/permission', type='json', auth='public', website=True, csrf=False)
    def update_camera_permission(self, access_token, permission_granted, **kwargs):
        """
        Update camera permission status
        
        Args:
            access_token: Survey user input access token
            permission_granted: Boolean indicating if permission was granted
            
        Returns:
            dict: Success status
        """
        try:
            user_input = request.env['survey.user_input'].sudo().search([
                ('access_token', '=', access_token)
            ], limit=1)
            
            if not user_input:
                return {
                    'success': False,
                    'error': 'Invalid access token'
                }
            
            user_input.sudo().write({
                'camera_permission_granted': permission_granted,
                'camera_permission_datetime': fields.Datetime.now()
            })
            
            _logger.info(f"Camera permission updated for user_input {user_input.id}: {permission_granted}")
            
            return {
                'success': True,
                'message': 'Permission status updated'
            }
            
        except Exception as e:
            _logger.error(f"Error updating camera permission: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
