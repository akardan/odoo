#!/usr/bin/env python3
"""
Shell Commands Test Script for AK AI Module
This script tests all commands from SHELL_COMMANDS.md
"""

import sys
from datetime import datetime

# Test results will be saved here
results = []

def log_test(test_name, success, message):
    """Log test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    results.append(f"{status} | {test_name}: {message}")
    print(f"{status} | {test_name}: {message}")

def run_tests():
    """Run all shell command tests"""
    print("=" * 80)
    print(f"AK AI Shell Commands Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test 1: AI Assistant Check
    print("\n=== TEST 1: AI Assistant Check ===")
    try:
        assistant = env['ak_ai.assistant'].search([('active', '=', True)], limit=1)
        if assistant:
            log_test("AI Assistant", True, f"Active assistant found: {assistant.name}")
            print(f"  - Provider: {assistant.ai_provider}")
            print(f"  - Model: {assistant.model_name}")
            print(f"  - API Key exists: {bool(assistant.api_key)}")
        else:
            log_test("AI Assistant", False, "No active assistant found")
    except Exception as e:
        log_test("AI Assistant", False, f"Error: {str(e)}")
    
    # Test 2: Model Mixin Check
    print("\n=== TEST 2: Model Mixin Check ===")
    try:
        tender = env['ak.tender'].search([], limit=1)
        if tender:
            has_mixin = 'ak_ai.mixin' in (tender._inherit if isinstance(tender._inherit, list) else [tender._inherit])
            log_test("Model Mixin", has_mixin, f"ak_ai.mixin in ak.tender: {has_mixin}")
            print(f"  - Model _inherit: {tender._inherit}")
        else:
            log_test("Model Mixin", False, "No tender records found")
    except Exception as e:
        log_test("Model Mixin", False, f"Error: {str(e)}")
    
    # Test 3: List Recent Conversations
    print("\n=== TEST 3: Recent Conversations ===")
    try:
        conversations = env['ak_ai.conversation'].search([], limit=5, order='create_date desc')
        log_test("Conversations", True, f"Found {len(conversations)} conversations")
        for i, conv in enumerate(conversations, 1):
            print(f"  {i}. ID: {conv.id} | {conv.title} | {conv.integration_type} | Messages: {len(conv.message_ids)}")
    except Exception as e:
        log_test("Conversations", False, f"Error: {str(e)}")
    
    # Test 4: Messages Count
    print("\n=== TEST 4: Messages Count ===")
    try:
        messages = env['ak_ai.message'].search([], limit=1)
        total_messages = env['ak_ai.message'].search_count([])
        log_test("Messages", True, f"Total messages in system: {total_messages}")
    except Exception as e:
        log_test("Messages", False, f"Error: {str(e)}")
    
    # Test 5: Interaction Logs
    print("\n=== TEST 5: Interaction Logs ===")
    try:
        logs = env['ak_ai.interaction_log'].search([], limit=10, order='create_date desc')
        log_test("Interaction Logs", True, f"Found {len(logs)} recent logs")
        error_count = 0
        for i, log_entry in enumerate(logs, 1):
            status = "✅" if not log_entry.error_message else "❌"
            print(f"  {i}. {status} {log_entry.create_date} | {log_entry.user_id.name} | Tokens: {log_entry.tokens_used}")
            if log_entry.error_message:
                error_count += 1
                print(f"     Error: {log_entry.error_message[:100]}...")
        if error_count > 0:
            print(f"  ⚠️  Warning: {error_count} logs with errors")
    except Exception as e:
        log_test("Interaction Logs", False, f"Error: {str(e)}")
    
    # Test 6: Module Installation Check
    print("\n=== TEST 6: Module Installation ===")
    try:
        modules = ['ak_ai', 'ak_tender']
        for module_name in modules:
            module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
            if module:
                status = module.state
                log_test(f"Module {module_name}", status == 'installed', f"State: {status}")
            else:
                log_test(f"Module {module_name}", False, "Module not found")
    except Exception as e:
        log_test("Module Installation", False, f"Error: {str(e)}")
    
    # Test 7: Database Configuration
    print("\n=== TEST 7: Database Configuration ===")
    try:
        db_name = env.cr.dbname
        user_name = env.user.name
        company = env.company.name
        log_test("Database Config", True, f"DB: {db_name}, User: {user_name}, Company: {company}")
    except Exception as e:
        log_test("Database Config", False, f"Error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    pass_count = sum(1 for r in results if "✅ PASS" in r)
    fail_count = sum(1 for r in results if "❌ FAIL" in r)
    total = len(results)
    
    for result in results:
        print(result)
    
    print("\n" + "-" * 80)
    print(f"Total Tests: {total} | Passed: {pass_count} | Failed: {fail_count}")
    success_rate = (pass_count / total * 100) if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    return pass_count, fail_count

# Run the tests
if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
