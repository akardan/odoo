from odoo import models, fields, api, _

class BadgeEvidence(models.Model):
    _name = 'badge.evidence'
    _description = _('Badge Evidence')

    # Çevrilecek alanlar
    name = fields.Char(string=_('Name'), required=True, translate=True)
    description = fields.Text(string=_('Description'), translate=True)
    narrative = fields.Text(string=_('Narrative'), translate=True)
    genre = fields.Char(string=_('Genre'), translate=True)
    audience = fields.Char(string=_('Audience'), translate=True)
    type = fields.Char(string=_('Type'), default="Evidence", translate=True)

    # Çevrilmeyecek alanlar
    assertion_id = fields.Many2one('badge.assertion', string=_('Assertion'), required=True)
    id = fields.Char(string=_("Evidence URL"))
    
    def get_json_ld(self):
        # Varsayılan dili kullan
        default_lang = 'en_US'
        self = self.with_context(lang=default_lang)

        evidence = {
            "type": self.type,
            "id": self.id,
            "name": self.name,
        }
        
        if self.description:
            evidence["description"] = self.description
        if self.narrative:
            evidence["narrative"] = self.narrative
        if self.genre:
            evidence["genre"] = self.genre
        if self.audience:
            evidence["audience"] = self.audience
            
        return evidence
    