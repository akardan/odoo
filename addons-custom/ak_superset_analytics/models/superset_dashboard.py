from odoo import models, fields, api
import requests
import time
from datetime import datetime, timedelta
import logging
import subprocess
import sys

_logger = logging.getLogger(__name__)

# Try to import PyJWT, but don't fail if it's not installed
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    _logger.warning("PyJWT package is not installed. JWT token generation will not work.")
    JWT_AVAILABLE = False

class SupersetDashboard(models.Model):
    _name = 'superset.dashboard'
    _description = 'Superset Dashboard Configuration'
    
    name = fields.Char('Dashboard Name', required=True)
    dashboard_id = fields.Char('Dashboard ID', required=True)
    superset_url = fields.Char('Superset URL', required=True, default='http://localhost:8088')
    jwt_secret = fields.Char('JWT Secret Key', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                  default=lambda self: self.env.company)
    allowed_groups = fields.Many2many('res.groups', string='Allowed Groups')
    
    # Superset user credentials
    superset_username = fields.Char('Superset Username', default='User')
    superset_email = fields.Char('Superset Email', default='example@mycompany.com')
    superset_first_name = fields.Char('Superset First Name', default='')
    superset_last_name = fields.Char('Superset Last Name', default='')
    
    def install_pyjwt(self):
        """Install PyJWT package"""
        try:
            # Get the Python executable path
            python_executable = sys.executable
            
            # Install PyJWT using pip
            subprocess.check_call([python_executable, '-m', 'pip', 'install', 'PyJWT'])
            
            # Show success message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PyJWT Installation',
                    'message': 'PyJWT package installed successfully. Please restart the Odoo server to apply the changes.',
                    'sticky': True,
                    'type': 'success',
                }
            }
        except Exception as e:
            # Show error message
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'PyJWT Installation',
                    'message': f'Failed to install PyJWT package: {str(e)}. Please install it manually with: pip install PyJWT',
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    def generate_jwt_token(self):
        """Generate JWT token for SSO authentication"""
        if not JWT_AVAILABLE:
            _logger.error("Cannot generate JWT token: PyJWT package is not installed.")
            return "ERROR_JWT_NOT_AVAILABLE"
            
        payload = {
            'username': self.superset_username,
            'email': self.superset_email,
            'first_name': self.superset_first_name,
            'last_name': self.superset_last_name,
            'exp': datetime.utcnow() + timedelta(hours=1),
        }
        
        try:
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token
        except Exception as e:
            _logger.error(f"Error generating JWT token: {e}")
            return "ERROR_JWT_GENERATION_FAILED"
    
    def get_embedded_url(self):
        """Generate embedded dashboard URL with SSO token"""
        # Generate JWT token using the stored Superset user credentials
        token = self.generate_jwt_token()
        
        # If token generation failed, return a URL without the token
        if token.startswith("ERROR_"):
            message = "JWT token generation failed. "
            if token == "ERROR_JWT_NOT_AVAILABLE":
                message += "PyJWT package is not installed. Please install it with: pip install PyJWT"
            else:
                message += "Check the logs for more details."
                
            # Show a warning message to the user
            if self.env.context.get('from_button'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Test',
                        'message': message,
                        'sticky': False,
                        'type': 'warning',
                    }
                }
            
            _logger.warning(message)
            base_url = self.superset_url.rstrip('/')
            # Use the same URL format but with a dummy token
            return f"{base_url}/login/?jwt=error_token&dashboard_id={self.dashboard_id}"
        
        # Create embedded URL with token using the correct format for Superset
        base_url = self.superset_url.rstrip('/')
        # Use the format with 'login' prefix for SSO authentication
        embedded_url = f"{base_url}/login/?jwt={token}&dashboard_id={self.dashboard_id}"
        
        # If called from button, show a success message
        if self.env.context.get('from_button'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Test',
                    'message': f"Connection successful! URL: {embedded_url}",
                    'sticky': False,
                    'type': 'success',
                }
            }
        
        return embedded_url
    
    def view_dashboard_new_window(self):
        """Open the dashboard directly in a new window/tab"""
        self.ensure_one()
        
        try:
            # Generate the embedded URL with JWT token
            embedded_url = self.get_embedded_url()
            
            # If token generation failed, show a warning
            if isinstance(embedded_url, dict):
                return embedded_url
            
            # Log the URL for debugging
            _logger.info(f"Opening Superset dashboard in new window with URL: {embedded_url}")
            
            # Return an action to open the URL in a new window/tab
            return {
                'type': 'ir.actions.act_url',
                'url': embedded_url,
                'target': 'new',
            }
        except Exception as e:
            _logger.error(f"Error opening dashboard in new window: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f"Failed to open dashboard in new window: {str(e)}",
                    'sticky': True,
                    'type': 'danger',
                }
            }
    
    # Override default read action for kanban view
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Override read_group to set default action on kanban card click"""
        res = super(SupersetDashboard, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)
        return res
    
    # Override default open action for kanban view
    def open_dashboard(self):
        """Default action when opening a record - redirect to view_dashboard_new_window"""
        self.ensure_one()
        if self.active:
            return self.view_dashboard_new_window()
        else:
            # If dashboard is inactive, open the form view
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'superset.dashboard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
            }