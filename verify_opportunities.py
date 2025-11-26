
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append('/media/sking/projects/1-pipelines/personal-projects/har-analyzer')

from analyzers.cache_analyzer import CacheAnalyzer

def test_analyze_caching_opportunities():
    df = pd.DataFrame(columns=['url', 'mime_type', 'response_size', 'total_time'])
    
    print("Testing analyze_caching_opportunities with empty DataFrame...")
    try:
        result = CacheAnalyzer.analyze_caching_opportunities(df)
        
        # Check for potential_savings_kb which is used in ui/tabs.py
        if 'potential_savings_kb' not in result:
            print("FAILED: Missing 'potential_savings_kb'")
            print("Result keys:", result.keys())
            sys.exit(1)
        
        print("SUCCESS: All keys present.")
            
    except Exception as e:
        print(f"FAILED: Exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_analyze_caching_opportunities()
