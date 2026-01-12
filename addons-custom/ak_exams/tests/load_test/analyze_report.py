from bs4 import BeautifulSoup
import json
import re
import sys

try:
    with open('addons-custom/ak_exams/tests/load_test/report.html', 'r') as f:
        html_content = f.read()

    # Find the script tag containing stats_data
    start_index = html_content.find('window.templateArgs = ')
        end_index = html_content.find(';\n', start_index)
        if start_index != -1 and end_index != -1:
            json_str = html_content[start_index + len('window.templateArgs = '):end_index]
    
    if script_tag_match:
        json_str = script_tag_match.group(1)
        print(json_str)
    else:
            print("Could not find window.templateArgs in report.")

except Exception as e:
    print(f"Error analyzing report: {e}")
