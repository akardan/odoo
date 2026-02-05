# Quick Fix Guide - "relation 'purchase_order' does not exist" Error

## Problem Summary

When trying to create a materialized view directly from SQL that uses functions, you get:
```
ERROR: relation "purchase_order" does not exist
LINE 8: FROM purchase_order po
```

## Root Cause

The error occurs because:
1. Functions reference the `purchase_order` table
2. When creating a materialized view, PostgreSQL executes the functions immediately
3. If the functions are called before the `purchase` module tables exist, the error occurs
4. The original script tried to create materialized view from non-existent `view_dashboard_detail_prep`

## Solution

The fix involves a **3-step installation process**:

### Step 1: Create Functions
```bash
psql -U odoo -d dbname -f functions_dashboard_helpers.sql
```

### Step 2: Create Preparation View
```bash
psql -U odoo -d dbname -f view_dashboard_detail_with_functions.sql
```
This creates `view_dashboard_detail_prep` (not materialized)

### Step 3: Create Materialized View
```bash
psql -U odoo -d dbname -f create_materialized_view.sql
```
This creates `view_dashboard_detail` materialized view from the prep view

## What Changed

### Before (Broken)
```sql
-- Tried to create materialized view directly with all SQL
DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;
CREATE MATERIALIZED VIEW view_dashboard_detail AS
SELECT ... (huge SQL with function calls) ...
FROM ak_tender t
...
```

### After (Fixed)

**File 1: view_dashboard_detail_with_functions.sql**
```sql
-- Creates a regular view first
DROP VIEW IF EXISTS view_dashboard_detail_prep CASCADE;
CREATE VIEW view_dashboard_detail_prep AS
SELECT ... (SQL with function calls) ...
FROM ak_tender t
...
```

**File 2: create_materialized_view.sql**
```sql
-- Creates materialized view from the prep view
DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;
CREATE MATERIALIZED VIEW view_dashboard_detail AS
SELECT * FROM view_dashboard_detail_prep;

-- Add indexes
CREATE UNIQUE INDEX idx_view_dashboard_detail_unique 
ON view_dashboard_detail (ihale_id, tender_line_id);
```

## Why This Works

1. **Functions are created first** - They exist but aren't executed yet
2. **Prep view is created** - It's a regular view, so functions aren't executed during creation
3. **Materialized view is created** - Now when functions execute, all tables exist

## Verification

After running all three steps, verify:

```sql
-- Check functions exist
\df get_round1_min_price

-- Check prep view exists
\dv view_dashboard_detail_prep

-- Check materialized view exists and has data
SELECT COUNT(*) FROM view_dashboard_detail;

-- Check indexes
\d+ view_dashboard_detail
```

## Quick Commands

**Full installation:**
```bash
cd /opt/odoo18/addons-custom/ak_tender/sql
psql -U odoo -d your_db_name -f functions_dashboard_helpers.sql
psql -U odoo -d your_db_name -f view_dashboard_detail_with_functions.sql
psql -U odoo -d your_db_name -f create_materialized_view.sql
```

**Refresh materialized view:**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
```

**Drop everything and start over:**
```sql
DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;
DROP VIEW IF EXISTS view_dashboard_detail_prep CASCADE;
DROP FUNCTION IF EXISTS get_npv_gain CASCADE;
DROP FUNCTION IF EXISTS get_current_round_min_price CASCADE;
DROP FUNCTION IF EXISTS get_round1_min_price CASCADE;
DROP FUNCTION IF EXISTS get_currency_rate_to_try CASCADE;
DROP FUNCTION IF EXISTS is_approved_supplier CASCADE;
```

## Common Mistakes to Avoid

❌ **Don't** create materialized view before prep view
❌ **Don't** skip creating functions first
❌ **Don't** try to create everything in one file
❌ **Don't** forget to refresh the materialized view after data changes

✅ **Do** follow the 3-step process in order
✅ **Do** verify each step before proceeding
✅ **Do** set up automated refresh for materialized view
✅ **Do** use CONCURRENTLY for production refreshes

## Performance Notes

- **Prep view** (`view_dashboard_detail_prep`): Slower, always current data
- **Materialized view** (`view_dashboard_detail`): Fast, needs periodic refresh
- Use materialized view for dashboards and reports
- Use prep view when you need real-time data

## See Also

- [`INSTALLATION_GUIDE.md`](INSTALLATION_GUIDE.md) - Detailed installation instructions
- [`FUNCTIONS_GUIDE.md`](FUNCTIONS_GUIDE.md) - Function documentation
- [`MATERIALIZED_VIEW_GUIDE.md`](MATERIALIZED_VIEW_GUIDE.md) - Materialized view best practices
