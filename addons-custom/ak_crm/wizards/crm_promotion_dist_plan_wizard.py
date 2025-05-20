from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
import math


class PromotionDistributionPlan(models.TransientModel):
    _name = 'crm.promotion.distribution.plan.wizard'
    _description = 'Plan Distribution of a new Promotion / DR.Sample'

    product_id = fields.Many2one('product.product', string='Product')
    available_quantity = fields.Float(string='Available Quantity', compute='_compute_available_quantity', readonly=True)
    planned_quantity = fields.Float(string='Planned Quantity')
    sales_team_id = fields.Many2one('crm.team', string='Sales Team')
    team_member_count = fields.Integer(compute='_compute_team_member_count', string='Team Member Count', readonly=True)
    distribution_type = fields.Selection([('eq', 'Equal'),
                                          ('cb', 'Lead Based'),
                                          ('sb', 'Selection Based'),
                                          ('fb', 'Frequency Based')], string='Distribution Type')

    @api.depends('product_id')
    def _compute_available_quantity(self):
        for record in self:
            if record.product_id:
                record.available_quantity = record.product_id.qty_available
            else:
                record.available_quantity = 0.0

    def _get_team_member_count_recursive(self, team):
        member_count = len(team.member_ids)
        child_teams = self.env['crm.team'].search([('parent_id', '=', team.id)])

        for child_team in child_teams:
            member_count += self._get_team_member_count_recursive(child_team)

        return member_count

    @api.depends('sales_team_id')
    def _compute_team_member_count(self):
        for record in self:
            if record.sales_team_id:
                # Get the member count of the selected sales team and its child teams
                member_count = self._get_team_member_count_recursive(record.sales_team_id)

                # Update the team_member_count field
                record.team_member_count = member_count
            else:
                record.team_member_count = 0

    def _get_team_members_recursive(self, team):
        # Search for team members with the given team id
        team_members = self.env['crm.team.member'].search([('crm_team_id', '=', team.id)])
        child_teams = self.env['crm.team'].search([('parent_id', '=', team.id)])

        for child_team in child_teams:
            team_members |= self._get_team_members_recursive(child_team)

        return team_members

    def action_distribute(self):
        # Ensure that the planned_quantity does not exceed the available_quantity
        if self.planned_quantity > self.available_quantity:
            raise ValidationError(_('Planned quantity cannot be greater than available quantity.'))

        if self.team_member_count == 0:
            raise ValidationError(_('No team members found. Please select a sales team with members.'))

        # Get the team members of the selected sales team and its child teams
        team_members = self._get_team_members_recursive(self.sales_team_id)

        # Calculate the planned quantity for each team member based on the distribution type
        if self.distribution_type == 'eq':
            quantity_per_member = math.floor(self.planned_quantity / self.team_member_count)
        elif self.distribution_type == 'cb':
            total_customer_count = 0
            member_customer_counts = {}

            # Calculate the total number of customers in the bricks of each team member
            for team_member in team_members:
                customer_count = 0
                for brick in team_member.brick_ids:
                    customer_count += self.env['res.partner'].search_count([('brick_id', '=', brick.id)])
                member_customer_counts[team_member.id] = customer_count
                total_customer_count += customer_count

            if total_customer_count == 0:
                raise ValidationError(
                    _('No customers found in the selected team members\' bricks. Please ensure team members have customers in their bricks.'))

            # Calculate the remaining quantity to be distributed
            remaining_quantity = self.planned_quantity - sum(member_customer_counts.values())

            # Calculate the quantity for each team member based on the customer count
            for team_member_id, customer_count in member_customer_counts.items():
                member_customer_counts[team_member_id] += math.floor(
                    (customer_count / total_customer_count) * remaining_quantity)

        # Create the promotion distribution plan records for each team member
        for team_member in team_members:
            if self.distribution_type == 'eq':
                calculated_quantity = quantity_per_member
            elif self.distribution_type == 'cb':
                calculated_quantity = member_customer_counts[team_member.id]
            elif self.distribution_type == 'sb':
                raise ValidationError(_('Not yet implimented!'))
            elif self.distribution_type == 'fb':
                raise ValidationError(_('Not yet implemented!'))

            self.env['crm.promotion.distribution.plan'].create({
                'product_id': self.product_id.id,
                'planned_quantity': calculated_quantity,
                'team_member_id': team_member.id,
                'state': 'd'
            })

        return {'type': 'ir.actions.act_window_close'}

