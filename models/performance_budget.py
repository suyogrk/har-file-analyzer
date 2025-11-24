# models/performance_budget.py - Performance budget tracking

from dataclasses import dataclass
from typing import Dict, List
import pandas as pd


@dataclass
class PerformanceBudget:
    """Performance budget thresholds."""
    max_requests: int = 50
    max_total_size_kb: int = 2000  # 2MB
    max_response_time_ms: int = 3000
    max_slow_requests: int = 5  # Requests >1000ms
    max_error_rate_percent: float = 5.0
    max_js_size_kb: int = 500
    max_css_size_kb: int = 200
    max_image_size_kb: int = 1000


class PerformanceBudgetTracker:
    """Tracks performance metrics against defined budgets."""
    
    def __init__(self, budget: PerformanceBudget = None):
        """
        Initialize budget tracker.
        
        Args:
            budget: PerformanceBudget instance (uses defaults if None)
        """
        self.budget = budget or PerformanceBudget()
    
    def check_budget(self, df: pd.DataFrame) -> Dict:
        """
        Check if performance metrics meet budget requirements.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with budget status and violations
        """
        if df.empty:
            return {
                'meets_budget': True,
                'violations': [],
                'health_score': 100
            }
        
        violations = []
        
        # Check total requests
        total_requests = len(df)
        if total_requests > self.budget.max_requests:
            violations.append({
                'metric': 'Total Requests',
                'current': total_requests,
                'budget': self.budget.max_requests,
                'exceeded_by': total_requests - self.budget.max_requests,
                'severity': 'Medium'
            })
        
        # Check total size
        total_size_kb = df['response_size'].sum() / 1024
        if total_size_kb > self.budget.max_total_size_kb:
            violations.append({
                'metric': 'Total Size',
                'current': round(total_size_kb, 2),
                'budget': self.budget.max_total_size_kb,
                'exceeded_by': round(total_size_kb - self.budget.max_total_size_kb, 2),
                'severity': 'High'
            })
        
        # Check max response time
        max_response_time = df['total_time'].max()
        if max_response_time > self.budget.max_response_time_ms:
            violations.append({
                'metric': 'Max Response Time',
                'current': round(max_response_time, 2),
                'budget': self.budget.max_response_time_ms,
                'exceeded_by': round(max_response_time - self.budget.max_response_time_ms, 2),
                'severity': 'High'
            })
        
        # Check slow requests
        slow_requests = (df['total_time'] > 1000).sum()
        if slow_requests > self.budget.max_slow_requests:
            violations.append({
                'metric': 'Slow Requests (>1s)',
                'current': slow_requests,
                'budget': self.budget.max_slow_requests,
                'exceeded_by': slow_requests - self.budget.max_slow_requests,
                'severity': 'Medium'
            })
        
        # Check error rate
        error_rate = (df['status'] >= 400).mean() * 100
        if error_rate > self.budget.max_error_rate_percent:
            violations.append({
                'metric': 'Error Rate',
                'current': round(error_rate, 2),
                'budget': self.budget.max_error_rate_percent,
                'exceeded_by': round(error_rate - self.budget.max_error_rate_percent, 2),
                'severity': 'High'
            })
        
        # Check resource-specific budgets
        resource_violations = self._check_resource_budgets(df)
        violations.extend(resource_violations)
        
        # Calculate health score
        health_score = self._calculate_health_score(violations)
        
        return {
            'meets_budget': len(violations) == 0,
            'violations': violations,
            'violation_count': len(violations),
            'health_score': health_score,
            'budget': self.budget
        }
    
    def _check_resource_budgets(self, df: pd.DataFrame) -> List[Dict]:
        """Check resource-specific budget violations."""
        from analyzers.resource_analyzer import ResourceAnalyzer
        
        violations = []
        
        # Classify resources
        df['resource_type'] = df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        # Check JavaScript size
        js_size_kb = df[df['resource_type'] == 'JavaScript']['response_size'].sum() / 1024
        if js_size_kb > self.budget.max_js_size_kb:
            violations.append({
                'metric': 'JavaScript Size',
                'current': round(js_size_kb, 2),
                'budget': self.budget.max_js_size_kb,
                'exceeded_by': round(js_size_kb - self.budget.max_js_size_kb, 2),
                'severity': 'Medium'
            })
        
        # Check CSS size
        css_size_kb = df[df['resource_type'] == 'CSS']['response_size'].sum() / 1024
        if css_size_kb > self.budget.max_css_size_kb:
            violations.append({
                'metric': 'CSS Size',
                'current': round(css_size_kb, 2),
                'budget': self.budget.max_css_size_kb,
                'exceeded_by': round(css_size_kb - self.budget.max_css_size_kb, 2),
                'severity': 'Low'
            })
        
        # Check image size
        image_size_kb = df[df['resource_type'] == 'Images']['response_size'].sum() / 1024
        if image_size_kb > self.budget.max_image_size_kb:
            violations.append({
                'metric': 'Image Size',
                'current': round(image_size_kb, 2),
                'budget': self.budget.max_image_size_kb,
                'exceeded_by': round(image_size_kb - self.budget.max_image_size_kb, 2),
                'severity': 'Medium'
            })
        
        return violations
    
    def _calculate_health_score(self, violations: List[Dict]) -> int:
        """Calculate budget health score (0-100)."""
        if not violations:
            return 100
        
        # Deduct points based on severity
        score = 100
        severity_penalties = {
            'High': 20,
            'Medium': 10,
            'Low': 5
        }
        
        for violation in violations:
            penalty = severity_penalties.get(violation['severity'], 10)
            score -= penalty
        
        return max(0, score)
    
    def get_budget_utilization(self, df: pd.DataFrame) -> Dict:
        """
        Get budget utilization percentages.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with utilization percentages
        """
        if df.empty:
            return {}
        
        total_requests = len(df)
        total_size_kb = df['response_size'].sum() / 1024
        max_response_time = df['total_time'].max()
        slow_requests = (df['total_time'] > 1000).sum()
        error_rate = (df['status'] >= 400).mean() * 100
        
        return {
            'requests': {
                'current': total_requests,
                'budget': self.budget.max_requests,
                'utilization': round((total_requests / self.budget.max_requests * 100), 2)
            },
            'total_size': {
                'current': round(total_size_kb, 2),
                'budget': self.budget.max_total_size_kb,
                'utilization': round((total_size_kb / self.budget.max_total_size_kb * 100), 2)
            },
            'max_time': {
                'current': round(max_response_time, 2),
                'budget': self.budget.max_response_time_ms,
                'utilization': round((max_response_time / self.budget.max_response_time_ms * 100), 2)
            },
            'slow_requests': {
                'current': slow_requests,
                'budget': self.budget.max_slow_requests,
                'utilization': round((slow_requests / self.budget.max_slow_requests * 100) if self.budget.max_slow_requests > 0 else 0, 2)
            },
            'error_rate': {
                'current': round(error_rate, 2),
                'budget': self.budget.max_error_rate_percent,
                'utilization': round((error_rate / self.budget.max_error_rate_percent * 100) if self.budget.max_error_rate_percent > 0 else 0, 2)
            }
        }
