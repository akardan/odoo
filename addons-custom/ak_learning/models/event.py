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
        store=True
    )
    
    @api.depends('event_type_id')
    def _compute_is_training_event(self):
        for record in self:
            # Assuming '2' is the ID for the event.type record that signifies a training event.
            # It's better to use an XML ID or a configuration parameter for this.
            # For now, we'll correct the comparison.
            if record.event_type_id:
                record.is_training_event = (record.event_type_id.id == 2)
            else:
                record.is_training_event = False
    
