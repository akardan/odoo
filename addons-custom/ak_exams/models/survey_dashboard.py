# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import json

class SurveyDashboard(models.TransientModel):
    _name = 'survey.dashboard'
    _description = 'Survey Dashboard'

    survey_id = fields.Many2one('survey.survey', string='Survey')
    team_id = fields.Many2one('crm.team', string='Team')
    
    # Dashboard data fields (kept for backward compatibility)
    top_performers_data = fields.Text(string='Top Performers Data', compute='_compute_dashboard_data')
    region_averages_data = fields.Text(string='Region Averages Data', compute='_compute_dashboard_data')
    region_rankings_data = fields.Text(string='Region Rankings Data', compute='_compute_dashboard_data')
    turkey_average_data = fields.Text(string='Turkey Average Data', compute='_compute_dashboard_data')
    
    # Text fields for dashboard display
    top_performers_text = fields.Html(string='Top Performers Text', compute='_compute_dashboard_data')
    region_averages_text = fields.Html(string='Region Averages Text', compute='_compute_dashboard_data')
    region_rankings_text = fields.Html(string='Region Rankings Text', compute='_compute_dashboard_data')
    turkey_average_text = fields.Html(string='Turkey Average Text', compute='_compute_dashboard_data')

    @api.depends('survey_id', 'team_id')
    def _compute_dashboard_data(self):
        """Compute the dashboard data based on the selected filters"""
        for record in self:
            dashboard_data = record._get_dashboard_data()
            
            # Top performers data
            top_performers = dashboard_data.get('top_performers', [])
            top_performers_data = {
                'labels': [p['name'] for p in top_performers],
                'datasets': [{
                    'label': _('Score'),
                    'data': [p['score'] for p in top_performers],
                    'backgroundColor': ['#4CAF50' for _ in top_performers],
                }]
            }
            record.top_performers_data = json.dumps(top_performers_data)
            
            # Generate HTML for top performers
            top_performers_html = '<table class="table table-striped"><thead><tr><th>Name</th><th>Score</th></tr></thead><tbody>'
            for performer in top_performers:
                top_performers_html += f'<tr><td>{performer["name"]}</td><td>{performer["score"]}%</td></tr>'
            top_performers_html += '</tbody></table>'
            record.top_performers_text = top_performers_html
            
            # Region averages data
            region_averages = dashboard_data.get('region_averages', [])
            region_averages_data = {
                'labels': [r['name'] for r in region_averages],
                'datasets': [{
                    'label': _('Average Score'),
                    'data': [r['average'] for r in region_averages],
                    'backgroundColor': ['#2196F3' for _ in region_averages],
                }]
            }
            record.region_averages_data = json.dumps(region_averages_data)
            
            # Generate HTML for region averages
            region_averages_html = '<table class="table table-striped"><thead><tr><th>Region</th><th>Average Score</th></tr></thead><tbody>'
            for region in region_averages:
                region_averages_html += f'<tr><td>{region["name"]}</td><td>{region["average"]:.2f}%</td></tr>'
            region_averages_html += '</tbody></table>'
            record.region_averages_text = region_averages_html
            
            # Region rankings data
            region_rankings = dashboard_data.get('region_rankings', [])
            region_rankings_data = {
                'labels': [r['name'] for r in region_rankings],
                'datasets': [{
                    'label': _('Average Score'),
                    'data': [r['average'] for r in region_rankings],
                    'backgroundColor': ['#FF9800' for _ in region_rankings],
                }]
            }
            record.region_rankings_data = json.dumps(region_rankings_data)
            
            # Generate HTML for region rankings
            region_rankings_html = '<table class="table table-striped"><thead><tr><th>Rank</th><th>Region</th><th>Average Score</th></tr></thead><tbody>'
            for ranking in region_rankings:
                region_rankings_html += f'<tr><td>{ranking["rank"]}</td><td>{ranking["name"]}</td><td>{ranking["average"]:.2f}%</td></tr>'
            region_rankings_html += '</tbody></table>'
            record.region_rankings_text = region_rankings_html
            
            # Turkey average data
            group_average = dashboard_data.get('group_average', 0)
            turkey_average_data = {
                'labels': [_('Average Score'), _('Remaining')],
                'datasets': [{
                    'data': [group_average, 100 - group_average],
                    'backgroundColor': ['#FF9800', '#EEEEEE'],
                }]
            }
            record.turkey_average_data = json.dumps(turkey_average_data)
            
            # Generate HTML for Turkey average
            turkey_average_html = f'<div class="alert alert-info text-center"><h4>Turkey Average Score: {group_average:.2f}%</h4></div>'
            record.turkey_average_text = turkey_average_html

    def action_refresh_dashboard(self):
        """Refresh the dashboard data"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.dashboard',
            'view_mode': 'form',
            'view_id': self.env.ref('ak_exams.view_survey_dashboard_form').id,
            'target': 'current',
            'context': {
                'default_survey_id': self.survey_id.id if self.survey_id else False,
                'default_team_id': self.team_id.id if self.team_id else False,
            },
            'flags': {'mode': 'readonly'},
        }

    def _get_dashboard_data(self):
        """
        Get data for the survey dashboard
        
        :return: Dictionary with dashboard data
        """
        self.ensure_one()
        survey_id = self.survey_id.id if self.survey_id else False
        team_id = self.team_id.id if self.team_id else False
        
        # Get surveys of type 'assessment' (exams)
        domain = [('survey_type', '=', 'assessment')]
        surveys = self.env['survey.survey'].search_read(domain, ['id', 'title'])
        
        # Get teams
        teams = self.env['crm.team'].search_read([], ['id', 'name'])
        
        # Filter user inputs based on survey_id and team_id
        user_input_domain = [('state', '=', 'done')]
        if survey_id:
            user_input_domain.append(('survey_id', '=', survey_id))
        
        # Get user inputs
        user_inputs = self.env['survey.user_input'].search(user_input_domain)
        
        # Filter by team if specified
        if team_id:
            # Get users in this team
            team_users = self.env['res.users'].search([
                ('sale_team_id', '=', team_id)
            ])
            
            # Get employees for these users
            team_employees = self.env['hr.employee'].search([
                ('department_id.name', '=', 'Kaya Ekibi'),
                ('user_id', 'in', team_users.ids)
            ])
            
            # Get partners directly from users
            team_partners = team_users.mapped('partner_id')
            
            # Filter user inputs by team members
            user_inputs = user_inputs.filtered(lambda ui: ui.partner_id in team_partners)
        
        # Get top performers (top 10 or all with full marks)
        top_performers = []
        for user_input in user_inputs:
            if user_input.scoring_percentage == 100 or len(top_performers) < 10:
                top_performers.append({
                    'name': user_input.partner_id.name or user_input.nickname or user_input.email,
                    'score': user_input.scoring_percentage,
                })
        
        # Sort top performers by score (descending)
        top_performers = sorted(top_performers, key=lambda p: p['score'], reverse=True)
        
        # Limit to top 10 if there are more than 10 performers
        if len(top_performers) > 10:
            top_performers = top_performers[:10]
        
        # Get region averages
        region_averages = []
        region_teams = self.env['crm.team'].search([('team_type', '=', 'R')])
        
        for region_team in region_teams:
            # Get users in this team
            region_users = self.env['res.users'].search([
                ('sale_team_id', '=', region_team.id)
            ])
            
            # Get employees for these users
            region_employees = self.env['hr.employee'].search([
                ('department_id.name', '=', 'Kaya Ekibi'),
                ('user_id', 'in', region_users.ids)
            ])
            # Get partners directly from users
            region_partners = region_users.mapped('partner_id')
            
            # Get user inputs for this region
            region_user_inputs = user_inputs.filtered(lambda ui: ui.partner_id in region_partners)
            
            if region_user_inputs:
                # Calculate average score for this region
                region_average = sum(ui.scoring_percentage for ui in region_user_inputs) / len(region_user_inputs)
                
                region_averages.append({
                    'name': region_team.name,
                    'average': region_average,
                })
        
        # Sort region averages by average score (descending)
        region_averages = sorted(region_averages, key=lambda r: r['average'], reverse=True)
        
        # Calculate Group average
        group_average = 0
        if user_inputs:
            group_average = sum(ui.scoring_percentage for ui in user_inputs) / len(user_inputs)
        
        # Create region rankings
        region_rankings = []
        for i, region in enumerate(region_averages):
            region_rankings.append({
                'name': region['name'],
                'rank': i + 1,
                'average': region['average'],
            })
        
        return {
            'surveys': surveys,
            'teams': teams,
            'top_performers': top_performers,
            'region_averages': region_averages,
            'region_rankings': region_rankings,
            'group_average': group_average,
        }

    @api.model
    def default_get(self, fields_list):
        """Set default values for the dashboard"""
        res = super(SurveyDashboard, self).default_get(fields_list)
        return res