# analyzers/cache_analyzer.py - HTTP caching analysis

import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta


class CacheAnalyzer:
    """Analyzes HTTP caching headers and identifies optimization opportunities."""
    
    # Cache-Control directives
    CACHE_DIRECTIVES = [
        'max-age', 'no-cache', 'no-store', 'must-revalidate',
        'public', 'private', 'immutable', 's-maxage'
    ]
    
    @staticmethod
    def parse_cache_headers(df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse cache-related headers from HAR entries.
        
        Note: HAR files may not always include response headers.
        This is a best-effort analysis based on available data.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with cache header information
        """
        if df.empty:
            return pd.DataFrame()
        
        # Create a copy to avoid modifying original
        cache_df = df.copy()
        
        # Initialize cache-related columns
        cache_df['has_cache_control'] = False
        cache_df['has_etag'] = False
        cache_df['has_expires'] = False
        cache_df['has_last_modified'] = False
        cache_df['cache_directive'] = 'unknown'
        cache_df['max_age'] = 0
        cache_df['is_cacheable'] = False
        
        # Note: In a real HAR file, headers would be in response.headers
        # For now, we'll infer cacheability based on resource type and URL patterns
        cache_df['is_cacheable'] = CacheAnalyzer._infer_cacheability(cache_df)
        
        return cache_df
    
    @staticmethod
    def _infer_cacheability(df: pd.DataFrame) -> pd.Series:
        """
        Infer cacheability based on resource type and URL patterns.
        
        This is a heuristic approach when actual headers aren't available.
        """
        # Static file extensions that are typically cacheable
        cacheable_patterns = [
            r'\.js$', r'\.css$', r'\.png$', r'\.jpg$', r'\.jpeg$',
            r'\.gif$', r'\.webp$', r'\.svg$', r'\.ico$',
            r'\.woff$', r'\.woff2$', r'\.ttf$', r'\.eot$', r'\.otf$',
            r'\.mp4$', r'\.webm$', r'\.mp3$', r'\.pdf$'
        ]
        
        # Check if URL matches cacheable patterns
        is_cacheable = df['url'].str.contains('|'.join(cacheable_patterns), case=False, na=False, regex=True)
        
        # Exclude API calls (typically not cacheable)
        is_api = df['url'].str.contains(r'/api/|/graphql', case=False, na=False, regex=True)
        
        return is_cacheable & ~is_api
    
    @staticmethod
    def analyze_caching_opportunities(df: pd.DataFrame) -> Dict:
        """
        Analyze caching opportunities and potential savings.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with caching analysis
        """
        if df.empty:
            return {
                'total_requests': 0,
                'cacheable_requests': 0,
                'cacheable_percentage': 0,
                'potential_bandwidth_savings': 0,
                'recommendations': []
            }
        
        cache_df = CacheAnalyzer.parse_cache_headers(df)
        
        total_requests = len(cache_df)
        cacheable_requests = cache_df['is_cacheable'].sum()
        cacheable_percentage = (cacheable_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate potential bandwidth savings (assuming 80% cache hit rate on repeat visits)
        cacheable_size = cache_df[cache_df['is_cacheable']]['response_size'].sum()
        potential_savings = cacheable_size * 0.8  # 80% cache hit rate
        
        # Generate recommendations by resource type
        recommendations = CacheAnalyzer._generate_cache_recommendations(cache_df)
        
        # Get cacheable resources breakdown
        cacheable_breakdown = CacheAnalyzer._get_cacheable_breakdown(cache_df)
        
        return {
            'total_requests': total_requests,
            'cacheable_requests': int(cacheable_requests),
            'cacheable_percentage': round(cacheable_percentage, 2),
            'potential_bandwidth_savings': potential_savings,
            'potential_savings_kb': round(potential_savings / 1024, 2),
            'recommendations': recommendations,
            'cacheable_breakdown': cacheable_breakdown
        }
    
    @staticmethod
    def _generate_cache_recommendations(cache_df: pd.DataFrame) -> List[Dict]:
        """Generate caching recommendations based on analysis."""
        from analyzers.resource_analyzer import ResourceAnalyzer
        
        recommendations = []
        
        # Classify resources
        cache_df['resource_type'] = cache_df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        # Recommend cache durations by resource type
        cache_durations = {
            'JavaScript': '1 year (immutable)',
            'CSS': '1 year (immutable)',
            'Images': '1 year',
            'Fonts': '1 year (immutable)',
            'HTML': '5 minutes to 1 hour',
            'JSON': '5 minutes (API responses)',
        }
        
        for resource_type, duration in cache_durations.items():
            type_df = cache_df[
                (cache_df['resource_type'] == resource_type) &
                (cache_df['is_cacheable'])
            ]
            
            if not type_df.empty:
                total_size = type_df['response_size'].sum()
                count = len(type_df)
                
                recommendations.append({
                    'resource_type': resource_type,
                    'count': count,
                    'total_size': total_size,
                    'recommended_duration': duration,
                    'priority': 'High' if total_size > 100 * 1024 else 'Medium'
                })
        
        return recommendations
    
    @staticmethod
    def _get_cacheable_breakdown(cache_df: pd.DataFrame) -> Dict:
        """Get breakdown of cacheable vs non-cacheable resources."""
        from analyzers.resource_analyzer import ResourceAnalyzer
        
        cache_df['resource_type'] = cache_df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        breakdown = cache_df.groupby(['resource_type', 'is_cacheable']).agg({
            'url': 'count',
            'response_size': 'sum'
        }).reset_index()
        
        breakdown.columns = ['resource_type', 'is_cacheable', 'count', 'total_size']
        
        return breakdown.to_dict('records')
    
    @staticmethod
    def get_non_cacheable_resources(df: pd.DataFrame) -> pd.DataFrame:
        """
        Get resources that should be cacheable but aren't.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with non-cacheable resources
        """
        cache_df = CacheAnalyzer.parse_cache_headers(df)
        
        # Resources that could be cached but aren't
        should_cache = cache_df[cache_df['is_cacheable']].copy()
        
        if should_cache.empty:
            return pd.DataFrame()
        
        # Add resource type
        from analyzers.resource_analyzer import ResourceAnalyzer
        should_cache['resource_type'] = should_cache['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        # Sort by size (largest first)
        should_cache = should_cache.sort_values('response_size', ascending=False)
        
        return should_cache[['url', 'resource_type', 'response_size', 'total_time']]
    
    @staticmethod
    def calculate_repeat_visit_savings(df: pd.DataFrame, cache_hit_rate: float = 0.8) -> Dict:
        """
        Calculate bandwidth and time savings on repeat visits.
        
        Args:
            df: DataFrame with HAR entries
            cache_hit_rate: Expected cache hit rate (default 80%)
            
        Returns:
            Dictionary with savings calculations
        """
        cache_df = CacheAnalyzer.parse_cache_headers(df)
        
        cacheable_df = cache_df[cache_df['is_cacheable']]
        
        if cacheable_df.empty:
            return {
                'bandwidth_saved': 0,
                'time_saved': 0,
                'requests_saved': 0
            }
        
        # Calculate savings
        total_cacheable_size = cacheable_df['response_size'].sum()
        total_cacheable_time = cacheable_df['total_time'].sum()
        total_cacheable_requests = len(cacheable_df)
        
        bandwidth_saved = total_cacheable_size * cache_hit_rate
        time_saved = total_cacheable_time * cache_hit_rate
        requests_saved = total_cacheable_requests * cache_hit_rate
        
        return {
            'bandwidth_saved': bandwidth_saved,
            'bandwidth_saved_kb': round(bandwidth_saved / 1024, 2),
            'bandwidth_saved_mb': round(bandwidth_saved / (1024 * 1024), 2),
            'time_saved': round(time_saved, 2),
            'time_saved_seconds': round(time_saved / 1000, 2),
            'requests_saved': int(requests_saved),
            'cache_hit_rate': cache_hit_rate * 100
        }
    
    @staticmethod
    def get_cache_summary(df: pd.DataFrame) -> Dict:
        """
        Get comprehensive cache analysis summary.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with complete cache analysis
        """
        opportunities = CacheAnalyzer.analyze_caching_opportunities(df)
        savings = CacheAnalyzer.calculate_repeat_visit_savings(df)
        non_cacheable = CacheAnalyzer.get_non_cacheable_resources(df)
        
        return {
            'opportunities': opportunities,
            'repeat_visit_savings': savings,
            'non_cacheable_count': len(non_cacheable),
            'recommendations_count': len(opportunities['recommendations'])
        }
