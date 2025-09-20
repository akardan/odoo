# Dijital Prospektüs Yönetimi (e-KT Hub)

Bu modül, ilaç ve sağlık sektörü için dijital prospektüs ve elektronik kullanma talimatı (e-KT) yönetim sistemi sağlar.

## 🏥 Özellikler

### Ana Özellikler
- **Elektronik Kullanma Talimatı (e-KT)** oluşturma ve yönetimi
- **QR kod** otomatik oluşturma ve erişim sistemi
- **Paket bazlı hizmet** yönetimi (S/M/L/XL)
- **KVKK uyumlu** güvenli veri saklama
- **Çoklu dil desteği** (Türkçe, İngilizce, Arapça)
- **AI seslendirme** entegrasyonu
- **Kullanım raporlama** ve analitik
- **Tedarikçi/eczane portalı**

### Analitik ve Raporlama
- Gerçek zamanlı **görüntülenme/indirme** takibi
- **IP bazlı** kullanım analitiği
- **Dil tercih** istatistikleri
- **Coğrafi analiz** (ülke/şehir bazlı)
- **Excel/PDF** rapor çıktıları

### Güvenlik ve Uyumluluk
- **KVKK uyumlu** veri saklama
- **Rol bazlı** erişim kontrolü
- **Benzersiz kod** sistemi
- **Audit trail** (tüm değişikliklerin kaydı)

### Web Entegrasyonu
- **Responsive** mobil uyumlu tasarım
- **SEO dostu** URL yapısı
- **Herkese açık** erişim linkleri
- **Portal entegrasyonu**

## 📋 Hizmet Paketleri

| Paket | Prospektüs Sayısı | AI Seslendirme | Stüdyo Ses | Çoklu Dil | Özel Geliştirme |
|-------|-------------------|----------------|------------|-----------|-----------------|
| **S** | 25                | ❌             | ❌         | ❌        | ❌              |
| **M** | 50                | ✅             | ❌         | ✅        | ❌              |
| **L** | 100               | ✅             | ✅         | ✅        | ✅              |
| **XL**| Sınırsız          | ✅             | ✅         | ✅        | ✅              |

## 🚀 Kurulum

```bash
# 1. Modülü indirin ve Odoo addons dizinine kopyalayın
git clone https://github.com/kardan-digital/ak_eKT.git
cp -r ak_eKT /opt/odoo/addons/

# 2. Odoo servisini yeniden başlatın
sudo systemctl restart odoo

# 3. Odoo arayüzünden modülü aktif edin
# Apps → Update Apps List → "Digital Prospectus Management" → Install
```

## 💻 Kullanım

### Prospektüs Oluşturma
1. **Prospektüs Yönetimi** → **Dijital Prospektüsler** → **Yeni**
2. Temel bilgileri doldurun (ürün adı, etken madde, vb.)
3. İçeriği HTML editör ile hazırlayın
4. Ses dosyalarını yükleyin (opsiyonel)
5. **İnceleme Gönder** → **Onayla** → **Yayınla**

### QR Kod Erişimi
Yayınlanan her prospektüs için otomatik QR kod oluşturulur:
```
https://yoursite.com/ekt/{unique_code}
```

### Analitik Takip
- Dashboard üzerinden gerçek zamanlı istatistikler
- Prospektüs bazlı detaylı analitik
- Coğrafi dağılım haritaları
- Excel/PDF rapor dışa aktarımı

## 🔧 Teknik Gereksinimler

- **Odoo**: 18.0 Community Edition
- **Python**: 3.8+ (3.10 önerilir)
- **Veritabanı**: PostgreSQL 12+
- **İşletim Sistemi**: Linux (Ubuntu 20.04+ önerilir)
- **RAM**: Minimum 4GB (8GB önerilir)
- **Disk**: Minimum 10GB boş alan

## 📞 Destek ve İletişim

- 📧 **Email**: info@kardan.digital
- 📞 **Telefon**: +90 XXX XXX XX XX
- 🌐 **Website**: https://kardan.digital

## 📄 Lisans

Bu modül LGPL-3 lisansı altında dağıtılmaktadır.

---
*Kardan.Digital tarafından geliştirilmiştir.*