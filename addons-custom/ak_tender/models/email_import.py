# -*- coding: utf-8 -*-

from odoo import api, models, _
import logging

_logger = logging.getLogger(__name__)


class EmailImport(models.Model):
    _name = 'ak.tender.email.import'
    _description = 'Email Import Scheduler'

    @api.model
    def scheduled_email_import(self):
        """Scheduled action için email import fonksiyonu"""
        try:
            _logger.info("Scheduled email import başlatılıyor")
            
            # Import wizard'ı çağır
            wizard = self.env['import.sat.wizard']
            stats = wizard.import_sat_from_email()
            
            _logger.info(f"Scheduled email import tamamlandı: {stats}")
            
            # Sonuçları log'la
            if stats['sat']['processed'] > 0:
                _logger.info(f"Email import sonuçları - "
                           f"İşlenen: {stats['sat']['processed']}, "
                           f"Oluşturulan: {stats['sat']['created']}, "
                           f"Güncellenen: {stats['sat']['updated']}, "
                           f"Atlanan: {stats['sat']['skipped']}, "
                           f"Hatalı: {stats['sat']['errors']}")
            else:
                _logger.info("Email import - işlenecek dosya bulunamadı")
                
            return True
            
        except Exception as e:
            _logger.error(f"Scheduled email import hatası: {str(e)}", exc_info=True)
            return False