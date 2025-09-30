# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class WorkflowDynamicParameter(models.Model):
    _name = 'ak.workflow.dynamic.parameter'
    _description = 'Workflow Dynamic Parameter Configuration'
    _rec_name = 'name'

    name = fields.Char(string=_('Parametre Adı'), compute='_compute_name', store=True)
    
    # Model Seçimi
    model_id = fields.Many2one('ir.model', string=_('Model'), required=False, ondelete='set null')
    
    model_name = fields.Char(string=_('Model Name'), related='model_id.model', store=True, readonly=True)

    # Workflow Seçimi (Many2many - birden fazla workflow'da kullanılabilir)
    workflow_ids = fields.Many2many('ak.workflow.definition', string=_('Workflows'),
                                   help=_('This parameter will be active in which workflows'))
    
    # Domain Filtresi (workflow_current_state_id dahil)
    domain_filter = fields.Text(string=_('Kayıt Filtresi'), required=True)
    
    # Workflow Field ve Değer
    model_field = fields.Many2one(
        'ir.model.fields',
        string=_('Model Field'),
        required=False,
        domain="[('model_id', '=', model_id)]",
        ondelete='set null'
    )
    
    field_name = fields.Selection(
        selection='_get_field_selection',
        string=_('Field Name'),
        required=True,
        help=_('Field name (e.g., workflow_current_state_id.default_duration_days)')
    )
    
    available_fields = fields.Text(
        string=_('Available Fields'),
        compute='_compute_available_fields',
        help=_('Available fields for the selected model')
    )
    
    field_value_int = fields.Integer(string=_('Değer (Integer)'), required=False)
    field_value_str = fields.Char(string=_('Değer (String)'), required=False)
    field_value_float = fields.Float(string=_('Değer (Float)'), required=False)
    field_value_bool = fields.Boolean(string=_('Değer (Boolean)'), required=False)
    field_value_date = fields.Date(string=_('Değer (Date)'), required=False)
    field_value_datetime = fields.Datetime(string=_('Değer (Datetime)'), required=False)
    
    active = fields.Boolean(string=_('Aktif'), default=True)
    
    def _get_field_selection(self):
        if not self.model_id:
            return []
        try:
            model = self.env[self.model_id.model]
            fields_list = []
            for field_name, field in model._fields.items():
                if hasattr(field, 'store') and field.store:
                    fields_list.append((field_name, f"{field_name} ({field.type})"))
            return fields_list
        except:
            return []
    
    @api.depends('model_id')
    def _compute_available_fields(self):
        for record in self:
            if record.model_id:
                model = self.env[record.model_id.model]
                fields_info = []
                for field_name, field in model._fields.items():
                    if hasattr(field, 'store') and field.store:
                        fields_info.append(f"{field_name} ({field.type})")
                record.available_fields = "\n".join(fields_info[:20])  # İlk 20 field
            else:
                record.available_fields = ""
    
    @api.depends('domain_filter', 'field_value_int')
    def _compute_name(self):
        for record in self:
            if record.domain_filter:
                record.name = f"{record.domain_filter} → {record.field_value_int}"
            else:
                record.name = _('Yeni Parametre')
    
    @api.model
    def get_workflow_parameter_value(self, model_name, record, model_field='default_duration_days'):
        """Kayda göre workflow parametresini döndür"""
        # Model ID'sini bul
        model = self.env['ir.model'].search([('model', '=', model_name)], limit=1)
        if not model:
            return None
            
        # Kaydın workflow'unu al
        record_workflow_id = getattr(record, 'workflow_definition_id', None)
        if not record_workflow_id:
            return None
            
        # Aktif parametreleri ara (workflow dahil)
        params = self.search([
            ('model_id', '=', model.id),
            ('field_name', '=', model_field),
            ('active', '=', True),
            '|',
            ('workflow_ids', '=', False),  # Tüm workflowlar için
            ('workflow_ids', 'in', [record_workflow_id.id])  # Belirli workflow için
        ])
        
        for param in params:
            try:
                # Domain'i değerlendir
                domain = eval(param.domain_filter)
                # Kaydın domain'e uyup uymadığını kontrol et
                if record.search([('id', '=', record.id)] + domain):
                    # Field tipine göre uygun değeri döndür
                    if param.field_value_int:
                        return param.field_value_int
                    elif param.field_value_str:
                        return param.field_value_str
                    elif param.field_value_float:
                        return param.field_value_float
                    elif param.field_value_bool is not False:
                        return param.field_value_bool
                    elif param.field_value_date:
                        return param.field_value_date
                    elif param.field_value_datetime:
                        return param.field_value_datetime
                    else:
                        return None
            except:
                continue
        
        return None