# -*- coding: utf-8 -*-
import json
import logging
import random
import string
from odoo import http, fields, _
from odoo.http import request
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound

_logger = logging.getLogger(__name__)

def validate_api_key():
    """Odoo'nun yerleşik API Key doğrulama fonksiyonu"""
    api_key = request.httprequest.headers.get('X-API-Key')
    if not api_key:
        raise Unauthorized('API anahtarı eksik')
    
    uid = request.env['res.users.apikeys']._check_credentials(scope='ak_exams', key=api_key)
    if not uid:
        raise Unauthorized('Geçersiz API anahtarı')
    
    # Ortamı kullanıcı ID'si ile güncelle
    request.update_env(uid)
    return uid

class SyncController(http.Controller):
    
    @http.route('/api/v1/system/status', type='http', auth='none', methods=['GET'], csrf=False)
    def api_status(self, **kw):
        """API durumunu kontrol eder"""
        try:
            # API Key doğrula
            uid = validate_api_key()
            
            # Odoo sürüm bilgisi
            version_info = request.env['ir.module.module'].sudo().search(
                [('name', '=', 'base')], limit=1).latest_version
            
            return request.make_response(
                json.dumps({
                    'success': True,
                    'data': {
                        'version': version_info,
                        'api_version': '1.0.0',
                        'server_time': fields.Datetime.now(),
                        'services': [
                            {
                                'name': 'Field Force Sync',
                                'endpoint': '/api/v1/organization/sync',
                                'status': 'active'
                            },
                            {
                                'name': 'Users Sync',
                                'endpoint': '/api/v1/users/sync',
                                'status': 'active'
                            }
                        ]
                    },
                    'user': {
                        'id': uid,
                        'name': request.env['res.users'].browse(uid).name,
                    }
                }, default=str),
                headers=[('Content-Type', 'application/json')]
            )
        except Unauthorized as e:
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
        except Exception as e:
            _logger.error("API Status hatası: %s", str(e))
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': 'Sunucu hatası',
                    'message': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
    
    @http.route('/api/v1/organization/sync', type='http', auth='none', methods=['POST'], csrf=False)
    def sync_organization(self, **kw):
        """Organizasyon yapısını senkronize eder"""
        try:
            # API Key doğrula
            validate_api_key()
            
            # POST JSON verisini al
            try:
                organization_units = json.loads(request.httprequest.data.decode('utf-8'))
            except json.JSONDecodeError:
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': 'Geçersiz JSON formatı'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if not isinstance(organization_units, list):
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': 'Geçersiz veri formatı. Bir dizi bekleniyor.'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # İşlem sonuçları
            result = {
                'processed': 0,
                'created': 0,
                'updated': 0,
                'failed': 0,
                'failures': []
            }
            
            # Birim haritası oluştur
            unit_map = {}
            for unit in organization_units:
                unit_map[unit.get('unit_id')] = unit
            
            # Her birim için işlem yap
            for unit in organization_units:
                try:
                    unit_id = unit.get('unit_id')
                    unit_name = unit.get('unit_name')
                    parent_unit_id = unit.get('parent_unit_id')
                    
                    if not unit_id or not unit_name:
                        result['failed'] += 1
                        result['failures'].append({
                            'unit_id': unit_id,
                            'reason': 'Geçersiz birim verisi'
                        })
                        continue
                    
                    # Mevcut takımı ara
                    existing_team = request.env['crm.team'].sudo().search([
                        ('external_id', '=', unit_id)
                    ], limit=1)
                    
                    # Parent ID kontrolü
                    parent_id = False
                    is_root_unit = (not parent_unit_id or parent_unit_id == '' or 
                                   parent_unit_id == unit_id or parent_unit_id == 'Sihirli Kitap')
                    
                    if not is_root_unit and parent_unit_id in unit_map:
                        parent_team = request.env['crm.team'].sudo().search([
                            ('external_id', '=', parent_unit_id)
                        ], limit=1)
                        
                        if parent_team:
                            parent_id = parent_team.id
                    
                    if existing_team:
                        # Birim zaten var, güncelle
                        update_data = {}
                        
                        # Sadece değişiklik olan alanları güncelle
                        if existing_team.name != unit_name:
                            update_data['name'] = unit_name
                        
                        if ((parent_id and existing_team.parent_id.id != parent_id) or 
                            (not parent_id and existing_team.parent_id)):
                            update_data['parent_id'] = parent_id
                        
                        if update_data:
                            existing_team.write(update_data)
                            result['updated'] += 1
                        
                        result['processed'] += 1
                    else:
                        # Yeni birim oluştur
                        request.env['crm.team'].sudo().create({
                            'name': unit_name,
                            'external_id': unit_id,
                            'parent_id': parent_id,
                            # 'team_type': 'U',
                            'company_id': request.env.company.id
                        })
                        result['created'] += 1
                        result['processed'] += 1
                
                except Exception as e:
                    _logger.error("Birim işleme hatası (%s): %s", unit_id, str(e))
                    result['failed'] += 1
                    result['failures'].append({
                        'unit_id': unit_id,
                        'reason': str(e)
                    })
            
            return request.make_response(
                json.dumps({
                    'success': True,
                    'message': 'Organizasyon yapısı başarıyla senkronize edildi',
                    'data': result
                }),
                headers=[('Content-Type', 'application/json')]
            )
        
        except Unauthorized as e:
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
        except Exception as e:
            _logger.error("Organizasyon senkronizasyon hatası: %s", str(e))
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': 'Sunucu hatası',
                    'message': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
            
    @http.route('/api/v1/users/sync', type='http', auth='none', methods=['POST'], csrf=False)
    def sync_users(self, **kw):
        """Kullanıcıları senkronize eder"""
        try:
            # API Key doğrula
            validate_api_key()
            
            # POST JSON verisini al
            try:
                users = json.loads(request.httprequest.data.decode('utf-8'))
            except json.JSONDecodeError:
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': 'Geçersiz JSON formatı'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if not isinstance(users, list):
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': 'Geçersiz veri formatı. Bir dizi bekleniyor.'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # İşlem sonuçları
            result = {
                'processed': 0,
                'created': 0,
                'updated': 0,
                'failed': 0,
                'failures': [],
                'newUsers': []
            }
            
            # Varsayılan şirket (company) bilgisini al
            default_company = request.env.company
            
            # Her kullanıcı için işlem yap
            for user_data in users:
                try:
                    user_id = user_data.get('user_id')
                    user_email = user_data.get('user_email')
                    user_full_name = user_data.get('user_full_name')
                    unit_id = user_data.get('unit_id')
                    
                    if not user_id or not user_email or not user_full_name:
                        result['failed'] += 1
                        result['failures'].append({
                            'user_id': user_id,
                            'reason': 'Geçersiz kullanıcı verisi'
                        })
                        continue
                    
                    # Kullanıcının takımını ara
                    team = False
                    if unit_id:
                        team = request.env['crm.team'].sudo().search([
                            ('external_id', '=', unit_id),
                            ('company_id', '=', default_company.id)
                        ], limit=1)
                        
                        if not team:
                            result['failed'] += 1
                            result['failures'].append({
                                'user_id': user_id,
                                'reason': f'Belirtilen takım bulunamadı: {unit_id}'
                            })
                            continue
                    
                    # Mevcut kullanıcıyı ara (önce external_id ile, sonra email ile)
                    existing_user = request.env['res.users'].sudo().search([
                        ('external_id', '=', user_id)
                    ], limit=1)
                    
                    if not existing_user:
                        existing_user = request.env['res.users'].sudo().search([
                            ('login', '=', user_email)
                        ], limit=1)
                    
                    if existing_user:
                        # Kullanıcı zaten var, güncelle
                        update_data = {}
                        
                        # Sadece değişiklik olan alanları güncelle
                        if existing_user.name != user_full_name:
                            update_data['name'] = user_full_name
                        
                        if existing_user.login != user_email:
                            update_data['login'] = user_email
                            update_data['email'] = user_email
                        
                        if not existing_user.external_id:
                            update_data['external_id'] = user_id
                        
                        # Takım güncelleme
                        if team:
                            # Eğer farklı bir takıma atanacaksa
                            if not existing_user.sale_team_id or existing_user.sale_team_id.id != team.id:
                                update_data['sale_team_id'] = team.id
                                
                                # Ayrıca crm_team_ids alanını da güncelle
                                if team.id not in existing_user.crm_team_ids.ids:
                                    update_data['crm_team_ids'] = [(4, team.id)]
                                
                                # Önceki takım üyeliklerini kaldır
                                old_memberships = request.env['crm.team.member'].sudo().search([
                                    ('user_id', '=', existing_user.id),
                                    ('crm_team_id', '!=', team.id)
                                ])
                                if old_memberships:
                                    old_memberships.sudo().unlink()
                                
                                # Yeni takım üyeliği oluştur (eğer yoksa)
                                existing_membership = request.env['crm.team.member'].sudo().search([
                                    ('user_id', '=', existing_user.id),
                                    ('crm_team_id', '=', team.id)
                                ], limit=1)
                                
                                if not existing_membership:
                                    request.env['crm.team.member'].sudo().create({
                                        'user_id': existing_user.id,
                                        'crm_team_id': team.id,
                                        'active': True
                                    })
                        
                        # Kullanıcının şirket erişimlerini kontrol et
                        if default_company and default_company.id not in existing_user.company_ids.ids:
                            update_data['company_ids'] = [(4, default_company.id)]
                            
                            # Eğer aktif şirketi yoksa, varsayılan şirketi ata
                            if not existing_user.company_id:
                                update_data['company_id'] = default_company.id
                        
                        if update_data:
                            existing_user.write(update_data)
                            result['updated'] += 1
                        
                        result['processed'] += 1
                    else:
                        # Yeni kullanıcı oluştur
                        # Rastgele şifre oluştur
                        password_chars = string.ascii_letters + string.digits + '!@#$%^&*()'
                        password = ''.join(random.choice(password_chars) for i in range(10))
                        
                        # Portal kullanıcı grubu bul
                        portal_group = request.env.ref('base.group_portal')
                        survey_group = request.env.ref('survey.group_survey_user')
                        
                        # Yeni kullanıcı için veriler
                        user_vals = {
                            'name': user_full_name,
                            'login': user_email,
                            'email': user_email,
                            'external_id': user_id,
                            'groups_id': [(6, 0, [portal_group.id, survey_group.id])],
                            'password': password,
                            'company_id': default_company.id,  # Varsayılan şirket
                            'company_ids': [(6, 0, [default_company.id])],  # Erişim izni olan şirketler
                            'share': True,  # Portal user
                            'sel_groups_1_10_11': 10  # Portal user selection field (10=Portal)
                        }
                        
                        # Takım ataması varsa ekle
                        if team:
                            user_vals['sale_team_id'] = team.id
                            # CRM takımları için çoklu ilişki alanını da ekle
                            user_vals['crm_team_ids'] = [(4, team.id)]
                        
                        # Kullanıcıyı oluştur
                        new_user = request.env['res.users'].sudo().create(user_vals)
                        
                        # Takıma üyelik kaydı oluştur
                        if team:
                            request.env['crm.team.member'].sudo().create({
                                'user_id': new_user.id,
                                'crm_team_id': team.id,
                                'active': True
                            })
                        
                        # Oluşturulan kullanıcı bilgilerini kaydet
                        result['newUsers'].append({
                            'user_id': user_id,
                            'email': user_email,
                            # 'password': password,
                            'odoo_id': new_user.id
                        })
                        
                        result['created'] += 1
                        result['processed'] += 1
                
                except Exception as e:
                    _logger.error("Kullanıcı işleme hatası (%s): %s", user_id, str(e))
                    result['failed'] += 1
                    result['failures'].append({
                        'user_id': user_id,
                        'reason': str(e)
                    })
            
            return request.make_response(
                json.dumps({
                    'success': True,
                    'message': 'Kullanıcılar başarıyla senkronize edildi',
                    'data': result
                }, default=str),
                headers=[('Content-Type', 'application/json')]
            )
        
        except Unauthorized as e:
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
        except Exception as e:
            _logger.error("Kullanıcı senkronizasyon hatası: %s", str(e))
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': 'Sunucu hatası',
                    'message': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
            
    @http.route('/api/v1/exams/access', type='http', auth='none', methods=['POST'], csrf=False)
    def get_exam_access(self, **kw):
        """Kullanıcılara sınav erişim linki oluşturur - Aynı kullanıcı ve sınav için her zaman aynı URL döndürür"""
        try:
            _logger.info("get_exam_access API çağrısı başladı")
            
            # API Key doğrula
            _logger.info("API key doğrulaması yapılıyor...")
            validate_api_key()
            _logger.info("API key doğrulaması başarılı")
            
            # POST JSON verisini al
            try:
                _logger.info("JSON request verisi ayrıştırılıyor...")
                data = json.loads(request.httprequest.data.decode('utf-8'))
                _logger.info(f"Alınan data: {data}")
            except json.JSONDecodeError as e:
                _logger.error(f"JSON ayrıştırma hatası: {str(e)}")
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': 'Geçersiz JSON formatı'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            user_id = data.get('user_id')
            exam_id = data.get('exam_id')
            _logger.info(f"İstenen user_id: {user_id}, exam_id: {exam_id}")
            
            if not user_id or not exam_id:
                _logger.error(f"Eksik parametreler: user_id={user_id}, exam_id={exam_id}")
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': 'Eksik parametreler: user_id ve exam_id gerekli'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Kullanıcıyı bul
            _logger.info(f"external_id={user_id} ile kullanıcı aranıyor...")
            user = request.env['res.users'].sudo().search([
                ('external_id', '=', user_id)
            ], limit=1)
            
            if not user:
                _logger.error(f"Kullanıcı bulunamadı: external_id={user_id}")
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': f'Kullanıcı bulunamadı: {user_id}'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            _logger.info(f"Kullanıcı bulundu: id={user.id}, login={user.login}, name={user.name}")
            
            # Sınavı bul
            _logger.info(f"ID={exam_id} ile sınav aranıyor...")
            try:
                exam_id_int = int(exam_id)
                _logger.info(f"Sınav ID integer olarak dönüştürüldü: {exam_id_int}")
            except ValueError as e:
                _logger.error(f"Sınav ID integer'a dönüştürülemedi: {str(e)}")
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': f'Geçersiz sınav ID formatı: {exam_id}'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
                
            exam = request.env['survey.survey'].sudo().search([
                ('id', '=', exam_id_int)
            ], limit=1)
            
            if not exam:
                _logger.error(f"Sınav bulunamadı: ID={exam_id}")
                return request.make_response(
                    json.dumps({
                        'success': False,
                        'error': f'Sınav bulunamadı: {exam_id}'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            _logger.info(f"Sınav bulundu: id={exam.id}, title={exam.title}, access_token={exam.access_token}")
            
            # Kullanıcıya ait partner'ı al
            partner = user.partner_id
            _logger.info(f"Kullanıcının partner bilgileri: id={partner.id}, name={partner.name}")
            
            # User Input (katılımcı) bulma/oluşturma - Sabit token için önemli değişiklikler burada
            _logger.info(f"Partner ID={partner.id} için sınav katılımcı girişi aranıyor/oluşturuluyor...")
            try:
                # Öncelikle, tüm durumlardaki (tamamlanmış dahil) kullanıcı girişlerini ara
                UserInput = request.env['survey.user_input'].sudo()
                
                # ÖNEMLİ DEĞİŞİKLİK: Herhangi bir durumdaki (new, in_progress, done) girişi ara
                existing_user_input = UserInput.search([
                    ('survey_id', '=', exam.id),
                    ('partner_id', '=', partner.id)
                ], limit=1, order="create_date desc")  # En son oluşturulanı al
                
                if existing_user_input:
                    _logger.info(f"Mevcut sınav girişi bulundu: id={existing_user_input.id}, state={existing_user_input.state}")
                    user_input = existing_user_input
                    
                    # Tamamlanmış bir giriş ise, sınav tekrarı için eski girişi kullan
                    if user_input.state == 'done':
                        _logger.info("Tamamlanmış sınav girişi bulundu, ancak tutarlılık için aynı erişim token'ı kullanılacak")
                else:
                    _logger.info("Sınav girişi bulunamadı, yeni giriş oluşturuluyor...")
                    user_input = UserInput.create({
                        'survey_id': exam.id,
                        'partner_id': partner.id,
                        'email': user.email,
                        'state': 'new'
                    })
                    _logger.info(f"Yeni sınav girişi oluşturuldu: id={user_input.id}")
                
                access_token = user_input.access_token
                _logger.info(f"Erişim tokeni alındı: {access_token}")
                
            except Exception as e:
                _logger.error(f"Sınav katılımcı girişi işlemi hatası: {str(e)}", exc_info=True)
                raise
            
            # Erişim URL'si oluştur - Doğru formatta!
            _logger.info("Base URL alınıyor...")
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            _logger.info(f"Base URL: {base_url}")
            
            # DOĞRU URL FORMATI: /survey/start/[survey_token]?answer_token=[user_input_token]
            start_url = f"{base_url}/survey/start/{exam.access_token}?answer_token={access_token}"
            _logger.info(f"Oluşturulan sınav erişim URL'si: {start_url}")
            
            response_data = {
                'success': True,
                'data': {
                    'user_id': user_id,
                    'exam_id': exam_id,
                    'exam_title': exam.title,
                    'access_token': access_token,
                    'start_url': start_url
                }
            }
            _logger.info(f"Başarılı yanıt hazırlandı: {response_data}")
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Unauthorized as e:
            _logger.error(f"Yetkilendirme hatası: {str(e)}")
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=401
            )
        except Exception as e:
            _logger.error(f"Sınav erişim hatası: {str(e)}", exc_info=True)
            return request.make_response(
                json.dumps({
                    'success': False,
                    'error': 'Sunucu hatası',
                    'message': str(e)
                }),
                headers=[('Content-Type', 'application/json')],
                status=500
            )