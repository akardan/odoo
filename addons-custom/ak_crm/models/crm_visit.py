from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar


class CrmVisitType(models.Model):
    _name = 'crm.visit.type'
    _description = _('CRM Visit Type')

    name = fields.Char(string=_('Name'), required=True)
    code = fields.Char(string=_('Code'))


class CrmVisitsTransient(models.TransientModel):
    _name = 'crm.visits.transient'
    _description = _('CRM Visits')
    _rec_name = 'team_member_id'

    MEDICAL_TYPE_SELECTION = [
        ('D', 'Doktor'),
        ('P', 'Eczane'),
    ]

    def _default_team_member_id(self):
        user = self.env.user
        team_member_id = self.env['crm.team.member'].search([('user_id', '=', user.id)], limit=1)
        return team_member_id.id if team_member_id else False

    visit_date = fields.Date(string=_('Visit Date'), default=fields.Date.today())
    team_member_id = fields.Many2one('crm.team.member', string=_('Team Member'), required=True,
                                     default=_default_team_member_id)
    brick_id = fields.Many2one('crm.brick', string=_('Brick'))
    unit_id = fields.Many2one('crm.unit', string='Unit')
    medical_type = fields.Selection(MEDICAL_TYPE_SELECTION, string='Partner Type')

    crm_visit_transient_ids = fields.One2many('crm.visit.transient', 'crm_visits_transient_id', string=_('Partners to Visit'))

    crm_visit_ids = fields.Many2many('crm.visit', compute='_compute_crm_visits', string=_('Visits'))

    @api.onchange('team_member_id')
    def _onchange_team_member_id(self):
        domain = {}
        if self.team_member_id:
            domain = {'brick_id': [('id', 'in', self.team_member_id.brick_ids.ids)]}
        return {'domain': domain}

    @api.onchange('brick_id')
    def _onchange_brick_id(self):
        for rec in self:
            if rec.brick_id:
                return {'domain': {'unit_id': [('brick_id', '=', rec.brick_id.id)]}}

    def button_find_partners(self):
        for rec in self:
            if not rec.brick_id and not rec.unit_id:
                raise UserError(_("Please select at least one criteria (Brick or Unit)"))

            domain = []
            if rec.brick_id:
                domain.append(('brick_id', '=', rec.brick_id.id))
            if rec.unit_id:
                domain.append(('unit_id', '=', rec.unit_id.id))
            if rec.medical_type:
                domain.append(('medical_type', '=', rec.medical_type))

            # Partnerları ara ve bul
            found_partners = rec.env['res.partner'].search(domain)

            # Eşleşen partnerları crm_visit_transient_ids listesine ekle
            new_records = []
            for partner in found_partners:
                vals = {
                    'visit_date': rec.visit_date,
                    'team_member_id': rec.team_member_id.id,
                    'customer_id': partner.id,
                    'visit_type_id': False,  # Kullanıcı tarafından daha sonra düzenlenecek
                }
                # new_record = rec.env['crm.visit.transient'].create(vals)
                new_records.append((0,0, vals))
                
            # Mevcut kayıtları temizle
            rec.update({'crm_visit_transient_ids': [5]})
            # Ekleme işlemi
            rec.crm_visit_transient_ids = new_records

    @api.depends('visit_date', 'team_member_id')
    def _compute_crm_visits(self):
        for record in self:
            visit_ids = self.env['crm.visit'].search(
                [('visit_date', '=', record.visit_date), ('team_member_id', '=', record.team_member_id.id)])
            record.crm_visit_ids = [(6, 0, visit_ids.ids)]

    def button_filter_visits(self):
        self._compute_crm_visits()

    def button_crate_crm_visit(self):
        return {
            'name': _('Create Visit'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.visit',
            'view_mode': 'form',
            'view_id': self.env.ref('ak_crm.view_crm_visit_form').id,
            'target': 'new',
            'context': {
                'default_visit_date': self.visit_date,
                'default_team_member_id': self.team_member_id.id,
            }
        }


class CrmVisitTransient(models.TransientModel):
    _name = 'crm.visit.transient'
    _description = _('Visit Transient')

    crm_visits_transient_id = fields.Many2one('crm.visits.transient', string='CRM Visit')
    visit_date = fields.Date(string=_('Visit Date'))
    team_member_id = fields.Many2one('crm.team.member', string=_('Team Member'), required=True)
    customer_id = fields.Many2one('res.partner', string=_('Ziyaret edilen müşteri'))
    brick_id = fields.Many2one('crm.brick', string=_('Brick'), related='customer_id.brick_id', readonly=True)
    unit_id = fields.Many2one('crm.unit', string=_('Unit'), related='customer_id.unit_id', readonly=True)
    visit_type_id = fields.Many2one('crm.visit.type', string=_('Visit Type'))

    @api.onchange('visit_date')
    def _onchange_visit_date(self):
        if self.visit_date:
            days2future = 0
            days2past = 3
            today = fields.Date.today()
            future_date = today + timedelta(days=days2future)
            past_date = today - timedelta(days=days2past)

            if self.visit_date > future_date:
                raise ValidationError(
                    _("You cannot select a date more than {days} days in the future.").format(days=days2future))

            if self.visit_date < past_date:
                raise ValidationError(
                    _("You cannot select a date older than {days} days.").format(days=days2past))


class CrmVisit(models.Model):
    _name = 'crm.visit'
    _description = _('CRM Visit')
    # _check_company_auto = True

    visit_date = fields.Date(string="Visit Date")
    team_member_id = fields.Many2one('crm.team.member', string='Employee', required=True)
    brick_id = fields.Many2one('crm.brick', string=_('Brick'))
    unit_id = fields.Many2one('crm.unit', string='Unit')
    customer_ids = fields.Many2many('res.partner', string=_('Ziyaret edilen müşteriler'))
    visit_type_id = fields.Many2one('crm.visit.type', string='Visit Type')

    @api.onchange('team_member_id')
    def _onchange_team_member_id(self):
        if self.team_member_id:
            return {'domain': {'brick_id': [('id', 'in', self.team_member_id.brick_ids.ids)]}}

    @api.onchange('brick_id')
    def _onchange_brick_id(self):
        if self.brick_id:
            return {'domain': {'unit_id': [('brick_id', '=', self.brick_id.id)]}}

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        if self.unit_id:
            return {'domain': {'customer_ids': [('id', 'in', self.unit_id.partner_ids.ids)]}}

    @api.onchange('visit_date')
    def _onchange_visit_date(self):
        if self.visit_date:
            today = fields.Date.today()
            future_date = today + timedelta(days=3)
            past_date = today - timedelta(days=3)

            if self.visit_date > future_date:
                raise ValidationError("You cannot select a date more than 3 days in the future.")

            if self.visit_date < past_date:
                raise ValidationError("You cannot select a date older than 3 days.")

    def open_customer_selection_popup(self):
        return {
            'name': 'Müşteri Seçimi',
            'view_mode': 'form',
            'res_model': 'crm.visittransient',
            'view_id': self.env.ref('ak_crm.view_crm_visit_create_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_crm_visit_id': self.id,
            }
        }


class CrmVisitDashboard(models.TransientModel):
    _name = 'crm.visit.dashboard'
    _description = 'CRM Visit Dashboard'
    _rec_name = 'display_name'

    def _default_team_member_id(self):
        user = self.env.user
        team_member_id = self.env['crm.team.member'].search([('user_id', '=', user.id)], limit=1)
        return team_member_id.id if team_member_id else False

    active_period_id = fields.Many2one('crm.selection.period', string='Active Period',
                                       compute='_compute_active_period', readonly=True, store=False)
    team_member_id = fields.Many2one('crm.team.member', string=_('Team Member'), required=True,
                                     default=_default_team_member_id)
    date_from = fields.Date(string="Date From", compute="_compute_date_from")
    date_to = fields.Date(string="Date To", compute="_compute_date_to")
    daily_stats_ids = fields.One2many('crm.visit.dashboard.line', 'dashboard_id', string='Daily Stats')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=False)

    @api.depends()
    def _compute_active_period(self):
        # CrmSelectionPeriod modelinden aktif olan kaydı al
        active_period = self.env['crm.selection.period'].search([('active', '=', True)],
                                                                order='date_start desc',
                                                                limit=1)
        for record in self:
            record.active_period_id = active_period.id if active_period else False

    @api.depends('active_period_id')
    def _compute_date_from(self):
        for rec in self:
            if rec.active_period_id:
                rec.date_from = rec.active_period_id.date_start
            else:
                rec.date_from = datetime.today()

    @api.depends('active_period_id')
    def _compute_date_to(self):
        for rec in self:
            if rec.active_period_id:
                rec.date_to = rec.active_period_id.date_end
            else:
                rec.date_to = datetime.today()

    @api.depends('date_from', 'date_to')
    def _compute_display_name(self):
        for record in self:
            if record.date_from and record.date_to:
                record.display_name = f"Visits From {record.date_from} to {record.date_to}"
            elif record.date_from:
                record.display_name = f"Visits From {record.date_from}"
            elif record.date_to:
                record.display_name = f"Visits To {record.date_to}"
            else:
                record.display_name = "Visits-Undefined Period"

    def button_filter_visits(self):
        for rec in self:
            # Mevcut kayıtları temizle
            rec.update({'daily_stats_ids': [5]})

            date_from = rec.date_from
            date_to = rec.date_to

            daily_stats = []
            while date_from <= date_to:
                visits = self.env['crm.visit'].search(
                    [('visit_date', '=', date_from), ('team_member_id', '=', rec.team_member_id.id)])

                doctor_count = sum(
                    1 for visit in visits for customer in visit.customer_ids if customer.medical_type == 'D')
                pharmacy_count = sum(
                    1 for visit in visits for customer in visit.customer_ids if customer.medical_type == 'P')

                daily_stats.append((0, 0, {
                    'visit_date': date_from,
                    'team_member_id': rec.team_member_id.id,
                    'visit_count': len(visits),
                    'doctor_count': doctor_count,
                    'pharmacy_count': pharmacy_count,
                }))

                date_from += timedelta(days=1)

            rec.daily_stats_ids = daily_stats


class CrmVisitDashboardLine(models.TransientModel):
    _name = 'crm.visit.dashboard.line'
    _description = 'CRM Visit Dashboard Line'

    dashboard_id = fields.Many2one('crm.visit.dashboard', string='Dashboard')
    visit_date = fields.Date(string='Visit Date')
    team_member_id = fields.Many2one('crm.team.member', string=_('Team Member'))
    visit_count = fields.Integer(string='Visit Count')
    doctor_count = fields.Integer(string='Doctor Count')
    pharmacy_count = fields.Integer(string='Pharmacy Count')

    def open_daily_visits(self):
        view_id = self.env.ref('ak_crm.view_crm_visits_transient_form').id
        return {
            'name': 'Daily Visits',
            'view_mode': 'form',
            'res_model': 'crm.visits.transient',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'context': {
                'default_visit_date': self.visit_date,
                'default_team_member_id': self.team_member_id.id
            }
        }
