from odoo import http
from odoo.http import request
import json

class SupersetController(http.Controller):
    
    @http.route('/superset/dashboard/<int:dashboard_record_id>', 
                type='http', auth='user', website=True)
    def view_dashboard(self, dashboard_record_id, **kwargs):
        """Render dashboard page with embedded iframe"""
        dashboard = request.env['superset.dashboard'].browse(dashboard_record_id)
        
        if not dashboard.exists():
            return request.not_found()
        
        # Kullanıcı yetkilerini kontrol et
        if dashboard.allowed_groups:
            user_groups = request.env.user.groups_id
            if not any(group in dashboard.allowed_groups for group in user_groups):
                return request.render('http_routing.403')
        
        embedded_url = dashboard.get_embedded_url()
        
        return request.render('ak_superset_analytics.dashboard_view', {
            'dashboard': dashboard,
            'embedded_url': embedded_url,
        })
    
    @http.route('/superset/api/refresh_token', 
                type='json', auth='user')
    def refresh_token(self, dashboard_id):
        """Refresh JWT token for dashboard"""
        dashboard = request.env['superset.dashboard'].browse(dashboard_id)
        if dashboard.exists():
            return {'embedded_url': dashboard.get_embedded_url()}
        return {'error': 'Dashboard not found'}