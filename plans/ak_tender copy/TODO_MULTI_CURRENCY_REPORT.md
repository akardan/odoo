# TODO: Multi-Currency Support for Vendor Comparison Report

## 🚨 CRITICAL FIXES (Immediate Action Required)

### 1. Currency Field References
- [ ] **Line 424**: Replace `vendor_line.currency_id` with `vendor_line.line_currency_id`
- [ ] **Line 498**: Replace `vendor_line.currency_id` with `vendor_line.line_currency_id` 
- [ ] **Line 468**: Add currency display for `price_subtotal` using `line_currency_id`
- [ ] **Line 612**: Fix total amount currency display inconsistency
- [ ] **Line 650**: Fix total NPV currency display inconsistency

### 2. Price Display Updates
- [ ] **Birim Fiyat Row**: Show `line_price_unit` in `line_currency_id`
- [ ] **Computed Price**: Show converted `price_unit` in PO `currency_id`
- [ ] **Tutar Row**: Show `price_subtotal` in `line_currency_id`
- [ ] **NPV Row**: Show `npv_value` in `tender_line_currency_id`

## ⚠️ HIGH PRIORITY

### 3. Comparison Logic Fixes
- [ ] **Min Amount Logic**: Convert all amounts to tender currency before comparison
- [ ] **Min NPV Logic**: Convert all NPV values to tender currency before comparison
- [ ] **System Selection**: Base selection on converted values, not original currencies
- [ ] **Total Calculations**: Convert line totals to PO currency before summing

### 4. Currency Conversion Integration
- [ ] **Add Helper Method**: Create `_convert_to_tender_currency()` template helper
- [ ] **Two-Stage Conversion**: Use company currency as intermediate step
- [ ] **Rate Display**: Show conversion rates used in calculations
- [ ] **Error Handling**: Handle missing exchange rates gracefully

## 📋 MEDIUM PRIORITY

### 5. Template Structure Updates
- [ ] **Currency Headers**: Add currency column headers to show which currency is used
- [ ] **Dual Display**: Show both original and converted values where needed
- [ ] **Currency Legend**: Add legend explaining currency symbols and conversions
- [ ] **Conversion Notes**: Add footnotes about conversion dates and rates

### 6. JavaScript Updates
- [ ] **Frontend Calculations**: Update JS to handle multi-currency totals
- [ ] **User Selection Logic**: Ensure selections work with converted values
- [ ] **Total Updates**: Fix user total calculations for multi-currency
- [ ] **Grand Total Logic**: Update grand total calculations

## 🔧 LOW PRIORITY

### 7. PDF Report Updates
- [ ] **PDF Template**: Update `report_vendor_comparison_pdf` template
- [ ] **Currency Display**: Ensure PDF shows currencies correctly
- [ ] **Layout Fixes**: Adjust PDF layout for multi-currency display
- [ ] **Font Support**: Ensure currency symbols display correctly in PDF

### 8. Performance Optimizations
- [ ] **Cache Conversions**: Cache currency conversion results
- [ ] **Batch Conversions**: Convert multiple values in single calls
- [ ] **Lazy Loading**: Only convert currencies when needed for display
- [ ] **Query Optimization**: Optimize database queries for currency data

## 📊 SPECIFIC LINE FIXES NEEDED

### Current Issues by Line Number:
```xml
Line 424: t-options='{"widget": "monetary", "display_currency": vendor_line.currency_id}'
         → Should be: vendor_line.line_currency_id

Line 468: <span t-field="vendor_line.price_subtotal"/>
         → Missing currency display

Line 498: t-options='{"widget": "monetary", "display_currency": vendor_line.currency_id}'
         → Should be: vendor_line.line_currency_id

Line 612: t-options='{"widget": "monetary", "display_currency": vendor.currency_id}'
         → Need conversion to common currency

Line 650: t-options='{"widget": "monetary", "display_currency": vendor.currency_id}'
         → Need conversion to common currency
```

## 🎯 IMPLEMENTATION STRATEGY

### Phase 1: Critical Fixes (1-2 hours)
1. Fix currency field references
2. Add missing currency displays
3. Test basic functionality

### Phase 2: Comparison Logic (2-3 hours)
1. Implement currency conversion helpers
2. Fix min/max comparison logic
3. Update system selection logic

### Phase 3: UI/UX Improvements (1-2 hours)
1. Add currency headers and legends
2. Implement dual display where needed
3. Update JavaScript calculations

### Phase 4: Testing & Optimization (1 hour)
1. Test with multiple currencies
2. Verify conversion accuracy
3. Performance testing

## 🧪 TEST SCENARIOS

### Required Test Cases:
- [ ] **Single Currency**: All vendors use same currency
- [ ] **Multi Currency**: Vendors use different currencies  
- [ ] **Mixed Lines**: Same PO has lines in different currencies
- [ ] **NPV Calculations**: NPV values calculated correctly across currencies
- [ ] **System Selection**: Lowest NPV selected correctly after conversion
- [ ] **User Selection**: User selections work with multi-currency
- [ ] **Total Calculations**: All totals sum correctly after conversion
- [ ] **PDF Export**: PDF report displays currencies correctly

## 📝 NOTES

- **Backward Compatibility**: Ensure existing single-currency reports still work
- **Exchange Rates**: Use rates from the tender/PO date, not current date
- **Rounding**: Be consistent with currency rounding rules
- **Error Messages**: Provide clear messages when conversion fails
- **Documentation**: Update user documentation for multi-currency features

## 🔗 RELATED FILES TO UPDATE

- `/models/purchase_order_line.py` - Ensure NPV calculations are correct
- `/models/ak_tender.py` - Add currency conversion helpers
- `/static/src/js/vendor_comparison.js` - Update frontend calculations
- `/views/purchase_order_views.xml` - Ensure form views show correct currencies
- `/report/vendor_comparison_report.xml` - Main template updates (this file)

---
**Priority Order**: Critical → High → Medium → Low
**Estimated Total Time**: 6-8 hours
**Dependencies**: Multi-currency purchase order line implementation must be complete first