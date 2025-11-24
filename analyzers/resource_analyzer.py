# analyzers/resource_analyzer.py - Resource size and optimization analysis

import pandas as pd
from typing import Dict, List
import re


class ResourceAnalyzer:
    """Analyzes resource sizes and identifies optimization opportunities."""
    
    # Resource type mapping based on MIME types
    RESOURCE_TYPES = {
        'JavaScript': ['javascript', 'js', 'application/x-javascript'],
        'CSS': ['css', 'text/css'],
        'Images': ['image/', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico'],
        'Fonts': ['font/', 'woff', 'woff2', 'ttf', 'eot', 'otf'],
        'HTML': ['html', 'text/html'],
        'JSON': ['json', 'application/json'],
        'XML': ['xml', 'text/xml', 'application/xml'],
        'Video': ['video/', 'mp4', 'webm', 'ogg'],
        'Audio': ['audio/', 'mp3', 'wav', 'ogg'],
        'Other': []
    }
    
    # Size thresholds in bytes
    LARGE_RESOURCE_THRESHOLD = 100 * 1024  # 100KB
    VERY_LARGE_THRESHOLD = 500 * 1024  # 500KB
    
    @staticmethod
    def classify_resource_type(mime_type: str) -> str:
        """
        Classify resource based on MIME type.
        
        Args:
            mime_type: MIME type string
            
        Returns:
            Resource type category
        """
        if not mime_type or pd.isna(mime_type):
            return 'Other'
        
        mime_type = mime_type.lower()
        
        for resource_type, patterns in ResourceAnalyzer.RESOURCE_TYPES.items():
            for pattern in patterns:
                if pattern in mime_type:
                    return resource_type
        
        return 'Other'
    
    @staticmethod
    def analyze_by_resource_type(df: pd.DataFrame) -> pd.DataFrame:
        """
        Group resources by type and calculate statistics.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with resource type statistics
        """
        if df.empty:
            return pd.DataFrame()
        
        # Classify resources
        df['resource_type'] = df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        # Group by resource type
        resource_stats = df.groupby('resource_type').agg({
            'url': 'count',
            'response_size': ['sum', 'mean', 'max'],
            'total_time': ['mean', 'max']
        }).round(2)
        
        # Flatten column names
        resource_stats.columns = [
            'count',
            'total_size',
            'avg_size',
            'max_size',
            'avg_time',
            'max_time'
        ]
        
        resource_stats = resource_stats.reset_index()
        
        # Calculate percentage of total size
        total_size = df['response_size'].sum()
        if total_size > 0:
            resource_stats['size_percentage'] = (
                resource_stats['total_size'] / total_size * 100
            ).round(2)
        else:
            resource_stats['size_percentage'] = 0
        
        # Sort by total size
        resource_stats = resource_stats.sort_values('total_size', ascending=False)
        
        return resource_stats
    
    @staticmethod
    def identify_large_resources(df: pd.DataFrame, threshold: int = None) -> pd.DataFrame:
        """
        Identify resources exceeding size threshold.
        
        Args:
            df: DataFrame with HAR entries
            threshold: Size threshold in bytes (default: 100KB)
            
        Returns:
            DataFrame with large resources
        """
        if df.empty:
            return pd.DataFrame()
        
        if threshold is None:
            threshold = ResourceAnalyzer.LARGE_RESOURCE_THRESHOLD
        
        # Filter large resources
        large_df = df[df['response_size'] > threshold].copy()
        
        if large_df.empty:
            return pd.DataFrame()
        
        # Add resource type
        large_df['resource_type'] = large_df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        # Add size category
        large_df['size_category'] = large_df['response_size'].apply(
            lambda x: 'Very Large (>500KB)' if x > ResourceAnalyzer.VERY_LARGE_THRESHOLD
            else 'Large (100-500KB)'
        )
        
        # Sort by size
        large_df = large_df.sort_values('response_size', ascending=False)
        
        # Select relevant columns
        columns = ['url', 'resource_type', 'response_size', 'total_time', 'size_category']
        return large_df[columns]
    
    @staticmethod
    def analyze_compression_opportunities(df: pd.DataFrame) -> Dict:
        """
        Analyze potential compression savings.
        
        Note: HAR files may not always include transfer size vs content size.
        This is a simplified analysis based on available data.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with compression analysis
        """
        if df.empty:
            return {
                'total_size': 0,
                'compressible_size': 0,
                'potential_savings': 0,
                'savings_percentage': 0,
                'recommendations': []
            }
        
        # Identify compressible resource types
        compressible_types = ['JavaScript', 'CSS', 'HTML', 'JSON', 'XML']
        
        df['resource_type'] = df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        total_size = df['response_size'].sum()
        compressible_df = df[df['resource_type'].isin(compressible_types)]
        compressible_size = compressible_df['response_size'].sum()
        
        # Estimate 60-70% compression ratio for text-based resources
        estimated_savings = compressible_size * 0.65
        savings_percentage = (estimated_savings / total_size * 100) if total_size > 0 else 0
        
        recommendations = []
        
        # Generate recommendations by resource type
        for resource_type in compressible_types:
            type_df = compressible_df[compressible_df['resource_type'] == resource_type]
            if not type_df.empty:
                type_size = type_df['response_size'].sum()
                type_savings = type_size * 0.65
                if type_savings > 10 * 1024:  # Only recommend if savings > 10KB
                    recommendations.append({
                        'resource_type': resource_type,
                        'current_size': type_size,
                        'estimated_savings': round(type_savings, 2),
                        'file_count': len(type_df)
                    })
        
        return {
            'total_size': total_size,
            'compressible_size': compressible_size,
            'potential_savings': round(estimated_savings, 2),
            'savings_percentage': round(savings_percentage, 2),
            'recommendations': recommendations
        }
    
    @staticmethod
    def analyze_size_vs_time_correlation(df: pd.DataFrame) -> Dict:
        """
        Analyze correlation between resource size and load time.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with correlation data
        """
        if df.empty or len(df) < 2:
            return {
                'correlation': 0,
                'correlation_strength': 'N/A',
                'data_points': []
            }
        
        # Calculate correlation
        correlation = df[['response_size', 'total_time']].corr().iloc[0, 1]
        
        # Determine correlation strength
        abs_corr = abs(correlation)
        if abs_corr > 0.7:
            strength = 'Strong'
        elif abs_corr > 0.4:
            strength = 'Moderate'
        elif abs_corr > 0.2:
            strength = 'Weak'
        else:
            strength = 'Very Weak'
        
        # Prepare data points for visualization
        data_points = df[['response_size', 'total_time', 'mime_type']].copy()
        data_points['resource_type'] = data_points['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        return {
            'correlation': round(correlation, 3),
            'correlation_strength': strength,
            'data_points': data_points.to_dict('records')
        }
    
    @staticmethod
    def get_optimization_summary(df: pd.DataFrame) -> Dict:
        """
        Get comprehensive resource optimization summary.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with optimization recommendations
        """
        large_resources = ResourceAnalyzer.identify_large_resources(df)
        compression = ResourceAnalyzer.analyze_compression_opportunities(df)
        resource_stats = ResourceAnalyzer.analyze_by_resource_type(df)
        
        recommendations = []
        
        # Large resources recommendation
        if not large_resources.empty:
            recommendations.append({
                'priority': 'High',
                'category': 'Resource Size',
                'message': f"Found {len(large_resources)} large resources (>100KB). Consider optimization or lazy loading.",
                'count': len(large_resources)
            })
        
        # Compression recommendation
        if compression['savings_percentage'] > 10:
            recommendations.append({
                'priority': 'High',
                'category': 'Compression',
                'message': f"Enable compression to save ~{compression['savings_percentage']:.1f}% ({compression['potential_savings']/1024:.1f}KB) of bandwidth.",
                'savings': compression['potential_savings']
            })
        
        # Resource consolidation
        if not resource_stats.empty:
            js_count = resource_stats[resource_stats['resource_type'] == 'JavaScript']['count'].sum()
            css_count = resource_stats[resource_stats['resource_type'] == 'CSS']['count'].sum()
            
            if js_count > 10:
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Resource Consolidation',
                    'message': f"Consider bundling {int(js_count)} JavaScript files to reduce requests.",
                    'count': int(js_count)
                })
            
            if css_count > 5:
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Resource Consolidation',
                    'message': f"Consider bundling {int(css_count)} CSS files to reduce requests.",
                    'count': int(css_count)
                })
        
        return {
            'large_resources_count': len(large_resources),
            'potential_compression_savings': compression['potential_savings'],
            'recommendations': recommendations
        }
