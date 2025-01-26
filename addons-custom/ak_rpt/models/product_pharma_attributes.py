from odoo import models, fields, api, _


class ProductATC(models.Model):
    _name = 'product.atc'
    _description = _('ATC Code')

    code = fields.Char(string=_('ATC Code'), required=True, help=_('ATC classification code'))
    name = fields.Char(string=_('ATC Name'), translate=True, required=True, help=_('Name of the ATC code'))

class PriceDecreeReason(models.Model):
    _name = 'price.decree.reason'
    _description = _('Price Decree Reason')
    _order = 'code'

    code = fields.Integer(string=_("Code"), required=True)
    name = fields.Char(string=_("Reason"), translate=True, required=True)


class EquivalentStatus(models.Model):
    _name = 'equivalent.status'
    _description = _('Equivalent Status')

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('Equivalent Status'), translate=True, required=True)

class ReferenceStatus(models.Model):
    _name = 'reference.status'
    _description = _('Reference Status')

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('Reference Status'), translate=True, required=True)


class FDKAgokStatus(models.Model):
    _name = 'fdk.agok.status'
    _description = _('FDK - AGÖK Durumu')

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('FDK - AGÖK Status'), translate=True, required=True)


class SalesPriceType(models.Model):
    _name = 'sales.price.type'
    _description = _('Sales Price Type')

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('Sales Price Type'), translate=True, required=True)


class InhalerProductGroup(models.Model):
    _name = 'inhaler.product.group'
    _description = _('Inhaler Product Group')
    _display = 'display_name'

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('Inhaler Product Group'), translate=True, required=True)
    parent_id = fields.Many2one('inhaler.product.group', string=_('Parent Group'))
    display_name = fields.Char(string=_('Display Name'), translate=True, compute='_compute_display_name')

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.parent_id.name} / {record.name}" if record.parent_id else record.name


class InhalerResistanceGroup(models.Model):
    _name = 'inhaler.resistance.group'
    _description = _('Inhaler Resistance Group')

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('Inhaler Resistance Group'), translate=True, required=True)


class InhalerDeviceCode(models.Model):
    _name = 'inhaler.device.code'
    _description = _('Inhaler Device Code')

    code = fields.Char(string=_('Code'), required=True)
    name = fields.Char(string=_('Device Description'), translate=True, required=True)

class PrescriptionType(models.Model):
    _name = 'prescription.type'
    _description = _('Prescription Type')
    
    name = fields.Char(string=_('Name'), required=True, translate=True)
    code = fields.Char(string=_('Code'), required=True, translate=True)

