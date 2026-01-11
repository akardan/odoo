from bs4 import BeautifulSoup
import json
import re
import sys

try:
    with open('addons-custom/ak_exams/tests/load_test/report.html', 'r') as f:
        html = f.read()

    # Look for stats_data
    match = re.search(r'var stats_data = ({.*?});', html, re.DOTALL)
    if match:
        data = json.loads(match.group(1))
        
        print("--- LOAD TEST REPORT ANALYSIS ---")
        
        # Find Aggregated stats
        agg_stats = None
        for s in data.get('stats', []):
            if s['name'] == 'Aggregated':
                agg_stats = s
                break
        
        if agg_stats:
            total_reqs = agg_stats.get('num_requests', 0)
            total_fails = agg_stats.get('num_failures', 0)
            avg_time = agg_stats.get('avg_response_time', 0)
            max_time = agg_stats.get('max_response_time', 0)
            
            fail_rate = (total_fails / total_reqs * 100) if total_reqs > 0 else 0
            
            print(f"Total Requests: {total_reqs}")
            print(f"Total Failures: {total_fails}")
            print(f"Failure Rate: {fail_rate:.2f}%")
            print(f"Average Response Time: {avg_time:.2f} ms")
            print(f"Max Response Time: {max_time:.2f} ms")
            
            # Check for specific errors
            errors = data.get('errors', {})
            if errors:
                print("\n--- ERRORS ---")
                for err in list(errors.values())[:5]: # Show top 5 errors
                    print(f"{err['occurrences']}x {err['method']} {err['name']}: {err['error']}")
        else:
            print("Aggregated stats not found.")
            
    else:
        print("Could not find stats_data in report.")

except Exception as e:
    print(f"Error analyzing report: {e}")
