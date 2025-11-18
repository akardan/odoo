# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseRequisition(models.Model):
    """
    SAT Havuzu - SAP'den gelen satınalma taleplerini toplar
    Her SAT numarası bir purchase.requisition kaydı olur
    Kalemler purchase.requisition.line'da tutulur
    """
    _inherit = 'purchase.requisition'
    
    # SAP Entegrasyon Alanları (Header seviyesi)
    erp_pr_id = fields.Char(
        string='SAT No',
        copy=False,
        index=True,
        help="SAP Satınalma Talebi Numarası"
    )
    
    # İşleme Durumu (Header seviyesi)
    processing_status = fields.Selection([
        ('N', 'İşlenmedi'),
        ('T', 'İhaleye Alındı'),
        ('C', 'Tamamlandı'),
    ], string='İşleme Durumu', default='N', copy=False,
       help="SAT'ın genel işleme durumu")
    
    # İstatistikler
    total_lines = fields.Integer(
        string='Toplam Kalem',
        compute='_compute_line_stats',
        store=True
    )
    processed_lines = fields.Integer(
        string='İşlenen Kalem',
        compute='_compute_line_stats',
        store=True
    )
    
    preview_groups = fields.Text(
        string='Grup Önizleme',
        compute='_compute_preview_groups',
        help="Oluşturulacak ihale gruplarının önizlemesi"
    )
    
    @api.depends('line_ids', 'line_ids.line_processing_status')
    def _compute_line_stats(self):
        """Kalem istatistiklerini hesapla"""
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.processed_lines = len(rec.line_ids.filtered(
                lambda l: l.line_processing_status in ('T', 'B', 'K')
            ))
    
    @api.depends('line_ids', 'line_ids.line_processing_status', 'line_ids.material_group', 'line_ids.purchasing_group', 'line_ids.erp_company_code')
    def _compute_preview_groups(self):
        """İhale gruplarının önizlemesini hesapla"""
        for rec in self:
            # Sadece işlenmemiş kalemleri al
            unprocessed_lines = rec.line_ids.filtered(
                lambda l: l.line_processing_status == 'N' and not l.deletion_indicator
            )
            
            if not unprocessed_lines:
                rec.preview_groups = "İşlenebilir kalem yok"
                continue
            
            # Kalemleri grupla
            groups = unprocessed_lines.group_lines_for_tender(unprocessed_lines)
            
            if not groups:
                rec.preview_groups = "Grup oluşturulamadı"
                continue
            
            # İhale tipi etiketleri
            type_labels = {
                'direct': 'Direkt',
                'indirect': 'Endirekt',
                'promotion': 'Promosyon',
                'mice': 'MICE'
            }
            
            # Önizleme metni oluştur
            preview = f"{len(groups)} ihale oluşturulacak:\n\n"
            for idx, (key, group_data) in enumerate(groups.items(), 1):
                tender_type = group_data['tender_type']
                preview += f"İhale {idx}:\n"
                preview += f"  - Tip: {type_labels.get(tender_type, tender_type)}\n"
                preview += f"  - Mal Grubu: {group_data['material_group'] or 'Yok'}\n"
                preview += f"  - Satınalma Grubu: {group_data['purchasing_group'] or 'Yok'}\n"
                preview += f"  - Şirket: {group_data['company_code'] or 'Yok'}\n"
                if group_data.get('responsible'):
                    preview += f"  - Sorumlu: {group_data['responsible']}\n"
                preview += f"  - Kalem Sayısı: {len(group_data['line_ids'])}\n\n"
            
            rec.preview_groups = preview
    
    def action_create_tenders_from_lines(self):
        """Seçili SAT kalemlerinden ihaleler oluştur"""
        if not self:
            raise UserError(_('Lütfen en az bir SAT seçin.'))
        
        # Tüm kalemleri topla
        all_lines = self.mapped('line_ids')
        
        # İşlenebilir kalemleri filtrele
        valid_lines = all_lines.filtered(lambda l: 
            l.line_processing_status == 'N' and 
            not l.deletion_indicator
        )
        
        if not valid_lines:
            raise UserError(_('İşlenebilir kalem bulunamadı.'))
        
        # İhale oluşturma wizard'ını aç
        return {
            'name': _('İhale Oluştur'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.create.from.requisition.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_requisition_line_ids': [(6, 0, valid_lines.ids)],
            }
        }


class PurchaseRequisitionLine(models.Model):
    """
    SAT Kalemi - Her SAP SAT kalemi bir purchase.requisition.line kaydı olur
    Tüm SAP bilgileri burada tutulur
    """
    _inherit = 'purchase.requisition.line'
    
    # SAP Kalem Bilgileri
    erp_pr_id = fields.Char(
        string='SAT No',
        related='requisition_id.erp_pr_id',
        store=True,
        index=True
    )
    erp_pr_item = fields.Char(
        string='SAT Kalemi',
        copy=False,
        index=True,
        help="SAP Satınalma Talebi Kalem Numarası"
    )
    
    # İşleme Durumu (Kalem seviyesi)
    line_processing_status = fields.Selection([
        ('N', 'İşlenmedi'),
        ('B', 'SAS Oluşturuldu'),
        ('K', 'Sözleşme Oluşturuldu'),
        ('T', 'İhaleye Alındı'),
    ], string='Kalem İşleme Durumu', default='N', copy=False, index=True)
    
    deletion_indicator = fields.Boolean(
        string='Silme Göstergesi',
        default=False,
        help="SAP'ta silinmiş olarak işaretlenmiş"
    )
    
    # SAP Detay Alanları
    item_type = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Sınır'),
        ('2', 'Konsinye'),
        ('3', 'Fason Üretim'),
    ], string='Kalem Tipi')
    
    account_assignment_type = fields.Selection([
        ('K', 'Masraf Yeri'),
        ('A', 'Duran Varlıklar'),
        ('C', 'Müşteri Siparişi'),
        ('F', 'Sipariş'),
    ], string='Hesap Tayini Tipi')
    
    material_code = fields.Char(
        string='Malzeme Kodu',
        help="SAP Malzeme Kodu",
        index=True
    )
    
    material_group = fields.Char(
        string='Mal Grubu',
        help="SAP Mal Grubu - İhale tipi belirleme için kullanılır",
        index=True
    )
    
    purchasing_group = fields.Char(
        string='Satınalma Grubu',
        help="SAP Satınalma Grubu",
        index=True
    )
    
    erp_company_code = fields.Char(
        string='Şirket Kodu',
        help="SAP Şirket Kodu (2100: İlko, 2000: Merkez, 1100: İlkopol)",
        index=True
    )
    
    erp_plant_code = fields.Char(
        string='Tesis Kodu',
        help="SAP Tesis/Depo Kodu"
    )
    
    erp_requester = fields.Char(
        string='Talep Eden',
        help="SAP'ta SAT'ı açan kullanıcı"
    )
    
    request_date = fields.Date(
        string='Talep Tarihi',
        help="SAT'ın SAP'ta oluşturulma tarihi"
    )
    
    required_delivery_date = fields.Date(
        string='Gerekli Teslim Tarihi',
        help="SAP'ta belirtilen teslim tarihi"
    )
    
    # Aciliyet
    is_urgent = fields.Boolean(
        string='Acil',
        default=False,
        help="Acil talep"
    )
    
    # Ek SAP Bilgileri
    requirement_number = fields.Char(
        string='İhtiyaç Numarası',
        help="SAP İhtiyaç Numarası"
    )
    
    framework_agreement = fields.Char(
        string='Çerçeve Sözleşme',
        help="SAP Çerçeve Sözleşme Numarası"
    )
    
    purchasing_info_record = fields.Char(
        string='SA Bilgi Kaydı',
        help="SAP Satınalma Bilgi Kaydı"
    )
    
    manufacturer_part_number = fields.Char(
        string='Üretici Parça No',
        help="Üretici Parça Numarası"
    )
    
    approval_indicator = fields.Selection([
        ('X', 'Onay Bekliyor'),
        ('Z', 'Onay Tamamlandı'),
        ('2', 'Onaylandı (SAP)'),
    ], string='Onay Göstergesi')
    
    delivery_date_type = fields.Char(
        string='Teslimat Tarihi Tipi',
        help="SAP Teslimat Tarihi Tipi"
    )
    
    delivering_production_location = fields.Char(
        string='Teslimatı Yapan ÜY',
        help="Teslimatı yapan üretim yeri"
    )
    
    purchasing_organization = fields.Char(
        string='SA Organizasyonu',
        help="Satınalma Organizasyonu"
    )
    
    # İhale İlişkisi
    tender_line_id = fields.Many2one(
        'ak.tender.line',
        string='İhale Kalemi',
        ondelete='set null',
        help="Bu SAT kaleminden oluşturulan ihale kalemi"
    )
    
    tender_id = fields.Many2one(
        'ak.tender',
        string='İhale',
        related='tender_line_id.tender_id',
        store=True,
        help="Bu SAT kaleminin dahil olduğu ihale"
    )
    
    # Computed Fields
    can_create_tender = fields.Boolean(
        string='İhale Oluşturulabilir',
        compute='_compute_can_create_tender',
        store=True
    )
    
    tender_group_info = fields.Char(
        string='İhale Grubu',
        compute='_compute_tender_group_info',
        store=True,
        help="Bu kalemin dahil olacağı ihale grubu bilgisi"
    )
    
    @api.depends('line_processing_status', 'tender_line_id', 'deletion_indicator')
    def _compute_can_create_tender(self):
        """İhale oluşturulabilir mi kontrol et"""
        for rec in self:
            rec.can_create_tender = (
                rec.line_processing_status == 'N' and
                not rec.tender_line_id and
                not rec.deletion_indicator
            )
    
    @api.depends('material_group', 'purchasing_group', 'erp_company_code', 'erp_plant_code', 'line_processing_status', 'deletion_indicator')
    def _compute_tender_group_info(self):
        """İhale grup bilgisini hesapla"""
        for rec in self:
            if rec.line_processing_status != 'N' or rec.deletion_indicator:
                rec.tender_group_info = 'İşlenmiş/Silinmiş'
                continue
            
            # İhale tipi kurallarına göre belirle
            matrix = self.env['tender.type.matrix']
            tender_info = matrix.determine_tender_type(
                material_group=rec.material_group,
                purchasing_group=rec.purchasing_group,
                production_location=rec.erp_plant_code
            )
            
            tender_type = tender_info.get('tender_type', 'indirect')
            
            # Grup bilgisini oluştur
            parts = []
            if tender_type:
                type_labels = {
                    'direct': 'Direkt',
                    'indirect': 'Endirekt',
                    'promotion': 'Promosyon',
                    'mice': 'MICE'
                }
                parts.append(f"Tip: {type_labels.get(tender_type, tender_type)}")
            if rec.material_group:
                parts.append(f"MG: {rec.material_group}")
            if rec.purchasing_group:
                parts.append(f"SG: {rec.purchasing_group}")
            if rec.erp_company_code:
                parts.append(f"Şirket: {rec.erp_company_code}")
            
            rec.tender_group_info = ' | '.join(parts) if parts else 'Grup belirlenemedi'
    
    def action_create_tender(self):
        """Seçili SAT kalemlerinden ihale oluştur"""
        if not self:
            raise UserError(_('Lütfen en az bir SAT kalemi seçin.'))
        
        # İşlenebilir kalemleri filtrele
        valid_lines = self.filtered(lambda l: l.can_create_tender)
        
        if not valid_lines:
            raise UserError(_('Seçili kalemler zaten işlenmiş veya silinmiş.'))
        
        # İhale oluşturma wizard'ını aç
        return {
            'name': _('İhale Oluştur'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.create.from.requisition.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_requisition_line_ids': [(6, 0, valid_lines.ids)],
            }
        }
    
    def action_view_tender(self):
        """İlişkili ihaleyi görüntüle"""
        self.ensure_one()
        if not self.tender_id:
            raise UserError(_('Bu SAT kalemi için henüz ihale oluşturulmamış.'))
        
        return {
            'name': _('İhale'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender',
            'view_mode': 'form',
            'res_id': self.tender_id.id,
            'target': 'current',
        }
    
    @api.model
    def group_lines_for_tender(self, lines):
        """
        SAT kalemlerini ihale tipi kurallarına göre grupla
        Her SAT kalemi ayrı değerlendirilir ve uygun gruba eklenir
        
        Args:
            lines: purchase.requisition.line recordset
            
        Returns:
            dict: {
                'group_key': {
                    'tender_type': str,
                    'line_ids': [ids],
                    'material_group': str,
                    'purchasing_group': str,
                    'company_code': str,
                }
            }
        """
        groups = {}
        matrix = lines.env['tender.type.matrix']
        
        for line in lines:
            # İhale tipi kurallarına göre belirle
            tender_info = matrix.determine_tender_type(
                material_group=line.material_group,
                purchasing_group=line.purchasing_group,
                production_location=line.erp_plant_code
            )
            
            tender_type = tender_info.get('tender_type', 'indirect')
            
            # Gruplama anahtarı oluştur
            # Aynı ihale tipinde, mal grubunda, satınalma grubunda ve şirkette olanlar birleşir
            group_key = f"{tender_type}_{line.material_group or 'none'}_{line.purchasing_group or 'none'}_{line.erp_company_code or 'none'}"
            
            if group_key not in groups:
                groups[group_key] = {
                    'tender_type': tender_type,
                    'line_ids': [],
                    'material_group': line.material_group,
                    'purchasing_group': line.purchasing_group,
                    'company_code': line.erp_company_code,
                    'responsible': tender_info.get('responsible'),
                    'decision_source': tender_info.get('decision_source'),
                }
            
            groups[group_key]['line_ids'].append(line.id)
        
        return groups