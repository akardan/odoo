#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script helps diagnose and fix issues with the Superset Analytics module.
Run it from the Odoo shell:

    python3 odoo-bin shell -d your_database_name -c your_config_file.conf
    
Then in the Odoo shell:

    exec(open('addons-custom/ak_superset_analytics/tools/diagnostic.py').read())
"""

import sys
import os
import logging
import requests
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Set up console logging for better visibility when running the script
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
_logger.addHandler(console_handler)
_logger.setLevel(logging.INFO)

def check_dependencies():
    """Check if all required dependencies are installed"""
    _logger.info("Checking dependencies...")
    
    try:
        import jwt
        _logger.info("PyJWT is installed: %s", jwt.__version__)
    except ImportError:
        _logger.error("PyJWT is not installed. Install it with: pip install PyJWT")
        return False
    
    return True

def check_module_installation(env):
    """Check if the module is properly installed"""
    _logger.info("Checking module installation...")
    
    module = env['ir.module.module'].search([('name', '=', 'ak_superset_analytics')], limit=1)
    if not module:
        _logger.error("Module 'ak_superset_analytics' not found in ir.module.module")
        return False
    
    if module.state != 'installed':
        _logger.error("Module 'ak_superset_analytics' is not installed (state: %s)", module.state)
        return False
    
    _logger.info("Module 'ak_superset_analytics' is installed correctly")
    return True

def check_model_access(env):
    """Check if the model access rights are properly set up"""
    _logger.info("Checking model access rights...")
    
    access_rights = env['ir.model.access'].search([('model_id.model', '=', 'superset.dashboard')])
    if not access_rights:
        _logger.error("No access rights found for model 'superset.dashboard'")
        return False
    
    _logger.info("Found %s access rights for model 'superset.dashboard'", len(access_rights))
    return True

def check_views(env):
    """Check if the views are properly loaded"""
    _logger.info("Checking views...")
    
    views = env['ir.ui.view'].search([('model', '=', 'superset.dashboard')])
    if not views:
        _logger.error("No views found for model 'superset.dashboard'")
        return False
    
    _logger.info("Found %s views for model 'superset.dashboard'", len(views))
    
    # Check for OWL component registration
    owl_component = env['ir.asset'].search([
        ('name', 'like', 'superset_dashboard_iframe.js'),
        ('bundle', '=', 'web.assets_backend')
    ])
    
    if not owl_component:
        _logger.error("OWL component JS file not properly registered in assets")
        return False
    
    owl_template = env['ir.asset'].search([
        ('name', 'like', 'superset_dashboard_iframe.xml'),
        ('bundle', '=', 'web.assets_backend')
    ])
    
    if not owl_template:
        _logger.error("OWL component XML template not properly registered in assets")
        return False
    
    _logger.info("OWL component properly registered in assets")
    return True

def test_jwt_token_generation(env):
    """Test JWT token generation for a dashboard"""
    _logger.info("Testing JWT token generation...")
    
    dashboards = env['superset.dashboard'].search([], limit=1)
    if not dashboards:
        _logger.error("No dashboard records found to test")
        return False
    
    dashboard = dashboards[0]
    token = dashboard.generate_jwt_token()
    
    if token.startswith("ERROR_"):
        _logger.error("JWT token generation failed: %s", token)
        return False
    
    _logger.info("JWT token generated successfully")
    return True

def test_url_generation(env):
    """Test URL generation for both iframe and new window"""
    _logger.info("Testing URL generation...")
    
    dashboards = env['superset.dashboard'].search([], limit=1)
    if not dashboards:
        _logger.error("No dashboard records found to test")
        return False
    
    dashboard = dashboards[0]
    
    # Test new window URL
    new_window_url = dashboard.get_embedded_url()
    if isinstance(new_window_url, dict):
        _logger.error("New window URL generation failed")
        return False
    
    _logger.info("New window URL generated successfully: %s", new_window_url)
    
    # Test iframe URL
    iframe_url = dashboard.get_embedded_url_for_iframe()
    if isinstance(iframe_url, dict):
        _logger.error("Iframe URL generation failed")
        return False
    
    _logger.info("Iframe URL generated successfully: %s", iframe_url)
    
    # Check if URLs have the correct format
    if "/login/" not in new_window_url:
        _logger.warning("New window URL format may be incorrect, should contain '/login/?jwt={token}&dashboard_id={id}'")
    
    if "/login/" not in iframe_url:
        _logger.warning("Iframe URL format may be incorrect, should contain '/login/?jwt={token}&dashboard_id={id}'")
    
    return True

def test_superset_connectivity(env):
    """Test connectivity to Superset server"""
    _logger.info("Testing connectivity to Superset server...")
    
    dashboards = env['superset.dashboard'].search([], limit=1)
    if not dashboards:
        _logger.error("No dashboard records found to test")
        return False
    
    dashboard = dashboards[0]
    base_url = dashboard.superset_url.rstrip('/')
    
    try:
        # Just try to connect to the base URL
        response = requests.get(base_url, timeout=5)
        _logger.info("Connection to Superset server successful (status code: %s)", response.status_code)
        return True
    except requests.exceptions.RequestException as e:
        _logger.error("Failed to connect to Superset server: %s", e)
        return False

def check_iframe_issues(env):
    """Check for common iframe embedding issues"""
    _logger.info("Checking for common iframe embedding issues...")
    
    # Check if the OWL component is properly registered
    owl_component = env['ir.asset'].search([
        ('name', 'like', 'superset_dashboard_iframe.js'),
        ('bundle', '=', 'web.assets_backend')
    ])
    
    if not owl_component:
        _logger.error("OWL component JS file not properly registered in assets")
        _logger.info("Solution: Update the __manifest__.py file to include the JS file in assets")
        return False
    
    # Check if the dashboard_view template has the correct sandbox attributes
    view = env['ir.ui.view'].search([('name', '=', 'dashboard_view')], limit=1)
    if view and 'allow-same-origin allow-scripts allow-forms allow-popups allow-top-navigation' not in view.arch:
        _logger.warning("The dashboard_view template may not have the correct sandbox attributes")
        _logger.info("Solution: Update the template to include all necessary sandbox attributes")
    
    _logger.info("Iframe embedding setup looks correct")
    return True

def fix_issues(env):
    """Try to fix common issues"""
    _logger.info("Attempting to fix issues...")
    
    # Update the module
    module = env['ir.module.module'].search([('name', '=', 'ak_superset_analytics')], limit=1)
    if module:
        try:
            _logger.info("Updating module 'ak_superset_analytics'...")
            module.button_immediate_upgrade()
            _logger.info("Module updated successfully")
        except Exception as e:
            _logger.error("Failed to update module: %s", e)
    
    # Clear caches
    _logger.info("Clearing caches...")
    env.registry.clear_caches()
    
    # Reload registry
    _logger.info("Reloading registry...")
    env.registry.setup_models(env.cr)
    
    # Provide troubleshooting tips
    _logger.info("\nTroubleshooting tips for iframe embedding issues:")
    _logger.info("1. Check that your Superset server is accessible from the Odoo server")
    _logger.info("2. Verify that the JWT secret key matches between Odoo and Superset")
    _logger.info("3. Ensure that the dashboard ID is correct")
    _logger.info("4. Check that the URL formats are correct:")
    _logger.info("   - New window: /login/?jwt={token}&dashboard_id={id}")
    _logger.info("   - Iframe: /login/?jwt={token}&dashboard_id={id}")
    _logger.info("5. Verify that the iframe sandbox attributes include all necessary permissions")
    _logger.info("6. Try opening the dashboard in a new window to test authentication")
    _logger.info("7. Check browser console for any CORS or security-related errors")
    _logger.info("8. Ensure that Superset is configured to accept JWT authentication")
    
    _logger.info("Fix attempts completed")

def main(env):
    """Main diagnostic function"""
    _logger.info("\n========== SUPERSET ANALYTICS DIAGNOSTIC ==========\n")
    _logger.info("Starting diagnostic for ak_superset_analytics module")
    
    issues_found = False
    
    # Basic checks
    if not check_dependencies():
        issues_found = True
    
    if not check_module_installation(env):
        issues_found = True
    
    if not check_model_access(env):
        issues_found = True
    
    if not check_views(env):
        issues_found = True
    
    # Advanced checks
    _logger.info("\n----- Advanced Diagnostics -----\n")
    
    if not test_jwt_token_generation(env):
        issues_found = True
    
    if not test_url_generation(env):
        issues_found = True
    
    if not test_superset_connectivity(env):
        issues_found = True
    
    if not check_iframe_issues(env):
        issues_found = True
    
    if issues_found:
        _logger.info("\n----- Issues Found -----\n")
        _logger.info("Issues found. Attempting to fix...")
        fix_issues(env)
        _logger.info("\nPlease restart your Odoo server after this script completes")
    else:
        _logger.info("\n----- No Issues Found -----\n")
        _logger.info("No issues found with the module installation")
        _logger.info("If you're still experiencing problems with iframe embedding:")
        _logger.info("1. Try using the 'View Dashboard (New Window)' option to test authentication")
        _logger.info("2. Check browser console for any errors")
        _logger.info("3. Verify Superset configuration for JWT authentication")
    
    _logger.info("\nDiagnostic completed")
    _logger.info("\n========== END OF DIAGNOSTIC ==========\n")

# Run the diagnostic
try:
    env = env  # This will fail if not run from Odoo shell
except NameError:
    _logger.error("This script must be run from the Odoo shell")
    sys.exit(1)

main(env)