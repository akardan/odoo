from odoo import models, fields, api, _

class EventEvent(models.Model):
    _inherit = 'event.event'
    
    training_id = fields.Many2one(
        'slide.channel',
        string=_('Training'),
        help=_('Select the training channel for this event')
    )
    
    is_training_event = fields.Boolean(
        string=_('Is Training Event'), 
        compute='_compute_is_training_event',
        store=False
    )
    
    @api.depends('event_type_id')
    def _compute_is_training_event(self):
        for record in self:
            record.is_training_event = (
                record.event_type_id and 
                record.event_type_id.name == 'Training'
            )
    
