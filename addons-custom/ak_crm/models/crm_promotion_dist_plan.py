from odoo import api, models, fields
from itertools import groupby
from operator import attrgetter


class PromotionDistributionPlan(models.Model):
    _name = 'crm.promotion.distribution.plan'
    _description = 'Promotion/ DR.Sample Distribution Plan'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    planned_quantity = fields.Float(string='Planned Quantity', required=True)
    team_member_id = fields.Many2one('crm.team.member', string='Team Member', required=True)
    sales_team_id = fields.Many2one('crm.team', string='Sales Team', compute='_compute_sales_team', store=True)
    state = fields.Selection([('d', 'Draft'), ('c', 'Confirmed')], string='State', default='d')

    @api.depends('team_member_id')
    def _compute_sales_team(self):
        for record in self:
            record.sales_team_id = record.team_member_id.crm_team_id

    def create_delivery_order(self):
        Picking = self.env['stock.picking']
        PickingType = self.env['stock.picking.type']
        picking_type_out = PickingType.search([('code', '=', 'outgoing')], limit=1)

        # 'self' nesnesini 'team_member_id'ye göre sıralıyoruz.
        sorted_records = sorted(self, key=attrgetter('team_member_id'))

        for key, group in groupby(sorted_records, key=attrgetter('team_member_id')):
            # Bir grup için tek bir picking kaydı oluştururuz.
            picking_vals = {
                'partner_id': key.user_id.partner_id.id,
                'location_id': key.user_id.partner_id.property_stock_supplier.id,
                'location_dest_id': key.user_id.partner_id.property_stock_customer.id,
                'picking_type_id': picking_type_out.id,
            }
            picking = Picking.create(picking_vals)

            # Her bir ürün için bir 'move line' ekleriz.
            for record in group:
                move_line_vals = {
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.planned_quantity,
                    'name': record.product_id.name,
                    'product_uom': record.product_id.uom_id.id,
                    'location_id': key.user_id.partner_id.property_stock_supplier.id,
                    'location_dest_id': key.user_id.partner_id.property_stock_customer.id,
                    'picking_id': picking.id,
                }
                self.env['stock.move'].create(move_line_vals)

        return True


    # def create_delivery_order(self):
    #     picking = self.env['stock.picking']
    #     picking_type = self.env['stock.picking.type']
    #     picking_type_out = picking_type.search([('code', '=', 'outgoing')], limit=1)
    #     for key, group in groupby(sorted_records, key=attrgetter('team_member_id')):
    #         # Bir grup için tek bir picking kaydı oluştururuz.
    #         picking_vals = {
    #             'partner_id': key.user_id.partner_id.id,
    #             'location_id': key.user_id.partner_id.property_stock_supplier.id,
    #             'location_dest_id': key.user_id.partner_id.property_stock_customer.id,
    #             'picking_type_id': picking_type_out.id,
    #             'move_ids_without_package': [],
    #         }
    #         for record in group:
    #             # Her bir ürün için bir 'move line' ekleriz.
    #             picking_vals['move_ids_without_package'].append((0, 0, {
    #                 'product_id': record.product_id.id,
    #                 'product_uom_qty': record.planned_quantity,
    #                 'name': record.product_id.name,
    #                 'product_uom': record.product_id.uom_id.id,
    #                 'location_id': key.user_id.partner_id.property_stock_supplier.id,
    #                 'location_dest_id': key.user_id.partner_id.property_stock_customer.id,
    #             }))
    #         # picking kaydını oluştururuz.
    #         picking = picking.create(picking_vals)
    #     return True


