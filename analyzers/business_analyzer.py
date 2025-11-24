# analyzers/business_analyzer.py - Business impact analysis

import pandas as pd
from typing import Dict


class BusinessAnalyzer:
    """Analyzes business impact of performance metrics."""
    
    # Industry benchmarks for conversion impact
    # Based on research: 1 second delay = 7% conversion loss
    CONVERSION_IMPACT_PER_SECOND = 0.07
    
    # Page abandonment rates by load time
    ABANDONMENT_RATES = {
        1: 0.07,   # 7% abandon at 1s
        2: 0.11,   # 11% abandon at 2s
        3: 0.16,   # 16% abandon at 3s
        5: 0.32,   # 32% abandon at 5s
        10: 0.53   # 53% abandon at 10s
    }
    
    @staticmethod
    def calculate_user_experience_score(df: pd.DataFrame) -> Dict:
        """
        Calculate user experience score based on performance metrics.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with UX score and breakdown
        """
        if df.empty:
            return {'score': 0, 'grade': 'F'}
        
        score = 100
        
        # Factor 1: Average load time (40% weight)
        avg_time = df['total_time'].mean()
        if avg_time > 3000:
            score -= 40
        elif avg_time > 2000:
            score -= 30
        elif avg_time > 1000:
            score -= 20
        elif avg_time > 500:
            score -= 10
        
        # Factor 2: Consistency (20% weight)
        std_dev = df['total_time'].std()
        cv = (std_dev / avg_time) if avg_time > 0 else 0
        if cv > 1.0:
            score -= 20
        elif cv > 0.5:
            score -= 10
        
        # Factor 3: Error rate (20% weight)
        error_rate = (df['status'] >= 400).mean()
        if error_rate > 0.05:
            score -= 20
        elif error_rate > 0.02:
            score -= 10
        
        # Factor 4: Resource optimization (20% weight)
        total_size = df['response_size'].sum()
        if total_size > 5 * 1024 * 1024:  # >5MB
            score -= 20
        elif total_size > 3 * 1024 * 1024:  # >3MB
            score -= 10
        
        score = max(0, min(100, score))
        
        # Calculate grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': score,
            'grade': grade,
            'avg_load_time': round(avg_time, 2),
            'consistency_cv': round(cv, 3),
            'error_rate': round(error_rate * 100, 2),
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    @staticmethod
    def estimate_conversion_impact(df: pd.DataFrame, baseline_conversion_rate: float = 0.02) -> Dict:
        """
        Estimate conversion rate impact based on load time.
        
        Args:
            df: DataFrame with HAR entries
            baseline_conversion_rate: Baseline conversion rate (default 2%)
            
        Returns:
            Dictionary with conversion impact estimates
        """
        avg_time_seconds = df['total_time'].mean() / 1000
        
        # Calculate conversion loss
        if avg_time_seconds <= 1:
            conversion_loss = 0
        else:
            # Each second over 1s reduces conversion by 7%
            conversion_loss = (avg_time_seconds - 1) * BusinessAnalyzer.CONVERSION_IMPACT_PER_SECOND
        
        estimated_conversion = baseline_conversion_rate * (1 - conversion_loss)
        estimated_conversion = max(0, estimated_conversion)
        
        # Calculate abandonment rate
        abandonment_rate = BusinessAnalyzer._calculate_abandonment_rate(avg_time_seconds)
        
        return {
            'avg_load_time_seconds': round(avg_time_seconds, 2),
            'baseline_conversion_rate': round(baseline_conversion_rate * 100, 2),
            'estimated_conversion_rate': round(estimated_conversion * 100, 2),
            'conversion_loss_percentage': round(conversion_loss * 100, 2),
            'abandonment_rate': round(abandonment_rate * 100, 2)
        }
    
    @staticmethod
    def _calculate_abandonment_rate(load_time_seconds: float) -> float:
        """Calculate page abandonment rate based on load time."""
        if load_time_seconds <= 1:
            return 0.07
        elif load_time_seconds <= 2:
            return 0.11
        elif load_time_seconds <= 3:
            return 0.16
        elif load_time_seconds <= 5:
            return 0.32
        else:
            return 0.53
    
    @staticmethod
    def estimate_revenue_impact(
        df: pd.DataFrame,
        monthly_visitors: int = 10000,
        average_order_value: float = 50.0,
        baseline_conversion_rate: float = 0.02
    ) -> Dict:
        """
        Estimate revenue impact of performance.
        
        Args:
            df: DataFrame with HAR entries
            monthly_visitors: Monthly visitor count
            average_order_value: Average order value in currency
            baseline_conversion_rate: Baseline conversion rate
            
        Returns:
            Dictionary with revenue impact estimates
        """
        conversion_impact = BusinessAnalyzer.estimate_conversion_impact(df, baseline_conversion_rate)
        
        # Calculate revenue
        baseline_conversions = monthly_visitors * baseline_conversion_rate
        baseline_revenue = baseline_conversions * average_order_value
        
        estimated_conversions = monthly_visitors * (conversion_impact['estimated_conversion_rate'] / 100)
        estimated_revenue = estimated_conversions * average_order_value
        
        revenue_loss = baseline_revenue - estimated_revenue
        
        # Calculate potential gain from 1s improvement
        improved_time = max(1.0, conversion_impact['avg_load_time_seconds'] - 1.0)
        improved_conversion_loss = (improved_time - 1) * BusinessAnalyzer.CONVERSION_IMPACT_PER_SECOND
        improved_conversion = baseline_conversion_rate * (1 - improved_conversion_loss)
        improved_conversions = monthly_visitors * improved_conversion
        improved_revenue = improved_conversions * average_order_value
        
        potential_gain = improved_revenue - estimated_revenue
        
        return {
            'monthly_visitors': monthly_visitors,
            'average_order_value': average_order_value,
            'baseline_monthly_revenue': round(baseline_revenue, 2),
            'estimated_monthly_revenue': round(estimated_revenue, 2),
            'monthly_revenue_loss': round(revenue_loss, 2),
            'annual_revenue_loss': round(revenue_loss * 12, 2),
            'potential_monthly_gain': round(potential_gain, 2),
            'potential_annual_gain': round(potential_gain * 12, 2)
        }
    
    @staticmethod
    def get_business_summary(df: pd.DataFrame) -> Dict:
        """
        Get comprehensive business impact summary.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with complete business analysis
        """
        ux_score = BusinessAnalyzer.calculate_user_experience_score(df)
        conversion_impact = BusinessAnalyzer.estimate_conversion_impact(df)
        revenue_impact = BusinessAnalyzer.estimate_revenue_impact(df)
        
        return {
            'user_experience': ux_score,
            'conversion_impact': conversion_impact,
            'revenue_impact': revenue_impact
        }
