# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
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
    header_note = fields.Text(string="Başlık Notu", help="SAT başlık açıklaması veya notu.")
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
        string='SAT Talep Eden',
        help="SAP'ta SAT'ı açan kullanıcı"
    )
    
    # İşleme Durumu (Header seviyesi)
    processing_status = fields.Selection([
        ('N', 'İşlenmedi'),
        ('T', 'İhaleye Alındı'),
        ('C', 'Tamamlandı'),
    ], string='İşleme Durumu', default='N', copy=False,
       help="SAT'ın genel işleme durumu")

    # Manuel Giriş Alanları
    department_id = fields.Many2one(
        'hr.department', 
        string='Departman',
        default=lambda self: self.env.user.employee_id.department_id
    )

    @api.onchange('user_id')
    def _onchange_user_id_set_dept(self):
        if self.user_id and self.user_id.employee_id:
            self.department_id = self.user_id.employee_id.department_id

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
        """Seçili SAT kalemlerinden ihaleler oluştur - UI action"""
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
        
        # Direkt ihale oluştur
        created_tenders = valid_lines.create_tenders_from_lines()
        
        if not created_tenders:
            raise UserError(_('İhale oluşturulamadı.'))
        
        # İhaleleri göster
        if len(created_tenders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Oluşturulan İhale'),
                'res_model': 'ak.tender',
                'view_mode': 'form',
                'res_id': created_tenders.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Oluşturulan İhaleler'),
                'res_model': 'ak.tender',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_tenders.ids)],
                'target': 'current',
            }

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})


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
    
    # Yeni SAP Alanları
    vendor_preferred = fields.Char(
        string='Tercih Edilen Tedarikçi',
        help="SAP'den gelen tercih edilen tedarikçi kodu"
    )
    
    vendor_fixed = fields.Char(
        string='Sabit Tedarikçi',
        help="SAP'den gelen sabit tedarikçi kodu"
    )
    
    requester_comment = fields.Text(
        string='Talep Eden Yorumu',
        help="SAP'den gelen talep eden yorumu"
    )
    
    pr_count = fields.Char(
        string='SAT Sayısı',
        help="SAP'den gelen SAT Sayısı (Genellikle 1)"
    )
    
    po_number = fields.Char(
        string='SAS No',
        help="SAP Satınalma Siparişi Numarası"
    )
    
    approval_date = fields.Date(
        string='Onay Tarihi',
        help="SAT'ın onaylandığı tarih"
    )
    
    # İhale İlişkisi
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
    
    tender_state = fields.Char(
        related='tender_id.workflow_state_name',
        string='İhale Durumu',
        readonly=True
    )
    
    # Computed Fields
    can_create_tender = fields.Boolean(
        string='İhale Oluşturulabilir',
        compute='_compute_can_create_tender',
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id_set_price(self):
        for line in self:
            if not line.price_unit:
                line.price_unit = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'price_unit' not in vals:
                vals['price_unit'] = 0.0
        return super().create(vals_list)

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

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if not vals.get('erp_pr_id'):
    #             # Manuel girişlerde taslak durumunda başlasın
    #             vals['state'] = 'draft'
    #     return super().create(vals_list)

    def action_in_progress(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})
    
    @api.depends('erp_pr_id', 'material_group', 'purchasing_group', 'erp_company_code', 'erp_plant_code', 'line_processing_status', 'deletion_indicator')
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
            responsible_users = tender_info.get('responsible_user_ids', self.env['res.users'])
            
            # Grup bilgisini oluştur - SAT No ile başla
            parts = []
            if tender_type:
                type_labels = {
                    'direct': 'Direkt',
                    'indirect': 'Endirekt',
                    'promotion': 'Promosyon',
                    'mice': 'MICE'
                }
                parts.append(f"Tip: {type_labels.get(tender_type, tender_type)}")
            if rec.erp_pr_id:
                parts.append(f"SAT: {rec.erp_pr_id}")
            if rec.material_group:
                parts.append(f"MG: {rec.material_group}")
            if rec.purchasing_group:
                parts.append(f"SG: {rec.purchasing_group}")
            if rec.erp_company_code:
                parts.append(f"Şirket: {rec.erp_company_code}")
            if responsible_users:
                user_names = ', '.join(responsible_users.mapped('name'))
                parts.append(f"Sorumlu: {user_names}")
            
            rec.tender_group_info = ' | '.join(parts) if parts else 'Grup belirlenemedi'
    
    def action_create_tender(self):
        """Seçili SAT kalemlerinden ihale oluştur - UI action"""
        if not self:
            raise UserError(_('Lütfen en az bir SAT kalemi seçin.'))
        
        # İşlenebilir kalemleri filtrele
        valid_lines = self.filtered(lambda l: l.can_create_tender)
        
        if not valid_lines:
            raise UserError(_('Seçili kalemler zaten işlenmiş veya silinmiş.'))
        
        # Direkt ihale oluştur
        created_tenders = valid_lines.create_tenders_from_lines()
        
        if not created_tenders:
            raise UserError(_('İhale oluşturulamadı.'))
        
        # İhaleleri göster
        if len(created_tenders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Oluşturulan İhale'),
                'res_model': 'ak.tender',
                'view_mode': 'form',
                'res_id': created_tenders.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Oluşturulan İhaleler'),
                'res_model': 'ak.tender',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_tenders.ids)],
                'target': 'current',
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
        
        _logger.info(f"  Gruplama başlıyor: {len(lines)} kalem")
        
        # Ürünü olmayan kalemleri kontrol et
        lines_without_product = lines.filtered(lambda l: not l.product_id)
        if lines_without_product:
            _logger.warning(f"  ⚠ {len(lines_without_product)} kalemin ürünü yok!")
            # Sadece ürünü olanları işle
            lines = lines.filtered(lambda l: l.product_id)
            _logger.info(f"  Ürünü olan kalemler: {len(lines)}")
        
        if not lines:
            _logger.error("  ✗ Ürünü olan kalem bulunamadı!")
            return groups
        
        for line in lines:
            # İhale tipi kurallarına göre belirle
            tender_info = matrix.determine_tender_type(
                material_group=line.material_group,
                purchasing_group=line.purchasing_group,
                production_location=line.erp_plant_code
            )
            
            tender_type = tender_info.get('tender_type', 'indirect')
            
            # Gruplama anahtarı oluştur
            # Her SAT numarası için ayrı ihale oluşturulacak
            # Aynı SAT numarasında, aynı ihale tipinde, mal grubunda, satınalma grubunda ve şirkette olanlar birleşir
            group_key = f"{tender_type}_{line.erp_pr_id or 'none'}_{line.material_group or 'none'}_{line.purchasing_group or 'none'}_{line.erp_company_code or 'none'}"
            
            if group_key not in groups:
                groups[group_key] = {
                    'tender_type': tender_type,
                    'line_ids': [],
                    'material_group': line.material_group,
                    'purchasing_group': line.purchasing_group,
                    'company_code': line.erp_company_code,
                    'responsible_user_ids': tender_info.get('responsible_user_ids', self.env['res.users']),
                    'decision_source': tender_info.get('decision_source'),
                }
            
            groups[group_key]['line_ids'].append(line.id)
        
        _logger.info(f"  ✓ {len(groups)} grup oluşturuldu")
        return groups
    
    def create_tenders_from_lines(self):
        """
        SAT kalemlerinden otomatik ihale oluştur
        Hem manuel hem de otomasyonda kullanılabilir
        
        Returns:
            ak.tender recordset: Oluşturulan ihaleler
        """
        _logger.info("=" * 80)
        _logger.info("İHALE OLUŞTURMA BAŞLADI")
        _logger.info("=" * 80)
        
        if not self:
            # Eğer self boşsa, tüm işlenebilir kalemleri al
            self = self.env['purchase.requisition.line'].search([
                ('line_processing_status', '=', 'N'),
                ('deletion_indicator', '=', False)
            ])
            _logger.info(f"Tüm işlenebilir SAT kalemleri alındı: {len(self)} kalem")
        else:
            _logger.info(f"Seçili SAT kalemleri: {len(self)} kalem")
        
        if not self:
            _logger.info("İhale oluşturulacak SAT kalemi bulunamadı")
            return self.env['ak.tender']
        
        # Ürünü olmayan kalemlere ürün oluştur
        lines_without_product = self.filtered(lambda l: not l.product_id)
        if lines_without_product:
            _logger.info(f"{len(lines_without_product)} SAT kalemi için ürün oluşturuluyor...")
            created_count = 0
            for line in lines_without_product:
                try:
                    product = line._ensure_product()
                    if product:
                        line.product_id = product  # Direkt atama, write() yerine
                        created_count += 1
                        _logger.info(f"  ✓ SAT {line.erp_pr_id}/{line.erp_pr_item} -> Ürün: {product.name}")
                except Exception as e:
                    _logger.error(f"  ✗ SAT {line.erp_pr_id}/{line.erp_pr_item} için ürün oluşturulamadı: {str(e)}")
            _logger.info(f"✓ {created_count}/{len(lines_without_product)} ürün oluşturuldu")
        
        # Kalemleri grupla
        _logger.info(f"SAT kalemleri gruplandırılıyor...")
        groups = self.group_lines_for_tender(self)
        
        if not groups:
            _logger.warning(f"✗ {len(self)} SAT kalemi için ihale grubu oluşturulamadı")
            return self.env['ak.tender']
        
        _logger.info(f"✓ {len(groups)} ihale grubu oluşturuldu")
        
        created_tenders = self.env['ak.tender']
        
        for idx, (group_key, group_data) in enumerate(groups.items(), 1):
            _logger.info(f"\n--- İhale {idx}/{len(groups)} oluşturuluyor ---")
            tender_type = group_data['tender_type']
            line_ids = group_data['line_ids']
            
            # Grup kalemlerini al
            group_lines = self.env['purchase.requisition.line'].browse(line_ids)
            
            if not group_lines:
                _logger.warning(f"✗ Grup {idx}: Kalem bulunamadı")
                continue
            
            _logger.info(f"Grup {idx}: Tip={tender_type}, Kalem sayısı={len(group_lines)}")
            
            # İhale adı oluştur
            tender_name = self._generate_tender_name(tender_type, group_lines[0])
            _logger.info(f"İhale adı: {tender_name}")
            
            # İhale kurallarına göre buyer_id'yi belirle
            responsible_user_ids = group_data.get('responsible_user_ids', self.env['res.users'])
            decision_source = group_data.get('decision_source', 'unknown')
            responsible_id = False
            
            if responsible_user_ids:
                # İlk kullanıcıyı buyer_id olarak ata
                responsible_id = responsible_user_ids[0].id
                _logger.info(f"✓ Buyer ID atandı ({decision_source}): {responsible_user_ids[0].name}")
            else:
                _logger.warning(f"⚠ Buyer ID belirlenemedi - Kural kaynağı: {decision_source}")
            
            try:
                # İhale oluştur
                from datetime import datetime, timedelta
                
                tender_vals = {
                    'name': tender_name,
                    'tender_type': tender_type,
                    'start_date': datetime.now(),
                    'end_date': datetime.now() + timedelta(days=7),  # 7 gün sonra
                }
                
                # SAT başlık notunu al
                # Tüm kalemler aynı SAT başlığına ait olmalı
                sat_header = group_lines[0].requisition_id if group_lines and group_lines[0].requisition_id else False
                if sat_header:
                    if sat_header.header_note:
                        tender_vals['description'] = sat_header.header_note # ak.tender modelinde description alanı var
                    tender_vals['erp_pr_id'] = sat_header.erp_pr_id
                    tender_vals['erp_company_code'] = sat_header.erp_company_code # Transfer from PR header
                    tender_vals['erp_plant_code'] = sat_header.erp_plant_code # Transfer from PR header
                    tender_vals['erp_requester'] = sat_header.erp_requester # Transfer from PR header
                
                # SAT kalemlerinden tarihleri al (en erken tarihleri kullan)
                request_dates = group_lines.mapped('request_date')
                delivery_dates = group_lines.mapped('required_delivery_date')
                
                if request_dates and any(request_dates):
                    # None olmayan tarihleri filtrele ve en erkeni al
                    valid_request_dates = [d for d in request_dates if d]
                    if valid_request_dates:
                        tender_vals['request_date'] = min(valid_request_dates)
                
                if delivery_dates and any(delivery_dates):
                    # None olmayan tarihleri filtrele ve en erkeni al
                    valid_delivery_dates = [d for d in delivery_dates if d]
                    if valid_delivery_dates:
                        tender_vals['required_delivery_date'] = min(valid_delivery_dates)
                
                # Sorumlu varsa ekle (buyer_id alanına)
                if responsible_id:
                    tender_vals['buyer_id'] = responsible_id
                
                tender = self.env['ak.tender'].create(tender_vals)
                _logger.info(f"✓ İhale oluşturuldu: ID={tender.id}, Name={tender.name}")
                
                # Kalemleri ekle
                self._create_tender_lines(tender, group_lines)
                
                # SAT kalemlerini güncelle
                group_lines.write({'line_processing_status': 'T'})
                _logger.info(f"✓ {len(group_lines)} SAT kalemi 'İhaleye Alındı' olarak işaretlendi")
                
                created_tenders |= tender
                
            except Exception as e:
                _logger.error(f"✗ İhale {idx} oluşturulurken hata: {str(e)}", exc_info=True)
        
        _logger.info("=" * 80)
        _logger.info(f"✓ TOPLAM {len(created_tenders)} İHALE OLUŞTURULDU")
        _logger.info(f"✓ TOPLAM {len(self)} SAT KALEMİ İŞLENDİ")
        _logger.info("=" * 80)
        return created_tenders
    
    def _create_tender_lines(self, tender, requisition_lines):
        """İhale kalemlerini oluştur"""
        _logger.info(f"  İhale kalemleri oluşturuluyor: {len(requisition_lines)} kalem")
        
        for req_line in requisition_lines:
            try:
                # Açıklama alanını hazırla
                description = req_line.product_id.name or req_line.material_code
                
                # Onaylı üretici bilgilerini ekle
                if req_line.product_id and req_line.product_id.product_tmpl_id:
                    # Onaylı üreticileri bul (partner_type='manufacturer' ve is_approved=True)
                    approved_manufacturers = self.env['product.supplierinfo'].search([
                        ('product_tmpl_id', '=', req_line.product_id.product_tmpl_id.id),
                        ('partner_type', '=', 'manufacturer'),
                        ('is_approved', '=', True)
                    ])
                    
                    if approved_manufacturers:
                        manufacturer_names = ", ".join(approved_manufacturers.mapped('partner_id.name'))
                        description += f"\nOnaylı üretici: {manufacturer_names}"
                
                # İhale kalemi oluştur
                tender_line_vals = {
                    'tender_id': tender.id,
                    'product_id': req_line.product_id.id,
                    'name': description,
                    'quantity': req_line.product_qty,
                    'uom_id': req_line.product_uom_id.id,
                    'required_delivery_date': req_line.required_delivery_date,
                    'display_type': False,  # Normal product line (not section or note)
                    'erp_requester': req_line.erp_requester,
                    'requester_comment': req_line.requester_comment,
                }
                
                tender_line = self.env['ak.tender.line'].create(tender_line_vals)
                
                # SAT kalemi ile ilişkilendir
                req_line.write({'tender_line_id': tender_line.id})
                
                _logger.info(f"  ✓ İhale kalemi oluşturuldu: SAT {req_line.erp_pr_id}/{req_line.erp_pr_item} -> Tender Line {tender_line.id}")
                
            except Exception as e:
                _logger.error(f"  ✗ İhale kalemi oluşturulamadı: SAT {req_line.erp_pr_id}/{req_line.erp_pr_item} - Hata: {str(e)}")
                raise
    
    def _generate_tender_name(self, tender_type, sample_line=None):
        """
        İhale adı oluştur
        Format: SAT_NO-SIRA (örn: 20012977-1, 10006707-2)
        """
        if not sample_line or not sample_line.erp_pr_id:
            # SAT numarası yoksa eski format kullan
            type_labels = {
                'direct': 'Direkt',
                'indirect': 'Endirekt',
                'promotion': 'Promosyon',
                'mice': 'MICE'
            }
            type_label = type_labels.get(tender_type, tender_type)
            date_str = datetime.now().strftime('%Y%m%d')
            sequence = self.env['ir.sequence'].next_by_code('ak.tender') or '001'
            return f"İHALE_{type_label}_{date_str}_{sequence}"
        
        # SAT numarasını al ve başındaki sıfırları kaldır
        sat_no = sample_line.erp_pr_id.lstrip('0')
        
        # Aynı SAT numarasıyla kaç ihale var kontrol et
        existing_tenders = self.env['ak.tender'].search([
            ('name', 'like', f'{sat_no}-%')
        ])
        
        # Sıra numarasını belirle
        if existing_tenders:
            # Mevcut ihalelerin sıra numaralarını bul
            max_seq = 0
            for tender in existing_tenders:
                try:
                    # "20012977-3" formatından "3" ü çıkar
                    seq_part = tender.name.split('-')[-1]
                    seq_num = int(seq_part)
                    if seq_num > max_seq:
                        max_seq = seq_num
                except (ValueError, IndexError):
                    continue
            next_seq = max_seq + 1
        else:
            next_seq = 1
        
        return f"{sat_no}-{next_seq}"
    
    def _ensure_product(self):
        """Kalem için ürün oluştur veya bul"""
        self.ensure_one()
        
        material_code = self.material_code
        if not material_code:
            # Malzeme kodu yoksa oluştur
            material_code = f"SAT_{self.erp_pr_id}_{self.erp_pr_item}"
        
        # Önce kod ile ara
        product = self.env['product.product'].search([
            ('default_code', '=', material_code)
        ], limit=1)
        
        if product:
            return product
        
        # Ürün adı
        product_name = f"SAT {self.erp_pr_id}/{self.erp_pr_item}"
        if self.material_code:
            product_name = f"{self.material_code} - {product_name}"
        
        # Ürün oluştur
        product_vals = {
            'name': product_name,
            'default_code': material_code,
            'type': 'product',
            'purchase_ok': True,
            'sale_ok': False,
            'categ_id': self.env.ref('product.product_category_all').id,
        }
        
        product = self.env['product.product'].create(product_vals)
        _logger.info(f"Ürün oluşturuldu: {product.name} ({product.default_code})")
        
        return product
        return groups