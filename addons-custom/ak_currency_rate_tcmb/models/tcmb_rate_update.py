import requests
from xml.etree import ElementTree as ET
from datetime import datetime
from odoo import api, models, exceptions, fields

class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    @api.model
    def update_exchange_rates(self):
        try:
            # TCMB XML URL
            url = "https://www.tcmb.gov.tr/kurlar/today.xml"
            response = requests.get(url)

            if response.status_code != 200:
                raise exceptions.UserError("Failed to fetch exchange rates from TCMB.")

            # Parse XML
            root = ET.fromstring(response.content)

            # Extract date
            date_attr = root.attrib.get("Tarih")
            if date_attr:
                effective_date = datetime.strptime(date_attr, "%d.%m.%Y").date()
            else:
                effective_date = datetime.today().date()

            # Update rates in Odoo
            currency_obj = self.env["res.currency"]

            for currency in root.findall("Currency"):
                code = currency.attrib.get("CurrencyCode")
                forex_buying = currency.find("ForexBuying").text

                if code and forex_buying:
                    odoo_currency = currency_obj.search([("name", "=", code)], limit=1)
                    if odoo_currency:
                        # Check if rate exists for the day
                        existing_rate = self.search([
                            ("currency_id", "=", odoo_currency.id),
                            ("name", "=", effective_date),
                            ("company_id", "=", self.env.company.id)
                        ], limit=1)

                        if existing_rate:
                            # Update the existing rate
                            existing_rate.write({
                                "rate": float(forex_buying),
                                "inverse_company_rate": 1 / float(forex_buying),
                            })
                        else:
                            # Create a new rate
                            self.create({
                                "currency_id": odoo_currency.id,
                                "name": effective_date,
                                "rate": float(forex_buying),
                                "inverse_company_rate": 1 / float(forex_buying),
                                "company_id": self.env.company.id,
                            })

                        # Update currency fields
                        odoo_currency.write({
                            "date": effective_date,
                            "inverse_rate": 1 / float(forex_buying),
                        })

        except Exception as e:
            raise exceptions.UserError(f"An error occurred while updating exchange rates: {str(e)}")