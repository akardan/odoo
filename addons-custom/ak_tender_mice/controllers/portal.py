# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.ak_tender.controllers.portal import TenderPortal

_logger = logging.getLogger(__name__)


class MiceTenderPortal(TenderPortal):
    """
    MICE İhale Portalı Kontrolcüsü

    ak_tender'ın portal kontrolcüsünü genişleterek MICE ihalelerinde:
    - Senaryo bazlı PO satır gruplarını hazırla
    - Tedarikçilerin tarih seçeneği (scenario_date_id) belirtmesine imkân ver
    - Senaryo özetini portal şablonuna ilet
    """

    @http.route(
        ['/my/purchase/mice/update_scenario_date'],
        type='json',
        auth='public',
        website=True
    )
    def portal_update_mice_scenario_date(self, order_id, access_token=None, lines=None, **kw):
        """
        MICE senaryolarında tarih seçeneği (scenario_date_id) güncelleme endpoint'i.

        Her PO satırı için tedarikçi hangi tarih aralığında teklif verdiğini belirtir.
        Payload:
            lines: [{'line_id': int, 'scenario_date_id': int | ''}, ...]
        """
        try:
            order_sudo = self._document_check_access('purchase.order', order_id, access_token)
            if not order_sudo:
                return {'error': 'Geçersiz sipariş erişimi.'}

            if order_sudo.state not in ['draft', 'sent']:
                return {'error': 'Bu siparişte düzenleme yapılamaz.'}

            if not lines:
                return {'error': 'Güncellenecek satır bulunamadı.'}

            updated = 0
            for line_data in lines:
                line_id = line_data.get('line_id')
                if not line_id:
                    continue

                line = request.env['purchase.order.line'].sudo().browse(int(line_id))
                if not line or line.order_id.id != order_sudo.id:
                    continue

                scenario_date_id = line_data.get('scenario_date_id')
                if scenario_date_id:
                    try:
                        line.write({'scenario_date_id': int(scenario_date_id)})
                        updated += 1
                    except (ValueError, TypeError) as e:
                        _logger.warning('scenario_date_id güncelleme hatası: %s', str(e))
                else:
                    line.write({'scenario_date_id': False})
                    updated += 1

            return {'result': {'success': True, 'updated': updated}}

        except Exception as e:
            _logger.exception('MICE scenario_date güncelleme hatası: %s', str(e))
            return {'error': str(e)}

    def _prepare_mice_portal_data(self, order):
        """
        MICE portali için senaryo bazlı satır gruplarını hazırla.

        Dönüş: Her senaryo için dict listesi:
            [{'scenario': ak.tender.scenario, 'lines': purchase.order.line[]}]
        Senaryosu olmayan satırlar 'no_scenario' grubuna düşer.
        """
        if not order or order.tender_id.tender_type != 'mice':
            return []

        scenario_map = {}
        no_scenario_lines = []

        for line in order.order_line.filtered(lambda l: not l.display_type):
            scenario = line.scenario_id
            if scenario:
                if scenario.id not in scenario_map:
                    scenario_map[scenario.id] = {
                        'scenario': scenario,
                        'lines': [],
                    }
                scenario_map[scenario.id]['lines'].append(line)
            else:
                no_scenario_lines.append(line)

        groups = list(scenario_map.values())
        if no_scenario_lines:
            groups.append({'scenario': None, 'lines': no_scenario_lines})

        return groups
