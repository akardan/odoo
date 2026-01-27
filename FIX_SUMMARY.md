# Fix Summary: MICE Module Cleanup - action_view_scenarios and Related Errors

## Problems Encountered

### Problem 1: action_view_scenarios Error
When upgrading the `ak_tender` module, the following error occurred:

```
odoo.tools.convert.ParseError: while parsing /opt/odoo18/addons-custom/ak_tender/views/tender_views.xml:3
action_view_scenarios geçerli bir işlem değilak.tender
```

### Problem 2: scenario_id Field Error
After fixing Problem 1, a second error appeared:

```
"scenario_id" alanı "ak.tender.line" modelinde mevcut değil
```

### Problem 3: Runtime scenario_count Error
After module upgrade succeeded, runtime error when opening tender records:

```
ValueError: Invalid field 'scenario_count' on model 'ak.tender'
```

## Root Cause
The error was caused by an orphaned database view record (`view_tender_form_mice_scenarios`) that referenced a method `action_view_scenarios` which no longer exists in the codebase.

### Background
- The MICE views file (`tender_mice_views.xml`) was previously removed from the module
- However, the database still contained the view record with ID 6092
- This view included a button that called `action_view_scenarios` method
- During module upgrade, Odoo's view validator detected this invalid method reference

## Solution Applied

### 1. Identified the Issue
- Located the backup copy in `plans/ak_tender copy/views/tender_mice_views.xml`
- Found that the button was commented out in the backup but the view still existed in the database

### 2. Database Cleanup
Created and executed [`fix_mice_view.py`](fix_mice_view.py) which:
- Connected to the PostgreSQL database (od18)
- Found view ID 6092 (`ak.tender.form.mice.scenarios`) containing the invalid reference
- Deleted the orphaned view from `ir_ui_view` table
- Cleaned up the related `ir_model_data` entry

### 3. Additional MICE Field References
After fixing the first issue, a second error appeared:
```
"scenario_id" alanı "ak.tender.line" modelinde mevcut değil
```

Created and executed [`fix_scenario_field_references.py`](fix_scenario_field_references.py) which:
- Found view ID 6093 (`ak.tender.form.mice.lines`) containing MICE field references
- Deleted the orphaned view that referenced non-existent fields:
  - `scenario_id`
  - `line_type`
  - `mice_room_type`
  - `mice_meal_plan`
- Cleaned up the related `ir_model_data` entry

### 4. Verification
- Confirmed no other MICE-related action references remain in the database
- Verified the following actions are not referenced:
  - `action_create_scenario`
  - `action_start_next_round`
  - `action_add_to_shortlist`
  - `action_view_comparison`
- Removed all MICE field references from views

## Files Created During Fix

1. **fix_action_view_scenarios.sql** - Initial SQL investigation script
2. **fix_workflow_action.py** - Odoo shell script (not used due to missing dependencies)
3. **fix_workflow_direct.py** - Direct PostgreSQL connection script for workflow actions
4. **check_workflow_transitions.py** - Script to check workflow transitions
5. **fix_mice_view.py** - **First fix script** - removed view with action_view_scenarios (view ID 6092)
6. **check_remaining_mice_views.py** - Verification script for MICE actions
7. **fix_scenario_field_references.py** - **Second fix script** - removed view with MICE field references (view ID 6093)
8. **find_and_fix_all_mice_fields.py** - Comprehensive MICE field checker
9. **check_view_fields.py** - Check for custom MICE fields in ir_model_fields
10. **deep_search_scenario_count.py** - Deep search for scenario_count in all views
11. **clear_odoo_cache.py** - **Third fix script** - cleared Odoo assets and view cache

## Result
✅ Successfully removed 2 orphaned MICE view records (IDs: 6092, 6093)
✅ Cleaned up 2 related ir_model_data entries
✅ Cleared 496 cached assets from the database
✅ Updated 6 views to force cache refresh
✅ All MICE field and action references have been removed from code and database
✅ The `ak_tender` module can now be upgraded without errors

## Next Steps
1. **Restart Odoo service** to clear server-side cache:
   ```bash
   sudo systemctl restart odoo18
   ```

2. **Clear browser cache** or use Ctrl+Shift+R (hard refresh) when accessing the Odoo interface

3. The `ak_tender` module should now work without MICE-related errors

## Important Notes
- The MICE functionality has been completely removed from the database
- All related views (view_tender_form_mice_scenarios, view_tender_form_mice_lines) have been deleted
- If MICE functionality is needed in the future, it will need to be re-implemented from scratch

## Prevention
To prevent similar issues in the future:
1. When removing view files from a module, ensure to update the module to remove the views from the database
2. Use `noupdate="0"` in data files for views that might be modified
3. Consider using `unlink()` in migration scripts when removing views

---
**Date:** 2026-01-27
**Database:** od18
**Module:** ak_tender
**Fixed By:** Database cleanup script
