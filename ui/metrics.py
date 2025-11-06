# ui/metrics.py - Metrics display components

import streamlit as st
import pandas as pd
from analyzers.performance_analyzer import PerformanceAnalyzer


class MetricsDisplay:
    """Handles metrics display in the UI."""
    
    @staticmethod
    def render_overview_metrics(df: pd.DataFrame):
        """Render main overview metrics."""
        stats = PerformanceAnalyzer.get_statistics(df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", stats['total_requests'])
        
        with col2:
            st.metric("Unique Endpoints", stats['unique_endpoints'])
        
        with col3:
            st.metric("Error Rate", f"{stats['error_rate']:.1f}%")
        
        with col4:
            st.metric("Avg Response Time", f"{stats['avg_response_time']:.0f}ms")
    
    @staticmethod
    def render_detailed_statistics(df: pd.DataFrame):
        """Render detailed performance statistics."""
        stats = PerformanceAnalyzer.get_statistics(df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Max Response Time", f"{stats['max_response_time']:.0f}ms")
        
        with col2:
            st.metric("Min Response Time", f"{stats['min_response_time']:.0f}ms")
        
        with col3:
            st.metric("Problematic Requests", stats['problematic_count'])
