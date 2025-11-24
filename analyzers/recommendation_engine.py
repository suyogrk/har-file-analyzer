# analyzers/recommendation_engine.py - Automated performance recommendations

import pandas as pd
from typing import List, Dict
from dataclasses import dataclass
from analyzers.performance_analyzer import PerformanceAnalyzer
from analyzers.domain_analyzer import DomainAnalyzer
from analyzers.resource_analyzer import ResourceAnalyzer


@dataclass
class Recommendation:
    """Performance recommendation."""
    priority: str  # High, Medium, Low
    category: str
    title: str
    description: str
    impact: str
    effort: str  # Low, Medium, High
    
    def to_dict(self) -> Dict:
        return {
            'priority': self.priority,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'impact': self.impact,
            'effort': self.effort
        }


class RecommendationEngine:
    """Generates automated performance recommendations based on HAR analysis."""
    
    @staticmethod
    def generate_recommendations(df: pd.DataFrame) -> List[Recommendation]:
        """
        Generate comprehensive performance recommendations.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            List of Recommendation objects, sorted by priority
        """
        if df.empty:
            return []
        
        recommendations = []
        
        # DNS recommendations
        recommendations.extend(RecommendationEngine._check_dns_issues(df))
        
        # Connection recommendations
        recommendations.extend(RecommendationEngine._check_connection_issues(df))
        
        # Caching recommendations
        recommendations.extend(RecommendationEngine._check_caching_opportunities(df))
        
        # Compression recommendations
        recommendations.extend(RecommendationEngine._check_compression_opportunities(df))
        
        # Resource consolidation
        recommendations.extend(RecommendationEngine._check_resource_consolidation(df))
        
        # Third-party recommendations
        recommendations.extend(RecommendationEngine._check_third_party_impact(df))
        
        # Server performance
        recommendations.extend(RecommendationEngine._check_server_performance(df))
        
        # HTTP/2 recommendations
        recommendations.extend(RecommendationEngine._check_http_version(df))
        
        # Sort by priority
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return recommendations
    
    @staticmethod
    def _check_dns_issues(df: pd.DataFrame) -> List[Recommendation]:
        """Check for DNS-related issues."""
        recommendations = []
        
        avg_dns = df['dns'].mean()
        high_dns_count = (df['dns'] > 50).sum()
        high_dns_pct = (high_dns_count / len(df) * 100) if len(df) > 0 else 0
        
        if avg_dns > 50:
            recommendations.append(Recommendation(
                priority='High' if avg_dns > 100 else 'Medium',
                category='DNS',
                title='Implement DNS Prefetching',
                description=f'Average DNS lookup time is {avg_dns:.1f}ms. Implement DNS prefetching for external domains to reduce latency.',
                impact=f'Could save ~{avg_dns * 0.7:.0f}ms per request',
                effort='Low'
            ))
        
        if high_dns_pct > 20:
            recommendations.append(Recommendation(
                priority='Medium',
                category='DNS',
                title='Optimize DNS Resolution',
                description=f'{high_dns_pct:.1f}% of requests have slow DNS lookups (>50ms). Consider using a faster DNS provider or implementing DNS caching.',
                impact='Improved initial connection time',
                effort='Medium'
            ))
        
        return recommendations
    
    @staticmethod
    def _check_connection_issues(df: pd.DataFrame) -> List[Recommendation]:
        """Check for connection-related issues."""
        recommendations = []
        
        avg_connect = df['connect'].mean()
        high_connect_count = (df['connect'] > 200).sum()
        
        if avg_connect > 200:
            recommendations.append(Recommendation(
                priority='High',
                category='Connection',
                title='Implement Connection Pooling',
                description=f'Average connection time is {avg_connect:.1f}ms. Enable keep-alive and connection pooling to reuse connections.',
                impact=f'Could save ~{avg_connect * 0.8:.0f}ms per request',
                effort='Low'
            ))
        
        # Check SSL handshake time
        avg_ssl = df['ssl'].mean()
        if avg_ssl > 100:
            recommendations.append(Recommendation(
                priority='Medium',
                category='SSL/TLS',
                title='Optimize SSL/TLS Handshake',
                description=f'Average SSL handshake time is {avg_ssl:.1f}ms. Consider implementing TLS session resumption and OCSP stapling.',
                impact='Faster secure connections',
                effort='Medium'
            ))
        
        return recommendations
    
    @staticmethod
    def _check_caching_opportunities(df: pd.DataFrame) -> List[Recommendation]:
        """Check for caching opportunities."""
        recommendations = []
        
        # This is a simplified check - full cache header analysis would be in cache_analyzer
        static_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.woff', '.woff2', '.ttf']
        
        potentially_cacheable = df[df['url'].str.contains('|'.join(static_extensions), na=False, case=False)]
        
        if len(potentially_cacheable) > 10:
            recommendations.append(Recommendation(
                priority='High',
                category='Caching',
                title='Implement Browser Caching',
                description=f'Found {len(potentially_cacheable)} static resources that could benefit from caching. Set appropriate Cache-Control headers.',
                impact=f'Reduce bandwidth by ~{len(potentially_cacheable) * 0.8:.0f} requests on repeat visits',
                effort='Low'
            ))
        
        return recommendations
    
    @staticmethod
    def _check_compression_opportunities(df: pd.DataFrame) -> List[Recommendation]:
        """Check for compression opportunities."""
        recommendations = []
        
        compression_analysis = ResourceAnalyzer.analyze_compression_opportunities(df)
        
        if compression_analysis['savings_percentage'] > 15:
            recommendations.append(Recommendation(
                priority='High',
                category='Compression',
                title='Enable Gzip/Brotli Compression',
                description=f"Enable compression for text-based resources. Potential savings: {compression_analysis['potential_savings']/1024:.1f}KB ({compression_analysis['savings_percentage']:.1f}%).",
                impact=f"Reduce bandwidth by {compression_analysis['savings_percentage']:.1f}%",
                effort='Low'
            ))
        
        return recommendations
    
    @staticmethod
    def _check_resource_consolidation(df: pd.DataFrame) -> List[Recommendation]:
        """Check for resource consolidation opportunities."""
        recommendations = []
        
        resource_stats = ResourceAnalyzer.analyze_by_resource_type(df)
        
        if not resource_stats.empty:
            js_count = resource_stats[resource_stats['resource_type'] == 'JavaScript']['count'].sum()
            css_count = resource_stats[resource_stats['resource_type'] == 'CSS']['count'].sum()
            
            if js_count > 15:
                recommendations.append(Recommendation(
                    priority='Medium',
                    category='Resource Bundling',
                    title='Bundle JavaScript Files',
                    description=f'Found {int(js_count)} JavaScript files. Consider bundling to reduce HTTP requests.',
                    impact='Fewer requests, faster page load',
                    effort='Medium'
                ))
            
            if css_count > 8:
                recommendations.append(Recommendation(
                    priority='Medium',
                    category='Resource Bundling',
                    title='Bundle CSS Files',
                    description=f'Found {int(css_count)} CSS files. Consider bundling to reduce HTTP requests.',
                    impact='Fewer requests, faster rendering',
                    effort='Medium'
                ))
        
        # Check for large resources
        large_resources = ResourceAnalyzer.identify_large_resources(df)
        if not large_resources.empty and len(large_resources) > 5:
            recommendations.append(Recommendation(
                priority='High',
                category='Resource Optimization',
                title='Optimize Large Resources',
                description=f'Found {len(large_resources)} resources larger than 100KB. Consider lazy loading, code splitting, or image optimization.',
                impact='Faster initial page load',
                effort='Medium'
            ))
        
        return recommendations
    
    @staticmethod
    def _check_third_party_impact(df: pd.DataFrame) -> List[Recommendation]:
        """Check third-party resource impact."""
        recommendations = []
        
        third_party_analysis = DomainAnalyzer.identify_third_party_domains(df)
        
        if third_party_analysis['third_party_percentage'] > 40:
            recommendations.append(Recommendation(
                priority='Medium',
                category='Third-Party Resources',
                title='Reduce Third-Party Dependencies',
                description=f"{third_party_analysis['third_party_percentage']:.1f}% of requests are to third-party domains. Consider self-hosting critical resources or using a CDN.",
                impact='Better control over performance',
                effort='High'
            ))
        
        # Check for slow third-party domains
        if third_party_analysis['third_party_domains']:
            slow_third_party = [
                d for d in third_party_analysis['third_party_domains']
                if d['avg_time'] > 1000
            ]
            
            if slow_third_party:
                recommendations.append(Recommendation(
                    priority='High',
                    category='Third-Party Resources',
                    title='Optimize Slow Third-Party Resources',
                    description=f'Found {len(slow_third_party)} slow third-party domains. Consider async loading or finding alternatives.',
                    impact='Prevent blocking by slow external resources',
                    effort='Medium'
                ))
        
        return recommendations
    
    @staticmethod
    def _check_server_performance(df: pd.DataFrame) -> List[Recommendation]:
        """Check server performance issues."""
        recommendations = []
        
        avg_wait = df['wait'].mean()
        high_wait_pct = ((df['wait'] > 500).sum() / len(df) * 100) if len(df) > 0 else 0
        
        if avg_wait > 500:
            recommendations.append(Recommendation(
                priority='High',
                category='Server Performance',
                title='Optimize Server Response Time',
                description=f'Average server wait time is {avg_wait:.1f}ms. Optimize database queries, implement caching, or upgrade server resources.',
                impact='Faster response times across all endpoints',
                effort='High'
            ))
        
        if high_wait_pct > 20:
            recommendations.append(Recommendation(
                priority='Medium',
                category='Server Performance',
                title='Investigate Slow Endpoints',
                description=f'{high_wait_pct:.1f}% of requests have high server wait times (>500ms). Profile and optimize slow endpoints.',
                impact='Improved overall application performance',
                effort='High'
            ))
        
        return recommendations
    
    @staticmethod
    def _check_http_version(df: pd.DataFrame) -> List[Recommendation]:
        """Check for HTTP version optimization opportunities."""
        recommendations = []
        
        # Check for multiple requests to same domain (could benefit from HTTP/2)
        domain_stats = DomainAnalyzer.analyze_by_domain(df)
        
        if not domain_stats.empty:
            high_request_domains = domain_stats[domain_stats['request_count'] > 20]
            
            if not high_request_domains.empty:
                recommendations.append(Recommendation(
                    priority='Low',
                    category='Protocol',
                    title='Consider HTTP/2 or HTTP/3',
                    description=f'Found {len(high_request_domains)} domains with many requests. HTTP/2 multiplexing could improve performance.',
                    impact='Better connection utilization',
                    effort='Low'
                ))
        
        return recommendations
    
    @staticmethod
    def get_top_recommendations(df: pd.DataFrame, limit: int = 5) -> List[Dict]:
        """
        Get top N recommendations.
        
        Args:
            df: DataFrame with HAR entries
            limit: Number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = RecommendationEngine.generate_recommendations(df)
        top_recommendations = recommendations[:limit]
        
        return [rec.to_dict() for rec in top_recommendations]
