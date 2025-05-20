from odoo import models, fields, api
from datetime import date


class CrmSelectionPeriod(models.Model):
    _name = 'crm.selection.period'
    _description = 'CRM Selection Period'
    _rec_name = 'name'

    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=False)
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    planning_date_start = fields.Date(string='Planning Date Start')
    planning_date_end = fields.Date(string='Planning Date End')
    year = fields.Char(string='Year', compute='_compute_year_month', store=True)
    month = fields.Char(string='Month', compute='_compute_year_month', store=True)
    active_for_planning = fields.Boolean(string='Can Plan?', compute='_compute_active_for_planning', store=True)
    active = fields.Boolean(string='Active', compute='_compute_active', store=True)


    @api.depends('date_start', 'date_end')
    @api.onchange('date_start', 'date_end')
    def _compute_year_month(self):
        for record in self:
            if record.date_start:
                record.year = record.date_start.year
                record.month = record.date_start.month

    @api.onchange('year', 'month')
    def _compute_name(self):
        for record in self:
            if record.year and record.month:
                record.name = f"{record.year} {record.month} Selection"

    @api.depends('planning_date_start', 'planning_date_end')
    def _compute_active_for_planning(self):
        today = date.today()
        for record in self:
            if record.planning_date_start and record.planning_date_end:
                record.active_for_planning = record.planning_date_start <= today <= record.planning_date_end

    @api.depends('date_start', 'date_end')
    def _compute_active(self):
        for record in self:
            today = date.today()
            if record.date_start and record.date_end:
                record.active = record.date_start <= today <= record.date_end
