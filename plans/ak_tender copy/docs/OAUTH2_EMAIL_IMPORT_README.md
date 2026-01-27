# OAuth2 Email Import - Microsoft Graph API Entegrasyonu

## Genel Bakış

Bu dokümantasyon, `import_sat_from_email` fonksiyonunun Microsoft OAuth2 authentication kullanarak nasıl çalıştığını açıklar.

Microsoft'un "Improving Security - Together" kapsamında, Basic Authentication (kullanıcı adı-şifre) kullanımı devre dışı bırakılmıştır. Bu nedenle, email okuma işlemleri için Microsoft Graph API ve OAuth2 authentication kullanılması zorunludur.

## Microsoft'un Güvenlik Değişiklikleri

### Zaman Çizelgesi
- **2022 Aralık**: Eski Microsoft 365 panellerde Basic Auth hala çalışıyordu
- **2023**: Yeni tenantlarda Basic Auth devre dışı bırakıldı
- **2023 Sonu**: Tüm alanlarda Basic Auth kullanılamaz hale geldi

### Yeni Yöntem
Microsoft Entra (eski adıyla Azure AD) üzerinde uygulama oluşturup, gerekli yetkileri tanımlamak ve oluşturulan uygulamanın ayarlarını yazılımlara tanımlamak gerekiyor.

## Azure AD Yapılandırması

### Gerekli Bilgiler

Azure AD'den aşağıdaki bilgileri almanız gerekmektedir:

```
- Client ID (Application ID): [Azure Portal'dan alınacak]
- Client Secret (Gizli Dizi): [Azure Portal'dan alınacak]
- Tenant ID (Kiracı Kimliği): [Azure Portal'dan alınacak]
- Email Adresi: [Kullanılacak email adresi]
```

### Sistem Parametreleri

Bu bilgiler Odoo'da sistem parametreleri olarak saklanır:

1. **Settings > Technical > Parameters > System Parameters** menüsüne gidin
2. Aşağıdaki parametreleri oluşturun veya güncelleyin:

| Key | Value | Açıklama |
|-----|-------|----------|
| `ak_tender.azure_client_id` | [Azure Application (Client) ID] | Azure Application (Client) ID |
| `ak_tender.azure_client_secret` | [Azure Client Secret] | Azure Client Secret |
| `ak_tender.azure_tenant_id` | [Azure Tenant ID] | Azure Tenant ID |
| `ak_tender.email_user` | [Email adresi] | Email kullanıcısı |

**NOT**: Bu parametreler `data/azure_config_data.xml` dosyasında boş olarak tanımlanmıştır. Gerçek değerleri Odoo arayüzünden manuel olarak girmeniz gerekmektedir.

## Teknik Detaylar

### Kullanılan Kütüphaneler

1. **msal** (Microsoft Authentication Library)
   - OAuth2 token almak için kullanılır
   - Otomatik olarak yüklenir (runtime'da)

2. **requests**
   - Microsoft Graph API'ye HTTP istekleri yapmak için kullanılır
   - Otomatik olarak yüklenir (runtime'da)

### OAuth2 Flow

```python
# 1. Access Token Al
def _get_microsoft_access_token(self):
    # MSAL kullanarak token al
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}"
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    return result["access_token"]

# 2. Microsoft Graph API ile Email Oku
def import_sat_from_email(self):
    access_token = self._get_microsoft_access_token()
    
    # Graph API endpoint
    graph_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages"
    
    # Headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Okunmamış emailleri filtrele
    params = {
        '$filter': "isRead eq false and contains(subject, 'ME5A Günlük Rapor Sonuçları')",
        '$select': 'id,subject,from,receivedDateTime,hasAttachments',
    }
    
    response = requests.get(graph_url, headers=headers, params=params)
    messages = response.json().get('value', [])
```

### Microsoft Graph API Endpoints

1. **Email Listesi**: `GET /users/{email}/messages`
   - Okunmamış emailleri filtreler
   - Konu içeriğine göre arama yapar

2. **Email Ekleri**: `GET /users/{email}/messages/{messageId}/attachments`
   - Email eklerini alır
   - Base64 encoded içerik döner

3. **Email Güncelleme**: `PATCH /users/{email}/messages/{messageId}`
   - Email'i okundu olarak işaretler

## Kullanım

### Manuel Çalıştırma

Python shell'den:

```python
# Odoo shell'e gir
odoo-bin shell -d your_database

# Import fonksiyonunu çalıştır
env['import.sat.wizard'].import_sat_from_email()
```

### Otomatik Çalıştırma (Cron Job)

Modül zaten bir cron job içeriyor (`data/email_import_cron.xml`):

- **İsim**: SAT Email Import
- **Sıklık**: Her gün 08:00'de çalışır
- **Fonksiyon**: `import_sat_from_email()`

Cron job'u kontrol etmek için:
1. **Settings > Technical > Automation > Scheduled Actions** menüsüne gidin
2. "SAT Email Import" kaydını bulun
3. Gerekirse sıklığı değiştirin

## İşleyiş Akışı

1. **OAuth2 Token Al**
   - Azure AD'den access token alınır
   - Token 1 saat geçerlidir

2. **Email Listesi Al**
   - Okunmamış emailleri filtreler
   - "ME5A Günlük Rapor Sonuçları" konulu emailleri bulur

3. **Her Email İçin**
   - Email eklerini kontrol et
   - "ME5A Günlük Rapor Sonuçları.ZIP" dosyasını bul
   - ZIP içindeki Excel dosyasını çıkar
   - SAT verilerini import et
   - Email'i okundu olarak işaretle

4. **İstatistik Döndür**
   - İşlenen email sayısı
   - Oluşturulan/güncellenen kayıt sayıları
   - Hata sayısı

## Hata Ayıklama

### Log Kontrol

```bash
# Odoo log dosyasını takip et
tail -f /var/log/odoo/odoo.log | grep -i "email\|oauth\|graph"
```

### Yaygın Hatalar

1. **Token Alınamıyor**
   - Azure credentials'ları kontrol edin
   - Tenant ID doğru mu?
   - Client Secret süresi dolmuş olabilir

2. **Email Okunamıyor**
   - Email kullanıcısı doğru mu?
   - Graph API permissions verilmiş mi?
   - Email kutusunda erişim var mı?

3. **Kütüphane Hatası**
   - `msal` ve `requests` yüklü mü?
   - Manuel yükleme: `pip install msal requests`

## Güvenlik Notları

1. **Client Secret Güvenliği**
   - Client Secret'ı güvenli bir şekilde saklayın
   - Düzenli olarak yenileyin (Microsoft önerisi: 6 ayda bir)
   - Asla version control'e commit etmeyin

2. **Permissions**
   - Sadece gerekli Graph API permissions'ları verin
   - Minimum privilege principle'ı uygulayın

3. **Token Yönetimi**
   - Token'lar otomatik olarak yenilenir
   - Token cache kullanılmaz (her seferinde yeni token alınır)

## Referanslar

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/auth-register-app-v2)
- [Basic Authentication Deprecation](https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/deprecation-of-basic-authentication-exchange-online)
- [Improving Security Together](https://techcommunity.microsoft.com/t5/exchange-team-blog/improving-security-together/ba-p/805892)
- [MSAL Python Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-python)

## Destek

Sorunlar için:
1. Log dosyalarını kontrol edin
2. Azure AD portal'da uygulama ayarlarını kontrol edin
3. System Parameters'ı doğrulayın
4. Gerekirse Kardan.Digital ile iletişime geçin

---

**Son Güncelleme**: 2025-10-31
**Versiyon**: 1.0
**Yazar**: Kardan.Digital