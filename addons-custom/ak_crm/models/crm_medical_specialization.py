from odoo import fields, models

class MedicalSpecialization(models.Model):
    _name = 'crm.medical.specialization'
    _description = 'Medical Specialization'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Specialization', required=True)
