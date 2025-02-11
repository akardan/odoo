from odoo import models, fields, api, _

class BadgeType(models.Model):
    _name = 'badge.type'
    _description = _('Badge Type')
    _rec_name = 'display_name'

    # Çevrilecek alanlar
    name = fields.Char(string=_('Name'), required=True, translate=True)
    description = fields.Text(string=_('Description'), translate=True)
    phrase4recipient = fields.Char(string=_('Phrase for Recipient'), translate=True, 
                                   default=_("This certifies that"))
    phrase4certificate = fields.Char(string=_('Phrase for Certificate'), translate=True, 
                                     default=_("has successfully completed the"))
    phrase_last = fields.Char(string=_('Last Phrase'), translate=True, 
                              help=_("Phrase to be used after the badge class name"))
    
    # Çevrilmeyen alanlar
    code = fields.Char(string=_('Code'), required=True) 
    active = fields.Boolean(string=_('Active'), default=True)
    display_name = fields.Char(string=_('Display Name'), compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', _('Badge Type Code must be unique!'))  # Hata mesajı çevrilebilir
    ]

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.code} - {record.name}"
