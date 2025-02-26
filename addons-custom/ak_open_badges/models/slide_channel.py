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
            'verification_type': 'signed',
            'recipient_type': 'email',
            })
            # Set the badge_assertion_id field
            partner.badge_assertion_id = badge_assertion
        return True

    @api.model
    def reset_training(self, partner_id, course_id):
        record = self.env['slide.channel.partner'].search([
            ('partner_id', '=', partner_id),
            ('channel_id', '=', course_id)
        ])
        if record:
            record.write({'completed': False, 'progress': 0})  # Tamamlanma durumunu sıfırla
            return "Katılımcı eğitimi tamamlanmadı olarak işaretlendi."
        return "Katılımcı veya eğitim bulunamadı."