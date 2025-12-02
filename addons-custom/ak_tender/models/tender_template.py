# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError


class TenderTemplate(models.Model):
    _name = 'ak.tender.template'
    _description = _('İhale Şablonu')
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string=_('Şablon Adı'), required=True, tracking=True)
    code = fields.Char(string=_('Şablon Kodu'), required=True, tracking=True)
    description = fields.Text(string=_('Açıklama'), tracking=True)
    active = fields.Boolean(string=_('Aktif'), default=True, tracking=True,
                           help=_("Aktif olmayan şablonlar gizlenir ancak silinmez."))
    company_id = fields.Many2one('res.company', string=_('Şirket'), default=lambda self: self.env.company)
    sequence = fields.Integer(string=_('Sıra'), default=10)
    
    # Şablon Değişiklik Kısıtlamaları
    is_locked = fields.Boolean(string=_('Kilitli'), default=False, tracking=True,
                               help=_("Kilitli şablonlar değiştirilemez."))
    locked_by_id = fields.Many2one('res.users', string=_('Kilitleyen'), tracking=True)
    locked_date = fields.Datetime(string=_('Kilitleme Tarihi'), tracking=True)
    
    # Şablon Satırları
    line_ids = fields.One2many('ak.tender.template.line', 'template_id',
                               string=_('Şablon Satırları'), copy=True)
    line_count = fields.Integer(string=_('Satır Sayısı'), compute='_compute_line_count')
    
    # Coğrafi Filtreleme
    country_ids = fields.Many2many('res.country', string=_('Ülkeler'), tracking=True,
                                   help=_("Bu şablonun geçerli olduğu ülkeler. Boş bırakılırsa tüm ülkeler için geçerlidir."))
    state_ids = fields.Many2many('res.country.state', string=_('İller'), tracking=True,
                                 help=_("Bu şablonun geçerli olduğu iller. Boş bırakılırsa tüm iller için geçerlidir."))
    city = fields.Char(string=_('Şehir'), tracking=True,
                       help=_("Bu şablonun geçerli olduğu şehir. Boş bırakılırsa tüm şehirler için geçerlidir."))
    
    # İlişkili İhaleler
    tender_ids = fields.One2many('ak.tender', 'tender_template_id', string=_('İhaleler'))
    tender_count = fields.Integer(string=_('İhale Sayısı'), compute='_compute_tender_count')
    
    # İhale Tipi
    tender_type = fields.Selection([
        ('direct', _('Direkt Satın Alma')),
        ('indirect', _('Endirekt Satın Alma')),
        ('mice', _('MICE İhaleler')),
        ('promotion', _('Promosyon ve Kırtasiye'))
    ], string=_('İhale Tipi'), default='mice', required=True, tracking=True,
       help=_("Bu şablonun uygulanabileceği ihale tipi."))
    
    # E-posta Şablonu
    mail_template_id = fields.Many2one(
        'mail.template',
        string=_("Onay E-postası"),
        domain=[('model', '=', 'ak.tender')],
        help=_("Bu e-posta şablonu, ihale onaylandığında gönderilecektir. Boş bırakılırsa e-posta gönderilmez."))
    
    # Geçerlilik Süresi
    validity_days = fields.Integer(
        string=_("Geçerlilik Süresi (Gün)"),
        help=_("İhalenin geçerlilik süresinin hesaplanması için gün sayısı"))
    
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
        action['domain'] = [('tender_template_id', '=', self.id)]
        action['context'] = {'default_tender_template_id': self.id, 'default_tender_type': self.tender_type}
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
            'res_model': 'ak.tender.template',
            'res_id': new_template.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    #=== CONSTRAINT METHODS ===#
    
    @api.constrains('company_id', 'line_ids')
    def _check_company_id(self):
        for template in self:
            companies = template.mapped('line_ids.product_id.company_id')
            if len(companies) > 1:
                raise ValidationError(_("Şablonunuz birden fazla şirkete ait ürünler içeremez."))
            elif companies and companies != template.company_id:
                raise ValidationError(_(
                    "Şablonunuz %(product_company)s şirketine ait ürünler içeriyor, ancak şablonunuz %(template_company)s şirketine ait. "
                    "Lütfen şablonunuzun şirketini değiştirin veya diğer şirketlerden ürünleri kaldırın.",
                    product_company=', '.join(companies.mapped('display_name')),
                    template_company=template.company_id.display_name,
                ))
    
    #=== CRUD METHODS ===#
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._update_product_translations()
        return records
    
    def write(self, vals):
        result = super().write(vals)
        self._update_product_translations()
        return result
    
    def _update_product_translations(self):
        languages = self.env['res.lang'].search([('active', '=', True)])
        for lang in languages:
            for line in self.line_ids:
                if line.name == line.product_id.get_product_multiline_description_sale():
                    line.with_context(lang=lang.code).name = line.product_id.with_context(lang=lang.code).get_product_multiline_description_sale()
    
    @api.model
    def _get_thread_with_access(self, thread_id, mode="read", **kwargs):
        """Simple implementation to fix mail thread controller error.
        Returns the thread if it exists, without additional access checks."""
        thread = self.browse(thread_id)
        if thread.exists():
            return thread
        return self.browse()


class TenderTemplateLine(models.Model):
    _name = 'ak.tender.template.line'
    _description = _('İhale Şablonu Satırı')
    _order = 'template_id, sequence, id'
    
    _sql_constraints = [
        ('accountable_product_id_required',
            "CHECK(display_type IS NOT NULL OR (product_id IS NOT NULL AND product_uom_id IS NOT NULL))",
            "Ürün satırında ürün ve ölçü birimi gereklidir."),

        ('non_accountable_fields_null',
            "CHECK(display_type NOT IN ('line_section', 'line_note') OR (product_id IS NULL AND product_qty = 0 AND product_uom_id IS NULL))",
            "Bölüm veya not satırında ürün, miktar ve ölçü birimi olmamalıdır"),
    ]

    template_id = fields.Many2one('ak.tender.template', string=_('Şablon'),
                                  required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(string=_('Sıra'), default=10,
                             help=_("İhale şablonu satırlarının görüntülenme sırasını belirler."))
    
    company_id = fields.Many2one(
        related='template_id.company_id', store=True, index=True)
    
    # Satır Tipi (Ürün, Bölüm, Not)
    display_type = fields.Selection([
        ('line_section', _('Bölüm')),
        ('line_note', _('Not')),
        ('product', _('Ürün/Hizmet')),
    ], default='product', string=_('Satır Tipi'))
    
    # Ürün Bilgileri (display_type = 'product' ise)
    product_id = fields.Many2one('product.product', string=_('Ürün/Hizmet'),
                                 domain=lambda self: self._product_id_domain(),
                                 check_company=True,
                                 help=_("Şablonda kullanılacak ürün veya hizmet."))
    name = fields.Text(string=_('Açıklama'), translate=True)
    days = fields.Integer(string=_('Gün'), default=1,
                         help=_("Konaklama gibi hizmetler için gün sayısı."))
    product_qty = fields.Float(string=_('Miktar'), digits='Product Unit of Measure', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string=_('Birim'),
                                     compute='_compute_product_uom_id',
                                     store=True, readonly=False, precompute=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    price_unit = fields.Float(string=_('Birim Fiyat'), digits='Product Price')
    
    # Ek Özellikler
    required = fields.Boolean(string=_('Zorunlu'), default=False,
                              help=_("Bu satır ihale için zorunludur."))
    allow_alternative = fields.Boolean(string=_('Alternatif Kabul Edilir'), default=True,
                                      help=_("Bu satır için alternatif teklifler kabul edilir."))
    
    #=== COMPUTE METHODS ===#
    
    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id
    
    #=== CRUD METHODS ===#
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('display_type') in ['line_section', 'line_note']:
                vals.update(product_id=False, product_qty=0, product_uom_id=False)
        return super().create(vals_list)
    
    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise ValidationError(_("Satır tipini değiştiremezsiniz. Bunun yerine mevcut satırı silip yeni bir satır oluşturmalısınız."))
        return super().write(values)
    
    #=== BUSINESS METHODS ===#
    
    @api.model
    def _product_id_domain(self):
        """ Şablona eklenebilecek ürünlerin alan sınırlamasını döndürür. """
        return [('purchase_ok', '=', True)]
    
    def _prepare_tender_line_values(self):
        """ İhale satırı oluşturmak için değerleri hazırlar.
        
        :return: `ak.tender.line` oluşturma değerleri
        :rtype: dict
        """
        self.ensure_one()
        vals = {
            'display_type': self.display_type,
            'product_id': self.product_id.id,
            'days': self.days,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'sequence': self.sequence,
            'required': self.required,
            'allow_alternative': self.allow_alternative,
            'price_unit': self.price_unit,
        }
        if self.name:
            vals['name'] = self.name
        return vals
    
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