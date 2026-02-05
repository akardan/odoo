# Sistem Yöneticisi Kullanıcı Kılavuzu

**Versiyon:** 1.0  
**Tarih:** 3 Şubat 2026  
**Hedef Kullanıcı:** Sistem Yöneticileri, IT Ekibi

---

## 📋 İçindekiler

1. [Sistem Yapılandırması](#1-sistem-yapılandırması)
2. [Kullanıcı Yönetimi](#2-kullanıcı-yönetimi)
3. [Entegrasyon Ayarları](#3-entegrasyon-ayarları)
4. [Ekonomik Veri Yönetimi](#4-ekonomik-veri-yönetimi)
5. [İhale Tipi Kuralları](#5-ihale-tipi-kuralları)
6. [Email Yapılandırması](#6-email-yapılandırması)
7. [Yedekleme ve Bakım](#7-yedekleme-ve-bakım)
8. [Sorun Giderme](#8-sorun-giderme)
9. [Güvenlik ve İzleme](#9-güvenlik-ve-izleme)
10. [Performans Optimizasyonu](#10-performans-optimizasyonu)

---

## 1. Sistem Yapılandırması

### 1.1 Sistem Parametreleri

#### Parametrelere Erişim

```
Settings → Technical → Parameters → System Parameters
```

#### Gerekli Parametreler

| Parametre | Açıklama | Örnek Değer |
|-----------|----------|-------------|
| `ak_tender.azure_client_id` | Azure Application ID | abc123-def456-... |
| `ak_tender.azure_client_secret` | Azure Client Secret | XYZ789... |
| `ak_tender.azure_tenant_id` | Azure Tenant ID | tenant-id-123 |
| `ak_tender.email_user` | Email kullanıcısı | ilkoisdata@ilko.com.tr |
| `ak_tender.system_email` | Sistem email adresi | ilkois@ilko.com.tr |

#### Parametre Ekleme

1. **Create** butonuna tıklayın
2. **Key** alanına parametre adını girin
3. **Value** alanına değeri girin
4. **Save** butonuna tıklayın

### 1.2 Şirket Ayarları

#### Şirket Bilgilerini Yapılandırma

```
Settings → Users & Companies → Companies
```

**Yapılandırılacak Alanlar**:
- Şirket adı
- Logo
- Adres bilgileri
- Vergi numarası
- Varsayılan para birimi
- Zaman dilimi (Europe/Istanbul)

### 1.3 Para Birimleri

#### Para Birimi Aktivasyonu

```
Settings → Technical → Currencies
```

**Aktif Edilmesi Gerekenler**:
- TRY (Türk Lirası)
- USD (Amerikan Doları)
- EUR (Euro)
- GBP (İngiliz Sterlini)
- CHF (İsviçre Frangı)

#### Kur Güncelleme

1. Para birimi kaydını açın
2. **Update** butonuna tıklayın
3. Otomatik kur güncellenir

---

## 2. Kullanıcı Yönetimi

### 2.1 Kullanıcı Grupları

#### İhale Grupları

```
Settings → Users & Companies → Groups
```

**Mevcut Gruplar**:

| Grup | Teknik Ad | Yetkiler |
|------|-----------|----------|
| **Tender Requester** | `ak_tender.group_tender_requester` | Talep oluşturma |
| **Tender User** | `ak_tender.group_tender_user` | İhale oluşturma |
| **Tender Manager** | `ak_tender.group_tender_manager` | Tam yetki |

### 2.2 Yeni Kullanıcı Ekleme

#### Kullanıcı Oluşturma

1. **Settings → Users & Companies → Users** menüsüne gidin
2. **Create** butonuna tıklayın
3. Kullanıcı bilgilerini girin:

```
Ad: Ahmet Yılmaz
Email: ahmet.yilmaz@ilko.com.tr
Kullanıcı Adı: ahmet.yilmaz
```

4. **Access Rights** sekmesinde grupları seçin:
   - ✅ Tender User
   - ✅ Purchase / User
5. **Save** butonuna tıklayın

#### Şifre Sıfırlama

1. Kullanıcı kaydını açın
2. **Action → Send Password Reset Instructions** seçin
3. Kullanıcıya e-posta gönderilir

### 2.3 Tedarikçi Portal Erişimi

#### Portal Kullanıcısı Oluşturma

1. **Contacts** menüsünden tedarikçiyi açın
2. **Action → Grant Portal Access** seçin
3. Portal kullanıcısı otomatik oluşturulur
4. Tedarikçiye davet e-postası gönderilir

---

## 3. Entegrasyon Ayarları

### 3.1 Azure AD Yapılandırması

#### Azure Portal'da Uygulama Oluşturma

1. https://portal.azure.com adresine gidin
2. **Azure Active Directory → App registrations** seçin
3. **New registration** butonuna tıklayın
4. Uygulama bilgilerini girin:
   - Name: İLKOis Email Integration
   - Supported account types: Single tenant
5. **Register** butonuna tıklayın

#### API Permissions Ekleme

1. Oluşturulan uygulamayı açın
2. **API permissions → Add a permission** seçin
3. **Microsoft Graph → Application permissions** seçin
4. Gerekli izinleri ekleyin:
   - Mail.Read
   - Mail.ReadWrite
   - Mail.Send
5. **Grant admin consent** butonuna tıklayın

#### Client Secret Oluşturma

1. **Certificates & secrets → New client secret** seçin
2. Açıklama girin: "İLKOis Integration"
3. Süre seçin: 24 months
4. **Add** butonuna tıklayın
5. **Value** değerini kopyalayın (bir daha gösterilmez!)

#### Odoo'ya Bilgileri Girme

```
Settings → Technical → Parameters → System Parameters
```

- `ak_tender.azure_client_id`: Application (client) ID
- `ak_tender.azure_client_secret`: Client secret value
- `ak_tender.azure_tenant_id`: Directory (tenant) ID

### 3.2 SAT Email Import Yapılandırması

#### Cron Job Kontrolü

```
Settings → Technical → Automation → Scheduled Actions
```

**SAT Email Import** kaydını bulun:
- **Active**: ✅ İşaretli olmalı
- **Interval**: 1 Hours
- **Next Execution Date**: Kontrol edin

#### Manuel Test

1. Scheduled Action kaydını açın
2. **Run Manually** butonuna tıklayın
3. Log'ları kontrol edin

---

## 4. Ekonomik Veri Yönetimi

### 4.1 Ekonomik Veri Girişi

#### Menü Yolu

```
İhale → Konfigürasyon → Ekonomik Veriler
```

#### Yeni Ekonomik Veri Ekleme

1. **Create** butonuna tıklayın
2. Bilgileri girin:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| Para Birimi | Hangi para birimi | TRY |
| Güncel Kur | Otomatik hesaplanır | 1.0 |
| Enflasyon Oranı | TCMB/TÜİK | %65 |
| Faiz Oranı | TCMB politika faizi | %50 |
| NPV Oranı | Finans bölümü belirler | %60 |
| Veri Kaynağı | TCMB/TÜİK/Manuel | TCMB |
| Başlangıç Tarihi | Geçerlilik başlangıcı | 01.01.2024 |
| Bitiş Tarihi | Geçerlilik bitişi | 31.03.2024 |

3. **Save** butonuna tıklayın

### 4.2 NPV Oranı Belirleme

#### Finans Bölümü İşbirliği

NPV oranı belirleme süreci:

1. **Referans Göstergeleri Güncelle**:
   - TCMB politika faizi
   - TÜİK enflasyon oranı

2. **Finans Bölümü Değerlendirmesi**:
   - Referans göstergeler
   - Şirket risk politikaları
   - Para birimi bazında uygun NPV oranı

3. **Sisteme Girme**:
   - Ekonomik Veriler menüsünden
   - NPV Oranı alanına gir
   - Kaydet

---

## 5. İhale Tipi Kuralları

### 5.1 Kural Yönetimi

#### Menü Yapısı

```
İhale → Ayarlar → İhale Tipi Kuralları
├── İhale Tipi Matrisi
├── Özel Kurallar
├── Satınalma Grupları
├── Malzeme Grupları
└── Üretim Yerleri
```

### 5.2 Özel Kural Ekleme

#### Yeni Özel Kural

1. **İhale Tipi Kuralları → Özel Kurallar** menüsüne gidin
2. **Create** butonuna tıklayın
3. Kural bilgilerini girin:

```
Kural Adı: Hizmet Alımı (6XXX) → Indirect
Sequence: 10 (düşük = yüksek öncelik)
Malzeme Grubu Öneki: 6
İhale Tipi: indirect
Sorumlu: Ahmet/Bahar
Notlar: Tüm 6XXX kodlu malzemeler indirect
```

4. **Save** butonuna tıklayın

### 5.3 Satınalma Grubu Ekleme

1. **İhale Tipi Kuralları → Satınalma Grupları** menüsüne gidin
2. **Create** butonuna tıklayın
3. Grup bilgilerini girin:

```
Kod: 105
Ad: Ü