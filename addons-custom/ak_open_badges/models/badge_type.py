from odoo import models, fields, api, _

class BadgeType(models.Model):
    _name = 'badge.type'
    _description = _('Badge Type')

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

    _sql_constraints = [
        ('code_uniq', 'unique(code)', _('Badge Type Code must be unique!'))  # Hata mesajı çevrilebilir
    ]
