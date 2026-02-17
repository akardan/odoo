# KAI - Kullanim Kilavuzu

> **Modul:** ak_ai (KAI - Kardan AI Assistant)
> **Odoo Surumu:** 18.0
> **Dokuman Revizyonu:** 1.0 | 2026-02-17

---

## Icindekiler

1. [KAI Nedir?](#1-kai-nedir)
2. [Baslangic](#2-baslangic)
3. [Discuss Uzerinden Kullanim](#3-discuss-uzerinden-kullanim)
4. [Chatter Uzerinden Kullanim (Form Ekrani)](#4-chatter-uzerinden-kullanim-form-ekrani)
5. [Kod Calistirma](#5-kod-calistirma)
6. [Geri Bildirim Verme](#6-geri-bildirim-verme)
7. [Sik Sorulan Sorular (SSS)](#7-sik-sorulan-sorular-sss)
8. [Ipuclari ve En Iyi Uygulamalar](#8-ipuclari-ve-en-iyi-uygulamalar)

---

## 1. KAI Nedir?

KAI (Kardan AI), Odoo 18 icinde calisan yapay zeka destekli bir asistan modulu. Odoo arayuzunuzu terk etmeden:

- Sorularinizi dogal dilde sorabilir
- Kayitlar hakkinda baglamsal yardim alabilir
- Belirli islemleri KAI'ye yaptirabilir (fatura olusturma, siparis onaylama vb.)
- Odoo'nun yapisini, is sureclerini ve verilerinizi anlayan akilli bir yardimci kullanabilirsiniz

---

## 2. Baslangic

### 2.1 Erisim Kontrolu

KAI'yi kullanabilmeniz icin yoneticiniz sizi **KAI User** grubuna eklenmis olmalidir. Erisim sorununuz varsa sistem yoneticinizle iletisime gecin.

### 2.2 KAI'ye Erisim Yollari

KAI'ye iki farkli yoldan ulasabilirsiniz:

| Yontem | Nerede | Ne Zaman Kullanilir |
|--------|--------|---------------------|
| **Discuss Kanali** | Discuss uygulamasi | Genel sorular, rehberlik, Odoo ogrenme |
| **Chatter Butonu** | Form ekranlarindaki "Ask KAI" butonu | Belirli bir kayit hakkinda soru sorma |

---

## 3. Discuss Uzerinden Kullanim

### 3.1 Kanala Erisim

**KAI Assistant** kanali modul kurulumunda otomatik olusturulur.

1. Sol menuden **Discuss** uygulamasina gidin
2. Kanal listesinde **KAI Assistant** kanalini bulun (Kanallar bolumunde)
3. Kanala tiklayin

Kanali goremiyorsaniz modul guncellenmemis olabilir. Sistem yoneticinizden `ak_ai` modulunu guncellemesini isteyin.

### 3.2 Mesaj Gonderme

Normal bir sohbet gibi mesajinizi yazin ve gonderin. KAI birkar saniye icinde yanit verecektir.

### 3.3 Ornek Konusmalar

**Rehberlik isteme:**
```
Siz: Satis siparisi nasil olusturulur?
KAI: Satis siparisi olusturmak icin su adimlari izleyin:
     1. Satis > Siparisler > Teklifler menusune gidin
     2. 'Olustur' butonuna tiklayin
     3. Musteriyi secin ve urun satirlarini ekleyin
     4. 'Onayla' ile siparisi kesinlestirin
```

**Bilgi sorma:**
```
Siz: Stok hareketlerini nereden gorebilirim?
KAI: Stok > Raporlama > Stok Hareketleri menusunden
     tum giris-cikis hareketlerini gorebilirsiniz.
```

**Genel yardim:**
```
Siz: Fatura ile odeme nasil eslestirilir?
KAI: Muhasebe > Faturalar'dan ilgili faturayi acin,
     'Odeme Kaydet' butonuna tiklayin. Odeme bilgilerini
     girdikten sonra otomatik olarak eslestirilir.
```

---

## 4. Chatter Uzerinden Kullanim (Form Ekrani)

### 4.1 "Ask KAI" Butonu

Desteklenen form ekranlarinda (Satis Siparisi, Satin Alma, Fatura vb.) Chatter bolgesinde **"Ask KAI"** butonu bulunur.

### 4.2 Nasil Kullanilir

1. Ilgili kaydin form ekranini acin (ornegin bir Satis Siparisi)
2. **"Ask KAI"** butonuna tiklayin
3. Sohbet penceresi acilir
4. Sorunuzu yazin - KAI kaydin tum bilgilerini gorur

### 4.3 Baglam Farki

Chatter uzerinden soru sordugunuzda KAI su bilgilere erisir:

- Kaydin tum alanlari (musteri, tutar, durum, tarih vb.)
- Iliskili kayitlar (siparis satirlari, faturalar vb.)
- Sizin yetki seviyeniz
- Is sureci durumu

Bu sayede cok daha hedefli ve isabetli yanitlar alirsiniz.

### 4.4 Ornek Konusmalar

**Siparis hakkinda soru:**
```
(SO001 uzerinde)
Siz: Bu siparisi neden faturalandiramiyorum?
KAI: SO001'i inceliyorum:
     - Durum: Taslak
     - Faturalama icin once 'Onayla' butonuyla
       siparisi kesinlestirmeniz gerekiyor.
     - Onayladiktan sonra 'Fatura Olustur' aktif olacaktir.
```

**Kayit analizi:**
```
(PO005 uzerinde)
Siz: Bu satin alma siparisinin ozeti nedir?
KAI: PO005 ozeti:
     - Tedarikci: ABC Ltd.
     - Toplam: 15.420,00 TL
     - 3 urun satiri
     - Durum: Satin Alma Siparisi (onaylanmis)
     - Beklenen teslim: 25.02.2026
```

---

## 5. Kod Calistirma

KAI bazi durumlarda islem yapmanizi onerebilir. Bu durumda:

### 5.1 Nasil Calisir

1. KAI bir islem onerisi yaptiginda, yanit icinde **calistirilabilir kod** blogu gorursunuz
2. Kod blogunun altinda **"Calistir"** butonu bulunur
3. Calistirmadan once KAI size islemi ozetler:
   - Ne yapilacak
   - Hangi kayit etkilenecek
   - Beklenen sonuc

### 5.2 Guvenlik

- Kod **sizin yetki seviyenizde** calisir (sudo kullanilmaz)
- Yetkiniz olmayan bir islem yaptirilmaz
- Her islem denetim kaydinda (audit log) saklanir
- KAI semantik dogrulama yapar (orn. sifir fiyatli kayit olusturmayi engeller)

### 5.3 Ornek

```
Siz: Bu siparis icin fatura olustur
KAI: SO001 icin fatura olusturabilirim:
     - Musteri: Acme Corp
     - Tutar: 1.234,56 TL
     - Tam fatura (%100)

     [Calistir] butonu

     Sonuc: Fatura INV/2026/001 basariyla olusturuldu.
     Dogrulama: Tutar ve musteri SO001 ile eslesiyor.
```

---

## 6. Geri Bildirim Verme

### 6.1 Neden Onemli

Geri bildirimleriniz KAI'nin ogrenme sistemini besler. Daha iyi yanitlar almak icin degerlendirme yapin.

### 6.2 Nasil Yapilir

KAI yanitlarinin altinda degerlendirme secenekleri bulunur:

- **Faydali** - Yanit isime yaradi
- **Faydasiz** - Yanit isime yaramadi veya yanlis bilgi verdi

### 6.3 Kategoriler

Geri bildirimler su kategorilerde degerlendirilir:
- **Dogruluk**: Bilgi dogru muydu?
- **Faydalilik**: Sorunuza cozum oldu mu?
- **Guvenlik**: Uygun erisim kurallarina uyuldu mu?
- **Performans**: Yanit suresi tatmin edici miydi?

---

## 7. Sik Sorulan Sorular (SSS)

### KAI yanitlamiyorsa ne yapmaliyim?

1. Internet baglantinizi kontrol edin
2. Sayfayi yenileyip tekrar deneyin
3. Sorun devam ederse sistem yoneticinize bildirin (API kredisi bitebilir)

### KAI yanlis bilgi verdiyse ne yapmaliyim?

1. Geri bildirim olarak **Faydasiz** secin
2. Sorunuzu daha net bir sekilde yeniden sorun
3. Kritik islemler icin her zaman KAI'nin onerilerini dogrulayin

### Hangi ekranlarda "Ask KAI" butonu var?

Sistem yoneticinizin KAI mixin'ini ekledigi tum form ekranlarinda. Varsayilan olarak eklenmis olabilecek modeller:
- Satis Siparisleri
- Satin Alma Siparisleri
- Faturalar
- Iletisim Kayitlari

Ek modeller icin yoneticinize danisabilirsiniz.

### KAI verilerimi gorebilir mi?

KAI yalnizca **sizin gormeye yetkili oldugunuz** verilere erisebilir. Odoo'nun erisim kontrol kurallari (ACL ve Record Rules) tam olarak uygulanir.

### Konusmalarimi baskasi gorebilir mi?

Hayir. Her kullanici yalnizca kendi konusmalarini gorebilir. Yoneticiler (KAI Manager) tum konusmalari gorebilir.

### KAI Turkce anlyor mu?

Evet. KAI kullandiginiz AI modeline bagli olarak Turkce dahil bircok dili destekler. Sorunuzu Turkce sorabilir ve Turkce yanit alabilirsiniz.

---

## 8. Ipuclari ve En Iyi Uygulamalar

### Daha Iyi Yanitlar Icin

1. **Net ve spesifik sorun**: "Bu siparis hakkinda ne dusunuyorsun?" yerine "Bu siparisin faturalama durumu nedir?" diye sorun
2. **Baglami kullanin**: Mumkunse ilgili kaydin form ekranindan (Chatter) sorun - KAI otomatik olarak kayit bilgilerini gorur
3. **Tek seferde tek istek**: Birden fazla soruyu ayri mesajlarda sorun

### Guvenlik Icin

1. KAI'nin onerilerini calistirmadan once **ozetini okuyun**
2. Kritik islemlerde (silme, toplu guncelleme) ekstra dikkatli olun
3. **Sifrelerinizi veya API anahtarlarinizi** KAI ile paylasmmayin

### Verimlilik Icin

1. **Discuss kanali**: Genel sorular, ogrenme, rehberlik icin
2. **Chatter butonu**: Spesifik kayit islemleri icin
3. Tekrar eden islemler icin KAI'ye yaptirmak zaman kazandirir

---

## Revizyon Gecmisi

| Versiyon | Tarih | Degisiklikler |
|----------|-------|---------------|
| 1.0 | 2026-02-17 | Ilk kullanim kilavuzu |

---

Kardan.Digital - Akilli Odoo Cozumleri
