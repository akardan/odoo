# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class AkWorkflowTransition(models.Model):
    _name = 'ak.workflow.transition'
    _description = 'Workflow Transition Definition'
    _order = 'workflow_id, from_state_id, sequence'
    _rec_name = 'display_name'

    # Constants
    AUTO_TRANSITION_INDICATOR = '⚡'

    # Basic Info
    name = fields.Char('Transition Name', required=True, translate=True)
    code = fields.Char('Transition Code', help="Technical identifier")
    description = fields.Text('Description', translate=True)
    display_name = fields.Char(compute='_compute_display_name')
    
    # Workflow and States
    workflow_id = fields.Many2one(
        'ak.workflow.definition', 'Workflow',
        required=True, ondelete='cascade'
    )
    workflow_model_id = fields.Many2one(related='workflow_id.model_id', string="Workflow Model", store=True, readonly=True)
    from_state_id = fields.Many2one(
        'ak.workflow.state', 'From State',
        required=True, ondelete='cascade',
        domain="[('workflow_id', '=', workflow_id)]"
    )
    to_state_id = fields.Many2one(
        'ak.workflow.state', 'To State',
        required=True, ondelete='cascade',
        domain="[('workflow_id', '=', workflow_id)]"
    )
    
    # UI Configuration
    sequence = fields.Integer('Sequence', default=10)
    button_label = fields.Char('Button Label', translate=True,
                               help="Label shown on transition button")
    button_label_computed = fields.Char('Computed Button Label', compute='_compute_button_label_computed')
    button_class = fields.Selection([
        ('btn-primary', 'Primary (Blue)'),
        ('btn-success', 'Success (Green)'),
        ('btn-warning', 'Warning (Yellow)'),
        ('btn-danger', 'Danger (Red)'),
        ('btn-info', 'Info (Cyan)'),
        ('btn-secondary', 'Secondary (Gray)')
    ], string='Button Style', default='btn-primary')
    icon = fields.Char('Icon', help="FontAwesome icon class", default="fa-arrow-right")
    
    # Security and Authorization
    group_ids = fields.Many2many(
        'res.groups', 'transition_groups_rel',
        string='Required Groups',
        help="Groups required to execute this transition"
    )
    
    # Conditions
    condition_type = fields.Selection([
        ('none', 'No Condition'),
        ('python', 'Python Expression'),
        ('field', 'Field Condition'),
        ('method', 'Model Method'),
        ('amount', 'Amount Threshold'),
    ], string='Condition Type', default='none')
    
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
    
    amount_threshold = fields.Float('Amount Threshold')
    amount_currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    
    # Stages (Sub-transitions)
    stage_ids = fields.One2many(
        'ak.workflow.transition.stage',
        'transition_id',
        string='Transition Stages',
        help="Aşamalı onay için alt geçişler. Boş ise direkt geçiş yapılır."
    )
    stage_count = fields.Integer('Stage Count', compute='_compute_stage_count', store=True)
    has_stages = fields.Boolean('Has Stages', compute='_compute_stage_count', store=True)
    
    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for transition in self:
            transition.stage_count = len(transition.stage_ids)
            transition.has_stages = bool(transition.stage_ids)
    
    # Actions
    action_ids = fields.One2many('ak.workflow.action', 'transition_id',
                                 string='Transition Actions',
                                 help="Tüm aşamalar tamamlandıktan sonra çalışacak aksiyonlar")
    
    # Notifications
    send_notification = fields.Boolean('Send Notification', default=True)
    notification_template_id = fields.Many2one(
        'mail.template', 'Notification Template',
        domain="[('model_id', '=', workflow_model_id)]"
    )
    
    
    # Auto-transition on deadline
    auto_transition = fields.Boolean(
        'Auto-transition on Deadline',
        default=False,
        help="If enabled, this transition will be automatically executed when the workflow step deadline expires."
    )
    active = fields.Boolean('Active', default=True)
    
    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for transition in self:
            transition.stage_count = len(transition.stage_ids)
            transition.has_stages = bool(transition.stage_ids)
    
    def _compute_button_label_computed(self):
        """
        Dinamik button label hesapla - stage varsa stage label'ı göster
        """
        for transition in self:
            # Context'ten record bilgisini al
            record_id = self.env.context.get('record_id')
            model_name = self.env.context.get('model_name')
            
            if transition.has_stages and record_id and model_name:
                try:
                    record = self.env[model_name].browse(record_id)
                    next_stage = transition.get_next_pending_stage(record)
                    
                    if next_stage and next_stage.button_label:
                        transition.button_label_computed = next_stage.button_label
                    elif next_stage:
                        transition.button_label_computed = next_stage.name
                    else:
                        # Tüm stage'ler tamamlanmış
                        transition.button_label_computed = transition.button_label or transition.name
                except:
                    transition.button_label_computed = transition.button_label or transition.name
            else:
                transition.button_label_computed = transition.button_label or transition.name
    
    @api.depends('name', 'from_state_id.name', 'to_state_id.name', 'auto_transition')
    def _compute_display_name(self):
        """Compute display name with optional auto-transition indicator."""
        for transition in self:
            if transition.from_state_id and transition.to_state_id:
                base_name = transition.name or _('New')
                transition.display_name = (
                    f"{base_name} {self.AUTO_TRANSITION_INDICATOR}"
                    if transition.auto_transition
                    else base_name
                )
            else:
                transition.display_name = transition.name or _('New Transition')
    
    @api.constrains('from_state_id', 'to_state_id')
    def _check_states_same_workflow(self):
        for transition in self:
            if (transition.from_state_id.workflow_id != transition.workflow_id or
                transition.to_state_id.workflow_id != transition.workflow_id):
                raise ValidationError(_(
                    'All states in transition must belong to the same workflow'
                ))

    def check_transition_conditions(self, record):
        """
        Check if the transition conditions are met for the given record.
        """
        self.ensure_one()
        
        # If no condition is set, return True
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
                _logger.error(f"Field {field_name} not found on record {record}")
                return False
                
            field_value = getattr(record, field_name)
            _logger.info(f"Checking field condition: {field_name} {self.condition_operator} {self.condition_value}")
            _logger.info(f"Current field value: {field_value}")
            
            # Handle special operators
            if self.condition_operator == 'set':
                return bool(field_value)
            if self.condition_operator == 'not set':
                return not bool(field_value)
                
            # Convert condition value to appropriate type
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
                _logger.error(f"Error converting condition value {self.condition_value} to type {self.condition_field_id.ttype}")
                return False
                
            # Perform the comparison
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
            else:
                _logger.error(f"Method {self.condition_method} not found on record {record}")
                return False
                
        # Amount threshold condition
        if self.condition_type == 'amount':
            # Implement amount threshold logic here
            return True
            
        # Default fallback
        return True

    def _log_transition(self, record, old_state, status, comment=None):
        status_map = {'completed': '✅'}
        body = _(
            "<strong>%(icon)s Workflow Transition</strong><br/>"
            "From: <strong>%(from)s</strong> → To: <strong>%(to)s</strong><br/>"
            "Transition: %(trans)s"
        ) % {
            'icon': status_map.get(status, ''),
            'from': old_state.name,
            'to': self.to_state_id.name,
            'trans': self.name
        }
        if comment:
            body += _("<br/>Comment: %s") % comment
        record.message_post(body=body)

    def get_next_pending_stage(self, record):
        """
        Kayıt için bir sonraki bekleyen stage'i döndür
        """
        self.ensure_one()
        
        if not self.has_stages:
            return False
        
        # Eğer mevcut stage yoksa VEYA başka bir transition'a aitse, ilk stage'i döndür
        if not record.workflow_current_stage_id or record.workflow_current_stage_id.transition_id != self:
            first_stage = self.stage_ids.sorted('sequence')[:1]
            if record.workflow_current_stage_id:
                _logger.info(f"   Current stage belongs to different transition, returning first: {first_stage.name if first_stage else 'None'}")
            else:
                _logger.info(f"   No current stage, returning first: {first_stage.name if first_stage else 'None'}")
            return first_stage
        
        # Mevcut stage'den sonraki stage'i bul
        current_sequence = record.workflow_current_stage_id.sequence
        next_stage = self.stage_ids.filtered(lambda s: s.sequence > current_sequence).sorted('sequence')[:1]
        
        _logger.info(f"   Current stage: {record.workflow_current_stage_id.name}, Next: {next_stage.name if next_stage else 'None (all completed)'}")
        
        return next_stage if next_stage else False
    
    def are_all_stages_completed(self, record):
        """
        Tüm stage'ler tamamlandı mı kontrol et
        """
        self.ensure_one()
        
        if not self.has_stages:
            return True
        
        # SADECE MEVCUT STATE'DEKİ TAMAMLANMIŞ STAGE'LER
        completed_stage_ids = self.env['ak.workflow.transition.history'].search([
            ('res_model', '=', record._name),
            ('res_id', '=', record.id),
            ('transition_id', '=', self.id),
            ('from_state_id', '=', record.workflow_current_state_id.id),  # Mevcut state
            ('status', '=', 'completed'),
            ('stage_id', '!=', False)
        ]).mapped('stage_id').ids
        
        # Unique stage ID'lerini al
        unique_completed_stages = set(completed_stage_ids)
        required_stage_ids = set(self.stage_ids.ids)
        
        _logger.info(f"   Completed stages: {unique_completed_stages}, Required: {required_stage_ids}")
        
        # Tüm gerekli stage'ler tamamlandı mı?
        return required_stage_ids.issubset(unique_completed_stages)
    
    def execute_on_record(self):
        self.ensure_one()
        record_id = self.env.context.get('active_id')
        model_name = self.env.context.get('active_model')
        if not record_id or not model_name:
            raise UserError(_("Could not find the record to execute the transition on."))
        
        record = self.env[model_name].browse(record_id)
        record.ensure_one()
        
        # Check if the transition is available
        if self not in record.workflow_available_transition_ids:
            # Check if it's because of a condition failure
            if not self.check_transition_conditions(record):
                # Show specific error message based on condition type
                if self.condition_type == 'field' and self.condition_field_id:
                    field_name = self.condition_field_id.name
                    field_label = self.condition_field_id.field_description
                    field_value = getattr(record, field_name, None)
                    
                    raise UserError(_(
                        "Geçiş koşulu karşılanmadı: '%s' alanı koşulu sağlamıyor.\n"
                        "Mevcut değer: %s\n"
                        "Beklenen koşul: %s %s"
                    ) % (field_label, field_value, self.condition_operator, self.condition_value))
                else:
                    raise UserError(_("Bu geçiş için gerekli koşullar sağlanmıyor."))
            else:
                raise UserError(_("Bu geçiş mevcut durum veya kullanıcı için uygun değil."))

        comment = self.env.context.get('comment')
        old_state = record.workflow_current_state_id
        
        # Eğer stage'ler varsa, stage bazlı işlem yap
        _logger.info(f"🔍 Checking stages for transition {self.name}: has_stages={self.has_stages}, stage_count={self.stage_count}")
        _logger.info(f"   Stage IDs: {self.stage_ids.ids}")
        _logger.info(f"   Current state: {record.workflow_current_state_id.name}")
        
        if self.has_stages:
            _logger.info(f"   ✓ Transition {self.name} has {len(self.stage_ids)} stages")
            next_stage = self.get_next_pending_stage(record)
            _logger.info(f"   Next pending stage: {next_stage.name if next_stage else 'None (all completed)'}")
            
            if next_stage:
                _logger.info(f"   ⚡ Executing stage: {next_stage.name} (sequence: {next_stage.sequence})")
                
                # Mevcut stage'i ÖNCE güncelle (execute'dan önce) ve veritabanına yaz
                record.write({'workflow_current_stage_id': next_stage.id})
                _logger.info(f"   Updated workflow_current_stage_id to: {next_stage.name}")
                
                # Stage'i çalıştır
                next_stage.execute_stage(record, comment)
                
                # Bir sonraki stage var mı kontrol et
                next_next_stage = self.get_next_pending_stage(record)
                
                if not next_next_stage:
                    # Tüm stage'ler tamamlandı, state değiştir
                    _logger.info(f"   🎉 All stages completed! Changing state from '{old_state.name}' to '{self.to_state_id.name}'")
                    record.write({
                        'workflow_current_state_id': self.to_state_id.id,
                        'workflow_current_stage_id': False
                    })
                    
                    # Chatter'a mesaj at
                    body = _(
                        "<strong>✅ Tüm Aşamalar Tamamlandı - State Değişti</strong><br/>"
                        "From: <strong>%(from)s</strong> → To: <strong>%(to)s</strong>"
                    ) % {
                        'from': old_state.name,
                        'to': self.to_state_id.name
                    }
                    record.message_post(body=body)
                    
                    # Entry actions for new state
                    record._execute_state_actions('entry')
                    
                    # Ana transition aksiyonlarını çalıştır (sadece stage'e bağlı olmayanlar)
                    for action in self.action_ids:
                        if not action.stage_id:
                            action.execute_action(record)
                    
                    _logger.info(f"   ✅ Transition completed successfully")
                else:
                    # Henüz tamamlanmamış stage'ler var
                    _logger.info(f"   ⏸️  Stage completed, next stage: {next_next_stage.name}")
                    
                    body = _(
                        "<strong>⏳ Aşama Tamamlandı - Sonraki Aşama Bekleniyor</strong><br/>"
                        "Tamamlanan Aşama: <strong>%(stage)s</strong><br/>"
                        "Sonraki Aşama: <strong>%(next)s</strong>"
                    ) % {
                        'stage': next_stage.name,
                        'next': next_next_stage.name
                    }
                    record.message_post(body=body)
            else:
                _logger.warning(f"   ⚠️  No next stage found!")
                raise UserError(_("Tüm aşamalar zaten tamamlanmış."))
        else:
            # Stage yoksa direkt geçiş yap
            _logger.info(f"   ℹ️  No stages defined, proceeding directly to state change")
            _logger.info(f"   🔄 Changing state from '{old_state.name}' to '{self.to_state_id.name}'")
            record.workflow_current_state_id = self.to_state_id
            
            # History kaydı oluştur (mixin'deki metodu kullan)
            record._log_transition(self, old_state, 'completed', comment)
            
            # Entry actions for new state
            record._execute_state_actions('entry')
            
            # Execute all transition actions
            for action in self.action_ids:
                action.execute_action(record)
            
            _logger.info(f"   ✅ Transition completed successfully")
        
        return True