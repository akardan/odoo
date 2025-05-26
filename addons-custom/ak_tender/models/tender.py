# -*- coding: utf-8 -*-

# ak_tender/models/tender.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AkTenderLine(models.Model):
    _name = 'ak.tender.line'
    _description = 'İhale Kalemi'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sıra', default=10)
    tender_id = fields.Many2one('ak.tender', string='İhale', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Ürün/Malzeme', required=True,
                                 help="İhale edilecek ürün veya malzeme.")
    name = fields.Char(string='Açıklama', related='product_id.name', readonly=True)
    quantity = fields.Float(string='Miktar', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Birim', related='product_id.uom_id', readonly=True)
    required_delivery_date = fields.Date(string='Gerekli Teslim Tarihi',
                                         help="İstenen teslimat tarihi.")

class AkTender(models.Model):
    _name = 'ak.tender'
    _description = 'İLKOis Tender'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='İhale Adı', required=True, copy=False,
                       help="İhale sürecinin başlığı veya kısa adı.")
    code = fields.Char(string='İhale Kodu', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    
    # ERP Entegrasyon Alanları (Simülasyon)
    erp_pr_id = fields.Char(string='ERP SAT No', copy=False,
                             help="İlgili ERP Satın Alma Talebi Numarası (entegrasyon ile gelecek).")
    erp_company_code = fields.Char(string='ERP Şirket Kodu', help="İlgili ERP Şirket Kodu (entegrasyon ile gelecek).")
    erp_plant_code = fields.Char(string='ERP Tesis Kodu', help="İlgili ERP Tesis Kodu (entegrasyon ile gelecek).")
    
    # TEKLİF DOKÜMANINA GÖRE REVİZE EDİLEN DURUM ALANI
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('first_tender_round', '1. Teklif Toplama'), # RFQ Gönderildi / İlk Teklifler Alınıyor
        ('target_price_set', 'Hedef Fiyat Belirlendi'), # İlk Teklifler Değerlendirildi, Hedef Fiyat Belirlendi
        ('second_tender_round', '2. Teklif Toplama'), # Açık Eksiltme / Teklif Revizyonu
        ('evaluation', 'Değerlendirme'), # Son Tekliflerin Detaylı Değerlendirilmesi
        ('approval_pending', 'Onay Bekliyor'),
        ('approved', 'Onaylandı'),
        ('done', 'Tamamlandı'),
        ('cancel', 'İptal Edildi'),
    ], string='Durum', default='draft', tracking=True)

    tender_type = fields.Selection([
        ('standard', 'Standart İhale'), # Tek bir tur
        ('open_auction', 'Açık Eksiltme (Açık İhale)'), # Birden fazla tur, hedef fiyat ile
        ('sealed_bid', 'Kapalı Zarf Teklif'), # Genelde tek tur ama hedef fiyat ile revizyon olabilir
    ], string='İhale Tipi', default='standard', required=True)

    start_date = fields.Datetime(string='Başlangıç Tarihi', default=fields.Datetime.now(), required=True)
    end_date = fields.Datetime(string='Bitiş Tarihi', required=True)
    description = fields.Html(string='İhale Açıklaması',
                              help="İhale ile ilgili detaylı bilgiler ve şartnameler.")
    
    # İhale Kalemleri (One2many ilişki) - İhalenin temelini oluşturur
    tender_lines = fields.One2many('ak.tender.line', 'tender_id', string='İhale Kalemleri', required=True)

    # Davetli Tedarikçiler (Many2many ilişki)
    invited_partners = fields.Many2many('res.partner', string='Davetli Tedarikçiler',
                                       domain=[('supplier_rank', '>=', 0)],
                                       help="Bu ihaleye davet edilecek tedarikçiler.")

    # İhale Sonuçları (One2many ilişki)
    tender_results = fields.One2many('ak.tender.result', 'tender_id', string='Teklif Sonuçları')
    
    # Kazanan Teklif ve Hedef Fiyat (Raporlama için)
    winning_result_id = fields.Many2one('ak.tender.result', string='Kazanan Teklif', compute='_compute_winning_result', store=True, readonly=True)
    
    # TEKLİF DOKÜMANINA GÖRE KRİTİK ALAN: HEDEF FİYAT
    target_price = fields.Monetary(string='Hedef Fiyat', currency_field='currency_id', 
                                   help="Satın Alma Direktörü tarafından belirlenen hedef fiyat.",
                                   tracking=True) # Değişiklikleri takip et
    currency_id = fields.Many2one('res.currency', string='Para Birimi', default=lambda self: self.env.company.currency_id)
    
    # Onay Mekanizması için alanlar
    approval_user_id = fields.Many2one('res.users', string='Onaylayan Kullanıcı', copy=False, readonly=True,
                                      help="Bu ihaleyi onaylayan kullanıcı.")
    approval_date = fields.Datetime(string='Onay Tarihi', copy=False, readonly=True)
    
    # Akıllı Butonlar için compute field'lar
    purchase_order_count = fields.Integer(string='SAS Sayısı', compute='_compute_purchase_order_count')
    
    @api.depends('tender_results')
    def _compute_winning_result(self):
        # Bu prototipte en düşük fiyatlı teklifi kazanan kabul edelim
        for tender in self:
            if tender.tender_results:
                # Sadece 'selected' (seçilmiş) veya en düşük fiyatlı teklifi bul
                selected_result = tender.tender_results.filtered(lambda r: r.status == 'selected')
                if selected_result:
                    tender.winning_result_id = selected_result[0]
                else: # Henüz seçilmemişse en düşüğü göster
                    tender.winning_result_id = min(tender.tender_results, key=lambda r: r.total_price)
            else:
                tender.winning_result_id = False
    
    @api.depends('tender_results.purchase_order_id')
    def _compute_purchase_order_count(self):
        for tender in self:
            # İhale sonuçlarına bağlı olarak oluşturulan Purchase Order sayısını hesapla
            tender.purchase_order_count = len(tender.tender_results.mapped('purchase_order_id').filtered(lambda po: po.exists()))
            
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            vals['code'] = self.env['ir.sequence'].next_by_code('ak.tender.sequence') or _('New')
        result = super(AkTender, self).create(vals)
        return result

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("Başlangıç Tarihi, Bitiş Tarihinden sonra olamaz!"))
            
    # YENİ DURUM GEÇİŞ METOTLARI (TEKLİF DOKÜMANINA GÖRE)
    
    def action_start_first_round(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("İhale sadece 'Taslak' durumundayken 1. Teklif Toplama turuna başlatılabilir."))
        if not self.tender_lines:
            raise UserError(_("İhaleyi başlatmak için en az bir ihale kalemi tanımlanmalıdır."))
        if not self.invited_partners:
            raise UserError(_("İhaleyi başlatmak için en az bir tedarikçi davet edilmelidir."))
        
        # Bu noktada tedarikçilere davet e-postaları gönderilebilir ve portalda ilk teklif formu açılabilir.
        self.write({'state': 'first_tender_round'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('1. Teklif Toplama Başlatıldı'),
                'message': _('İhale ilk teklif toplama turuna başlatıldı. Tedarikçiler tekliflerini sunmaya başlayabilir.'),
                'sticky': False,
            }
        }

    def action_set_target_price(self):
        self.ensure_one()
        if self.state != 'first_tender_round':
            raise UserError(_("Hedef fiyat sadece '1. Teklif Toplama' aşamasında belirlenebilir."))
        if not self.tender_results:
            raise UserError(_("Hedef fiyat belirlemek için en az bir teklif sonucu girilmelidir."))
            
        # Hedef fiyat belirleme sihirbazını aç
        return {
            'name': _('Hedef Fiyat Belirleme'),
            'type': 'ir.actions.act_window',
            'res_model': 'ak.tender.set.target.price.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }

    def action_start_second_round(self):
        self.ensure_one()
        if self.state != 'target_price_set':
            raise UserError(_("İkinci teklif toplama turu sadece 'Hedef Fiyat Belirlendi' aşamasında başlatılabilir."))
        
        # Bu noktada tedarikçilere hedef fiyat bilgisi ve revizyon linkleri gönderilebilir.
        self.write({'state': 'second_tender_round'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('2. Teklif Toplama Başlatıldı'),
                'message': _('İhale ikinci teklif toplama turuna (açık eksiltme/revizyon) başlatıldı. Tedarikçiler tekliflerini revize edebilir.'),
                'sticky': False,
            }
        }

    def action_to_evaluation(self):
        self.ensure_one()
        if self.state not in ('first_tender_round', 'second_tender_round', 'target_price_set'):
            raise UserError(_("Değerlendirme aşamasına geçiş sadece '1. Teklif Toplama', '2. Teklif Toplama' veya 'Hedef Fiyat Belirlendi' aşamasından yapılabilir."))
        if not self.tender_results:
            raise UserError(_("Değerlendirme aşamasına geçmek için en az bir teklif sonucu olmalıdır."))
            
        # Teklif toplama süresi bitmiş mi kontrol edilebilir (gerçek entegrasyon)
        # Bu noktada tedarikçilerin teklif verme linkleri devre dışı bırakılır.
        self.write({'state': 'evaluation'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Değerlendirme Aşamasında'),
                'message': _('İhale değerlendirme aşamasına alındı. Teklifleri detaylı inceleyebilir ve kazananı belirleyebilirsiniz.'),
                'sticky': False,
            }
        }

    def action_request_approval(self):
        self.ensure_one()
        if self.state != 'evaluation':
            raise UserError(_("Onay talebi sadece 'Değerlendirme' aşamasında yapılabilir."))
        if not self.winning_result_id:
            raise UserError(_("Onay talep etmeden önce kazanan bir teklif seçilmelidir."))
        
        # Doğrudan onay bekliyor durumuna geç
        self.write({'state': 'approval_pending'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Onay Talebi Gönderildi'),
                'message': _('İhale için onay talebi gönderildi. Lütfen onay sürecini takip edin.'),
                'sticky': False,
            }
        }
        
    # Onay talebi görüntüleme metodu kaldırıldı - approvals modülü olmadığı için

    def action_approve_tender(self):
        self.ensure_one()
        if self.state != 'approval_pending':
            raise UserError(_("İhale sadece 'Onay Bekliyor' durumundayken onaylanabilir."))
        
        if not self.winning_result_id:
            raise UserError(_("İhaleyi onaylamak için kazanan bir teklif belirlenmelidir."))
            
        # Onay bilgilerini kaydet
        self.write({
            'approval_user_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })

        # *** ODOO PURCHASE.ORDER OLUŞTURMA BAŞLANGICI ***
        winning_result = self.winning_result_id
        
        if winning_result and winning_result.partner_id:
            # Satın Alma Siparişi (PO) oluşturma
            purchase_order = self.env['purchase.order'].create({
                'partner_id': winning_result.partner_id.id,
                'currency_id': winning_result.currency_id.id,
                'date_order': fields.Datetime.now(),
                'picking_type_id': self.env.ref('stock.picking_type_in').id, # Default alım türü
                'origin': self.code, # İhale kodunu referans olarak ekleyelim
                'company_id': self.env.company.id,
                'payment_term_id': winning_result.payment_terms.id if winning_result.payment_terms else False,
                # Diğer gerekli alanlar eklenebilir (örn: incoterm_id)
            })

            # SAS kalemlerini oluşturma (ihale kalemlerini temel alarak)
            for tender_line in self.tender_lines:
                # Basitlik için her ihale kalemi için kazananın birim fiyatı uygulandı.
                # Gerçekte her ihale kalemi için ayrı birim fiyatlar gerekebilir, bu durumda tender_result_line modeli daha uygun olur.
                self.env['purchase.order.line'].create({
                    'order_id': purchase_order.id,
                    'product_id': tender_line.product_id.id,
                    'name': tender_line.name,
                    'product_qty': tender_line.quantity,
                    'product_uom': tender_line.uom_id.id,
                    'price_unit': winning_result.price_unit, 
                    'date_planned': tender_line.required_delivery_date,
                })
            
            # Oluşturulan SAS'ı ihale sonucuna bağla
            winning_result.purchase_order_id = purchase_order.id
            self._compute_purchase_order_count() # Akıllı buton sayacını güncelle

            # ERP'ye SAS gönderme işlemi burada tetiklenecek (simülasyon)
            # Örneğin: self.env['erp.connector'].create_po_in_erp(purchase_order)
            
            notification_message = _('İhale başarıyla onaylandı. Satın Alma Siparişi %s oluşturuldu ve ERP\'ye gönderiliyor.') % (purchase_order.name)
        else:
            notification_message = _('İhale başarıyla onaylandı. Ancak kazanan teklif bilgileri eksik olduğu için SAS oluşturulamadı.')

        self.write({'state': 'approved'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İhale Onaylandı'),
                'message': notification_message,
                'sticky': False,
            }
        }
        # *** ODOO PURCHASE.ORDER OLUŞTURMA BİTİŞİ ***
        
    def action_complete_tender(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("İhale sadece 'Onaylandı' durumundayken tamamlanabilir."))
            
        # Burası aslında SAS oluşturma ve SAP'a gönderme işleminin ardından gerçekleşir.
        self.write({'state': 'done'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İhale Tamamlandı'),
                'message': _('İhale süreci başarıyla tamamlandı.'),
                'sticky': False,
            }
        }

    def action_cancel_tender(self):
        self.ensure_one()
        if self.state in ('approved', 'done'):
            raise UserError(_("Onaylanmış veya tamamlanmış ihale iptal edilemez."))
        self.write({'state': 'cancel'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İhale İptal Edildi'),
                'message': _('İhale başarıyla iptal edildi.'),
                'sticky': False,
            }
        }
        
    def action_set_draft(self):
        self.ensure_one()
        if self.state != 'cancel':
            raise UserError(_("Sadece iptal edilmiş ihaleler taslak durumuna çevrilebilir."))
        self.write({'state': 'draft'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('İhale Taslağa Çevrildi'),
                'message': _('İhale taslak durumuna çevrildi. Düzenlemeye devam edebilirsiniz.'),
                'sticky': False,
            }
        }
    
    def action_view_tender_results(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Teklif Sonuçları'),
            'res_model': 'ak.tender.result',
            'view_mode': 'list,form',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id},
            'target': 'current',
            'views': [
                (False, 'list'),
                (False, 'form'),
            ],
        }
    
    def action_view_purchase_orders(self):
        self.ensure_one()
        purchase_orders = self.tender_results.mapped('purchase_order_id').filtered(lambda po: po.exists())
        action = self.env.ref('purchase.purchase_rfq_action').read()[0]
        if len(purchase_orders) > 1:
            action['domain'] = [('id', 'in', purchase_orders.ids)]
            # Update view_mode to use list instead of tree
            if 'view_mode' in action and 'tree' in action['view_mode']:
                action['view_mode'] = action['view_mode'].replace('tree', 'list')
            # Update views to use list instead of tree
            if 'views' in action:
                action['views'] = [(view_id, view_type.replace('tree', 'list') if view_type == 'tree' else view_type) for view_id, view_type in action['views']]
        elif purchase_orders:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchase_orders.id
        else:
            action = {'type': 'ir.actions.act_window_close'} # No PO to show
        return action
