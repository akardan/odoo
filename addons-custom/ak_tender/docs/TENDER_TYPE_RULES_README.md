# İhale Tipi Belirleme Kuralları Sistemi

## Genel Bakış

Bu sistem, SAP verilerinden (Malzeme Grubu, Satınalma Grubu, Üretim Yeri) otomatik olarak ihale tipini belirlemek için geliştirilmiş model tabanlı bir çözümdür.

## Özellikler

### 1. Model Tabanlı Kural Yönetimi
- Kullanıcı dostu arayüz ile kuralları yönetme
- Kod değişikliği gerektirmeden kural güncelleme
- Dinamik öncelik sıralaması

### 2. Öncelik Sırası

Sistem aşağıdaki öncelik sırasına göre ihale tipini belirler:

1. **Özel Kurallar** (En yüksek öncelik)
   - 6XXX (Hizmet Alımları) → DAIMA indirect
   - 9XXX + PG:110 (Bakım Yedek Parça) → indirect
   - 9XXX + Direct Gruplar (Üretim Yedek Parça) → direct

2. **Satınalma Grubu**
   - Direct Gruplar: 105, 107, 108, 110, 114, 116, 120, 201
   - Indirect Gruplar: 101, 103, 111, 112, 113, 115, 118, 121, 122, 303, 308
   - Promotion: 104
   - MICE: 600
   - R&D: 109

3. **Malzeme Grubu**
   - 1XXX, 2XXX, 3XXX, 4XXX → direct
   - 5XXX, 7XXX → promotion
   - 6XXX, 8XXX, 9XXX → indirect

4. **Üretim Yeri**
   - 2100 (İlko) → direct
   - 2000 (Merkez), 1100 (İlkopol) → indirect

5. **Varsayılan**
   - indirect

## Modeller

### 1. tender.type.material.group
Malzeme gruplarını ve varsayılan ihale tiplerini tanımlar.

**Alanlar:**
- `code`: SAP Malzeme Grubu Kodu (örn: 1000, 6000)
- `name`: Grup Adı
- `default_tender_type`: Varsayılan İhale Tipi
- `description`: Açıklama

### 2. tender.type.purchasing.group
Satınalma gruplarını ve ihale tiplerini tanımlar.

**Alanlar:**
- `code`: SAP Satınalma Grubu Kodu (örn: 105, 110)
- `name`: Grup Adı
- `tender_type`: İhale Tipi
- `responsible_names`: Sorumlu Kişiler
- `responsible_user_ids`: Sorumlu Kullanıcılar

### 3. tender.type.special.rule
Özel durumlar için kurallar tanımlar.

**Alanlar:**
- `name`: Kural Adı
- `sequence`: Öncelik (düşük numara = yüksek öncelik)
- `material_group_prefix`: Malzeme Grubu Öneki (örn: 6, 9)
- `purchasing_group_code`: Satınalma Grubu Kodu (örn: 110)
- `tender_type`: Sonuç İhale Tipi
- `responsible_names`: Sorumlu Kişiler
- `notes`: Notlar

### 4. tender.type.production.location
Üretim yerlerini ve varsayılan ihale tiplerini tanımlar.

**Alanlar:**
- `code`: SAP Üretim Yeri Kodu (örn: 2100, 2000)
- `name`: Yer Adı
- `default_tender_type`: Varsayılan İhale Tipi

### 5. tender.type.matrix
Tüm kuralları birleştiren ana model.

**Metod:**
```python
determine_tender_type(material_group, purchasing_group, production_location)
```

**Dönüş Değeri:**
```python
{
    'tender_type': str,      # 'direct', 'indirect', 'promotion', 'mice'
    'responsible': str,      # Sorumlu kişi/ekip
    'decision_source': str,  # Karar kaynağı
    'notes': list           # Açıklama notları
}
```

## Kullanım

### Menü Yapısı

```
İhaleler
└── Ayarlar
    └── İhale Tipi Kuralları
        ├── İhale Tipi Matrisi (Tüm kuralları görüntüle)
        ├── Özel Kurallar
        ├── Satınalma Grupları
        ├── Malzeme Grupları
        └── Üretim Yerleri
```

### Yeni Kural Ekleme

#### 1. Özel Kural Eklemek
```
İhaleler → Ayarlar → İhale Tipi Kuralları → Özel Kurallar → Oluştur
```

**Örnek:**
- Kural Adı: "Hizmet Alımı (6XXX) → Indirect"
- Malzeme Grubu Öneki: 6
- İhale Tipi: indirect
- Sorumlu: Ahmet/Bahar

#### 2. Satınalma Grubu Eklemek
```
İhaleler → Ayarlar → İhale Tipi Kuralları → Satınalma Grupları → Oluştur
```

**Örnek:**
- Kod: 105
- Ad: Üretim Satınalma
- İhale Tipi: direct
- Sorumlu: Gülcan/Eda/Peri

#### 3. Malzeme Grubu Eklemek
```
İhaleler → Ayarlar → İhale Tipi Kuralları → Malzeme Grupları → Oluştur
```

**Örnek:**
- Kod: 1000
- Ad: Etken Madde
- Varsayılan İhale Tipi: direct

### Kural Güncelleme

1. İlgili menüden kaydı açın
2. Gerekli alanları güncelleyin
3. Kaydedin

### Kural Devre Dışı Bırakma

Her kayıtta `Active` alanı bulunur. Bu alanı kapatarak kuralı devre dışı bırakabilirsiniz.

## SAT İçe Aktarma Entegrasyonu

SAT dosyası içe aktarılırken, sistem otomatik olarak:

1. Malzeme Grubu, Satınalma Grubu ve Üretim Yeri bilgilerini alır
2. `tender.type.matrix.determine_tender_type()` metodunu çağırır
3. Dönen sonuca göre ihale tipini belirler
4. Karar kaynağını ve notları ihale açıklamasına ekler

**Örnek Log:**
```
Tender type determined: indirect (Source: special_rule_1) 
for SAT: 4500123456, MG: 6000-03, PG: 114, PL: 2100
```

## Güvenlik

### Erişim Hakları

- **Kullanıcılar (base.group_user)**: Okuma
- **İhale Yöneticileri (ak_tender.group_tender_manager)**: Tam Erişim

## Veri Dosyaları

### data/tender_type_rules_data.xml

Bu dosya, sistemin başlangıç verilerini içerir:
- 9 Malzeme Grubu
- 21 Satınalma Grubu
- 3 Özel Kural
- 3 Üretim Yeri

**Not:** `noupdate="1"` olduğu için, bu veriler sadece ilk kurulumda yüklenir. Sonraki güncellemelerde değişmez.

## Örnekler

### Örnek 1: Hizmet Alımı
```python
result = matrix.determine_tender_type(
    material_group='6000-03',
    purchasing_group='114',
    production_location='2100'
)
# Sonuç: {'tender_type': 'indirect', 'decision_source': 'special_rule_1', ...}
```

### Örnek 2: Üretim Malzemesi
```python
result = matrix.determine_tender_type(
    material_group='1000-01',
    purchasing_group='105',
    production_location='2100'
)
# Sonuç: {'tender_type': 'direct', 'decision_source': 'purchasing_group', ...}
```

### Örnek 3: Bakım Yedek Parçası
```python
result = matrix.determine_tender_type(
    material_group='9000-01',
    purchasing_group='110',
    production_location='2100'
)
# Sonuç: {'tender_type': 'indirect', 'decision_source': 'special_rule_2', ...}
```

## Sorun Giderme

### Problem: Yanlış ihale tipi belirleniyor

**Çözüm:**
1. İhale Tipi Matrisi'ni açın
2. İlgili kuralları kontrol edin
3. Öncelik sırasını gözden geçirin
4. Gerekirse özel kural ekleyin

### Problem: Kural çalışmıyor

**Çözüm:**
1. Kuralın `Active` olduğunu kontrol edin
2. Özel kurallarda `sequence` değerini kontrol edin (düşük = yüksek öncelik)
3. Koşulların doğru girildiğini kontrol edin

### Problem: Varsayılan değer kullanılıyor

**Çözüm:**
1. SAP verilerinin doğru geldiğini kontrol edin
2. İlgili malzeme/satınalma grubu tanımlı mı kontrol edin
3. Log kayıtlarını inceleyin

## Geliştirme Notları

### Yeni İhale Tipi Eklemek

1. Model tanımlarında `Selection` alanlarına yeni tipi ekleyin
2. View'larda filtreleri güncelleyin
3. Veri dosyasında örnek kayıtlar ekleyin

### Yeni Koşul Eklemek

1. `tender.type.special.rule` modeline yeni alan ekleyin
2. `determine_tender_type()` metodunda koşul kontrolünü ekleyin
3. View'ları güncelleyin

## Versiyon Geçmişi

- **v1.0** (2024-10-31): İlk sürüm
  - Model tabanlı kural sistemi
  - Özel kurallar desteği
  - SAT entegrasyonu

## Destek

Sorularınız için: support@kardan.digital