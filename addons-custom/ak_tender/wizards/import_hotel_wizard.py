# -*- coding: utf-8 -*-

import base64
import io
import logging
import tempfile
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug('Cannot import xlrd')

class ImportHotelWizard(models.TransientModel):
    _name = 'import.hotel.wizard'
    _description = 'Import Hotels from Excel'

    excel_file = fields.Binary(string='Excel Dosyası', required=True)
    file_name = fields.Char(string='Dosya Adı')

    def action_import(self):
        """
        Import hotels from Excel file
        Excel columns should be:
        Şehir, Yöre, Konum, Otel, Yıldız, Oda, Pansiyon, Döviz
        """
        if not self.excel_file:
            raise UserError(_('Lütfen bir Excel dosyası seçin.'))

        try:
            # Read the Excel file
            data = base64.b64decode(self.excel_file)
            book = xlrd.open_workbook(file_contents=data)
            sheet = book.sheet_by_index(0)

            # Check if the file has data
            if sheet.nrows <= 1:
                raise UserError(_('Excel dosyası boş veya sadece başlık satırı içeriyor.'))

            # Process each row (skip header row)
            created_count = 0
            updated_count = 0
            
            for row_idx in range(1, sheet.nrows):
                row = sheet.row_values(row_idx)
                
                # Extract data from row
                city = row[0] if len(row) > 0 else ''
                region = row[1] if len(row) > 1 else ''
                location = row[2] if len(row) > 2 else ''
                hotel_name = row[3] if len(row) > 3 else ''
                star_rating = row[4] if len(row) > 4 else ''
                room_type = row[5] if len(row) > 5 else ''
                pension_type = row[6] if len(row) > 6 else ''
                currency = row[7] if len(row) > 7 else ''
                
                # Skip row if hotel name is empty
                if not hotel_name:
                    continue
                
                # Convert star rating to string format expected by the field
                if isinstance(star_rating, (int, float)):
                    star_rating = str(int(star_rating))
                elif isinstance(star_rating, str) and 'Yıldız' in star_rating:
                    star_rating = star_rating.replace('Yıldız', '').strip()
                elif isinstance(star_rating, str) and star_rating.isdigit():
                    star_rating = star_rating
                else:
                    star_rating = False
                
                # Get state_id for the city
                state_id = self._get_state_id(city) if city else False
                
                # Check if hotel already exists - more comprehensive check
                domain = [
                    '|',
                    '&', ('name', '=', hotel_name), ('is_hotel', '=', True),
                    '&', ('name', 'ilike', hotel_name), ('is_hotel', '=', True)
                ]
                
                if state_id:
                    domain.append(('state_id', '=', state_id))
                
                existing_hotel = self.env['res.partner'].search(domain, limit=1)
                
                # Prepare values for create/write
                vals = {
                    'name': hotel_name,
                    'is_hotel': True,
                    'hotel_star_rating': star_rating,
                    'state_id': self._get_state_id(city) if city else False,  # Use city as state (Il/Eyalet)
                    'country_id': self._get_country_id('TR'),  # Default to Turkey
                    'street': location,  # Use location as street address
                    'comment': f"Şehir: {city}\nYöre: {region}\nKonum: {location}\nOda Tipi: {room_type}\nPansiyon: {pension_type}\nPara Birimi: {currency}",
                    'company_type': 'company',
                }
                
                if existing_hotel:
                    # Update existing hotel
                    existing_hotel.write(vals)
                    updated_count += 1
                else:
                    # Create new hotel
                    self.env['res.partner'].create(vals)
                    created_count += 1
            
            # Show success message
            message = _(f'{created_count} yeni otel oluşturuldu, {updated_count} mevcut otel güncellendi.')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('İçe Aktarma Başarılı'),
                    'message': message,
                    'sticky': False,
                    'type': 'success',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
                
        except xlrd.XLRDError:
            raise UserError(_('Geçersiz Excel dosyası. Lütfen doğru formatta bir dosya yükleyin.'))
        except Exception as e:
            raise UserError(_(f'İçe aktarma sırasında hata oluştu: {str(e)}'))
    
    def _get_state_id(self, city_name):
        """Find state_id by name or create if not exists"""
        if not city_name:
            return False
        
        # Get Turkey country ID
        country_id = self._get_country_id('TR')
        if not country_id:
            return False
            
        # Search for existing state
        state = self.env['res.country.state'].search([
            ('name', 'ilike', city_name),
            ('country_id.code', '=', 'TR')
        ], limit=1)
        
        if state:
            return state.id
            
        # Create new state if not found
        try:
            new_state = self.env['res.country.state'].create({
                'name': city_name,
                'code': city_name[:3].upper(),
                'country_id': country_id
            })
            return new_state.id
        except Exception as e:
            _logger.error(f"Error creating state: {str(e)}")
            return False
        
    def _get_country_id(self, country_code):
        """Find country_id by code"""
        if not country_code:
            return False
        
        country = self.env['res.country'].search([
            ('code', '=', country_code)
        ], limit=1)
        
        return country.id if country else False