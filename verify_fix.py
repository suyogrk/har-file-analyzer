
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append('/media/sking/projects/1-pipelines/personal-projects/har-analyzer')

from analyzers.cache_analyzer import CacheAnalyzer

def test_empty_dataframe():
    df = pd.DataFrame(columns=['url', 'mime_type', 'response_size', 'total_time'])
    
    print("Testing with empty DataFrame...")
    try:
        result = CacheAnalyzer.calculate_repeat_visit_savings(df)
        
        required_keys = [
            'bandwidth_saved', 'bandwidth_saved_kb', 'bandwidth_saved_mb',
            'time_saved', 'time_saved_seconds', 'requests_saved', 'cache_hit_rate'
        ]
        
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"FAILED: Missing keys: {missing_keys}")
            sys.exit(1)
        else:
            print("SUCCESS: All keys present.")
            print("Result:", result)
            
    except Exception as e:
        print(f"FAILED: Exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_empty_dataframe()
