# purchase.order.group Entegrasyonu Kaldırıldı

Bu dokümantasyon, "purchase.order.group" modelinin "ak_tender" modülünden kaldırılmasını açıklamaktadır.

## Genel Bakış

"purchase.order.group" modeli ve ilgili alternatif teklif özellikleri, "ak_tender" modülünden kaldırılmıştır. Bu değişiklik, modülün daha basit ve daha kararlı olmasını sağlamak amacıyla yapılmıştır.

## Yapılan Değişiklikler

1. **Bağımlılık Kaldırma**: "purchase_requisition" modülü, "ak_tender" modülünün bağımlılıklarından kaldırıldı.

2. **Model Sadeleştirme**: "purchase.order" modelinden "purchase_group_id", "alternative_po_ids" ve "has_alternatives" alanları kaldırıldı.

3. **Metot Kaldırma**: "ak.tender" modelinden "group_alternative_offers" metodu kaldırıldı ve "create_purchase_orders_for_suppliers" metodu güncellendi.

4. **Görünüm Güncelleme**: "purchase_order_views.xml" dosyası güncellenerek, alternatif tekliflerle ilgili tüm özellikler kaldırıldı.

## Neden Kaldırıldı?

Bu entegrasyon, "Cannot read properties of undefined (reading '0')" hatasına neden oluyordu. Hata, teklif görüntüleme sırasında ortaya çıkıyordu ve kullanıcı deneyimini olumsuz etkiliyordu.

Alternatif teklif yönetimi, "ak_tender" modülünün temel işlevselliği için gerekli olmadığından, bu özellik kaldırılarak modül daha kararlı hale getirildi.

## Etkilenen Özellikler

Aşağıdaki özellikler artık kullanılamaz:

1. Alternatif teklif oluşturma
2. Alternatif teklifleri gruplandırma
3. Alternatif teklifleri karşılaştırma

## Geçiş Kılavuzu

Eğer alternatif teklif yönetimi özelliklerini kullanıyorsanız, artık her teklifi ayrı bir satın alma siparişi olarak yönetmeniz gerekecektir. İhale formundaki "Teklifler (SAT)" görünümünde tüm teklifleri görebilir ve manuel olarak karşılaştırabilirsiniz.

## Notlar

- Bu değişiklik, "ak_tender" modülünün temel işlevselliğini etkilemez.
- Tüm tedarikçiler için satın alma siparişi oluşturma özelliği hala mevcuttur ve sorunsuz çalışmaktadır.
- İhale yönetimi ve teklif değerlendirme süreçleri aynı şekilde devam etmektedir.