# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AddPackagesWizard(models.TransientModel):
    """
    Senaryo altına paket ekleme sihirbazı.

    Kullanıcı hangi paket tiplerini eklemek istediğini seçer,
    wizard seçilen her paket tipi için yeni bir alt senaryo oluşturur.
    İzin verilen tipler, üst senaryonun tipinin allowed_child_type_ids'inden gelir.
    """
    _name = 'ak.tender.add.packages.wizard'
    _description = 'Paket Ekleme Sihirbazı'

    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        string=_('Üst Senaryo'),
        required=True,
        readonly=True,
        help=_("Paketlerin ekleneceği üst senaryo.")
    )
    tender_id = fields.Many2one(
        'ak.tender',
        related='scenario_id.tender_id',
        string=_('İhale'),
        readonly=True
    )
    parent_scenario_type_id = fields.Many2one(
        'ak.tender.scenario.type',
        related='scenario_id.scenario_type_id',
        string=_('Üst Senaryo Tipi'),
        readonly=True,
    )

    # Seçilen paket tipleri (Many2many — işaretli olanlar)
    selected_type_ids = fields.Many2many(
        'ak.tender.scenario.type',
        'add_packages_wizard_type_rel',
        'wizard_id',
        'type_id',
        string=_('Eklenecek Paket Tipleri'),
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
        """Varsayılan değerleri üst senaryodan al; is_default tipler işaretli gelsin."""
        res = super().default_get(fields_list)
        scenario_id = self.env.context.get('default_scenario_id')
        if scenario_id:
            scenario = self.env['ak.tender.scenario'].browse(scenario_id)
            res.update({
                'location_id': scenario.location_id.id if scenario.location_id else False,
                'person_count': scenario.person_count or scenario.tender_id.total_person_count or 0,
            })
            # is_default=True olan tipleri varsayılan seçili getir
            # (üst senaryonun izin verdiği tipler arasından)
            if scenario.scenario_type_id:
                allowed = scenario.scenario_type_id.get_allowed_children()
            else:
                allowed = self.env['ak.tender.scenario.type'].search([
                    ('active', '=', True), ('is_root', '=', False)
                ])
            default_types = allowed.filtered('is_default')
            if default_types:
                res['selected_type_ids'] = [(6, 0, default_types.ids)]
        return res

    def action_add_packages(self):
        """Seçilen paket tiplerini alt senaryo olarak oluştur."""
        self.ensure_one()

        if not self.selected_type_ids:
            raise UserError(_("Lütfen en az bir paket tipi seçin!"))

        created_scenarios = self.env['ak.tender.scenario']
        sequence = 10

        for pkg_type in self.selected_type_ids.sorted('sequence'):
            scenario_name = ' — '.join(filter(None, [self.scenario_id.name, pkg_type.name]))
            vals = {
                'name': scenario_name,
                'tender_id': self.tender_id.id,
                'parent_id': self.scenario_id.id,
                'scenario_type_id': pkg_type.id,
                'location_id': self.location_id.id if self.location_id else False,
                'person_count': self.person_count,
                'sequence': sequence,
            }
            created_scenarios |= self.env['ak.tender.scenario'].create(vals)
            sequence += 10

        if created_scenarios:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Başarılı'),
                    'message': _('%d paket başarıyla oluşturuldu.') % len(created_scenarios),
                    'type': 'success',
                    'sticky': False,
                }
            }
        return {'type': 'ir.actions.act_window_close'}
