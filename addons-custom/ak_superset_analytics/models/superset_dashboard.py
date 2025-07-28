from odoo import models, fields, api
import requests
import jwt
import time
from datetime import datetime, timedelta

class SupersetDashboard(models.Model):
    _name = 'superset.dashboard'
    _description = 'Superset Dashboard Configuration'
    
    name = fields.Char('Dashboard Name', required=True)
    dashboard_id = fields.Char('Dashboard ID', required=True)
    superset_url = fields.Char('Superset URL', required=True, default='http://localhost:8088')
    jwt_secret = fields.Char('JWT Secret Key', required=True)
    active = fields.Boolean('Active', default=True)
    allowed_groups = fields.Many2many('res.groups', string='Allowed Groups')
    
    def generate_jwt_token(self, user_id, username, email):
        """Generate JWT token for SSO authentication"""
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'first_name': self.env.user.name.split()[0] if self.env.user.name else '',
            'last_name': ' '.join(self.env.user.name.split()[1:]) if len(self.env.user.name.split()) > 1 else '',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        return token
    
    def get_embedded_url(self):
        """Generate embedded dashboard URL with SSO token"""
        user = self.env.user
        
        # JWT token oluştur
        token = self.generate_jwt_token(
            user_id=user.id,
            username=user.login,
            email=user.email or user.login
        )
        
        # Embedded URL oluştur
        base_url = self.superset_url.rstrip('/')
        embedded_url = f"{base_url}/superset/dashboard/{self.dashboard_id}/?standalone=1&jwt={token}"
        
        return embedded_url