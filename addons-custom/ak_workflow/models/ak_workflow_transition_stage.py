# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AkWorkflowTransitionStage(models.Model):
    _name = 'ak.workflow.transition.stage'
    _description = 'Workflow Transition Stage (Sub-Transition)'
    _order = 'transition_id, sequence, id'
    _rec_name = 'display_name'

    # Basic Info
    name = fields.Char('Stage Name', required=True, translate=True,
                      help="Örn: Review, İlk Onay, Son Onay, vb.")
    code = fields.Char('Stage Code', help="Technical identifier")
    description = fields.Text('Description', translate=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    
    # Transition Reference
    transition_id = fields.Many2one(
        'ak.workflow.transition', 
        'Parent Transition',
        required=True, 
        ondelete='cascade',
        help="Ana geçiş tanımı"
    )
    
    # Sequence
    sequence = fields.Integer('Sequence', default=10, 
                             help="Aşamaların sırası (küçükten büyüğe)")
    
    # Security and Authorization (Ana transition'dan bağımsız)
    group_ids = fields.Many2many(
        'res.groups', 
        'transition_stage_groups_rel',
        'stage_id', 
        'group_id',
        string='Required Groups',
        help="Bu aşamayı gerçekleştirebilecek gruplar"
    )
    
    # Conditions (Ana transition'dan bağımsız koşullar)
    condition_type = fields.Selection([
        ('none', 'No Condition'),
        ('python', 'Python Expression'),
        ('field', 'Field Condition'),
        ('method', 'Model Method'),
    ], string='Condition Type', default='none',
       help="Bu aşama için özel koşul")
    
    condition_expression = fields.Text('Python Expression',
                                       help="Python expression that must return True")
    condition_field_id = fields.Many2one(
        'ir.model.fields', 'Field',
        domain="[('model_id', '=', workflow_model_id)]"
    )
    condition_operator = fields.Selection([
        ('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<='),
        ('in', 'in'), ('not in', 'not in'), ('set', 'is set'), ('not set', 'is not set')
    ], string='Operator', default='=')
    condition_value = fields.Text('Value')
    condition_method = fields.Char('Method Name')
    
    # Related fields for domain
    workflow_model_id = fields.Many2one(
        related='transition_id.workflow_model_id',
        string='Workflow Model',
        store=True,
        readonly=True
    )
    
    # UI Configuration
    button_label = fields.Char('Button Label', translate=True,
                               help="Bu aşama için buton etiketi")
    button_class = fields.Selection([
        ('btn-primary', 'Primary (Blue)'),
        ('btn-success', 'Success (Green)'),
        ('btn-warning', 'Warning (Yellow)'),
        ('btn-danger', 'Danger (Red)'),
        ('btn-info', 'Info (Cyan)'),
        ('btn-secondary', 'Secondary (Gray)')
    ], string='Button Style', default='btn-primary')
    icon = fields.Char('Icon', help="FontAwesome icon class", default="fa-check")
    
    # Notifications
    send_notification = fields.Boolean('Send Notification', default=True)
    notification_template_id = fields.Many2one(
        'mail.template',
        'Notification Template',
        domain="[('model_id', '=', workflow_model_id)]",
        help="Bu aşama tamamlandığında gönderilecek bildirim"
    )
    
    # Actions (Bu aşama tamamlandığında çalışacak aksiyonlar)
    action_ids = fields.One2many(
        'ak.workflow.action', 
        'stage_id',
        string='Stage Actions',
        help="Bu aşama tamamlandığında çalışacak aksiyonlar"
    )
    
    # Stage Status
    active = fields.Boolean('Active', default=True)
    
    @api.depends('name', 'sequence')
    def _compute_display_name(self):
        for stage in self:
            if stage.name:
                stage.display_name = f"{stage.sequence}. {stage.name}"
            else:
                stage.display_name = 'New Stage'
    
    def check_stage_conditions(self, record):
        """
        Bu aşamanın koşullarını kontrol et
        """
        self.ensure_one()
        
        if self.condition_type == 'none':
            return True
            
        # Python expression condition
        if self.condition_type == 'python' and self.condition_expression:
            try:
                eval_context = {'record': record, 'env': self.env, 'user': self.env.user}
                result = eval(self.condition_expression, eval_context)
                return bool(result)
            except Exception as e:
                _logger.error(f"Error evaluating Python expression: {str(e)}")
                return False
                
        # Field condition
        if self.condition_type == 'field' and self.condition_field_id:
            field_name = self.condition_field_id.name
            if not hasattr(record, field_name):
                return False
                
            field_value = getattr(record, field_name)
            
            if self.condition_operator == 'set':
                return bool(field_value)
            if self.condition_operator == 'not set':
                return not bool(field_value)
                
            try:
                if self.condition_field_id.ttype in ('float', 'monetary'):
                    condition_value = float(self.condition_value)
                elif self.condition_field_id.ttype == 'integer':
                    condition_value = int(self.condition_value)
                elif self.condition_field_id.ttype == 'boolean':
                    condition_value = self.condition_value.lower() in ('true', '1', 'yes')
                else:
                    condition_value = self.condition_value
            except (ValueError, TypeError):
                return False
                
            if self.condition_operator == '=':
                return field_value == condition_value
            elif self.condition_operator == '!=':
                return field_value != condition_value
            elif self.condition_operator == '>':
                return field_value > condition_value
            elif self.condition_operator == '>=':
                return field_value >= condition_value
            elif self.condition_operator == '<':
                return field_value < condition_value
            elif self.condition_operator == '<=':
                return field_value <= condition_value
            elif self.condition_operator == 'in':
                values = [v.strip() for v in condition_value.split(',')]
                return field_value in values
            elif self.condition_operator == 'not in':
                values = [v.strip() for v in condition_value.split(',')]
                return field_value not in values
                
        # Method condition
        if self.condition_type == 'method' and self.condition_method:
            if hasattr(record, self.condition_method):
                try:
                    return bool(getattr(record, self.condition_method)())
                except Exception as e:
                    _logger.error(f"Error calling method {self.condition_method}: {str(e)}")
                    return False
                    
        return True
    
    def can_execute(self, record, user=None):
        """
        Kullanıcının bu aşamayı gerçekleştirebilip gerçekleştiremeyeceğini kontrol et
        """
        self.ensure_one()
        if user is None:
            user = self.env.user
        
        # Grup kontrolü
        if self.group_ids and not any(group in user.groups_id for group in self.group_ids):
            return False
        
        # Koşul kontrolü
        if not self.check_stage_conditions(record):
            return False
            
        return True
    
    def execute_stage(self, record, comment=None):
        """
        Bu aşamayı gerçekleştir
        """
        self.ensure_one()
        
        # Kullanıcı yetkisi kontrolü
        if not self.can_execute(record):
            raise ValidationError(_("Bu aşamayı gerçekleştirmek için yetkiniz yok."))
        
        # History kaydı oluştur (sudo ile, çünkü normal kullanıcıların create yetkisi yok)
        self.env['ak.workflow.transition.history'].sudo().create({
            'res_model': record._name,
            'res_id': record.id,
            'from_state_id': self.transition_id.from_state_id.id,
            'to_state_id': self.transition_id.to_state_id.id,  # Hedef state (sonraki state)
            'transition_id': self.transition_id.id,
            'stage_id': self.id,
            'user_id': self.env.user.id,
            'status': 'completed',
            'comment': comment,
        })
        
        # Log mesajı
        body = _(
            "<strong>✅ Aşama Tamamlandı</strong><br/>"
            "Aşama: <strong>%(stage)s</strong><br/>"
            "Geçiş: %(trans)s"
        ) % {
            'stage': self.name,
            'trans': self.transition_id.name
        }
        if comment:
            body += _("<br/>Yorum: %s") % comment
        record.message_post(body=body)
        
        # Aksiyonları çalıştır
        for action in self.action_ids:
            action.execute_action(record)
        
        return True