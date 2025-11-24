# analyzers/connection_analyzer.py - Network connection analysis

import pandas as pd
from typing import Dict, List


class ConnectionAnalyzer:
    """Analyzes network connection patterns and efficiency."""
    
    @staticmethod
    def analyze_connections(df: pd.DataFrame) -> Dict:
        """
        Analyze connection patterns and efficiency.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with connection analysis
        """
        if df.empty:
            return {
                'total_requests': 0,
                'analysis_available': False
            }
        
        # Calculate connection metrics
        total_requests = len(df)
        avg_connect_time = df['connect'].mean()
        avg_ssl_time = df['ssl'].mean()
        
        # Identify requests with new connections (connect > 0)
        new_connections = df[df['connect'] > 0]
        reused_connections = df[df['connect'] == 0]
        
        new_conn_count = len(new_connections)
        reused_conn_count = len(reused_connections)
        
        # Calculate connection reuse ratio
        reuse_ratio = (reused_conn_count / total_requests * 100) if total_requests > 0 else 0
        
        # SSL/TLS overhead
        ssl_requests = df[df['ssl'] > 0]
        ssl_overhead = ssl_requests['ssl'].sum()
        total_ssl_requests = len(ssl_requests)
        
        # Connection setup time impact
        total_connect_time = df['connect'].sum()
        total_time = df['total_time'].sum()
        connect_percentage = (total_connect_time / total_time * 100) if total_time > 0 else 0
        
        return {
            'total_requests': total_requests,
            'new_connections': new_conn_count,
            'reused_connections': reused_conn_count,
            'connection_reuse_ratio': round(reuse_ratio, 2),
            'avg_connect_time': round(avg_connect_time, 2),
            'avg_ssl_time': round(avg_ssl_time, 2),
            'total_ssl_requests': total_ssl_requests,
            'ssl_overhead_ms': round(ssl_overhead, 2),
            'connect_time_percentage': round(connect_percentage, 2),
            'analysis_available': True
        }
    
    @staticmethod
    def identify_connection_opportunities(df: pd.DataFrame) -> List[Dict]:
        """
        Identify connection pooling and optimization opportunities.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            List of optimization opportunities
        """
        opportunities = []
        
        analysis = ConnectionAnalyzer.analyze_connections(df)
        
        if not analysis['analysis_available']:
            return opportunities
        
        # Low connection reuse
        if analysis['connection_reuse_ratio'] < 50:
            opportunities.append({
                'priority': 'High',
                'category': 'Connection Pooling',
                'title': 'Low Connection Reuse Detected',
                'description': f"Only {analysis['connection_reuse_ratio']:.1f}% of connections are reused. Enable HTTP keep-alive and connection pooling.",
                'impact': 'Reduce connection overhead by 30-50%',
                'current_value': f"{analysis['connection_reuse_ratio']:.1f}%",
                'target_value': '>80%'
            })
        
        # High connection time
        if analysis['avg_connect_time'] > 100:
            opportunities.append({
                'priority': 'Medium',
                'category': 'Connection Time',
                'title': 'High Connection Setup Time',
                'description': f"Average connection time is {analysis['avg_connect_time']:.1f}ms. Consider using a CDN or optimizing server location.",
                'impact': 'Reduce latency by 50-100ms per request',
                'current_value': f"{analysis['avg_connect_time']:.1f}ms",
                'target_value': '<50ms'
            })
        
        # High SSL overhead
        if analysis['avg_ssl_time'] > 100:
            opportunities.append({
                'priority': 'Medium',
                'category': 'SSL/TLS',
                'title': 'High SSL Handshake Time',
                'description': f"Average SSL handshake takes {analysis['avg_ssl_time']:.1f}ms. Enable TLS session resumption and OCSP stapling.",
                'impact': 'Reduce SSL overhead by 50-80%',
                'current_value': f"{analysis['avg_ssl_time']:.1f}ms",
                'target_value': '<50ms'
            })
        
        # HTTP/2 recommendation
        if analysis['new_connections'] > 10:
            opportunities.append({
                'priority': 'High',
                'category': 'Protocol Upgrade',
                'title': 'Consider HTTP/2 or HTTP/3',
                'description': f"With {analysis['new_connections']} new connections, HTTP/2 multiplexing could significantly improve performance.",
                'impact': 'Reduce connection overhead and enable request multiplexing',
                'current_value': 'HTTP/1.1 (assumed)',
                'target_value': 'HTTP/2 or HTTP/3'
            })
        
        return opportunities
    
    @staticmethod
    def get_connection_breakdown(df: pd.DataFrame) -> pd.DataFrame:
        """
        Get breakdown of connection metrics by domain.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with connection breakdown by domain
        """
        from urllib.parse import urlparse
        
        if df.empty:
            return pd.DataFrame()
        
        # Extract domain
        df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
        
        # Group by domain
        breakdown = df.groupby('domain').agg({
            'connect': ['count', 'mean', 'sum'],
            'ssl': ['mean', 'sum']
        }).reset_index()
        
        # Flatten column names
        breakdown.columns = ['domain', 'request_count', 'avg_connect', 'total_connect', 'avg_ssl', 'total_ssl']
        
        # Calculate new connections (connect > 0)
        new_conn_by_domain = df[df['connect'] > 0].groupby('domain').size().reset_index(name='new_connections')
        breakdown = breakdown.merge(new_conn_by_domain, on='domain', how='left')
        breakdown['new_connections'] = breakdown['new_connections'].fillna(0).astype(int)
        
        # Calculate reuse ratio
        breakdown['reuse_ratio'] = ((breakdown['request_count'] - breakdown['new_connections']) / breakdown['request_count'] * 100).round(2)
        
        # Sort by total connect time
        breakdown = breakdown.sort_values('total_connect', ascending=False)
        
        return breakdown[['domain', 'request_count', 'new_connections', 'reuse_ratio', 'avg_connect', 'avg_ssl']]
