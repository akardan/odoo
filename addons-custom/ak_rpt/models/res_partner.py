from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import logging
import re

# Define your username and password
username = "86800010864430000"  # Replace with your actual username
password = "9413N05>H3D3F"  # Replace with your actual password

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    gln_number = fields.Char(string="GLN", help="Global Location Number (GLN)")

    def normalize_phone_number(self, phone):
        """
        Normalize phone numbers to the format "0 - (000) 000 - 0000"
        """
        if not phone:
            return phone
        # Remove any unwanted characters (e.g., spaces, dashes, parentheses)
        phone = re.sub(r'[^0-9]', '', phone)
        # Check the length and format accordingly
        if len(phone) == 10:
            return f"0 - ({phone[:3]}) {phone[3:6]} - {phone[6:]}"
        elif len(phone) == 11 and phone.startswith('0'):
            return f"0 - ({phone[1:4]}) {phone[4:7]} - {phone[7:]}"
        return phone

    def action_import_stakeholders(self):
        """
        Import stakeholders from the provided list if they do not already exist.
        """
        try:
            all_producers = self.fetch_and_import_stakeholders(username, password)
            if all_producers.empty:
                raise UserError(_('No producer data could be retrieved.'))

            industry = self.env['res.partner.industry'].search([('name', '=', 'İlaç')], limit=1)

            # Iterate through each DataFrame in the list of producers
            for index, row in all_producers.iterrows():
                gln = str(row.get('gln', '')).strip()
                company_name = str(row.get('companyName', '')).strip()
                authorized_person = str(row.get('authorized', '')).strip()
                email = str(row.get('email', '')).strip()
                phone = self.normalize_phone_number(str(row.get('phone', '')).strip())
                state_id = self.env['res.country.state'].search([('name', '=ilike', str(row.get('city', '')).strip())], limit=1).id
                city = str(row.get('town', '')).strip()
                address = str(row.get('address', '')).strip()
                active_status = True

                if not gln:
                    # GLN is essential for identification, skip if missing
                    continue

                # Check if a contact with the given GLN number already exists
                existing_contact = self.env['res.partner'].search([('gln_number', '=', gln)], limit=1)

                if existing_contact:
                    # Update the existing contact
                    existing_contact.write({
                        'name': company_name,
                        'street': address,
                        'city': city,
                        'state_id': state_id,
                        'country_code': 'Türkiye',
                        'phone': phone,
                        'email': email,
                        'is_company': True,
                        'company_type': 'company',
                        # 'function': authorized_person,
                        'active': active_status,
                        'barcode': gln,
                    })
                    # _logger.info(f"Stakeholder updated: {company_name} ({gln})")
                else:
                    # Create a new contact
                    self.env['res.partner'].create({
                        'name': company_name,
                        'gln_number': gln,
                        'street': address,
                        'city': city,
                        'state_id': state_id,
                        'phone': phone,
                        'email': email,
                        'is_company': True,
                        'company_type': 'company',
                        # 'function': authorized_person,
                        'active': active_status,
                        'industry_id' : industry.id if industry else False,
                        'barcode' : gln,
                    })
                    _logger.info(f"New stakeholder added: {company_name} ({gln})")
        except Exception as e:
            _logger.error(f"An error occurred while importing stakeholders: {str(e)}")
            raise UserError(_('An error occurred while importing stakeholders: %s') % str(e))

    @api.model
    def fetch_and_import_stakeholders(self, username, password):
        """
        Fetch stakeholder data using an API and import into Odoo.
        :param username: API username for authentication
        :param password: API password for authentication
        """
        # Fetch producers for all cities in Turkey
        city_plates = range(1, 82)
        all_producers = pd.DataFrame()

        for city_plate in city_plates:
            stakeholder_df = fetch_stakeholder_data(username, password, stakeholder_type="uretici", get_all=True,
                                                    city_plate=city_plate)
            if not stakeholder_df.empty:
                # Remove duplicate records and concatenate with existing data
                stakeholder_df = stakeholder_df.drop_duplicates()
                all_producers = pd.concat([all_producers, stakeholder_df], ignore_index=True)

        return all_producers

def fetch_stakeholder_data(username, password, stakeholder_type="uretici", get_all=True, city_plate=34):
    import requests

    # Define the API endpoint for token retrieval
    token_url = "https://its2.saglik.gov.tr/token/app/token/"
    # Define the API endpoint for stakeholder list retrieval
    stakeholder_url = "https://its2.saglik.gov.tr/reference/app/stakeholder/"

    # Request access token
    token_payload = {
        "username": username,
        "password": password
    }
    token_response = requests.post(token_url, json=token_payload)

    if token_response.status_code == 200:
        token = token_response.json().get("token")

        # Define the request payload for stakeholder list
        stakeholder_payload = {
            "stakeholderType": stakeholder_type,
            "getAll": get_all,
            "cityPlate": city_plate
        }

        # Set the headers for stakeholder list request
        stakeholder_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Send the POST request to get the stakeholder list
        stakeholder_response = requests.post(stakeholder_url, json=stakeholder_payload, headers=stakeholder_headers)

        if stakeholder_response.status_code == 200:
            company_list = stakeholder_response.json().get("companyList", [])

            # Create a DataFrame from the company list
            stakeholder_df = pd.DataFrame(company_list)
            return stakeholder_df
        else:
            raise UserError(_('Error fetching stakeholder list: %s') % stakeholder_response.text)
    else:
        raise UserError(_('Error obtaining access token: %s') % token_response.text)
