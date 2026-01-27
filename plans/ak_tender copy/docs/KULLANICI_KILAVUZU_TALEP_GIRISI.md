# Talep Girişi Kullanıcı Kılavuzu

## İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Talep Girişine Erişim](#talep-girişine-erişim)
3. [Yeni Talep Oluşturma](#yeni-talep-oluşturma)
4. [Talep Durumları](#talep-durumları)
5. [Talep Listeleme ve Filtreleme](#talep-listeleme-ve-filtreleme)
6. [Sık Sorulan Sorular](#sık-sorulan-sorular)

---

## Genel Bakış

**Talep Girişi** modülü, kullanıcıların manuel olarak satınalma talebi (Purchase Requisition) oluşturmasına olanak tanır. Bu modül, SAP'den otomatik olarak import edilen SAT (Satınalma Talebi) kayıtlarından bağımsız olarak, kullanıcıların kendi taleplerini sisteme girebilmelerini sağlar.

### Özellikler
- ✅ Basit ve kullanıcı dostu arayüz
- ✅ Çoklu ürün ekleme desteği
- ✅ Onay iş akışı (Draft → Onayda → Onaylandı)
- ✅ Departman bazlı takip
- ✅ İhale durumu takibi
- ✅ Notlar ve açıklamalar için alan

### Kim Kullanabilir?
- Tüm yetkili kullanıcılar talep oluşturabilir
- Sadece `Tender User` ve `Tender Manager` grupları talepleri onaylayabilir

---

## Talep Girişine Erişim

### Menü Yolu
```
Ana Menü → İhale Yönetimi → Talepler → Talep Girişi
```

veya

```
ak_tender → Talepler → Talep Girişi
```

### Menü ID Bilgileri
- **Menü ID:** `menu_purchase_requisition_manual`
- **Action ID:** `action_purchase_requisition_manual`
- **View:** `view_purchase_requisition_form_simple`

---

## Yeni Talep Oluşturma

### Adım 1: Yeni Talep Formu Açma

1. Menüden **Talepler → Talep Girişi** seçin
2. **Oluştur** butonuna tıklayın
3. Sistem otomatik olarak yeni bir talep numarası oluşturur

### Adım 2: Temel Bilgileri Girme

#### Talep Eden Bilgileri
- **Talep Eden:** Varsayılan olarak giriş yapan kullanıcı seçilir (değiştirilebilir)
- **Departman:** Talep edenin departmanı
- **Talep Tarihi:** Talebin oluşturulma tarihi (varsayılan: bugün)

> 💡 **Not:** Bu alanlar sadece "Taslak" durumundayken düzenlenebilir.

### Adım 3: Ürün Ekleme

#### Ürünler Sekmesi
Ürün eklemek için:

1. **Ürünler** sekmesine gidin
2. Satır ekle butonu ile yeni satır oluşturun
3. Her ürün için aşağıdaki bilgileri girin:

| Alan | Açıklama | Zorunlu |
|------|----------|---------|
| **Ürün (Product)** | Talep edilen ürün | ✅ Evet |
| **Miktar (Quantity)** | İstenen miktar | ✅ Evet |
| **Birim (UoM)** | Ölçü birimi (Adet, Kg, vb.) | ✅ Evet |
| **Hesap Atama Tipi** | Muhasebe atama türü | ❌ Hayır |
| **Durum** | Otomatik - Kalem işlenme durumu | - |
| **İhale Durumu** | Otomatik - İhaleye bağlıysa durumu | - |

#### Ürün Ekleme Örneği
```
Ürün: Yazıcı Kartuşu HP 305A (Siyah)
Miktar: 10
Birim: Adet
```

> ⚠️ **Önemli:** Birden fazla ürün ekleyebilirsiniz. Liste görünümünde alt alta sıralanacaktır.

### Adım 4: Açıklama ve Notlar

**Açıklama Alanı** (Ürünler sekmesi altında):
- Talebinizle ilgili ek bilgiler girebilirsiniz
- Özel talimatlar, tercih edilen tedarikçi, vb.
- Bu alan sadece taslak durumunda düzenlenebilir

Örnek açıklama:
```
Acil ihtiyaç - Stoklar kritik seviyede
Mümkünse XYZ Tedarikçiden alınması tercih edilir
Teslim adresi: Merkez Depo
```

### Adım 5: Onaya Gönderme

1. Tüm bilgileri girdikten sonra **Kaydet** butonuna tıklayın
2. **Onaya Gönder** butonuna tıklayın
3. Talep durumu **"Taslak"** → **"Onayda"** olarak değişir

> 💡 **Not:** Onaya gönderdikten sonra talep düzenlenemez.

---

## Talep Durumları

Talep girişi 3 temel durumdan oluşur:

### 1. 📝 Taslak (Draft)
- **Ne Demek:** Talep henüz oluşturulma aşamasında
- **Kim Düzenleyebilir:** Talep sahibi
- **Yapılabilecekler:**
  - Ürün ekleme/çıkarma/düzenleme
  - Talep bilgilerini değiştirme
  - Açıklama güncelleme
- **Eylem:** "Onaya Gönder" butonu ile bir sonraki aşamaya geçer

### 2. ⏳ Onayda (In Progress)
- **Ne Demek:** Talep onay bekliyor
- **Kim Düzenleyebilir:** Kimse (salt okunur)
- **Yapılabilecekler:**
  - Sadece görüntüleme
  - Onaylayanlar "Onayla" veya "Reddet" işlemi yapabilir
- **Eylem:** Yetkili kullanıcı "Onayla" butonuna tıklar

### 3. ✅ Onaylandı (Done)
- **Ne Demek:** Talep onaylanmış, ihale sürecine alınabilir
- **Kim Düzenleyebilir:** Kimse (salt okunur)
- **Yapılabilecekler:**
  - Talep kalemleri otomatik olarak SAT Havuzuna eklenir
  - İhale oluşturma sürecine dahil edilir
  - İhale durumu takip edilebilir

### Durum Geçişi Akışı
```
[Taslak] 
   ↓ (Onaya Gönder)
[Onayda] 
   ↓ (Onayla - Sadece Yetkili Kullanıcılar)
[Onaylandı]
```

---

## Talep Listeleme ve Filtreleme

### Liste Görünümü

Talep Girişi menüsünü açtığınızda tüm talepler liste halinde görünür:

| Sütun | Açıklama |
|-------|----------|
| **Talep No** | Otomatik oluşturulan talep numarası |
| **SAT No** | SAP'den geliyorsa SAT numarası (manuel talepler için boş) |
| **Talep Eden** | Talebi oluşturan kullanıcı |
| **Durum** | Taslak / Onayda / Onaylandı |
| **Toplam Kalem** | Talepteki ürün sayısı |
| **İşlenen** | İhaleye alınmış kalem sayısı |
| **İhale Grupları** | Hangi ihale gruplarına dahil |

### Filtreleme

Liste görünümünde arama ve filtreleme yapabilirsiniz:

**Arama Çubuğu:**
- Talep numarasına göre arama
- Talep eden kişiye göre arama
- Ürün adına göre arama

**Filtreler:**
- Durum bazlı filtreleme (Taslak, Onayda, Onaylandı)
- Tarih bazlı filtreleme
- Departman bazlı filtreleme

### Grup Bazlı Görünüm
- Duruma göre grupla
- Talep edene göre grupla
- Departmana göre grupla

---

## Sık Sorulan Sorular

### S1: Onaya gönderdikten sonra talep düzenleyebilir miyim?
**C:** Hayır. Talep "Onayda" veya "Onaylandı" durumuna geçtikten sonra düzenlenemez. Eğer değişiklik gerekiyorsa, yeni bir talep oluşturmanız gerekir.

### S2: Talebimi nasıl iptal edebilirim?
**C:** Şu anda iptal butonu bulunmamaktadır. Taslak durumundayken talebi silebilirsiniz. Onaya gönderdiyseniz, sistem yöneticisiyle iletişime geçin.

### S3: Talep onaylandıktan sonra ne olur?
**C:** Onaylandıktan sonra talep kalemleri SAT Havuzuna eklenir ve ihale oluşturma sürecine dahil edilir. "SAT Kalemleri" menüsünden görüntüleyebilirsiniz.

### S4: Birden fazla ürün ekleyebilir miyim?
**C:** Evet. İstediğiniz kadar ürün satırı ekleyebilirsiniz.

### S5: Hangi durumda "İhale Durumu" alanı dolar?
**C:** Talep kaleminiz bir ihaleye dahil edildiğinde, o ihalenin durumu bu alanda görünür.

### S6: SAP'den gelen SAT ile manuel talep arasındaki fark nedir?
**C:** 
- **SAP SAT:** `erp_pr_id` alanı dolu, SAP'den otomatik import edilir
- **Manuel Talep:** `erp_pr_id` alanı boş, kullanıcı tarafından sisteme girilir
- Her iki tipte de aynı ihale sürecine dahil edilebilir

### S7: "SAT No" alanı neden boş?
**C:** Manuel olarak girilen taleplerde SAT No alanı boş kalır. Bu alan sadece SAP'den gelen kayıtlar için doldurulur.

### S8: Oluşturduğum talepleri nasıl bulabilirim?
**C:** Liste görünümünde "Talep Eden" kolonuna göre filtreleme yapabilir veya arama çubuğunda kendi adınızı aratabilirsiniz.

### S9: Talep güncelleme bildirimi alabilir miyim?
**C:** Evet, Chatter (sohbet) özelliği sayesinde taleple ilgili tüm aktiviteler ve mesajlar kaydedilir. Takipçi olarak eklenirseniz bildirim alırsınız.

### S10: Acil talep için nasıl işaretleme yapabilirim?
**C:** Açıklama kısmında "ACİL" veya "URGENT" yazabilirsiniz. İleride aciliyet opsiyonu eklenebilir.

---

## İlgili Modüller ve Menüler

### SAT Kalemleri
Onaylanan talep kalemleri burada görünür ve ihale oluşturmak için kullanılabilir.
- **Menü:** Talepler → SAT Kalemleri
- **İşlev:** İhale oluşturma, filtreleme, gruplandırma

### SAT Başlıkları
SAP'den import edilen SAT başlıkları burada listelenir.
- **Menü:** Talepler → SAT Başlıkları
- **İşlev:** SAP kayıtlarını görüntüleme, ihale oluşturma

### Otomatik İhale Oluştur
Tüm uygun SAT kalemlerinden otomatik ihale oluşturur.
- **Menü:** Talepler → Otomatik İhale Oluştur
- **İşlev:** Toplu ihale oluşturma işlemi

---

## Teknik Detaylar

### Model
- **Model Adı:** `purchase.requisition`
- **Form View ID:** `view_purchase_requisition_form_simple`
- **Tree View ID:** `view_purchase_requisition_tree`

### Domain Filtresi
```python
[('erp_pr_id', '=', False)]  # Sadece manuel talepleri gösterir
```

### Güvenlik Grupları
- **Talep Oluşturma:** Tüm kullanıcılar
- **Talep Onaylama:** 
  - `ak_tender.group_tender_user`
  - `ak_tender.group_tender_manager`

### Alanlar

#### Başlık Alanları
- `name`: Talep numarası (otomatik)
- `user_id`: Talep eden kullanıcı
- `department_id`: Departman
- `date_start`: Talep tarihi
- `state`: Durum (draft/in_progress/done)
- `description`: Açıklama
- `erp_pr_id`: SAP SAT No (manuel taleplerde boş)

#### Satır Alanları (line_ids)
- `product_id`: Ürün
- `product_qty`: Miktar
- `product_uom_id`: Ölçü birimi
- `line_processing_status`: İşlenme durumu
- `tender_state`: İhale durumu
- `account_assignment_type`: Hesap atama tipi

---

## Değişiklik Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 1.0 | 2026-01-12 | İlk kullanıcı kılavuzu oluşturuldu |

---

## Destek ve İletişim

Sorunlar veya sorular için:
- Sistem yöneticinize başvurun
- Geliştirme ekibiyle iletişime geçin
- Talep takip sisteminizden destek talebi oluşturun

---

**Son Güncelleme:** 12 Ocak 2026  
**Belge Sahibi:** İhale Yönetimi Modülü  
**Versiyon:** 1.0
