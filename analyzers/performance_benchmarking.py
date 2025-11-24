# analyzers/performance_benchmarking.py - Performance benchmarking and scoring

import pandas as pd
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class PerformanceBenchmark:
    """Performance benchmark thresholds in milliseconds."""
    excellent: int = 100
    good: int = 300
    average: int = 1000
    poor: int = 3000


class PerformanceBenchmarking:
    """Analyzes performance against industry benchmarks and provides scoring."""
    
    BENCHMARK = PerformanceBenchmark()
    
    @staticmethod
    def calculate_performance_score(df: pd.DataFrame) -> Dict:
        """
        Calculate overall performance score (0-100) and grade (A-F).
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with score, grade, and breakdown
        """
        if df.empty:
            return {
                'score': 0,
                'grade': 'F',
                'breakdown': {},
                'summary': 'No data available'
            }
        
        score = 100
        breakdown = {}
        
        # 1. Average response time (max -25 points)
        avg_time = df['total_time'].mean()
        if avg_time > PerformanceBenchmarking.BENCHMARK.poor:
            time_penalty = 25
        elif avg_time > PerformanceBenchmarking.BENCHMARK.average:
            time_penalty = 15
        elif avg_time > PerformanceBenchmarking.BENCHMARK.good:
            time_penalty = 5
        else:
            time_penalty = 0
        
        score -= time_penalty
        breakdown['avg_response_time'] = {
            'value': round(avg_time, 2),
            'penalty': time_penalty,
            'status': PerformanceBenchmarking._get_time_status(avg_time)
        }
        
        # 2. Error rate (max -30 points)
        error_rate = (df['status'] >= 400).mean() * 100
        if error_rate > 10:
            error_penalty = 30
        elif error_rate > 5:
            error_penalty = 20
        elif error_rate > 1:
            error_penalty = 10
        else:
            error_penalty = 0
        
        score -= error_penalty
        breakdown['error_rate'] = {
            'value': round(error_rate, 2),
            'penalty': error_penalty,
            'status': 'critical' if error_rate > 5 else 'warning' if error_rate > 1 else 'good'
        }
        
        # 3. Slow requests percentage (max -20 points)
        slow_requests_pct = (df['total_time'] > 1000).mean() * 100
        if slow_requests_pct > 30:
            slow_penalty = 20
        elif slow_requests_pct > 15:
            slow_penalty = 15
        elif slow_requests_pct > 5:
            slow_penalty = 10
        else:
            slow_penalty = 0
        
        score -= slow_penalty
        breakdown['slow_requests'] = {
            'value': round(slow_requests_pct, 2),
            'penalty': slow_penalty,
            'status': 'critical' if slow_requests_pct > 15 else 'warning' if slow_requests_pct > 5 else 'good'
        }
        
        # 4. High server wait time (max -15 points)
        high_wait_pct = (df['wait'] > 500).mean() * 100
        if high_wait_pct > 25:
            wait_penalty = 15
        elif high_wait_pct > 10:
            wait_penalty = 10
        elif high_wait_pct > 5:
            wait_penalty = 5
        else:
            wait_penalty = 0
        
        score -= wait_penalty
        breakdown['high_wait_time'] = {
            'value': round(high_wait_pct, 2),
            'penalty': wait_penalty,
            'status': 'critical' if high_wait_pct > 10 else 'warning' if high_wait_pct > 5 else 'good'
        }
        
        # 5. Connection issues (max -10 points)
        connection_issues_pct = (df['connect'] > 1000).mean() * 100
        if connection_issues_pct > 20:
            conn_penalty = 10
        elif connection_issues_pct > 10:
            conn_penalty = 5
        else:
            conn_penalty = 0
        
        score -= conn_penalty
        breakdown['connection_issues'] = {
            'value': round(connection_issues_pct, 2),
            'penalty': conn_penalty,
            'status': 'critical' if connection_issues_pct > 10 else 'warning' if connection_issues_pct > 5 else 'good'
        }
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        # Calculate grade
        grade = PerformanceBenchmarking._calculate_grade(score)
        
        # Generate summary
        summary = PerformanceBenchmarking._generate_summary(score, grade, breakdown)
        
        return {
            'score': score,
            'grade': grade,
            'breakdown': breakdown,
            'summary': summary
        }
    
    @staticmethod
    def _calculate_grade(score: int) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    @staticmethod
    def _get_time_status(avg_time: float) -> str:
        """Get status label for average response time."""
        if avg_time <= PerformanceBenchmarking.BENCHMARK.excellent:
            return 'excellent'
        elif avg_time <= PerformanceBenchmarking.BENCHMARK.good:
            return 'good'
        elif avg_time <= PerformanceBenchmarking.BENCHMARK.average:
            return 'average'
        else:
            return 'poor'
    
    @staticmethod
    def _generate_summary(score: int, grade: str, breakdown: Dict) -> str:
        """Generate human-readable summary."""
        if score >= 90:
            return "Excellent performance! Your application is performing very well."
        elif score >= 80:
            return "Good performance with minor areas for improvement."
        elif score >= 70:
            return "Average performance. Consider optimizing key areas."
        elif score >= 60:
            return "Below average performance. Optimization recommended."
        else:
            return "Poor performance. Immediate optimization required."
    
    @staticmethod
    def compare_to_benchmarks(df: pd.DataFrame) -> Dict:
        """
        Compare key metrics to industry benchmarks.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with benchmark comparisons
        """
        avg_time = df['total_time'].mean()
        p95_time = df['total_time'].quantile(0.95)
        p99_time = df['total_time'].quantile(0.99)
        
        return {
            'avg_response_time': {
                'value': round(avg_time, 2),
                'benchmark': PerformanceBenchmarking.BENCHMARK.good,
                'status': PerformanceBenchmarking._get_time_status(avg_time),
                'meets_benchmark': avg_time <= PerformanceBenchmarking.BENCHMARK.good
            },
            'p95_response_time': {
                'value': round(p95_time, 2),
                'benchmark': PerformanceBenchmarking.BENCHMARK.average,
                'status': PerformanceBenchmarking._get_time_status(p95_time),
                'meets_benchmark': p95_time <= PerformanceBenchmarking.BENCHMARK.average
            },
            'p99_response_time': {
                'value': round(p99_time, 2),
                'benchmark': PerformanceBenchmarking.BENCHMARK.poor,
                'status': PerformanceBenchmarking._get_time_status(p99_time),
                'meets_benchmark': p99_time <= PerformanceBenchmarking.BENCHMARK.poor
            }
        }
