# exporters/report_generator.py - Report generation in multiple formats

import pandas as pd
import json
from datetime import datetime
from typing import Dict, Optional
import io


class ReportGenerator:
    """Generates performance reports in multiple formats."""
    
    @staticmethod
    def generate_csv_report(df: pd.DataFrame, analysis_results: Dict = None) -> str:
        """
        Generate CSV report with request data.
        
        Args:
            df: DataFrame with HAR entries
            analysis_results: Optional dictionary with analysis results
            
        Returns:
            CSV string
        """
        # Select key columns for export
        export_columns = [
            'method', 'url', 'status', 'total_time', 'wait', 'receive',
            'response_size', 'mime_type', 'is_problematic', 'problems'
        ]
        
        # Filter to available columns
        available_columns = [col for col in export_columns if col in df.columns]
        
        export_df = df[available_columns].copy()
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        
        return csv_buffer.getvalue()
    
    @staticmethod
    def generate_json_report(df: pd.DataFrame, analysis_results: Dict = None) -> str:
        """
        Generate JSON report with structured data.
        
        Args:
            df: DataFrame with HAR entries
            analysis_results: Optional dictionary with analysis results
            
        Returns:
            JSON string
        """
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_requests': len(df),
                'report_version': '1.0'
            },
            'summary': {
                'total_requests': len(df),
                'total_size_bytes': int(df['response_size'].sum()),
                'avg_response_time_ms': round(df['total_time'].mean(), 2),
                'error_count': int((df['status'] >= 400).sum()),
                'slow_requests': int((df['total_time'] > 1000).sum())
            }
        }
        
        # Add analysis results if provided
        if analysis_results:
            report['analysis'] = analysis_results
        
        # Add request details
        report['requests'] = df.to_dict('records')
        
        return json.dumps(report, indent=2, default=str)
    
    @staticmethod
    def generate_summary_report(df: pd.DataFrame, analysis_results: Dict = None) -> str:
        """
        Generate human-readable text summary report.
        
        Args:
            df: DataFrame with HAR entries
            analysis_results: Optional dictionary with analysis results
            
        Returns:
            Text summary
        """
        from analyzers.performance_analyzer import PerformanceAnalyzer
        
        stats = PerformanceAnalyzer.get_statistics(df)
        
        summary = f"""
HAR FILE ANALYSIS REPORT
========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
--------
Total Requests: {len(df)}
Total Size: {stats['total_size'] / 1024:.2f} KB
Average Response Time: {stats['avg_time']:.2f} ms
Median Response Time: {stats['median_time']:.2f} ms
Max Response Time: {stats['max_time']:.2f} ms

ERROR ANALYSIS
--------------
Total Errors: {stats['error_count']}
Error Rate: {stats['error_rate']:.2f}%

PERFORMANCE ISSUES
------------------
Problematic Requests: {stats['problematic_count']}
Slow Requests (>1s): {(df['total_time'] > 1000).sum()}
Very Slow Requests (>3s): {(df['total_time'] > 3000).sum()}

TIMING BREAKDOWN
----------------
Average DNS: {df['dns'].mean():.2f} ms
Average Connect: {df['connect'].mean():.2f} ms
Average SSL: {df['ssl'].mean():.2f} ms
Average Wait: {df['wait'].mean():.2f} ms
Average Receive: {df['receive'].mean():.2f} ms
"""
        
        # Add analysis results if provided
        if analysis_results:
            if 'performance_score' in analysis_results:
                summary += f"\nPERFORMANCE SCORE\n"
                summary += f"-----------------\n"
                summary += f"Score: {analysis_results['performance_score']['score']}/100\n"
                summary += f"Grade: {analysis_results['performance_score']['grade']}\n"
        
        return summary
    
    @staticmethod
    def export_to_file(content: str, filename: str, format: str = 'csv') -> bytes:
        """
        Export content to downloadable file.
        
        Args:
            content: Content to export
            filename: Base filename (without extension)
            format: Export format ('csv', 'json', 'txt')
            
        Returns:
            Bytes content for download
        """
        return content.encode('utf-8')
    
    @staticmethod
    def create_download_filename(base_name: str = 'har_analysis', format: str = 'csv') -> str:
        """
        Create timestamped filename for download.
        
        Args:
            base_name: Base name for file
            format: File format extension
            
        Returns:
            Filename with timestamp
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}.{format}"
