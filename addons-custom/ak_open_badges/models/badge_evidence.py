from odoo import models, fields, api, _

class BadgeEvidence(models.Model):
    _name = 'badge.evidence'
    _description = _('Badge Evidence')

    assertion_id = fields.Many2one('badge.assertion', string=_('Assertion'), required=True)
    type = fields.Char(string=_('Type'), default="Evidence")
    id = fields.Char(string=_("Evidence URL"))
    name = fields.Char(string=_('Name'), required=True)
    description = fields.Text(string=_('Description'))
    narrative = fields.Text(string=_('Narrative'))
    genre = fields.Char(string=_('Genre'))
    audience = fields.Char(string=_('Audience'))
    
    def get_json_ld(self):
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
    