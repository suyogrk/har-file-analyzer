# analyzers/performance_analyzer.py - Performance analysis

import pandas as pd
from typing import List, Dict, Any, Union, Optional
from config import (
    SLOW_RESPONSE_THRESHOLD_MS,
    HIGH_WAIT_TIME_THRESHOLD_MS,
    CONNECTION_DELAY_THRESHOLD_MS,
    DNS_DELAY_THRESHOLD_MS,
)


class PerformanceAnalyzer:
    """Analyzes HAR data for performance issues."""
    
    @staticmethod
    def identify_problematic_apis(df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify problematic APIs based on performance criteria.
        Uses fully vectorized operations for optimal performance.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with additional 'problems' and 'is_problematic' columns
        """
        if df.empty:
            return df
        
        # Create boolean masks for each issue type (vectorized)
        slow_response = df['total_time'] > SLOW_RESPONSE_THRESHOLD_MS
        high_wait = df['wait'] > HIGH_WAIT_TIME_THRESHOLD_MS
        error_status = df['status'] >= 400
        connection_delay = df['connect'] > CONNECTION_DELAY_THRESHOLD_MS
        dns_delay = df['dns'] > DNS_DELAY_THRESHOLD_MS
        
        # Create a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Use vectorized string operations to build problems list
        # This is much faster than using apply with a function
        problems = pd.Series(index=df.index, dtype=str)
        
        # Initialize with 'No Issues'
        problems[:] = 'No Issues'
        
        # Add issues using vectorized operations
        # Each condition updates only the rows that match
        mask = slow_response
        problems.loc[mask] = problems.loc[mask] + ', Slow Response'
        
        mask = high_wait
        problems.loc[mask] = problems.loc[mask] + ', High Server Wait'
        
        mask = error_status
        problems.loc[mask] = problems.loc[mask] + ', Error Response'
        
        mask = connection_delay
        problems.loc[mask] = problems.loc[mask] + ', Connection Delay'
        
        mask = dns_delay
        problems.loc[mask] = problems.loc[mask] + ', DNS Delay'
        
        # Clean up the leading ', ' for entries with issues
        problems = problems.str.replace('^No Issues, ', '', regex=True)
        
        # Add the problems column to the DataFrame
        df['problems'] = problems
        
        # Mark problematic entries (vectorized)
        df['is_problematic'] = df['problems'] != 'No Issues'
        
        return df
    
    @staticmethod
    def _identify_issues(row: pd.Series) -> str:
        """Identify issues in a single request."""
        issues = []
        
        # Slow response (>1000ms)
        if row['total_time'] > SLOW_RESPONSE_THRESHOLD_MS:
            issues.append('Slow Response')
        
        # High server wait time (>500ms)
        if row['wait'] > HIGH_WAIT_TIME_THRESHOLD_MS:
            issues.append('High Server Wait')
        
        # Error status codes
        if row['status'] >= 400:
            issues.append('Error Response')
        
        # Connection issues
        if row['connect'] > CONNECTION_DELAY_THRESHOLD_MS:
            issues.append('Connection Delay')
        
        # DNS issues
        if row['dns'] > DNS_DELAY_THRESHOLD_MS:
            issues.append('DNS Delay')
        
        return ', '.join(issues) if issues else 'No Issues'
    
    @staticmethod
    def get_statistics(df: pd.DataFrame) -> Dict[str, Union[int, float]]:
        """Get performance statistics from the data."""
        return {
            'total_requests': len(df),
            'unique_endpoints': df['endpoint'].nunique(),
            'error_rate': (df['status'] >= 400).mean() * 100,
            'avg_response_time': df['total_time'].mean(),
            'max_response_time': df['total_time'].max(),
            'min_response_time': df['total_time'].min(),
            'problematic_count': (df['is_problematic']).sum() if 'is_problematic' in df.columns else 0,
        }
    
    @staticmethod
    def get_slowest_endpoints(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """Get the slowest endpoints."""
        endpoint_stats = df.groupby('endpoint').agg({
            'total_time': ['mean', 'count']
        }).round(2)
        
        endpoint_stats.columns = ['avg_response_time', 'request_count']
        endpoint_stats = endpoint_stats.reset_index()
        endpoint_stats = endpoint_stats[endpoint_stats['request_count'] >= 1]
        endpoint_stats = endpoint_stats.sort_values(
            'avg_response_time', 
            ascending=False
        ).head(limit)
        
        return endpoint_stats
