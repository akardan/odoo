# Installation Guide for Dashboard View with Functions

## Overview

This guide explains how to properly install the dashboard view system that uses PostgreSQL functions for better performance and maintainability.

## Architecture

The system consists of three layers:

1. **Helper Functions** (`functions_dashboard_helpers.sql`) - Reusable PostgreSQL functions
2. **Preparation View** (`view_dashboard_detail_with_functions.sql`) - Creates `view_dashboard_detail_prep` view
3. **Materialized View** (`create_materialized_view.sql`) - Creates `view_dashboard_detail` materialized view

## Prerequisites

- PostgreSQL database with Odoo 18 CE installed
- The following Odoo modules must be installed and have data:
  - `purchase` (purchase_order table)
  - `product` (product_product, product_template tables)
  - `ak_tender` (custom tender module)
- Database user with CREATE FUNCTION and CREATE VIEW privileges

## Installation Steps

### Step 1: Create Helper Functions

First, create the PostgreSQL helper functions:

```bash
psql -U odoo -d your_database_name -f addons-custom/ak_tender/sql/functions_dashboard_helpers.sql
```

**What this does:**
- Creates `is_approved_supplier()` function
- Creates `get_currency_rate_to_try()` function
- Creates `get_round1_min_price()` function
- Creates `get_current_round_min_price()` function
- Creates `get_npv_gain()` function

**Verify:**
```sql
\df is_approved_supplier
\df get_round1_min_price
\df get_current_round_min_price
\df get_npv_gain
\df get_currency_rate_to_try
```

### Step 2: Create Preparation View

Next, create the preparation view that uses the functions:

```bash
psql -U odoo -d your_database_name -f addons-custom/ak_tender/sql/view_dashboard_detail_with_functions.sql
```

**What this does:**
- Drops any existing `view_dashboard_detail_prep` view
- Creates new `view_dashboard_detail_prep` view using the helper functions

**Verify:**
```sql
SELECT COUNT(*) FROM view_dashboard_detail_prep;
```

### Step 3: Create Materialized View

Finally, create the materialized view for optimal performance:

```bash
psql -U odoo -d your_database_name -f addons-custom/ak_tender/sql/create_materialized_view.sql
```

**What this does:**
- Drops any existing `view_dashboard_detail` materialized view
- Creates new `view_dashboard_detail` materialized view from prep view
- Creates indexes for better query performance

**Verify:**
```sql
SELECT COUNT(*) FROM view_dashboard_detail;
\d+ view_dashboard_detail
```

## Troubleshooting

### Error: "relation 'purchase_order' does not exist"

**Cause:** The `purchase` module is not installed or the database doesn't have the purchase_order table.

**Solution:**
1. Verify the purchase module is installed:
   ```sql
   SELECT name, state FROM ir_module_module WHERE name = 'purchase';
   ```
2. Check if the table exists:
   ```sql
   \dt purchase_order
   ```
3. If not installed, install it through Odoo UI or:
   ```bash
   odoo-bin -d your_database_name -i purchase --stop-after-init
   ```

### Error: "function get_round1_min_price does not exist"

**Cause:** Step 1 (creating functions) was skipped or failed.

**Solution:**
1. Run Step 1 again:
   ```bash
   psql -U odoo -d your_database_name -f addons-custom/ak_tender/sql/functions_dashboard_helpers.sql
   ```
2. Verify functions exist:
   ```sql
   \df get_*
   ```

### Error: "relation 'view_dashboard_detail_prep' does not exist"

**Cause:** Step 2 (creating prep view) was skipped or failed.

**Solution:**
1. Run Step 2 again:
   ```bash
   psql -U odoo -d your_database_name -f addons-custom/ak_tender/sql/view_dashboard_detail_with_functions.sql
   ```
2. Verify view exists:
   ```sql
   \dv view_dashboard_detail_prep
   ```

### Error: "could not create unique index"

**Cause:** Duplicate records exist with same (ihale_id, tender_line_id) combination.

**Solution:**
1. Check for duplicates:
   ```sql
   SELECT ihale_id, tender_line_id, COUNT(*) 
   FROM view_dashboard_detail_prep 
   GROUP BY ihale_id, tender_line_id 
   HAVING COUNT(*) > 1;
   ```
2. Fix data issues in source tables before creating materialized view

## Maintenance

### Refreshing the Materialized View

The materialized view needs to be refreshed periodically to reflect new data:

**Manual refresh (locks the view):**
```sql
REFRESH MATERIALIZED VIEW view_dashboard_detail;
```

**Concurrent refresh (no locking, requires unique index):**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;
```

### Automated Refresh with Cron

Add to your system crontab to refresh every 15 minutes:

```bash
*/15 * * * * psql -U odoo -d your_database_name -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;" >> /var/log/odoo/view_refresh.log 2>&1
```

Or every hour:
```bash
0 * * * * psql -U odoo -d your_database_name -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_dashboard_detail;" >> /var/log/odoo/view_refresh.log 2>&1
```

### Monitoring View Performance

Check view size:
```sql
SELECT pg_size_pretty(pg_total_relation_size('view_dashboard_detail'));
```

Check last refresh time:
```sql
SELECT schemaname, matviewname, last_refresh 
FROM pg_matviews 
WHERE matviewname = 'view_dashboard_detail';
```

Check index usage:
```sql
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE relname = 'view_dashboard_detail';
```

## Uninstallation

To remove all components:

```sql
-- Drop materialized view
DROP MATERIALIZED VIEW IF EXISTS view_dashboard_detail CASCADE;

-- Drop preparation view
DROP VIEW IF EXISTS view_dashboard_detail_prep CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS get_npv_gain(INTEGER, INTEGER, INTEGER, INTEGER, BOOLEAN);
DROP FUNCTION IF EXISTS get_current_round_min_price(INTEGER, INTEGER, INTEGER, INTEGER, TEXT, BOOLEAN);
DROP FUNCTION IF EXISTS get_round1_min_price(INTEGER, INTEGER, INTEGER, TEXT, BOOLEAN);
DROP FUNCTION IF EXISTS get_currency_rate_to_try(INTEGER, INTEGER, DATE);
DROP FUNCTION IF EXISTS is_approved_supplier(INTEGER, INTEGER, INTEGER);
```

## Performance Tips

1. **Use the materialized view** for reporting and dashboards
2. **Use the prep view** for real-time queries when you need latest data
3. **Refresh frequency** depends on your needs:
   - Real-time dashboards: Every 5-15 minutes
   - Daily reports: Once per day
   - Historical analysis: Once per week
4. **Monitor query performance** and add indexes as needed
5. **Consider partitioning** if the view grows very large (>1M rows)

## Support

For issues or questions:
1. Check the error message carefully
2. Verify all prerequisites are met
3. Follow the troubleshooting guide above
4. Check PostgreSQL logs: `/var/log/postgresql/`
5. Check Odoo logs for related errors
