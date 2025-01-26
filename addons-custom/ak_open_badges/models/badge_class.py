from odoo import models, fields, api, _

class BadgeClass(models.Model):
    _name = 'badge.class'
    _description = _('Open Badge Class Definition')
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    name = fields.Char(string=_('Name'), required=True)
    description = fields.Text(string=_('Description'), required=True)
    badge_type_id = fields.Many2one('badge.type', string=_('Badge Type'))
    image = fields.Binary(string=_('Image'), required=True)
    criteria_url = fields.Char(string=_("Criteria URL"), required=True)
    criteria_narrative = fields.Text(string=_("Criteria Narrative"))
    issuer_id = fields.Many2one('badge.issuer', string=_('Issuer'), required=True)
    tags = fields.Many2many('badge.tag', string=_('Tags'))
    alignment = fields.One2many('badge.alignment', 'badge_class_id', string=_('Alignments'))
    active = fields.Boolean(default=True)  # Arşivleme özelliği için eklendi
    
    def get_image_url(self):
        """Badge görselinin URL'ini oluştur"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web/image?model=badge.class&id={self.id}&field=image"
    
    def get_json_ld(self):
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
