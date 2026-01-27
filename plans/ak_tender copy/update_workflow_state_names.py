#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to update workflow_state_name field for all existing tender records
Run this script from Odoo shell to recompute workflow_state_name field

Usage:
    odoo-bin shell -d your_database_name --addons-path=addons,addons-custom
    
Then in the Odoo shell:
    >>> exec(open('addons-custom/ak_tender/update_workflow_state_names.py').read())
"""

# Get all tender records
tenders = env['ak.tender'].search([])

print(f"Found {len(tenders)} tender records to update...")

# Force recomputation of workflow_state_name field
if tenders:
    # Method 1: Using _compute method directly
    tenders._compute_workflow_state_name()
    print(f"Successfully recomputed workflow_state_name for {len(tenders)} records")
    
    # Verify some results
    print("\nSample results:")
    for tender in tenders[:5]:
        print(f"  Tender {tender.code}: workflow_state_name = '{tender.workflow_state_name}'")
else:
    print("No tender records found")

print("\nDone!")
