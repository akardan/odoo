from odoo import models, fields, _, api

class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    badge_class_id = fields.Many2one('badge.class', string=_('Certificate Class'), tracking=True)
    issuance_date = fields.Datetime(string=_('Issuance Date'), default=fields.Datetime.now, required=True, tracking=True)
    
class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'
    badge_assertion_id = fields.Many2one('badge.assertion', string=_('Badge Assertion'), tracking=True)
    
    def create_certificates(self):
        for partner in self:
            # Create a badge.assertion record for each partner
            badge_assertion = self.env['badge.assertion'].create({
            'badge_class_id': partner.channel_id.badge_class_id.id,
            'recipient_id': partner.partner_id.id,
            'issuance_date': partner.channel_id.issuance_date,
            'recipient_type': 'email',
            })
            # Set the badge_assertion_id field
            partner.badge_assertion_id = badge_assertion
        return True
