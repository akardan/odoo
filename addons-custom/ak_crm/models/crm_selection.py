from odoo import _, fields, models, api
from odoo.exceptions import ValidationError

class CrmSelection(models.Model):
    _name = 'crm.selection'
    _description = 'CRM Selection'

    def _default_team_member_id(self):
        team_member = self.env['crm.team.member'].search([('user_id', '=', self.env.uid)], limit=1)
        return team_member

    period_id = fields.Many2one('crm.selection.period', string='Selection Period')
    team_member_id = fields.Many2one('crm.team.member', string='Representative', required=True,
                                     default=_default_team_member_id, readonly=True)
    group_id = fields.Many2one('crm.team', string='Group', related='team_member_id.crm_team_id.group_id', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    # partner_id = fields.Many2one('res.partner', string='Customer', required=True, domain="[('brick_id', 'in', team_member_id.brick_ids)]")
    visit_location = fields.Many2one('res.partner', string='Visit Location',
                                     domain="[('parent_id', '=', partner_id)]")
    brick_id = fields.Many2one('crm.brick', string='Brick', related='partner_id.brick_id')
    segment_id = fields.Many2one('crm.segment', string='Segment', compute='_compute_segment_id', store=True)
    frequency = fields.Integer(string='Frequency', default=lambda self: self.segment_id.frequency_min)
    change_reason = fields.Selection([
        ('1', _('İlk Seleksiyon')),
        ('2', _('Potansiyel Var')),
        ('3', _('Potansiyel Yok')),
        ('4', _('İzinli')),
        ('5', _('Doğum İzninde')),
        ('6', _('Ulaşmak Zor')),
        ('7', _('Diğer'))],
        string='Change Reason')
    info_note = fields.Text(string='Information Note')
    return_date = fields.Date(string='Return Date')
    introduced_product1 = fields.Many2one('product.product', string='Product 1')
    introduced_product2 = fields.Many2one('product.product', string='Product 2')
    introduced_product3 = fields.Many2one('product.product', string='Product 3')

    @api.depends('team_member_id', 'partner_id.segmentation_ids')
    def _compute_segment_id(self):
        for record in self:
            segmentation = record.partner_id.segmentation_ids.filtered(
                lambda s: s.sales_team_id == record.group_id)
            record.segment_id = segmentation.segment_id if segmentation else False
            record.frequency = record.segment_id.frequency_min

    @api.constrains('frequency', 'segment_id')
    def _check_frequency(self):
        for record in self:
            if record.frequency < record.segment_id.frequency_min or record.frequency > record.segment_id.frequency_max:
                raise ValidationError(_("Frequency must be between {} and {}.").format(record.segment_id.frequency_min,
                                                                  record.segment_id.frequency_max))

    @api.onchange('team_member_id')
    def _onchange_team_member_id(self):
        if self.team_member_id:
            # Update partner_id domain
            self.partner_id = False
            partners = self.env['res.partner'].search([('brick_id', 'in', self.team_member_id.brick_ids.ids)])
            partner_domain = [('id', 'in', partners.ids)]

            # Update introduced_product1, introduced_product2, and introduced_product3 domains
            self.introduced_product1 = False
            self.introduced_product2 = False
            self.introduced_product3 = False
            products = self.env['product.product'].search(
                [('id', 'in', self.group_id.product_ids.ids)])
            product_domain = [('id', 'in', products.ids)]

            return {'domain': {'partner_id': partner_domain, 'introduced_product1': product_domain,
                               'introduced_product2': product_domain, 'introduced_product3': product_domain}}
        else:
            return {'domain': {'partner_id': [], 'introduced_product1': [], 'introduced_product2': [],
                               'introduced_product3': []}}

    @api.model
    def create(self, vals):
        period = self.env['crm.selection.period'].browse(vals.get('period_id'))
        if not period.active_for_planning:
            raise ValidationError(_("You can't create a selection plan if the selection period is not active for planning."))
        return super(CrmSelection, self).create(vals)

    def write(self, vals):
        if 'period_id' in vals:
            period = self.env['crm.selection.period'].browse(vals.get('period_id'))
            if not period.active_for_planning:
                raise ValidationError(_("You can't modify a selection plan if the selection period is not active for planning."))
        return super(CrmSelection, self).write(vals)

