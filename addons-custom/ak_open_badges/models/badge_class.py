from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BadgeClass(models.Model):
    _name = 'badge.class'
    _description = _('Open Badge Class Definition')
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    def _get_langs(self):
        """Sistemde yüklü olan dillerin listesini döndürür"""
        return [(lang.code, lang.name) for lang in self.env['res.lang'].search([('active', '=', True)])]

    # Çevrilmesi gereken alanlar
    name = fields.Char(string=_('Name'), required=True, translate=True, tracking=True)
    description = fields.Text(string=_('Description'), required=True, translate=True, tracking=True)
    criteria_narrative = fields.Text(string=_("Criteria Narrative"), translate=True, tracking=True)

    # Çevrilmeyen alanlar
    badge_type_id = fields.Many2one('badge.type', string=_('Badge Type'), tracking=True)
    image = fields.Binary(string=_('Image'), required=True, tracking=True)
    criteria_url = fields.Char(string=_("Criteria URL"), required=True)
    issuer_id = fields.Many2one('badge.issuer', string=_('Issuer'), required=True, tracking=True)
    tags = fields.Many2many('badge.tag', string=_('Tags'))
    alignment = fields.One2many('badge.alignment', 'badge_class_id', string=_('Alignments'), tracking=True)
    active = fields.Boolean(string=_('Active'), default=True, tracking=True)  # Arşivleme özelliği için eklendi

    primary_lang = fields.Selection(
        selection='_get_langs',
        string=_('Primary Language'),
        default=lambda self: self.env.user.lang or 'en_US',
        required=True
    )
    secondary_lang = fields.Selection(
        selection='_get_langs',
        string=_('Secondary Language')
    )    

    @api.constrains('primary_lang', 'secondary_lang')
    def _check_different_languages(self):
        for record in self:
            if record.primary_lang == record.secondary_lang:
                raise ValidationError(_('Primary and Secondary languages must be different'))
                
    def get_image_url(self):
        """Badge görselinin URL'ini oluştur"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web/image?model=badge.class&id={self.id}&field=image"
    
    def get_json_ld(self):
        """JSON-LD formatında rozet sınıfı verisi"""
        # Varsayılan dili kullan
        default_lang = 'en_US'
        self = self.with_context(lang=default_lang)

        return {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "BadgeClass",
            "id": f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/badge/class/{self.id}",
            "name": self.name,
            "description": self.description,
            "image": self.get_image_url(),
            "criteria": {
                "id": self.criteria_url,
                "narrative": self.criteria_narrative,
            },
            "issuer": self.issuer_id.get_json_ld(),
            "tags": self.tags.mapped('name') if self.tags else [],
            "alignment": [align.get_json_ld() for align in self.alignment] if self.alignment else [],
        }
