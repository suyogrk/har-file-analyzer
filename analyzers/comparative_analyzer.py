# analyzers/comparative_analyzer.py - Multi-file HAR comparison

import pandas as pd
from typing import Dict, List, Tuple
from analyzers.performance_analyzer import PerformanceAnalyzer
from analyzers.performance_benchmarking import PerformanceBenchmarking


class ComparativeAnalyzer:
    """Compares multiple HAR files for before/after analysis."""
    
    @staticmethod
    def compare_har_files(df1: pd.DataFrame, df2: pd.DataFrame, 
                          label1: str = "Before", label2: str = "After") -> Dict:
        """
        Compare two HAR DataFrames.
        
        Args:
            df1: First DataFrame (baseline)
            df2: Second DataFrame (comparison)
            label1: Label for first dataset
            label2: Label for second dataset
            
        Returns:
            Dictionary with comparison results
        """
        if df1.empty or df2.empty:
            return {'error': 'One or both datasets are empty'}
        
        # Calculate key metrics for both
        metrics1 = ComparativeAnalyzer._calculate_metrics(df1)
        metrics2 = ComparativeAnalyzer._calculate_metrics(df2)
        
        # Calculate deltas
        deltas = ComparativeAnalyzer._calculate_deltas(metrics1, metrics2)
        
        # Performance scores
        score1 = PerformanceBenchmarking.calculate_performance_score(df1)
        score2 = PerformanceBenchmarking.calculate_performance_score(df2)
        
        return {
            'labels': [label1, label2],
            'metrics': {
                label1: metrics1,
                label2: metrics2
            },
            'deltas': deltas,
            'scores': {
                label1: score1,
                label2: score2
            },
            'score_delta': score2['score'] - score1['score'],
            'improvement': score2['score'] > score1['score']
        }
    
    @staticmethod
    def _calculate_metrics(df: pd.DataFrame) -> Dict:
        """Calculate key metrics for a dataset."""
        return {
            'total_requests': len(df),
            'total_size_kb': round(df['response_size'].sum() / 1024, 2),
            'avg_response_time': round(df['total_time'].mean(), 2),
            'median_response_time': round(df['total_time'].median(), 2),
            'p95_response_time': round(df['total_time'].quantile(0.95), 2),
            'max_response_time': round(df['total_time'].max(), 2),
            'error_count': int((df['status'] >= 400).sum()),
            'error_rate': round((df['status'] >= 400).mean() * 100, 2),
            'slow_requests': int((df['total_time'] > 1000).sum())
        }
    
    @staticmethod
    def _calculate_deltas(metrics1: Dict, metrics2: Dict) -> Dict:
        """Calculate delta between two metric sets."""
        deltas = {}
        
        for key in metrics1.keys():
            val1 = metrics1[key]
            val2 = metrics2[key]
            
            # Calculate absolute and percentage change
            delta = val2 - val1
            pct_change = ((val2 - val1) / val1 * 100) if val1 != 0 else 0
            
            # Determine if change is improvement
            # Lower is better for: response times, errors, slow requests, size
            lower_is_better = key in [
                'avg_response_time', 'median_response_time', 'p95_response_time',
                'max_response_time', 'error_count', 'error_rate', 'slow_requests',
                'total_size_kb'
            ]
            
            is_improvement = (delta < 0) if lower_is_better else (delta > 0)
            
            deltas[key] = {
                'delta': round(delta, 2),
                'pct_change': round(pct_change, 2),
                'is_improvement': is_improvement
            }
        
        return deltas
    
    @staticmethod
    def compare_endpoints(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Compare endpoint performance between two datasets.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            
        Returns:
            DataFrame with endpoint comparison
        """
        # Get endpoint stats for both
        endpoints1 = df1.groupby('endpoint')['total_time'].agg(['mean', 'count']).reset_index()
        endpoints1.columns = ['endpoint', 'avg_time_before', 'count_before']
        
        endpoints2 = df2.groupby('endpoint')['total_time'].agg(['mean', 'count']).reset_index()
        endpoints2.columns = ['endpoint', 'avg_time_after', 'count_after']
        
        # Merge
        comparison = pd.merge(endpoints1, endpoints2, on='endpoint', how='outer')
        comparison = comparison.fillna(0)
        
        # Calculate delta
        comparison['time_delta'] = comparison['avg_time_after'] - comparison['avg_time_before']
        comparison['time_delta_pct'] = (
            (comparison['time_delta'] / comparison['avg_time_before'] * 100)
            .replace([float('inf'), -float('inf')], 0)
            .fillna(0)
        )
        
        # Mark improvements
        comparison['improved'] = comparison['time_delta'] < 0
        
        # Sort by absolute delta (biggest changes first)
        comparison['abs_delta'] = comparison['time_delta'].abs()
        comparison = comparison.sort_values('abs_delta', ascending=False)
        
        return comparison[['endpoint', 'avg_time_before', 'avg_time_after', 
                          'time_delta', 'time_delta_pct', 'improved']]
    
    @staticmethod
    def generate_comparison_summary(comparison: Dict) -> List[str]:
        """
        Generate human-readable comparison summary.
        
        Args:
            comparison: Comparison dictionary from compare_har_files
            
        Returns:
            List of summary statements
        """
        summary = []
        
        label1, label2 = comparison['labels']
        deltas = comparison['deltas']
        
        # Overall performance
        if comparison['improvement']:
            summary.append(f"✅ Overall performance improved from {comparison['scores'][label1]['grade']} to {comparison['scores'][label2]['grade']}")
        else:
            summary.append(f"⚠️ Overall performance degraded from {comparison['scores'][label1]['grade']} to {comparison['scores'][label2]['grade']}")
        
        # Response time
        rt_delta = deltas['avg_response_time']
        if rt_delta['is_improvement']:
            summary.append(f"✅ Average response time improved by {abs(rt_delta['pct_change']):.1f}%")
        else:
            summary.append(f"⚠️ Average response time degraded by {abs(rt_delta['pct_change']):.1f}%")
        
        # Error rate
        err_delta = deltas['error_rate']
        if err_delta['is_improvement']:
            summary.append(f"✅ Error rate improved by {abs(err_delta['pct_change']):.1f}%")
        elif err_delta['delta'] != 0:
            summary.append(f"⚠️ Error rate increased by {abs(err_delta['pct_change']):.1f}%")
        
        # Page size
        size_delta = deltas['total_size_kb']
        if size_delta['is_improvement']:
            summary.append(f"✅ Total size reduced by {abs(size_delta['pct_change']):.1f}%")
        elif size_delta['delta'] > 0:
            summary.append(f"⚠️ Total size increased by {abs(size_delta['pct_change']):.1f}%")
        
        return summary
    
    @staticmethod
    def create_comparison_dataframe(comparison: Dict) -> pd.DataFrame:
        """
        Create DataFrame for easy display of comparison.
        
        Args:
            comparison: Comparison dictionary
            
        Returns:
            DataFrame with comparison data
        """
        label1, label2 = comparison['labels']
        metrics1 = comparison['metrics'][label1]
        metrics2 = comparison['metrics'][label2]
        deltas = comparison['deltas']
        
        data = []
        
        metric_labels = {
            'total_requests': 'Total Requests',
            'total_size_kb': 'Total Size (KB)',
            'avg_response_time': 'Avg Response Time (ms)',
            'median_response_time': 'Median Response Time (ms)',
            'p95_response_time': 'P95 Response Time (ms)',
            'max_response_time': 'Max Response Time (ms)',
            'error_count': 'Error Count',
            'error_rate': 'Error Rate (%)',
            'slow_requests': 'Slow Requests (>1s)'
        }
        
        for key, label in metric_labels.items():
            data.append({
                'Metric': label,
                label1: metrics1[key],
                label2: metrics2[key],
                'Delta': deltas[key]['delta'],
                'Change (%)': deltas[key]['pct_change'],
                'Status': '✅' if deltas[key]['is_improvement'] else '⚠️' if deltas[key]['delta'] != 0 else '➖'
            })
        
        return pd.DataFrame(data)
