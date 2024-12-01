from odoo import models, fields, api, _
import base64
import io
import pandas as pd
from odoo.exceptions import UserError
import unicodedata


class CountryImportWizard(models.TransientModel):
    _name = 'country.import.wizard'
    _description = 'Country Code Import Wizard'

    file = fields.Binary(string="Excel File", required=True)
    filename = fields.Char(string="File Name", required=True)

    def normalize_text(self, text):
        # Unicode karakterlerini normalleştirerek harflerin standardize edilmesi
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').casefold()

    def action_import_country_codes(self):
        # Excel dosyasını okuyun ve verileri işleyin
        if not self.file:
            raise UserError(_('Please upload a file to proceed.'))

        try:
            # Dosyayı oku
            file_data = base64.b64decode(self.file)
            excel_data = io.BytesIO(file_data)
            df = pd.read_excel(excel_data, dtype={'titck_country_code': str})

            # Excel'den verileri işlemek
            for index, row in df.iterrows():
                country_code = str(row['countrycode']).strip() if 'countrycode' in row and row['countrycode'] else ''
                country_name = str(row['countryName']).strip() if 'countryName' in row and row['countryName'] else ''
                country_name = self.normalize_text(country_name)
                titck_country_code = str(row['titck_country_code']).strip() if 'titck_country_code' in row and row['titck_country_code'] else ''

                # Ülkeleri adına göre ara ve güncelle (İngilizce ve Türkçe çevirileri kontrol et, case insensitive)
                country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
                if not country:
                    country = self.env['res.country'].with_context(lang='tr_TR').search(
                        [('name', '=ilike', country_name)], limit=1)
                if not country:
                    country = self.env['res.country'].with_context(lang='en_US').search(
                        [('name', '=ilike', country_name)], limit=1)

                if country:
                    country.write({'titck_country_code': titck_country_code})
                else:
                    # raise UserError(_(f"{row['countryName']} bulunamadı."))
                    continue

        except UserError as ue:
            raise ue
        except Exception as e:
            raise UserError(_('An unexpected error occurred while importing country codes: %s') % str(e))
