# analyzers/statistical_analyzer.py - Advanced statistical analysis

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats as scipy_stats


class StatisticalAnalyzer:
    """Provides advanced statistical analysis of performance metrics."""
    
    @staticmethod
    def calculate_percentiles(df: pd.DataFrame, column: str = 'total_time') -> Dict:
        """
        Calculate percentiles for a given metric.
        
        Args:
            df: DataFrame with HAR entries
            column: Column to analyze
            
        Returns:
            Dictionary with percentile values
        """
        if df.empty or column not in df.columns:
            return {}
        
        percentiles = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
        percentile_values = {}
        
        for p in percentiles:
            percentile_values[f'p{int(p*100)}'] = round(df[column].quantile(p), 2)
        
        return percentile_values
    
    @staticmethod
    def calculate_statistics(df: pd.DataFrame, column: str = 'total_time') -> Dict:
        """
        Calculate comprehensive statistics for a metric.
        
        Args:
            df: DataFrame with HAR entries
            column: Column to analyze
            
        Returns:
            Dictionary with statistical measures
        """
        if df.empty or column not in df.columns:
            return {}
        
        data = df[column].dropna()
        
        if len(data) == 0:
            return {}
        
        return {
            'count': len(data),
            'mean': round(data.mean(), 2),
            'median': round(data.median(), 2),
            'std_dev': round(data.std(), 2),
            'variance': round(data.var(), 2),
            'min': round(data.min(), 2),
            'max': round(data.max(), 2),
            'range': round(data.max() - data.min(), 2),
            'iqr': round(data.quantile(0.75) - data.quantile(0.25), 2),
            'cv': round((data.std() / data.mean() * 100) if data.mean() != 0 else 0, 2)  # Coefficient of variation
        }
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, column: str = 'total_time', method: str = 'iqr') -> Dict:
        """
        Detect outliers using various methods.
        
        Args:
            df: DataFrame with HAR entries
            column: Column to analyze
            method: Detection method ('iqr', 'zscore', or 'both')
            
        Returns:
            Dictionary with outlier information
        """
        if df.empty or column not in df.columns:
            return {'outliers': pd.DataFrame(), 'count': 0}
        
        data = df[column].dropna()
        
        if method == 'iqr' or method == 'both':
            # IQR method
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            iqr_outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
        
        if method == 'zscore' or method == 'both':
            # Z-score method (>3 standard deviations)
            mean = data.mean()
            std = data.std()
            z_scores = np.abs((data - mean) / std) if std != 0 else np.zeros(len(data))
            
            zscore_outliers = df[z_scores > 3]
        
        # Combine results based on method
        if method == 'iqr':
            outliers = iqr_outliers
        elif method == 'zscore':
            outliers = zscore_outliers
        else:  # both
            outliers = pd.concat([iqr_outliers, zscore_outliers]).drop_duplicates()
        
        return {
            'outliers': outliers,
            'count': len(outliers),
            'percentage': round((len(outliers) / len(df) * 100) if len(df) > 0 else 0, 2)
        }
    
    @staticmethod
    def analyze_distribution(df: pd.DataFrame, column: str = 'total_time') -> Dict:
        """
        Analyze the distribution of a metric.
        
        Args:
            df: DataFrame with HAR entries
            column: Column to analyze
            
        Returns:
            Dictionary with distribution analysis
        """
        if df.empty or column not in df.columns:
            return {}
        
        data = df[column].dropna()
        
        if len(data) < 3:
            return {'error': 'Insufficient data for distribution analysis'}
        
        # Calculate skewness and kurtosis
        skewness = scipy_stats.skew(data)
        kurtosis = scipy_stats.kurtosis(data)
        
        # Interpret skewness
        if abs(skewness) < 0.5:
            skew_interpretation = 'Fairly symmetric'
        elif skewness > 0:
            skew_interpretation = 'Right-skewed (long tail on right)'
        else:
            skew_interpretation = 'Left-skewed (long tail on left)'
        
        # Interpret kurtosis
        if abs(kurtosis) < 0.5:
            kurt_interpretation = 'Normal distribution'
        elif kurtosis > 0:
            kurt_interpretation = 'Heavy-tailed (more outliers)'
        else:
            kurt_interpretation = 'Light-tailed (fewer outliers)'
        
        return {
            'skewness': round(skewness, 3),
            'skew_interpretation': skew_interpretation,
            'kurtosis': round(kurtosis, 3),
            'kurt_interpretation': kurt_interpretation
        }
    
    @staticmethod
    def calculate_correlation(df: pd.DataFrame, col1: str = 'response_size', col2: str = 'total_time') -> Dict:
        """
        Calculate correlation between two metrics.
        
        Args:
            df: DataFrame with HAR entries
            col1: First column
            col2: Second column
            
        Returns:
            Dictionary with correlation analysis
        """
        if df.empty or col1 not in df.columns or col2 not in df.columns:
            return {}
        
        # Remove rows with missing values
        clean_df = df[[col1, col2]].dropna()
        
        if len(clean_df) < 2:
            return {'error': 'Insufficient data for correlation analysis'}
        
        # Pearson correlation
        pearson_corr, pearson_p = scipy_stats.pearsonr(clean_df[col1], clean_df[col2])
        
        # Spearman correlation (rank-based, more robust to outliers)
        spearman_corr, spearman_p = scipy_stats.spearmanr(clean_df[col1], clean_df[col2])
        
        # Interpret correlation strength
        abs_corr = abs(pearson_corr)
        if abs_corr > 0.7:
            strength = 'Strong'
        elif abs_corr > 0.4:
            strength = 'Moderate'
        elif abs_corr > 0.2:
            strength = 'Weak'
        else:
            strength = 'Very Weak'
        
        direction = 'Positive' if pearson_corr > 0 else 'Negative'
        
        return {
            'pearson_correlation': round(pearson_corr, 3),
            'pearson_p_value': round(pearson_p, 4),
            'spearman_correlation': round(spearman_corr, 3),
            'spearman_p_value': round(spearman_p, 4),
            'strength': strength,
            'direction': direction,
            'interpretation': f'{strength} {direction.lower()} correlation'
        }
    
    @staticmethod
    def perform_trend_analysis(df: pd.DataFrame, column: str = 'total_time') -> Dict:
        """
        Perform trend analysis on sequential requests.
        
        Args:
            df: DataFrame with HAR entries
            column: Column to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        if df.empty or column not in df.columns:
            return {}
        
        data = df[column].dropna()
        
        if len(data) < 3:
            return {'error': 'Insufficient data for trend analysis'}
        
        # Create sequence index
        x = np.arange(len(data))
        y = data.values
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
        
        # Interpret trend
        if abs(slope) < 0.1:
            trend = 'Stable'
        elif slope > 0:
            trend = 'Increasing'
        else:
            trend = 'Decreasing'
        
        return {
            'trend': trend,
            'slope': round(slope, 3),
            'r_squared': round(r_value ** 2, 3),
            'p_value': round(p_value, 4),
            'is_significant': p_value < 0.05
        }
    
    @staticmethod
    def get_comprehensive_analysis(df: pd.DataFrame) -> Dict:
        """
        Get comprehensive statistical analysis.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with complete statistical analysis
        """
        return {
            'percentiles': StatisticalAnalyzer.calculate_percentiles(df),
            'statistics': StatisticalAnalyzer.calculate_statistics(df),
            'outliers': StatisticalAnalyzer.detect_outliers(df, method='both'),
            'distribution': StatisticalAnalyzer.analyze_distribution(df),
            'size_time_correlation': StatisticalAnalyzer.calculate_correlation(df),
            'trend': StatisticalAnalyzer.perform_trend_analysis(df)
        }
