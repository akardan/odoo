from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import logging
import requests
import xlrd
import base64
from datetime import datetime


_logger = logging.getLogger(__name__)

# Define your username and password
username = "86800010864430000"  # Replace with your actual username
password = "9413N05>H3D3F"  # Replace with your actual password


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    gtin = fields.Char(string=_("GTIN"), help=_("Global Trade Item Number"))
    barcode = fields.Char(string=_("Barcode"))
    manufacturer_id = fields.Many2one('res.partner', string=_("Manufacturer"), help=_("Manufacturer of the product"))
    imported = fields.Boolean(string=_("Imported"), help=_("Indicates if the drug is imported"))
    active_status = fields.Boolean(string=_("Active Status"), help=_("Indicates if the drug is active"))
    # message_partner_ids = fields.Many2many('res.partner', string="Message Partners",
    #                                        help="Partners associated with the manufacturer GLN")
    # seller_ids = fields.One2many('product.supplierinfo', 'product_tmpl_id', string="Vendors")

    atc_id = fields.Many2one('product.atc', string=_("ATC Code"))
    price_decree_reason_id = fields.Many2one('price.decree.reason', string=_("Price Decree Reason"))
    equivalent_status_id = fields.Many2one('equivalent.status', string=_("Equivalent Status"))
    reference_status_id = fields.Many2one('reference.status', string=_("Reference Status"))
    fdk_agok_status_id = fields.Many2one('fdk.agok.status', string=_("FDK - AGÖK Status"))
    sales_price_type_id = fields.Many2one('sales.price.type', string=_("Sales Price Type"))
    inhaler_product_group_id = fields.Many2one('inhaler.product.group', string=_("Inhaler Product Group"))
    inhaler_resistance_group_id = fields.Many2one('inhaler.resistance.group', string=_("Inhaler Resistance Group"))
    inhaler_device_code_id = fields.Many2one('inhaler.device.code', string=_("Inhaler Device Code"))

    active_ingredients = fields.Char(string=_("Active Ingredients"))
    active_ingredients_amount = fields.Char(string=_("Active Ingredients Amount"))
    active_ingredients_uom = fields.Char(string=_("Active Ingredients Unit of Measure"))
    
    package_amount = fields.Char(string=_("Package Amount"))
    
    prescription_type_id = fields.Many2one('prescription.type', string=_("Prescription Type"))
    
    its_movement_status = fields.Selection([
                                            ('0', 'Yok'),
                                            ('1', 'Var'),
                                            ('2', 'Bildirim zorunluluğu yok')
                                        ], string='İTS Hareket Durumu', default='0')    

    #EK4A - BEDELİ ÖDENECEK İLAÇLAR LİSTESİ  Fields
    public_no = fields.Char(string=_("Public Number"))
    equivalent_drug_group = fields.Char(string=_("Equivalent Drug Group"))
    therapeutic_ref_group = fields.Char(string=_("Therapeutic Reference Group"))
    list_entry_date = fields.Date(string=_("List Entry Date"))
    activation_date = fields.Date(string=_("Activation Date"))
    deactivation_date = fields.Date(string=_("Deactivation Date"))
    discount_status = fields.Char(string=_("Discount Status Base"))
    depot_price_range_4_discount_rate = fields.Float(string=_("Discount Rate 4 for Depot Price ≥ 91.17 TL"), digits=(5, 2))
    depot_price_range_3_discount_rate = fields.Float(string=_("Discount Rate 3 for Depot Price 60.52-91.16 TL"), digits=(5, 2))
    depot_price_range_2_discount_rate = fields.Float(string=_("Discount Rate 2 for Depot Price 31.62-60.51 TL"), digits=(5, 2))
    depot_price_range_1_discount_rate = fields.Float(string=_("Discount Rate 1 for Depot Price ≤ 31.61 TL"), digits=(5, 2))
    special_discount = fields.Float(string=_("Special Discount"), digits=(5, 2))
    pharmacy_discount = fields.Float(string=_("Pharmacy Discount Rate"), digits=(5, 2))    

    equivalent_drug_ids = fields.Many2many(
        'product.template',
        'product_equivalent_drug_rel',
        'product_id',
        'equivalent_id',
        string=_("Equivalent Drugs"),
        compute='_compute_equivalent_drug_ids',
        store=True,
        help=_("Products in the same equivalent drug group")
    )
    pricelist_item_ids = fields.One2many(
        'product.pricelist.item',
        'product_tmpl_id',
        string=_("Price History"),
        domain=[('pricelist_id.is_pharma_pricelist', '=', True)],
        order='pricelist_id.effective_date desc'
    )
    
    @api.depends('equivalent_drug_group')
    def _compute_equivalent_drug_ids(self):
        """Compute related drugs in the same equivalent group"""
        for product in self:
            if product.equivalent_drug_group:
                product.equivalent_drug_ids = self.search([
                    ('equivalent_drug_group', '=', product.equivalent_drug_group),
                    ('id', '!=', product.id)
                ])
            else:
                product.equivalent_drug_ids = False
    
    def action_import_drugs_from_titck(self):
        """
        Import drug data from the provided list if they do not already exist.
        """
        try:
            all_drugs = self.fetch_drug_data(username, password)
            if not isinstance(all_drugs, pd.DataFrame) or len(all_drugs) == 0:
                raise UserError(_('No drug data could be retrieved.'))

            # Kategoriyi ismine göre sorgulama veya oluşturma
            category = self.env['product.category'].search([('name', '=', 'İlaç')], limit=1)
            if not category:
                category = self.env['product.category'].create({'name': 'İlaç'})

            # Iterate through each row in the DataFrame
            for index, row in all_drugs.iterrows():
                gtin = str(row.get('gtin', '')).strip()
                barcode = gtin[1:] if gtin.startswith('0') else gtin
                drug_name = str(row.get('drugName', '')).strip()
                manufacturer_gln = str(row.get('manufacturerGln', '')).strip()
                imported = bool(row.get('imported', False))
                active_status = bool(row.get('active', False))

                if not gtin:
                    # GTIN is essential for identification, skip if missing
                    continue

                # Check if a product with the given GTIN already exists
                existing_product = self.env['product.template'].search([('gtin', '=', gtin)], limit=1)

                manufacturer = self.env['res.partner'].search([('gln_number', '=', manufacturer_gln)], limit=1)

                if existing_product:
                    # Update the existing product
                    existing_product.write({
                        'name': drug_name,
                        'manufacturer_id': manufacturer.id if manufacturer else False,
                        'imported': imported,
                        'active_status': active_status,
                        'barcode': barcode,
                        'categ_id': category.id,
                        'message_partner_ids': [(4, manufacturer.id)] if manufacturer else False,
                    })
                    if manufacturer:
                        existing_supplierinfo = self.env['product.supplierinfo'].search([
                            ('partner_id', '=', manufacturer.id),
                            ('product_tmpl_id', '=', existing_product.id)
                        ], limit=1)
                        if not existing_supplierinfo:
                            self.env['product.supplierinfo'].create({
                                'partner_id': manufacturer.id,
                                'product_tmpl_id': existing_product.id,
                            })
                else:
                    # Create a new product
                    new_product = self.env['product.template'].create({
                        'name': drug_name,
                        'gtin': gtin,
                        'barcode': barcode,
                        'manufacturer_id': manufacturer.id if manufacturer else False,
                        'imported': imported,
                        'active_status': active_status,
                        'type': 'consu',
                        'categ_id': category.id,
                        'message_partner_ids': [(4, manufacturer.id)] if manufacturer else False,
                    })
                    if manufacturer:
                        self.env['product.supplierinfo'].create({
                            'partner_id': manufacturer.id,
                            'product_tmpl_id': new_product.id,
                        })
                    _logger.info(f"New drug added: {drug_name} ({gtin})")
        except Exception as e:
            _logger.error(f"An error occurred while importing drugs: {str(e)}")
            raise UserError(_('An error occurred while importing drugs: %s') % str(e))

    @api.model
    def fetch_drug_data(self, username, password, get_all=False):
        """
        Fetch drug data using an API and return as a DataFrame.
        :param username: API username for authentication
        :param password: API password for authentication
        :param get_all: Boolean flag to indicate whether to get all drugs
        """
        # Define the API endpoint for token retrieval
        token_url = "https://its2.saglik.gov.tr/token/app/token/"
        # Define the API endpoint for drug list retrieval
        drug_url = "https://its2.saglik.gov.tr/reference/app/drug/"

        # Request access token
        token_payload = {
            "username": username,
            "password": password
        }
        token_response = requests.post(token_url, json=token_payload)

        if token_response.status_code == 200:
            token = token_response.json().get("token")

            # Define the request payload for drug list
            drug_payload = {
                "getAll": get_all  # Use the parameter to determine if all drugs should be fetched
            }

            # Set the headers for drug list request
            drug_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Send the POST request to get the drug list
            drug_response = requests.post(drug_url, json=drug_payload, headers=drug_headers)

            if drug_response.status_code == 200:
                drug_list = drug_response.json().get("drugList", [])

                # Create a DataFrame from the drug list
                drug_df = pd.DataFrame(drug_list)
                return drug_df
            else:
                raise UserError(_('Error fetching drug list: %s') % drug_response.text)
        else:
            raise UserError(_('Error obtaining access token: %s') % token_response.text)
        
    def action_import_titck_detailed_price(self):
        """
        Open wizard for TITCK detailed price import
        """
        return {
            'name': _('Import TITCK Detailed Price / Ek4A'),
            'type': 'ir.actions.act_window',
            'res_model': 'titck.detailed.price.import',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': self._name,
                'active_ids': self.ids,
            }
        }
    
