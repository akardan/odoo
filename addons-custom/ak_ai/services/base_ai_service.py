# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError, AccessError
import logging
import json

_logger = logging.getLogger(__name__)


class AkAiService(models.AbstractModel):
    """Base AI Service - Security-First Architecture"""
    _name = 'ak_ai.service'
    _description = 'Base AI Service'

    SECURITY_RULES = """
CRITICAL SECURITY RULES (NEVER VIOLATE):

1. ❌ NEVER use sudo() or with_user(SUPERUSER_ID)
2. ❌ NEVER access env.cr directly for write operations  
3. ❌ NEVER use os, sys, subprocess modules
4. ❌ NEVER use eval() or exec() with user input
5. ❌ NEVER access file system (open, file, etc.)

6. ✅ ALWAYS use env (which has current user's rights)
7. ✅ ALWAYS check permissions before operations
8. ✅ ALWAYS handle AccessError gracefully
9. ✅ ALWAYS inform user if they lack permissions
10. ✅ ALWAYS log user attribution in audit trail

If an operation requires elevated permissions:
- Inform the user they don't have required access
- Suggest who they should contact (admin/manager)
- DO NOT attempt to bypass security
"""

    @api.model
    def get_service(self):
        """Get the appropriate AI service based on configuration"""
        assistant = self.env['ak_ai.assistant'].get_active_assistant()
        
        if assistant.ai_provider == 'openai':
            return self.env['ak_ai.service.openai']
        elif assistant.ai_provider == 'anthropic':
            return self.env['ak_ai.service.anthropic']
        elif assistant.ai_provider == 'openrouter':
            return self.env['ak_ai.service.openrouter']
        else:
            raise ValidationError(_('Unsupported AI provider: %s') % assistant.ai_provider)
    
    @api.model
    def get_available_models(self, provider):
        """Get available models for a provider - can be overridden by subclasses"""
        raise NotImplementedError('Subclasses should implement get_available_models')
    
    def generate_response(self, user_message, context):
        """Generate AI response - must be implemented by subclasses"""
        raise NotImplementedError('Subclasses must implement generate_response')
    
    def _build_system_prompt(self, context):
        """Build system prompt with security rules and context"""
        
        user_context = context.get('user', {})
        conversation_context = context.get('conversation', {})
        record_context = context.get('record', {})
        
        # Use record_context for the actual data
        full_context = record_context if record_context else conversation_context
        
        user_name = user_context.get('name', 'Bilinmiyor')
        user_lang = user_context.get('lang', 'tr_TR')
        context_str = self._format_full_context(full_context)
        
        system_prompt = f"""Sen KAI (Kardan AI), Odoo ERP sistemi için akıllı bir asistansın.

{self.SECURITY_RULES}

KULLANICI BİLGİLERİ:
- İsim: {user_name}
- Dil: {user_lang}

MEVCUT KAYIT VERİLERİ (TÜM BİLGİLER ELİNDE):
{context_str}

ÖNEMLİ TALİMATLAR:
1. MEVCUT KAYIT VERİLERİ'nde veri varsa → DOĞRUDAN kullan, kod YAZMA!
2. MEVCUT KAYIT VERİLERİ'nde yeterli veri YOKSA → Python kodu göster
3. Kullanıcı "ihale kalemlerini listele" derse:
   a) Eğer tender_lines.items içinde product_id, quantity vs varsa → Listeyi DOĞRUDAN göster
   b) Eğer tender_lines.items boşsa veya sadece ID varsa → Python kodu ile okumayı göster
4. Kullanıcı datayı GÜNCELLEMEK/OLUŞTURMAK istiyorsa → Kod örneği göster ve [EXECUTE_CODE] bloğu içine al!
5. MODEL VE ALAN BİLGİLERİNİ ÖĞRENEBİLİRSİN - Kullanıcı model/alan sorarsa, env ile öğrenmeyi açıkla
6. YETKİ SORMA - Eğer veriyi görüyorsan zaten yetkin var

KOD ÇALIŞTIRMA KURALLARI:
- Kullanıcı bir kayıt oluşturmanı veya güncellemeni isterse, Python kodunu şu formatta yaz:
  [EXECUTE_CODE]
  # Kod buraya
  # ÖNEMLİ: İşlem sonrası kritik alanları (fiyat, miktar, toplam) kontrol et!
  result = {{"success": True, "message": "İşlem tamamlandı", "details": "Oluşturulan kayıt: ..."}}
  [/EXECUTE_CODE]
- Bu blok içindeki kod kullanıcı onayıyla OTOMATİK çalıştırılabilir.
- Kod içinde `env`, `record`, `datetime`, `fields` kullanılabilir.
- `sudo()` KULLANMA! Kullanıcının yetkisi varsa çalışacaktır.
- **SEMANTİK KONTROL:** Kodun sonunda mutlaka bir özet hazırla. Eğer bir fiyat 0 ise veya beklenen bir değer atanmamışsa kullanıcıyı uyar!
- **DOĞRULAMA:** Kayıt oluşturduktan sonra `new_record.read()` ile veriyi tekrar oku ve result["details"] içine ekle ki kullanıcı ne oluştuğunu görsün.

İLİŞKİLİ VERİLERİ OKUMA KURALLARI:
- tender_lines.items içinde product_id, quantity, name, target_price varsa → DOĞRUDAN kullan
- tender_lines.items boş veya eksikse → Python kodu ile okumayı göster:
```python
tender = env['ak.tender'].browse(record_id)
for tender_line in tender.tender_lines:
    print(f"{{tender_line.product_id.name}} - {{tender_line.quantity}} {{tender_line.uom_id.name}}")
```

MODEL VE ALAN ÖĞRENME:
Odoo modelleri ve alanları hakkında bilgi edinmek için şu kodları kullanabilirsin:

# Model bilgilerini öğrenmek:
model = env['model.adı']  # Örnek: env['ak.tender']
model_info = model.fields_get()  # Tüm alanları gösterir

# Belirli alanları görmek:
field_info = model.fields_get(['field_name'])

# Model kayıtlarını aramak:
records = model.search([('field', '=', 'value')])

# Kayıt okumak:
record = model.browse(record_id)
data = record.read(['field1', 'field2'])

Kullanıcı model/alan bilgisi istediğinde yukarıdaki kodları gösterebilirsin!

GÖREVLER:
1. Kullanıcıya Odoo ile ilgili sorularında yardım et
2. MEVCUT KAYIT VERİLERİ'ndeki bilgileri kullanarak sorulara DOĞRUDAN cevap ver
3. Model/alan bilgisi istendiğinde kod örnekleri göster (env ile öğrenme)
4. Güvenlik kurallarını asla ihlal etme
5. Türkçe yanıt ver (kullanıcı başka dil isterse o dilde)

YASAKLAR:
- sudo() kullanma
- Dosya sistemi erişimi
- Sistem komutları
- Kullanıcı yetkilerini aşma
- Veriler zaten elindeyken "veriye erişmek için şu kodu çalıştır" demek

ÖRNEKLER:

DURUM 1 - MEVCUT DATA OKUMA:
Kullanıcı: "Bu ihalenin detaylarını anlat"
YANLIŞ ❌: "İhale bilgilerini almak için: env['ak.tender'].search([...]) ..."
DOĞRU ✅: "İhale kodu: İHALE-2025-0716\nDurum: 1. Teklif Toplama\nBaşlangıç: 19 Kasım 2025\nBitiş: 26 Kasım 2025\nİhale Kalemleri: 2 adet..."

Kullanıcı: "ihale kalemlerini listele"
YANLIŞ ❌: "Kayıt detayları elimde yok"
DOĞRU ✅: "İhale kalemleri:\n1. [product_name] - Miktar: X, Fiyat: Y\n2. [product_name2] - Miktar: X, Fiyat: Y"

DURUM 2 - MODEL/ALAN ÖĞRENME:
Kullanıcı: "ak.tender modelinin alanlarını göster"
DOĞRU ✅: "ak.tender modelinin alanlarını öğrenmek için:\n```python\nmodel = env['ak.tender']\nmodel.fields_get()\n```"

Kullanıcı: "purchase.order'da hangi alanlar var?"
DOĞRU ✅: "purchase.order model alanlarını görmek için:\n```python\nenv['purchase.order'].fields_get()\n```"

Her zaman yardımcı, güvenli ve kullanıcı dostu ol!"""

        return system_prompt
    
    def _format_full_context(self, context):
        """Format FULL conversation context with ALL data for system prompt"""
        if not context:
            return "Genel sohbet - kayıt bağlamı yok"
            
        try:
            # Use JSON for complete data representation
            formatted = json.dumps(context, ensure_ascii=False, indent=2, default=str)
            # Use string concatenation to avoid f-string formatting issues with curly braces in JSON
            return "```json\n" + formatted + "\n```\n\nYukarıdaki JSON verisi kayıtın BÜTÜN bilgilerini içeriyor. Bu datayı DOĞRUDAN kullanarak cevap ver!"
        except Exception as e:
            _logger.error(f"Error formatting full context: {e}")
            # Fallback to simple format
            return self._format_context(context)
    
    def _format_permissions(self, permissions):
        """Format user permissions for system prompt"""
        if not permissions:
            return "Yetki bilgisi alınamadı"
            
        formatted = []
        for model, perms in permissions.items():
            model_name = self._get_model_display_name(model)
            allowed = [k for k, v in perms.items() if v]
            if allowed:
                formatted.append(f"- {model_name}: {', '.join(allowed)}")
                
        return '\n'.join(formatted) if formatted else "Özel yetki bulunamadı"
    
    def _format_context(self, context):
        """Format conversation context for system prompt"""
        if not context:
            return "Genel sohbet - kayıt bağlamı yok"
            
        model = context.get('model', 'Bilinmiyor')
        display_name = context.get('display_name', 'Bilinmiyor')
        
        formatted = f"Model: {self._get_model_display_name(model)}\n"
        formatted += f"Kayıt: {display_name}\n"
        
        fields = context.get('fields', {})
        if fields:
            formatted += "Önemli Alanlar:\n"
            for field, value in list(fields.items())[:10]:  # First 10 fields
                if value is not None:
                    formatted += f"- {field}: {value}\n"
                    
        related = context.get('related', {})
        if related:
            formatted += "İlişkili Veriler:\n"
            for key, value in related.items():
                formatted += f"- {key}: {value}\n"
                
        return formatted
    
    def _get_model_display_name(self, model_name):
        """Get user-friendly model name"""
        model_names = {
            'sale.order': 'Satış Siparişi',
            'purchase.order': 'Satın Alma Siparişi', 
            'account.move': 'Fatura/Makbuz',
            'res.partner': 'İş Ortağı',
            'product.product': 'Ürün',
            'stock.picking': 'Sevkiyat',
            'project.project': 'Proje',
            'hr.employee': 'Çalışan',
        }
        return model_names.get(model_name, model_name)
    
    def _validate_response(self, response):
        """Validate AI response for security violations"""
        
        # Check for forbidden patterns
        forbidden_patterns = [
            'sudo()',
            '.with_user(',
            'SUPERUSER_ID',
            'env.cr.execute',
            'import os',
            'import sys',
            'import subprocess',
            'eval(',
            'exec(',
            'open(',
            '__import__',
        ]
        
        for pattern in forbidden_patterns:
            if pattern in response:
                _logger.error(f"AI response contains forbidden pattern: {pattern}")
                raise ValidationError(_('AI response contains security violation'))
                
        return True
    
    def _log_interaction(self, user_message, ai_response, context, tokens_used=0, response_time=0, tokens_input=0, tokens_output=0, cost=0.0):
        """Log AI interaction for audit and learning"""
        try:
            assistant = self.env['ak_ai.assistant'].get_active_assistant()
            self.env['ak_ai.interaction_log'].create({
                'user_id': self.env.user.id,
                'user_message': user_message,
                'ai_response': ai_response,
                'context_data': json.dumps(context),
                'tokens_used': tokens_used,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'cost': cost,
                'response_time': response_time,
                'ai_provider': assistant.ai_provider,
                'model_name': assistant.get_model_name(),
            })
        except Exception as e:
            _logger.error(f"Error logging AI interaction: {e}")
    
    def _handle_permission_error(self, operation, model_name):
        """Generate helpful message when user lacks permissions"""
        
        model_display = self._get_model_display_name(model_name)
        
        suggestions = {
            'read': f"{model_display} kayıtlarını görüntüleme yetkiniz bulunmamaktadır.",
            'create': f"{model_display} oluşturma yetkiniz bulunmamaktadır.",
            'write': f"{model_display} düzenleme yetkiniz bulunmamaktadır.", 
            'unlink': f"{model_display} silme yetkiniz bulunmamaktadır.",
        }
        
        message = suggestions.get(operation, f"{operation} işlemi için yetkiniz bulunmamaktadır.")
        message += "\n\nYetki almak için sistem yöneticiniz ile iletişime geçin."
        
        return message