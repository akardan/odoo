from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductPricelistInherit(models.Model):
    _inherit = 'product.pricelist'

    is_pharma_pricelist = fields.Boolean(string=_("Pharmaceutical Pricelist"))
    effective_date = fields.Date(string=_("Effective Date"))

    @api.constrains('is_pharma_pricelist', 'effective_date')
    def _check_pharma_pricelist(self):
        for record in self:
            if record.is_pharma_pricelist and not record.effective_date:
                raise ValidationError(_("Pharmaceutical pricelists must have an effective date"))

class ProductPricelistItemInherit(models.Model):
    _inherit = 'product.pricelist.item'
    _order = 'create_date desc'
    
    effective_date = fields.Date(related='pricelist_id.effective_date', string=_("Effective Date"), store=True)

    # Source Country and Price Information
    source_country = fields.Char(string=_("Source Country"))
    actual_source_country = fields.Char(string=_("Calculation Source Country"))

    # Source Price Information
    real_source_price = fields.Float(string=_("Real Source Price (GKF) (€)"), digits='Product Price')
    calculation_source_price = fields.Float(string=_("Calculation Source Price (GKF)"), digits='Product Price')
    source_price_euro = fields.Float(string=_("Source Price (€)"), digits='Product Price')

    # Exchange Rate Information
    euro_rate = fields.Float(string=_("Euro Exchange Rate"), digits=(16, 4))

    # Prices in TL
    depot_price_wo_vat = fields.Float(string=_("Depot Sales Price (Excl. VAT)"), digits='Product Price')
    depot_sales_price_wo_vat = fields.Float(string=_("Depot Sales Price** (Excl. VAT)"), digits='Product Price')
    pharmacy_sales_price_wo_vat = fields.Float(string=_("Pharmacy Sales Price*** (Excl. VAT)"), digits='Product Price')
    retail_price_w_vat = fields.Float(string=_("Retail Sales Price (Incl. VAT)"), digits='Product Price')

    # Status and Classification
    decree_id = fields.Many2one('price.decree.reason', string=_("Price Decree"))
    equivalent_status_id = fields.Many2one('equivalent.status', string=_("Equivalent Status"))
    reference_status_id = fields.Many2one('reference.status', string=_("Reference Status"))
    fdk_agok_status_id = fields.Many2one('fdk.agok.status', string=_("FDK/AGOK Status"))
    its_movement_status = fields.Selection([
        ('0', _("No ITS Movement")),
        ('1', _("Has ITS Movement")),
        ('2', _("No ITS Reporting Obligation"))
    ], string=_("ITS Movement Status"))

    # Change Tracking
    changed_this_week = fields.Boolean(string=_("Changed This Week"), default=False)
    change_description = fields.Text(string=_("Change Description"))
    last_operation = fields.Text(string=_("Last Operation"))
    previous_item_id = fields.Many2one('product.pricelist.item', string=_("Previous Price Item"))

    @api.model
    def create(self, vals):
        """Create method with history tracking for pharmaceutical products"""
        if vals.get('product_tmpl_id'):
            previous_item = self.search([
                ('product_tmpl_id', '=', vals['product_tmpl_id']),
                ('pricelist_id', '=', vals.get('pricelist_id'))
            ], limit=1, order='create_date desc')
            
            if previous_item:
                vals['previous_item_id'] = previous_item.id

        return super(ProductPricelistItemInherit, self).create(vals)

    def get_price_history(self):
        """Retrieve complete price history for the item"""
        self.ensure_one()
        history = []
        current_item = self
        
        while current_item:
            history.append({
                'date': current_item.create_date,
                'gkf': current_item.gkf,
                'reference_price': current_item.reference_price,
                'depot_price': current_item.depot_price,
                'fixed_price': current_item.fixed_price,
                'decree_id': current_item.decree_id,
                'change_description': current_item.change_description,
                'last_operation': current_item.last_operation
            })
            current_item = current_item.previous_item_id
            
        return history