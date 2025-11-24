import logging
import requests
from xml.etree import ElementTree as ET
from datetime import datetime
from odoo import api, models, exceptions, fields

_logger = logging.getLogger(__name__)

class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    @api.model
    def update_exchange_rates(self):
        try:
            url = self.env["ir.config_parameter"].sudo().get_param("ak_currency_rate_tcmb.tcmb_url")
            if not url:
                _logger.warning("TCMB Exchange Rate URL is not configured. Using default URL.")
                url = "https://www.tcmb.gov.tr/kurlar/today.xml" # Fallback to default

            _logger.info(f"Fetching exchange rates from TCMB URL: {url}")
            response = requests.get(url)

            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

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
                    if not odoo_currency:
                        _logger.warning(f"Currency with code '{code}' not found in Odoo. Skipping.")
                        continue

                    try:
                        rate_value = float(forex_buying)
                        if rate_value == 0:
                            _logger.warning(f"ForexBuying rate for {code} is zero. Skipping to avoid ZeroDivisionError.")
                            continue
                        inverse_rate_value = 1 / rate_value
                    except ValueError:
                        _logger.error(f"Invalid ForexBuying value '{forex_buying}' for currency '{code}'. Skipping.")
                        continue
                    except ZeroDivisionError:
                        _logger.error(f"Zero ForexBuying value for currency '{code}'. Skipping to avoid division by zero.")
                        continue

                    # Check if rate exists for the day
                    existing_rate = self.search([
                        ("currency_id", "=", odoo_currency.id),
                        ("name", "=", effective_date),
                        ("company_id", "=", self.env.company.id)
                    ], limit=1)

                    if existing_rate:
                        # Update the existing rate
                        existing_rate.write({
                            "rate": inverse_rate_value, # Corrected: Odoo rate is 1/ForexBuying
                            "inverse_company_rate": rate_value, # Corrected: Inverse rate is ForexBuying
                        })
                        _logger.info(f"Updated exchange rate for {code} to {rate_value} on {effective_date}.")
                    else:
                        # Create a new rate
                        self.create({
                            "currency_id": odoo_currency.id,
                            "name": effective_date,
                            "rate": inverse_rate_value, # Corrected: Odoo rate is 1/ForexBuying
                            "inverse_company_rate": rate_value, # Corrected: Inverse rate is ForexBuying
                            "company_id": self.env.company.id,
                        })
                        _logger.info(f"Created new exchange rate for {code} to {rate_value} on {effective_date}.")

        except requests.exceptions.RequestException as e:
            _logger.error(f"HTTP Request failed while fetching exchange rates from TCMB: {e}")
            raise exceptions.UserError(f"Failed to fetch exchange rates from TCMB: {e}")
        except ET.ParseError as e:
            _logger.error(f"XML parsing failed for TCMB exchange rates: {e}")
            raise exceptions.UserError(f"Failed to parse TCMB exchange rates XML: {e}")
        except Exception as e:
            _logger.error(f"An unexpected error occurred while updating exchange rates: {e}")
            raise exceptions.UserError(f"An error occurred while updating exchange rates: {str(e)}")