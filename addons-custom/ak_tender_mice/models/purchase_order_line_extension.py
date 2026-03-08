# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    """
    purchase.order.line modelini MICE ihaleleri için genişletir.

    NOT: ak_tender zaten `npv_value` ve `calculate_npv()` metodunu içeriyor.
    Bu model yalnızca MICE'a özgü ek alanları ekler:
        - scenario_id    : İlgili MICE senaryosu (tender_line_id üzerinden)
        - scenario_date_id : Tedarikçinin seçtiği tarih seçeneği
        - is_package_price : Paket fiyat mı?

    NPV karşılaştırmaları için mevcut `npv_value` alanı kullanılır.
    """
    _inherit = 'purchase.order.line'

    # ===== SENARYO İLİŞKİSİ =====
    scenario_id = fields.Many2one(
        'ak.tender.scenario',
        compute='_compute_mice_scenario_id',
        store=True,
        string=_('Senaryo'),
        help=_("Bu satırın ait olduğu MICE senaryosu (tender_line_id.scenario_id üzerinden).")
    )

    scenario_date_id = fields.Many2one(
        'ak.tender.scenario.date',
        string=_('Seçilen Tarih Seçeneği'),
        domain="[('scenario_id', '=', scenario_id)]",
        help=_(
            "Tedarikçi hangi tarih aralığı için fiyat veriyor? "
            "Birden fazla tarih seçeneği varsa tedarikçi seçimini belirtmeli."
        )
    )

    # ===== PAKET FİYAT =====
    is_package_price = fields.Boolean(
        string=_('Paket Fiyat'),
        default=False,
        help=_(
            "Tedarikçi satır bazlı fiyat yerine toplam paket fiyat verdi mi? "
            "İşaretlenirse tek satırda toplam tutar girilir."
        )
    )

    # ===== COMPUTED METHODS =====

    @api.depends('tender_line_id', 'tender_line_id.scenario_id')
    def _compute_mice_scenario_id(self):
        """tender_line_id.scenario_id üzerinden senaryo değerini doldur."""
        for line in self:
            line.scenario_id = (
                line.tender_line_id.scenario_id
                if line.tender_line_id
                else False
            )
