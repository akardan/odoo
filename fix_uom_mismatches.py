#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOM Uyumsuzluk Düzeltme Script'i
Havuzdaki (purchase.requisition.line) kayıtların UOM'larını ürünlerdeki UOM'larla karşılaştırır
ve uyumsuz olanları düzeltir.
"""

import sys
import logging

_logger = logging.getLogger(__name__)

def fix_uom_mismatches(env):
    """Havuzdaki kayıtlarla ürünlerdeki UOM'ları karşılaştır ve düzelt"""
    print("=" * 80)
    print("UOM Uyumsuzluk Kontrolü ve Düzeltme Başlıyor")
    print("=" * 80)
    
    stats = {
        'total': 0,
        'checked': 0,
        'mismatched': 0,
        'fixed': 0,
        'errors': 0,
        'error_details': []
    }
    
    # Tüm havuz satırlarını al
    lines = env['purchase.requisition.line'].search([
        ('product_id', '!=', False),
        ('product_uom_id', '!=', False),
    ])
    
    stats['total'] = len(lines)
    print(f"Toplam {stats['total']} havuz satırı kontrol edilecek\n")
    
    for line in lines:
        stats['checked'] += 1
        
        try:
            product = line.product_id
            line_uom = line.product_uom_id
            product_uom = product.uom_po_id or product.uom_id
            
            # UOM kategorilerini kontrol et
            if line_uom.category_id != product_uom.category_id:
                stats['mismatched'] += 1
                error_msg = (
                    f"SAT {line.erp_pr_id}/{line.erp_pr_item} - "
                    f"Ürün: {product.default_code} ({product.name[:50]}) - "
                    f"Havuz UOM: {line_uom.name} ({line_uom.category_id.name}), "
                    f"Ürün UOM: {product_uom.name} ({product_uom.category_id.name})"
                )
                print(f"❌ UYUMSUZLUK: {error_msg}")
                
                # Ürünün UOM'unu havuzdaki UOM ile güncelle
                try:
                    product.sudo().write({
                        'uom_id': line_uom.id,
                        'uom_po_id': line_uom.id,
                    })
                    stats['fixed'] += 1
                    print(f"   ✓ DÜZELTİLDİ: Ürün {product.default_code} UOM'u '{line_uom.name}' olarak güncellendi\n")
                except Exception as e:
                    stats['errors'] += 1
                    error_detail = f"HATA - {error_msg} - Düzeltme Hatası: {str(e)}"
                    stats['error_details'].append(error_detail)
                    print(f"   ❌ DÜZELTME HATASI: {str(e)}\n")
                    
        except Exception as e:
            stats['errors'] += 1
            error_detail = f"SAT {line.erp_pr_id}/{line.erp_pr_item} - Kontrol Hatası: {str(e)}"
            stats['error_details'].append(error_detail)
            print(f"❌ KONTROL HATASI: {error_detail}\n")
    
    # Özet rapor
    print("=" * 80)
    print("UOM Uyumsuzluk Kontrolü Tamamlandı")
    print("=" * 80)
    print(f"Toplam Kontrol Edilen: {stats['checked']}")
    print(f"Uyumsuz Bulunan: {stats['mismatched']}")
    print(f"Düzeltilen: {stats['fixed']}")
    print(f"Hata Alan: {stats['errors']}")
    print("=" * 80)
    
    if stats['error_details']:
        print("\n❌ HATA DETAYLARI:")
        print("-" * 80)
        for i, error in enumerate(stats['error_details'], 1):
            print(f"{i}. {error}")
        print("=" * 80)
    
    return stats

if __name__ == '__main__':
    # Odoo ortamında çalıştırılacak
    print("Bu script Odoo shell içinden çalıştırılmalıdır:")
    print("python odoo-bin shell -d DATABASE_NAME -c odoo.conf")
    print("Sonra:")
    print("exec(open('fix_uom_mismatches.py').read())")
    print("fix_uom_mismatches(env)")
