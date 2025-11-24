# analyzers/domain_analyzer.py - Domain-wise performance analysis

import pandas as pd
from urllib.parse import urlparse
from typing import Dict, List
from collections import defaultdict


class DomainAnalyzer:
    """Analyzes requests grouped by domain to identify third-party dependencies."""
    
    @staticmethod
    def analyze_by_domain(df: pd.DataFrame) -> pd.DataFrame:
        """
        Group requests by domain and calculate statistics.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with domain-wise statistics
        """
        if df.empty:
            return pd.DataFrame()
        
        # Extract domain from URL if not already present
        if 'domain' not in df.columns:
            df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
        
        # Group by domain and calculate statistics
        domain_stats = df.groupby('domain').agg({
            'url': 'count',
            'total_time': ['sum', 'mean', 'max'],
            'response_size': 'sum',
            'status': lambda x: (x >= 400).sum()
        }).round(2)
        
        # Flatten column names
        domain_stats.columns = [
            'request_count',
            'total_time_sum',
            'avg_time',
            'max_time',
            'total_size',
            'error_count'
        ]
        
        domain_stats = domain_stats.reset_index()
        
        # Calculate percentage of total requests
        total_requests = len(df)
        domain_stats['request_percentage'] = (
            domain_stats['request_count'] / total_requests * 100
        ).round(2)
        
        # Calculate percentage of total time
        total_time = df['total_time'].sum()
        if total_time > 0:
            domain_stats['time_percentage'] = (
                domain_stats['total_time_sum'] / total_time * 100
            ).round(2)
        else:
            domain_stats['time_percentage'] = 0
        
        # Sort by total time (descending)
        domain_stats = domain_stats.sort_values('total_time_sum', ascending=False)
        
        return domain_stats
    
    @staticmethod
    def identify_third_party_domains(df: pd.DataFrame, main_domain: str = None) -> Dict:
        """
        Identify third-party domains (external dependencies).
        
        Args:
            df: DataFrame with HAR entries
            main_domain: Main domain to compare against (auto-detected if None)
            
        Returns:
            Dictionary with third-party analysis
        """
        if df.empty:
            return {
                'main_domain': None,
                'third_party_domains': [],
                'third_party_count': 0,
                'third_party_percentage': 0
            }
        
        # Extract domains
        if 'domain' not in df.columns:
            df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
        
        # Auto-detect main domain if not provided
        if main_domain is None:
            # Use the domain with the most requests
            main_domain = df['domain'].value_counts().index[0]
        
        # Identify third-party domains
        third_party_mask = ~df['domain'].str.contains(main_domain, na=False, regex=False)
        third_party_df = df[third_party_mask]
        
        third_party_domains = third_party_df['domain'].unique().tolist()
        third_party_count = len(third_party_df)
        third_party_percentage = (third_party_count / len(df) * 100) if len(df) > 0 else 0
        
        # Get statistics for third-party domains
        third_party_stats = []
        for domain in third_party_domains:
            domain_df = third_party_df[third_party_df['domain'] == domain]
            third_party_stats.append({
                'domain': domain,
                'request_count': len(domain_df),
                'total_time': domain_df['total_time'].sum(),
                'avg_time': domain_df['total_time'].mean(),
                'total_size': domain_df['response_size'].sum()
            })
        
        # Sort by total time
        third_party_stats = sorted(
            third_party_stats,
            key=lambda x: x['total_time'],
            reverse=True
        )
        
        return {
            'main_domain': main_domain,
            'third_party_domains': third_party_stats,
            'third_party_count': third_party_count,
            'third_party_percentage': round(third_party_percentage, 2),
            'total_requests': len(df)
        }
    
    @staticmethod
    def detect_cdn_usage(df: pd.DataFrame) -> List[Dict]:
        """
        Detect CDN usage based on common CDN domain patterns.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            List of detected CDN services
        """
        if df.empty:
            return []
        
        # Common CDN patterns
        cdn_patterns = {
            'Cloudflare': ['cloudflare', 'cdnjs.cloudflare.com'],
            'AWS CloudFront': ['cloudfront.net'],
            'Fastly': ['fastly.net'],
            'Akamai': ['akamai', 'akamaihd.net'],
            'Google Cloud CDN': ['googleapis.com', 'gstatic.com'],
            'Azure CDN': ['azureedge.net'],
            'Cloudinary': ['cloudinary.com'],
            'jsDelivr': ['jsdelivr.net'],
            'unpkg': ['unpkg.com'],
            'MaxCDN': ['maxcdn.com'],
        }
        
        # Extract domains
        if 'domain' not in df.columns:
            df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
        
        detected_cdns = []
        
        for cdn_name, patterns in cdn_patterns.items():
            for pattern in patterns:
                cdn_df = df[df['domain'].str.contains(pattern, na=False, case=False)]
                if not cdn_df.empty:
                    detected_cdns.append({
                        'cdn_name': cdn_name,
                        'request_count': len(cdn_df),
                        'total_size': cdn_df['response_size'].sum(),
                        'avg_time': cdn_df['total_time'].mean(),
                        'domains': cdn_df['domain'].unique().tolist()
                    })
                    break  # Only count each CDN once
        
        return detected_cdns
    
    @staticmethod
    def get_slowest_domains(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """
        Get the slowest domains by average response time.
        
        Args:
            df: DataFrame with HAR entries
            limit: Number of domains to return
            
        Returns:
            DataFrame with slowest domains
        """
        domain_stats = DomainAnalyzer.analyze_by_domain(df)
        
        if domain_stats.empty:
            return pd.DataFrame()
        
        # Filter domains with at least 2 requests to avoid outliers
        domain_stats = domain_stats[domain_stats['request_count'] >= 2]
        
        # Sort by average time
        slowest = domain_stats.sort_values('avg_time', ascending=False).head(limit)
        
        return slowest[['domain', 'request_count', 'avg_time', 'max_time', 'total_size']]
    
    @staticmethod
    def calculate_domain_impact(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate performance impact of each domain.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with domain impact scores
        """
        domain_stats = DomainAnalyzer.analyze_by_domain(df)
        
        if domain_stats.empty:
            return pd.DataFrame()
        
        # Calculate impact score (combination of time and request percentage)
        domain_stats['impact_score'] = (
            domain_stats['time_percentage'] * 0.7 +
            domain_stats['request_percentage'] * 0.3
        ).round(2)
        
        # Add impact level
        domain_stats['impact_level'] = domain_stats['impact_score'].apply(
            lambda x: 'High' if x > 20 else 'Medium' if x > 10 else 'Low'
        )
        
        # Sort by impact score
        domain_stats = domain_stats.sort_values('impact_score', ascending=False)
        
        return domain_stats
