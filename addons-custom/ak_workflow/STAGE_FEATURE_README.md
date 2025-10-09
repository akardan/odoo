# Workflow Transition Stages (Aşamalı Onay) Özelliği

## Genel Bakış

Bu özellik, workflow transition'larına çok aşamalı onay süreci eklemenizi sağlar. Bir transition'dan diğerine geçerken birden fazla aşamadan (stage) geçmesi gereken süreçler için idealdir.

## Özellikler

### 1. Transition Stage Modeli (`ak.workflow.transition.stage`)

Her stage şunları içerir:
- **Temel Bilgiler**: İsim, kod, açıklama, sıra
- **Onaylayıcı Yapılandırması**:
  - Belirli kullanıcı
  - Kullanıcı grubu
  - Rol/Pozisyon
  - Alan değeri (kayıttaki bir kullanıcı alanı)
- **Koşullar**: Python expression, alan koşulu, metod koşulu
- **UI Yapılandırması**: Buton etiketi, stil, ikon
- **Bildirimler**: E-posta şablonu
- **Aksiyonlar**: Stage tamamlandığında çalışacak aksiyonlar

### 2. Çalışma Mantığı

#### Aşamasız Transition (Mevcut Davranış)
```
State A --[Transition]--> State B
```
Direkt geçiş yapılır.

#### Aşamalı Transition (Yeni Özellik)
```
State A --[Transition]
    ├─> Stage 1: Review (Grup: Reviewers)
    ├─> Stage 2: İlk Onay (Grup: Managers)
    └─> Stage 3: Son Onay (Kullanıcı: CEO)
--> State B
```

Her stage sırayla tamamlanmalıdır. Son stage tamamlandığında hedef state'e geçiş yapılır.

### 3. Kullanım Örneği

#### Satın Alma Onay Süreci

**Transition**: "Taslak" → "Onaylandı"

**Stages**:
1. **Review** (Sequence: 10)
   - Approver Type: Group
   - Group: Satın Alma Uzmanları
   - Condition: amount_total > 0

2. **İlk Onay** (Sequence: 20)
   - Approver Type: Group
   - Group: Satın Alma Müdürleri
   - Condition: amount_total > 1000

3. **Son Onay** (Sequence: 30)
   - Approver Type: User
   - User: Genel Müdür
   - Condition: amount_total > 10000

### 4. Teknik Detaylar

#### Yeni Modeller
- `ak.workflow.transition.stage`: Stage tanımları
- History modeline `stage_id` alanı eklendi

#### Güncellenmiş Modeller
- `ak.workflow.transition`: 
  - `stage_ids` (One2many)
  - `stage_count` (Computed)
  - `has_stages` (Computed)
  - `get_next_pending_stage()` metodu
  - `are_all_stages_completed()` metodu
  - Güncellenmiş `execute_on_record()` metodu

- `ak.workflow.transition.history`:
  - `stage_id` alanı eklendi
  - `status` alanına 'pending' seçeneği eklendi

- `ak.workflow.action`:
  - `stage_id` alanı eklendi (stage'e özel aksiyonlar için)

#### Execution Flow

```python
# Transition çalıştırıldığında
if transition.has_stages:
    next_stage = transition.get_next_pending_stage(record)
    if next_stage:
        next_stage.execute_stage(record, comment)
        
        if transition.are_all_stages_completed(record):
            # Tüm stage'ler tamamlandı
            record.workflow_current_state_id = transition.to_state_id
            # Ana transition aksiyonlarını çalıştır
        else:
            # Henüz tamamlanmamış stage'ler var
            # Kullanıcıya bilgi ver
else:
    # Stage yoksa direkt geçiş
    record.workflow_current_state_id = transition.to_state_id
```

### 5. View Yapısı

#### Transition Form View
- Yeni "Aşamalar" (Stages) sekmesi eklendi
- Stage'leri inline tree view ile yönetme
- Sürükle-bırak ile sıralama (sequence)

#### Stage Form View
- Tam özellikli stage yapılandırması
- Onaylayıcı tipi seçimi
- Koşul tanımlama
- UI özelleştirme
- Bildirim ayarları
- Aksiyon tanımlama

### 6. Güvenlik

`ir.model.access.csv` dosyasına eklenen kayıtlar:
- `access_ak_workflow_transition_stage_user`: Normal kullanıcılar için okuma/yazma
- `access_ak_workflow_transition_stage_manager`: Sistem yöneticileri için tam yetki

### 7. Kurulum

1. Modülü güncelle:
```bash
odoo-bin -u ak_workflow -d your_database
```

2. Veya Odoo arayüzünden:
   - Apps → AK Workflow → Upgrade

### 8. Kullanım Adımları

1. **Workflow Tanımı Oluştur**
   - Workflow → Definitions → Create

2. **State'leri Tanımla**
   - Workflow içinde state'leri ekle

3. **Transition Oluştur**
   - From State ve To State seç
   - "Aşamalar" sekmesine git

4. **Stage'leri Ekle**
   - Her stage için:
     - İsim ver (örn: "İlk Onay")
     - Sequence belirle (10, 20, 30...)
     - Approver Type seç
     - Onaylayıcıları belirle
     - İsteğe bağlı koşullar ekle

5. **Test Et**
   - Workflow'u bir kayda ata
   - Transition'ı çalıştır
   - Her stage'i sırayla tamamla

## Avantajlar

✅ **Esneklik**: Her stage için farklı onaylayıcılar ve koşullar
✅ **Şeffaflık**: Her stage tamamlanması history'de kaydedilir
✅ **Kontrol**: Stage bazlı aksiyonlar ve bildirimler
✅ **Geriye Uyumluluk**: Mevcut stage'siz transition'lar çalışmaya devam eder
✅ **Jenerik Yapı**: Sub-transition mantığı ile her türlü süreç modellenebilir

## Notlar

- Stage'ler sequence'a göre sırayla çalıştırılır
- Bir stage atlanamaz, sırayla tamamlanmalıdır
- Stage yoksa transition direkt çalışır (mevcut davranış)
- Her stage tamamlanması history'de ayrı kayıt oluşturur
- Stage'e özel aksiyonlar tanımlanabilir