# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceCategoryTemplate(models.Model):
    _name = 'ak.tender.service.template'
    _description = _('MICE Hizmet Şablonu')
    _order = 'name'

    name = fields.Char(string=_('Şablon Adı'), required=True)
    code = fields.Char(string=_('Şablon Kodu'), required=True)
    description = fields.Text(string=_('Açıklama'))
    active = fields.Boolean(string=_('Aktif'), default=True)
    
    # Şablon Değişiklik Kısıtlamaları
    is_locked = fields.Boolean(string=_('Kilitli'), default=False,
                              help=_("Kilitli şablonlar değiştirilemez."))
    locked_by_id = fields.Many2one('res.users', string=_('Kilitleyen'))
    locked_date = fields.Datetime(string=_('Kilitleme Tarihi'))
    
    # Şablon Satırları
    line_ids = fields.One2many('ak.tender.template.line', 'template_id',
                              string=_('Şablon Satırları'))
    line_count = fields.Integer(string=_('Satır Sayısı'), compute='_compute_line_count')
    
    # Coğrafi Filtreleme
    country_ids = fields.Many2many('res.country', string=_('Ülkeler'),
                                  help=_("Bu şablonun geçerli olduğu ülkeler. Boş bırakılırsa tüm ülkeler için geçerlidir."))
    state_ids = fields.Many2many('res.country.state', string=_('İller'),
                                help=_("Bu şablonun geçerli olduğu iller. Boş bırakılırsa tüm iller için geçerlidir."))
    city = fields.Char(string=_('Şehir'),
                      help=_("Bu şablonun geçerli olduğu şehir. Boş bırakılırsa tüm şehirler için geçerlidir."))
    
    # İlişkili İhaleler
    tender_ids = fields.One2many('ak.tender', 'service_template_id', string=_('İhaleler'))
    tender_count = fields.Integer(string=_('İhale Sayısı'), compute='_compute_tender_count')
    
    @api.depends('line_ids')
    def _compute_line_count(self):
        for template in self:
            template.line_count = len(template.line_ids)
    
    @api.depends('tender_ids')
    def _compute_tender_count(self):
        for template in self:
            template.tender_count = len(template.tender_ids)
    
    def action_lock_template(self):
        """Lock the template to prevent modifications."""
        self.ensure_one()
        if self.is_locked:
            raise ValidationError(_("Bu şablon zaten kilitli."))
        
        self.write({
            'is_locked': True,
            'locked_by_id': self.env.user.id,
            'locked_date': fields.Datetime.now()
        })
        
        return True
    
    def action_unlock_template(self):
        """Unlock the template to allow modifications."""
        self.ensure_one()
        if not self.is_locked:
            raise ValidationError(_("Bu şablon zaten kilidi açık."))
        
        self.write({
            'is_locked': False,
            'locked_by_id': False,
            'locked_date': False
        })
        
        return True
    
    def action_view_tenders(self):
        """View tenders using this template."""
        self.ensure_one()
        action = self.env.ref('ak_tender.action_ak_tender').read()[0]
        action['domain'] = [('service_template_id', '=', self.id)]
        action['context'] = {'default_service_template_id': self.id, 'default_tender_type': 'mice'}
        return action
    
    def action_duplicate_template(self):
        """Duplicate the template."""
        self.ensure_one()
        
        # Create a copy of the template
        new_template = self.copy(default={
            'name': _('%s (Kopya)') % self.name,
            'code': _('%s-COPY') % self.code,
            'is_locked': False,
            'locked_by_id': False,
            'locked_date': False
        })
        
        # Redirect to the new template
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.service.template',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def apply_template_to_tender(self, tender_id):
        """Apply this template to a tender."""
        self.ensure_one()
        tender = self.env['ak.tender'].browse(tender_id)
        
        if tender.tender_type != 'mice':
            raise ValidationError(_("Hizmet şablonları sadece MICE ihaleleri için uygulanabilir."))
        
        # Link the template to the tender
        tender.write({'service_template_id': self.id})
        
        # Create tender lines based on template lines
        for template_line in self.line_ids:
            if template_line.display_type in ['line_section', 'line_note']:
                # Create section or note
                vals = {
                    'tender_id': tender.id,
                    'display_type': template_line.display_type,
                    'name': template_line.name,
                    'sequence': template_line.sequence,
                }
                self.env['ak.tender.line'].create(vals)
            elif template_line.product_id:
                # Create product line
                vals = {
                    'tender_id': tender.id,
                    'product_id': template_line.product_id.id,
                    'name': template_line.name or template_line.product_id.name,
                    'product_qty': template_line.product_qty,
                    'product_uom_id': template_line.product_uom_id.id,
                    'price_unit': template_line.price_unit,
                    'sequence': template_line.sequence,
                    'required': template_line.required,
                    'allow_alternative': template_line.allow_alternative,
                }
                self.env['ak.tender.line'].create(vals)
        
        return True


class ServiceTemplateLines(models.Model):
    _name = 'ak.tender.template.line'
    _description = _('MICE Hizmet Şablonu Satırı')
    _order = 'sequence, id'

    template_id = fields.Many2one('ak.tender.service.template', string=_('Şablon'),
                                 required=True, ondelete='cascade')
    sequence = fields.Integer(string=_('Sıra'), default=10)
    
    # Satır Tipi (Ürün, Bölüm, Not)
    display_type = fields.Selection([
        ('line_section', _('Bölüm')),
        ('line_note', _('Not')),
        ('product', _('Ürün/Hizmet')),
    ], default='product', string=_('Satır Tipi'))
    
    # Ürün Bilgileri (display_type = 'product' ise)
    product_id = fields.Many2one('product.product', string=_('Ürün/Hizmet'),
                                domain=[('purchase_ok', '=', True)],
                                help=_("Şablonda kullanılacak ürün veya hizmet."))
    name = fields.Text(string=_('Açıklama'))
    product_qty = fields.Float(string=_('Miktar'), digits='Product Unit of Measure', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string=_('Birim'),
                                    domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    price_unit = fields.Float(string=_('Birim Fiyat'), digits='Product Price')
    
    # Ek Özellikler
    required = fields.Boolean(string=_('Zorunlu'), default=False,
                             help=_("Bu satır ihale için zorunludur."))
    allow_alternative = fields.Boolean(string=_('Alternatif Kabul Edilir'), default=True,
                                     help=_("Bu satır için alternatif teklifler kabul edilir."))
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        
        self.product_uom_id = self.product_id.uom_po_id or self.product_id.uom_id
        if not self.name:
            self.name = self.product_id.name
        
        # Get the standard price as default
        self.price_unit = self.product_id.standard_price
    
    @api.constrains('template_id')
    def _check_template_locked(self):
        for line in self:
            if line.template_id.is_locked:
                raise ValidationError(_("Bu şablon kilitli olduğu için satır eklenemez veya değiştirilemez."))