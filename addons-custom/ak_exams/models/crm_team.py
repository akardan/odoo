# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    external_id = fields.Char('Harici ID', help='Entegrasyon için harici kimlik')
    
    @api.model
    def get_team_hierarchy(self, team_id=None):
        """Takım hiyerarşisini getirir"""
        if not team_id:
            return []
        
        team = self.browse(team_id)
        if not team:
            return []
        
        hierarchy = []
        current_team = team
        
        # Önce üst takımları ekle
        parent_teams = []
        while current_team.parent_id:
            parent_teams.insert(0, {
                'id': current_team.parent_id.id,
                'name': current_team.parent_id.name,
            })
            current_team = current_team.parent_id
        
        hierarchy.extend(parent_teams)
        
        # Şimdi kendisini ekle
        hierarchy.append({
            'id': team.id,
            'name': team.name,
        })
        
        return hierarchy