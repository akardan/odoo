# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TenderTypeMaterialGroup(models.Model):
    """SAP Malzeme Grubu Tanımları"""
    _name = 'tender.type.material.group'
    _description = 'Tender Type Material Group'
    _order = 'code'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Material Group Code', required=True, help='SAP Material Group Code (e.g., 1000, 2000, 6000)')
    code_prefix = fields.Char(string='Code Prefix', compute='_compute_code_prefix', store=True, 
                              help='First digit of material group code')
    description = fields.Text(string='Description', translate=True)
    default_tender_type = fields.Selection([
        ('direct', 'Direct'),
        ('indirect', 'Indirect'),
        ('promotion', 'Promotion'),
        ('mice', 'MICE'),
    ], string='Default Tender Type', required=True)
    responsible_user_ids = fields.Many2many('res.users', string='Responsible Users',
                                           help='Users responsible for this material group')
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Material Group Code must be unique!')
    ]

    @api.depends('code')
    def _compute_code_prefix(self):
        for record in self:
            record.code_prefix = record.code[0] if record.code else ''

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result


class TenderTypePurchasingGroup(models.Model):
    """SAP Satınalma Grubu Tanımları"""
    _name = 'tender.type.purchasing.group'
    _description = 'Tender Type Purchasing Group'
    _order = 'code'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Purchasing Group Code', required=True, help='SAP Purchasing Group Code (e.g., 105, 110, 600)')
    description = fields.Text(string='Description', translate=True)
    tender_type = fields.Selection([
        ('direct', 'Direct'),
        ('indirect', 'Indirect'),
        ('promotion', 'Promotion'),
        ('mice', 'MICE'),
    ], string='Tender Type', required=True)
    responsible_user_ids = fields.Many2many('res.users', string='Responsible Users',
                                           help='Users responsible for this purchasing group')
    responsible_names = fields.Char(string='Responsible Names', 
                                   help='Names of responsible persons (e.g., Gülcan/Eda/Peri)')
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Purchasing Group Code must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result


class TenderTypeSpecialRule(models.Model):
    """Özel Kurallar (6XXX, 9XXX gibi istisnalar için)"""
    _name = 'tender.type.special.rule'
    _description = 'Tender Type Special Rule'
    _order = 'sequence, id'

    name = fields.Char(string='Rule Name', required=True, translate=True)
    sequence = fields.Integer(string='Priority', default=10, 
                             help='Lower number = higher priority. Special rules are checked first.')
    active = fields.Boolean(string='Active', default=True)
    
    # Koşullar
    material_group_prefix = fields.Char(string='Material Group Prefix', 
                                       help='Material group starts with (e.g., 6, 9)')
    purchasing_group_code = fields.Char(string='Purchasing Group Code',
                                       help='Specific purchasing group code (e.g., 110)')
    
    # Sonuç
    tender_type = fields.Selection([
        ('direct', 'Direct'),
        ('indirect', 'Indirect'),
        ('promotion', 'Promotion'),
        ('mice', 'MICE'),
    ], string='Tender Type', required=True)
    responsible_user_ids = fields.Many2many('res.users', string='Responsible Users',
                                           help='Users responsible for this special rule')
    responsible_names = fields.Char(string='Responsible Names')
    notes = fields.Text(string='Notes', translate=True)
    
    @api.constrains('material_group_prefix', 'purchasing_group_code')
    def _check_conditions(self):
        for record in self:
            if not record.material_group_prefix and not record.purchasing_group_code:
                raise ValidationError(_('At least one condition (Material Group Prefix or Purchasing Group Code) must be specified!'))


class TenderTypeProductionLocation(models.Model):
    """Üretim Yeri Tanımları"""
    _name = 'tender.type.production.location'
    _description = 'Tender Type Production Location'
    _order = 'code'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Location Code', required=True, help='SAP Production Location Code (e.g., 2100, 2000)')
    description = fields.Text(string='Description', translate=True)
    default_tender_type = fields.Selection([
        ('direct', 'Direct'),
        ('indirect', 'Indirect'),
        ('promotion', 'Promotion'),
        ('mice', 'MICE'),
    ], string='Default Tender Type', required=True)
    responsible_user_ids = fields.Many2many('res.users', string='Responsible Users',
                                           help='Users responsible for this production location')
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Production Location Code must be unique!')
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result


class TenderTypeMatrix(models.Model):
    """
    Tender Type Belirleme Matrisi
    Bu model, tüm kuralları birleştirerek tender type'ı belirler
    """
    _name = 'tender.type.matrix'
    _description = 'Tender Type Determination Matrix'

    name = fields.Char(string='Matrix Name', default='Tender Type Matrix', readonly=True)
    
    # İlişkiler
    material_group_ids = fields.One2many('tender.type.material.group', compute='_compute_relations')
    purchasing_group_ids = fields.One2many('tender.type.purchasing.group', compute='_compute_relations')
    special_rule_ids = fields.One2many('tender.type.special.rule', compute='_compute_relations')
    production_location_ids = fields.One2many('tender.type.production.location', compute='_compute_relations')
    
    def _compute_relations(self):
        """Tüm ilişkili kayıtları göster"""
        for record in self:
            record.material_group_ids = self.env['tender.type.material.group'].search([])
            record.purchasing_group_ids = self.env['tender.type.purchasing.group'].search([])
            record.special_rule_ids = self.env['tender.type.special.rule'].search([])
            record.production_location_ids = self.env['tender.type.production.location'].search([])

    @api.model
    def determine_tender_type(self, material_group=None, purchasing_group=None, production_location=None):
        """
        SAP verilerinden ihale tipini belirle
        
        ÖNCELİK SIRASI:
        1. ÖZEL KURALLAR (6XXX ve 9XXX için)
        2. Satınalma Grubu
        3. Malzeme Grubu  
        4. Üretim Yeri
        5. Varsayılan (indirect)
        
        Args:
            material_group: SAP Malzeme Grubu (ör: '6000-03', '9000-01')
            purchasing_group: SAP Satınalma Grubu (ör: '105', '110')
            production_location: Üretim Yeri (ör: '2100', '2000')
        
        Returns:
            dict: {
                'tender_type': str,
                'responsible': str,
                'responsible_user_ids': recordset,
                'decision_source': str,
                'notes': list
            }
        """
        result = {
            'tender_type': None,
            'responsible_user_ids': self.env['res.users'],
            'decision_source': None,
            'notes': []
        }
        
        # Normalize inputs
        mg = str(material_group).strip() if material_group else ''
        mg_prefix = mg[0] if mg and len(mg) > 0 else ''
        pg = str(purchasing_group).strip() if purchasing_group else ''
        pl = str(production_location).strip() if production_location else ''
        
        # ========================================================================
        # 1. ÖZEL KURALLAR (En yüksek öncelik)
        # ========================================================================
        special_rules = self.env['tender.type.special.rule'].search([
            ('active', '=', True)
        ], order='sequence, id')
        
        for rule in special_rules:
            # Koşulları kontrol et
            mg_match = not rule.material_group_prefix or (mg_prefix and mg_prefix == rule.material_group_prefix)
            pg_match = not rule.purchasing_group_code or (pg and pg == rule.purchasing_group_code)
            
            # Her iki koşul da sağlanıyorsa kural uygulanır
            if rule.material_group_prefix and rule.purchasing_group_code:
                # İki koşul da var, ikisi de eşleşmeli (1. öncelik)
                if mg_match and pg_match:
                    result['tender_type'] = rule.tender_type
                    result['responsible_user_ids'] = rule.responsible_user_ids
                    result['decision_source'] = f'special_rule_{rule.id}'
                    result['notes'].append(f'Special Rule: {rule.name}')
                    if rule.notes:
                        result['notes'].append(rule.notes)
                    return result
            elif rule.purchasing_group_code:
                # Sadece satınalma grubu koşulu var (2. öncelik)
                if pg_match:
                    result['tender_type'] = rule.tender_type
                    result['responsible_user_ids'] = rule.responsible_user_ids
                    result['decision_source'] = f'special_rule_{rule.id}'
                    result['notes'].append(f'Special Rule: {rule.name}')
                    if rule.notes:
                        result['notes'].append(rule.notes)
                    return result
            elif rule.material_group_prefix:
                # Sadece malzeme grubu koşulu var (3. öncelik)
                if mg_match:
                    result['tender_type'] = rule.tender_type
                    result['responsible_user_ids'] = rule.responsible_user_ids
                    result['decision_source'] = f'special_rule_{rule.id}'
                    result['notes'].append(f'Special Rule: {rule.name}')
                    if rule.notes:
                        result['notes'].append(rule.notes)
                    return result
        
        # ========================================================================
        # 2. SATINALMA GRUBUNA GÖRE BELİRLE
        # ========================================================================
        if pg:
            pg_record = self.env['tender.type.purchasing.group'].search([
                ('code', '=', pg),
                ('active', '=', True)
            ], limit=1)
            
            if pg_record:
                result['tender_type'] = pg_record.tender_type
                result['responsible_user_ids'] = pg_record.responsible_user_ids
                result['decision_source'] = 'purchasing_group'
                result['notes'].append(f'Purchasing Group: {pg_record.name}')
                return result
        
        # ========================================================================
        # 3. MALZEME GRUBUNA GÖRE BELİRLE
        # ========================================================================
        if mg_prefix:
            # Önce tam kod ile ara
            mg_record = self.env['tender.type.material.group'].search([
                ('code', '=', mg),
                ('active', '=', True)
            ], limit=1)
            
            # Bulunamazsa prefix ile ara
            if not mg_record:
                mg_record = self.env['tender.type.material.group'].search([
                    ('code_prefix', '=', mg_prefix),
                    ('active', '=', True)
                ], limit=1)
            
            if mg_record:
                result['tender_type'] = mg_record.default_tender_type
                result['responsible_user_ids'] = mg_record.responsible_user_ids
                result['decision_source'] = 'material_group'
                result['notes'].append(f'Material Group: {mg_record.name}')
                return result
        
        # ========================================================================
        # 4. ÜRETİM YERİNE GÖRE BELİRLE
        # ========================================================================
        if pl:
            pl_record = self.env['tender.type.production.location'].search([
                ('code', '=', pl),
                ('active', '=', True)
            ], limit=1)
            
            if pl_record:
                result['tender_type'] = pl_record.default_tender_type
                result['responsible_user_ids'] = pl_record.responsible_user_ids
                result['decision_source'] = 'production_location'
                result['notes'].append(f'Production Location: {pl_record.name}')
                return result
        
        # ========================================================================
        # 5. VARSAYILAN
        # ========================================================================
        result['tender_type'] = 'indirect'
        result['decision_source'] = 'default'
        result['notes'].append('Default value used')
        
        return result