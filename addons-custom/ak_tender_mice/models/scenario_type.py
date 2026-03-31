# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AkTenderScenarioType(models.Model):
    """
    MICE Senaryo Tipi Tanımları — Hiyerarşik

    Yöneticiler yeni senaryo tipleri tanımlayabilir ve hangi tiplerin
    birbirinin altına eklenebileceğini yapılandırabilir.

    Varsayılan tipler (data/scenario_types.xml):
        region          → Lokasyon / Bölge (kök)
        location_hotel  → Otel Paketi
        flight          → Uçuş Paketi
        transfer        → Transfer Paketi
        meal            → Yemek Paketi
        technical       → Teknik Paket
        custom          → Özel Paket
    """
    _name = 'ak.tender.scenario.type'
    _description = 'MICE Senaryo Tipi'
    _order = 'sequence, id'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'name'

    name = fields.Char(string=_('Tip Adı'), required=True, translate=True)
    code = fields.Char(
        string=_('Kod'),
        required=True,
        help=_("Dahili teknik kod. Mevcut kodları değiştirmeyiniz (region, location_hotel, vb.).")
    )
    sequence = fields.Integer(default=10, string=_('Sıra'))
    active = fields.Boolean(default=True, string=_('Aktif'))

    parent_id = fields.Many2one(
        'ak.tender.scenario.type',
        string=_('Üst Tip'),
        ondelete='restrict',
        index=True
    )
    child_ids = fields.One2many(
        'ak.tender.scenario.type',
        'parent_id',
        string=_('Alt Tipler')
    )
    parent_path = fields.Char(index=True, unaccent=False)

    # ===== DAVRANIŞ BAYRAKLARI =====
    can_have_children = fields.Boolean(
        string=_('Alt Paket Eklenebilir'),
        default=True,
        help=_("Bu tipteki senaryolara 'Paket Ekle' butonu ile alt paket eklenebilir mi?")
    )
    is_root = fields.Boolean(
        string=_('Kök Tip'),
        default=False,
        help=_(
            "Bu tip en üst düzey (bölge/lokasyon) senaryoları temsil eder. "
            "Kök tiplerde otel, pansiyon, fiyatlandırma gibi alanlar gizlenir."
        )
    )
    show_hotel_fields = fields.Boolean(
        string=_('Otel Alanları Göster'),
        default=False,
        help=_("Senaryo formunda Otel/Mekan ve Pansiyon Tipi alanlarını göster.")
    )
    show_pricing_fields = fields.Boolean(
        string=_('Fiyatlandırma Sekmesi Göster'),
        default=True,
        help=_("Senaryo formunda Fiyatlandırma ve Teklifler sekmesini göster.")
    )
    is_default = fields.Boolean(
        string=_('Varsayılan'),
        default=False,
        help=_(
            "'Paket Ekle' sihirbazı açıldığında bu tip işaretli gelsin. "
            "Birden fazla tip varsayılan olabilir."
        )
    )
    color = fields.Integer(string=_('Renk'), default=0)

    allowed_child_type_ids = fields.Many2many(
        'ak.tender.scenario.type',
        'scenario_type_allowed_children_rel',
        'parent_type_id',
        'child_type_id',
        string=_('İzin Verilen Alt Tipler'),
        help=_(
            "Bu tipteki senaryolara hangi tip alt paketler eklenebilir? "
            "Boş bırakılırsa tüm aktif tipler eklenebilinir."
        )
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Senaryo tipi kodu benzersiz olmalıdır!'),
    ]

    # is_default: birden fazla tip default olabilir — kısıtlama yok.

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Döngüsel tip hiyerarşisi oluşturulamaz!'))

    def get_allowed_children(self):
        """
        Bu tip için alt paket eklenebilecek tipleri döndür.
        allowed_child_type_ids boşsa tüm aktif tipler (kökler hariç) döner.
        """
        self.ensure_one()
        if self.allowed_child_type_ids:
            return self.allowed_child_type_ids
        return self.search([('active', '=', True), ('is_root', '=', False)])
