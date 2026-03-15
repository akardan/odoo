# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddPackagesWizard(models.TransientModel):
    """
    Senaryo altına paket ekleme sihirbazı.
    
    Kullanıcı hangi paket tiplerini eklemek istediğini seçer,
    wizard seçilen her paket tipi için yeni bir alt senaryo oluşturur.
    """
    _name = 'ak.tender.add.packages.wizard'
    _description = 'Paket Ekleme Sihirbazı'

    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Üst Senaryo'),
        required=True,
        readonly=True,
        help=_("Paketlerin ekleneceği üst senaryo (genellikle bölge senaryosu).")
    )
    
    tender_id = fields.Many2one(
        'ak.tender',
        related='scenario_id.tender_id',
        string=_('İhale'),
        readonly=True
    )

    # Paket seçenekleri - TEMEL PAKETLER
    add_flight = fields.Boolean(
        string=_('Uçuş Paketi'),
        default=False,
        help=_("Uçuş paketi ekle")
    )
    add_transfer = fields.Boolean(
        string=_('Transfer Paketi'),
        default=False,
        help=_("Transfer hizmeti paketi ekle")
    )
    add_location_hotel = fields.Boolean(
        string=_('Otel Paketi'),
        default=True,
        help=_("Otel konaklama paketi ekle")
    )
    
    # Paket seçenekleri - EK PAKETLER
    add_technical = fields.Boolean(
        string=_('Teknik Paket'),
        default=False,
        help=_("Teknik ekipman ve hizmet paketi ekle")
    )
    add_meal = fields.Boolean(
        string=_('Yemek Paketi'),
        default=False,
        help=_("F&B / Yemek paketi ekle")
    )
    add_tour = fields.Boolean(
        string=_('Gezi Paketi'),
        default=False,
        help=_("Gezi ve aktivite paketi ekle")
    )
    add_custom = fields.Boolean(
        string=_('Özel Paket'),
        default=False,
        help=_("Özel/diğer paket ekle")
    )

    # Ortak bilgiler
    location_id = fields.Many2one(
        'res.country.state',
        string=_('İl / Bölge'),
        help=_("Tüm paketler için varsayılan lokasyon")
    )
    
    person_count = fields.Integer(
        string=_('Kişi Sayısı'),
        help=_("Tüm paketler için varsayılan kişi sayısı")
    )

    @api.model
    def default_get(self, fields_list):
        """Varsayılan değerleri üst senaryodan al."""
        res = super().default_get(fields_list)
        scenario_id = self.env.context.get('default_scenario_id')
        if scenario_id:
            scenario = self.env['ak.tender.scenario'].browse(scenario_id)
            res.update({
                'location_id': scenario.location_id.id if scenario.location_id else False,
                'person_count': scenario.person_count or scenario.tender_id.total_person_count or 0,
            })
        return res

    def action_add_packages(self):
        """Seçilen paketleri oluştur."""
        self.ensure_one()
        
        # En az bir paket seçilmiş olmalı
        if not any([
            self.add_flight,
            self.add_transfer,
            self.add_location_hotel,
            self.add_technical,
            self.add_meal,
            self.add_tour,
            self.add_custom
        ]):
            raise UserError(_("Lütfen en az bir paket tipi seçin!"))

        created_scenarios = self.env['ak.tender.scenario']
        sequence = 10

        # Paket tiplerini ve isimlerini tanımla (sıralama önemli)
        package_types = [
            (self.add_flight, 'flight', _('Uçuş Paketi')),
            (self.add_transfer, 'transfer', _('Transfer Paketi')),
            (self.add_location_hotel, 'location_hotel', _('Otel Paketi')),
            (self.add_technical, 'technical', _('Teknik Paket')),
            (self.add_meal, 'meal', _('Yemek Paketi')),
            (self.add_tour, 'custom', _('Gezi Paketi')),
            (self.add_custom, 'custom', _('Özel Paket')),
        ]

        for should_add, pkg_type, pkg_name in package_types:
            if should_add:
                # Senaryo adını oluştur
                name_parts = []
                if self.scenario_id.name:
                    name_parts.append(self.scenario_id.name)
                name_parts.append(pkg_name)
                scenario_name = ' — '.join(name_parts)

                # Yeni senaryo oluştur
                vals = {
                    'name': scenario_name,
                    'tender_id': self.tender_id.id,
                    'parent_id': self.scenario_id.id,
                    'scenario_type': pkg_type,
                    'location_id': self.location_id.id if self.location_id else False,
                    'person_count': self.person_count,
                    'sequence': sequence,
                }
                
                scenario = self.env['ak.tender.scenario'].create(vals)
                created_scenarios |= scenario
                sequence += 10

        # Başarı mesajı
        if created_scenarios:
            message = _('%d paket başarıyla oluşturuldu.') % len(created_scenarios)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Başarılı'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        
        return {'type': 'ir.actions.act_window_close'}
