# Agile Proje Yönetimi Modülü - Fonksiyonel Spesifikasyon

**Versiyon:** 18.0.1.0  
**Yazar:** Kardan Digital  
**Tarih:** 01.06.2025

## 1. Genel Bakış

Agile Proje Yönetimi modülü, Odoo'nun standart proje yönetimi özelliklerini genişleterek çevik (agile) proje yönetimi metodolojilerini destekleyen bir eklentidir. Bu modül, proje ekiplerinin daha verimli çalışmasını sağlamak için sprint planlama, görev takibi, ekip yönetimi ve belge yönetimi gibi özellikler sunar.

## 2. Amaç ve Kapsam

Bu modül, aşağıdaki ihtiyaçları karşılamak üzere tasarlanmıştır:

- Projelerin çevik metodolojilere uygun olarak yönetilmesi
- Proje ekiplerinin daha etkili organizasyonu
- Sprint bazlı görev planlaması ve takibi
- Proje belgelerinin merkezi yönetimi
- Departman ve ekip bazlı iş akışlarının oluşturulması
- Görevlerin daha detaylı izlenmesi ve raporlanması

## 3. Temel Özellikler

### 3.1. Çalışma Alanları ve Panolar (Workspace & Board)

- **Çalışma Alanları:** Projelerin organize edildiği üst seviye yapılar
- **Panolar:** Çalışma alanları içinde yer alan, projelerin görselleştirildiği alanlar
- **Pano Tipleri:** Kanban veya diğer görünüm tipleri desteklenir

#### 3.1.1. Çalışma Alanı Bazlı Çalışmanın Faydaları

Çalışma alanı (workspace) bazlı proje yönetimi yaklaşımı, aşağıdaki nedenlerle tercih edilmektedir:

1. **Organizasyonel Netlik:** Farklı departmanlar, müşteriler veya iş alanları için ayrı çalışma alanları oluşturarak organizasyonel yapıyı daha net hale getirir.
2. **Ölçeklenebilirlik:** Büyüyen organizasyonlarda proje sayısı arttıkça, bunları çalışma alanları altında gruplamak yönetimi kolaylaştırır.
3. **Erişim Kontrolü:** Çalışma alanı seviyesinde izin yönetimi, hangi kullanıcıların hangi projelere erişebileceğini daha kolay kontrol etmeyi sağlar.
4. **Özelleştirilebilir İş Akışları:** Her çalışma alanı için farklı iş akışları, aşamalar ve süreçler tanımlanabilir.
5. **Odaklanmış Görünüm:** Kullanıcılar sadece ilgilendikleri çalışma alanlarına odaklanabilir, bu da karmaşıklığı azaltır.
6. **Raporlama Kolaylığı:** Çalışma alanı bazlı raporlar, belirli bir iş alanı veya departman için daha anlamlı veriler sunar.

#### 3.1.2. Çalışma Alanı Bazlı Çalışma Nasıl Yapılır

**Çalışma Alanı Hiyerarşisi:**

```
Çalışma Alanı (Workspace)
  └── Pano (Board)
       └── Proje (Project)
            └── Görev (Task)
```

**Uygulama Adımları:**

1. **Çalışma Alanlarının Tanımlanması:**
   - Organizasyon yapısına göre çalışma alanları oluşturulur (örn. Departmanlar, Müşteriler, İş Alanları)
   - Her çalışma alanı için yöneticiler ve erişim hakları belirlenir
   - Çalışma alanı meta verileri (açıklama, kategori, öncelik) tanımlanır

2. **Panoların Oluşturulması:**
   - Her çalışma alanı içinde ihtiyaca göre panolar oluşturulur
   - Pano tipleri belirlenir (Kanban, Liste, vb.)
   - Pano aşamaları ve iş akışları tanımlanır

3. **Projelerin Panolara Atanması:**
   - Projeler oluşturulur ve ilgili panolara atanır
   - Proje, pano aşamalarını kullanacak şekilde yapılandırılır
   - Proje ekipleri ve departmanlar atanır

4. **Görevlerin Yönetimi:**
   - Görevler projelere atanır
   - Görevler sprint ve versiyonlarla ilişkilendirilir
   - Görev durumları pano aşamalarına göre takip edilir

**Çalışma Alanı Yönetimi İçin En İyi Uygulamalar:**

1. **Tutarlı Yapı:** Tüm çalışma alanları için tutarlı bir yapı ve isimlendirme standardı belirleyin
2. **Aşırı Bölünmeden Kaçının:** Çok fazla çalışma alanı oluşturmak yerine, mantıklı gruplamalar yapın
3. **Düzenli Gözden Geçirme:** Çalışma alanlarını ve panoları düzenli olarak gözden geçirin ve optimize edin
4. **Dokümantasyon:** Her çalışma alanı için amaç ve kapsamı açıkça belgelendirin
5. **Eğitim:** Kullanıcıları çalışma alanı bazlı yaklaşım konusunda eğitin

### 3.2. Proje Yönetimi Genişletmeleri

- **Departman Entegrasyonu:** Projelerin belirli departmanlara atanabilmesi
- **Ekip Yönetimi:** Proje ekiplerinin oluşturulması ve yönetilmesi
- **Belge Yönetimi:** Projeye ait belgelerin merkezi olarak yönetilmesi
- **Aşama Yönetimi:** Proje aşamalarının özelleştirilmesi ve pano bazlı filtrelenmesi

### 3.3. Görev Yönetimi Genişletmeleri

- **Sprint Entegrasyonu:** Görevlerin sprintlere atanabilmesi
- **Görev Tipleri:** Hikaye (Story), Görev (Task), Hata (Bug) gibi görev tiplerinin desteklenmesi
- **Görev Geçmişi:** Sprint geçmişi gibi görev değişikliklerinin takibi
- **Ekip Üyesi Ataması:** Ekip bazlı kullanıcı atama kısıtlamaları
- **Alt Görevler:** Görevlerin alt görevlere bölünebilmesi ve kopyalanabilmesi

### 3.4. Sprint Yönetimi

- **Sprint Oluşturma ve Planlama:** Sprint döngülerinin oluşturulması
- **Görev Atama:** Sprintlere görev atama ve takip etme
- **Sprint Geçmişi:** Görevlerin hangi sprintlerde yer aldığının takibi

### 3.5. Versiyon Yönetimi

- **Versiyon Tanımlama:** Proje versiyonlarının tanımlanması
- **Görev-Versiyon İlişkisi:** Görevlerin belirli versiyonlara atanabilmesi

## 4. Veri Modelleri

### 4.1. Proje Modeli Genişletmeleri (project.project)

- `department_id`: Proje departmanı (hr.department)
- `board_id`: Proje panosu (project.board)
- `board_desc`: Pano açıklaması (hesaplanan alan)
- `team_id`: Proje ekibi (crm.team)
- `members_ids`: Proje üyeleri (res.users)
- `added_followers`: Otomatik eklenen takipçiler (res.users)
- `only_team_members_can_be_assigned`: Sadece ekip üyelerinin atanabilmesi kısıtlaması
- `add_the_team_members_to_the_followers`: Ekip üyelerinin takipçilere otomatik eklenmesi
- `document_count`: Belge sayısı (hesaplanan alan)

### 4.2. Görev Modeli Genişletmeleri (project.task)

- `project_department_id`: Proje departmanı (ilişkili alan)
- `project_team_id`: Proje ekibi (ilişkili alan)
- `allowed_assigned_user_ids`: İzin verilen kullanıcılar (hesaplanan alan)
- `document_count`: Belge sayısı (hesaplanan alan)
- `issue_type`: Görev tipi (Story, Task, Bug)
- `board_type`: Pano tipi (hesaplanan alan)
- `version_id`: Versiyon (project.version)
- `sprint_id`: Sprint (project.sprint)
- `sprint_history_ids`: Sprint geçmişi (project.task.sprint.history)

### 4.3. Diğer Modeller

- `project.board`: Proje panoları
- `project.workspace`: Çalışma alanları
- `project.sprint`: Sprint yönetimi
- `project.version`: Versiyon yönetimi
- `project.task.sprint.history`: Görev-sprint geçmişi

## 5. Kullanıcı Arayüzü

### 5.1. Proje Görünümleri

- **Liste Görünümü:** Genişletilmiş proje listesi
- **Form Görünümü:** Departman, ekip ve pano bilgilerini içeren form
- **Kanban Görünümü:** Görsel proje takibi
- **Arama Görünümü:** Gelişmiş filtreleme seçenekleri

### 5.2. Görev Görünümleri

- **Form Görünümü:** Sprint, versiyon ve diğer ek alanları içeren form
- **Liste Görünümü:** Departman, ekip ve sprint bilgilerini içeren liste
- **Kanban Görünümü:** Görsel görev takibi
- **Arama Görünümü:** Departman, sprint ve diğer kriterlere göre filtreleme

### 5.3. Diğer Görünümler

- Çalışma Alanı ve Pano görünümleri
- Sprint yönetimi görünümleri
- Versiyon yönetimi görünümleri
- Ekip yönetimi görünümleri

## 6. İş Akışları

### 6.1. Proje Oluşturma ve Yönetimi

1. Çalışma alanı oluşturma
2. Pano oluşturma
3. Proje oluşturma ve panoya atama
4. Ekip ve departman atama
5. Proje aşamalarının yönetimi

### 6.2. Sprint Planlama ve Yönetimi

1. Sprint oluşturma
2. Görevlerin sprinte atanması
3. Sprint ilerleme takibi
4. Sprint kapatma ve değerlendirme

### 6.3. Görev Yönetimi

1. Görev oluşturma ve tiplendirme
2. Görevin sprint ve versiyona atanması
3. Görevin ekip üyelerine atanması
4. Alt görevlerin yönetimi
5. Görev durumunun takibi ve güncellenmesi

### 6.4. Belge Yönetimi

1. Projeye belge ekleme
2. Göreve belge ekleme
3. Belgelerin görüntülenmesi ve yönetimi

## 7. Güvenlik ve Erişim Kontrolü

- Proje yöneticileri için genişletilmiş yetkiler
- Ekip bazlı erişim kısıtlamaları
- Görev aşama değişikliklerinde yetki kontrolü

## 8. Raporlama

- Departman bazlı proje raporları
- Sprint bazlı ilerleme raporları
- Ekip performans raporları

## 9. Entegrasyonlar

- İnsan Kaynakları (HR) modülü ile departman entegrasyonu
- CRM modülü ile ekip entegrasyonu
- Mail modülü ile bildirim entegrasyonu
- Belge yönetimi entegrasyonu

## 10. Teknik Gereksinimler

- Odoo 18.0 veya üzeri
- Bağımlı modüller: project, hr, crm, mail, base_automation

## 11. Kurulum ve Yapılandırma

1. Modülün yüklenmesi
2. Departman ve ekiplerin tanımlanması
3. Çalışma alanları ve panoların oluşturulması
4. Proje aşamalarının yapılandırılması
5. Kullanıcı yetkilerinin ayarlanması

---

Bu doküman, Agile Proje Yönetimi modülünün fonksiyonel özelliklerini tanımlamaktadır. Teknik detaylar ve geliştirme spesifikasyonları ayrı bir dokümanda ele alınacaktır.