
import streamlit as st
import pandas as pd
from visualizations.charts import ChartFactory
from ui.filters import FilterManager
from ui.metrics import MetricsDisplay
from analyzers.performance_analyzer import PerformanceAnalyzer


class TabManager:
    """Manages tab content and layouts."""
    
    @staticmethod
    def render_overview_tab(df: pd.DataFrame):
        """Render the Overview tab."""
        st.subheader("Performance Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist, key_hist = ChartFactory.create_response_time_histogram(df, key="overview_histogram")
            st.plotly_chart(fig_hist, width='stretch', key=key_hist)
            
            fig_status, key_status = ChartFactory.create_status_code_chart(df, key="overview_status")
            st.plotly_chart(fig_status, width='stretch', key=key_status)
        
        with col2:
            fig_timing, key_timing = ChartFactory.create_timing_breakdown_chart(df, key="overview_timing")
            st.plotly_chart(fig_timing, width='stretch', key=key_timing)
            
            fig_endpoints, key_endpoints = ChartFactory.create_slowest_endpoints_chart(df, key="overview_endpoints")
            st.plotly_chart(fig_endpoints, width='stretch', key=key_endpoints)
    
    @staticmethod
    def render_requests_tab(df: pd.DataFrame):
        """Render the All Requests tab."""
        st.subheader("All Requests")
        
        # Get filter values
        search_term, method_filter, status_filter = FilterManager.render_filter_controls(df)
        
        # Apply filters
        filtered_df = FilterManager.apply_filters(
            df,
            search_term=search_term,
            method_filter=method_filter,
            status_filter=status_filter
        )
        
        # Display results
        st.write(f"Showing {len(filtered_df)} of {len(df)} requests")
        
        # Display table
        display_columns = ['method', 'endpoint', 'status', 'total_time', 'problems']
        st.dataframe(
            filtered_df[display_columns],
            width='stretch',
            hide_index=True
        )
    
    @staticmethod
    def render_problematic_tab(df: pd.DataFrame):
        """Render the Problematic APIs tab."""
        st.subheader("Problematic APIs")
        
        problematic_df = df[df['is_problematic']].sort_values('total_time', ascending=False)
        
        if problematic_df.empty:
            st.success("✅ No problematic APIs found!")
        else:
            st.warning(f"⚠️ Found {len(problematic_df)} problematic requests")
            
            display_columns = ['method', 'endpoint', 'status', 'total_time', 'problems']
            st.dataframe(
                problematic_df[display_columns],
                width='stretch',
                hide_index=True
            )
    
    @staticmethod
    def render_timing_tab(df: pd.DataFrame):
        """Render the Timing Analysis tab."""
        st.subheader("Detailed Timing Analysis")
        
        MetricsDisplay.render_detailed_statistics(df)
        
        st.markdown("---")
        
        # Show timing breakdown chart with unique key
        fig_timing, key_timing = ChartFactory.create_timing_breakdown_chart(df, key="timing_analysis_breakdown")
        st.plotly_chart(fig_timing, width='stretch', key=key_timing)
        
        # Show average timing by endpoint
        st.subheader("Average Timing by Endpoint")
        endpoint_timing = df.groupby('endpoint')[
            ['blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl']
        ].mean().round(2)
        
        st.dataframe(endpoint_timing, width='stretch')
    
    @staticmethod
    def render_endpoint_tab(df: pd.DataFrame):
        """Render the Endpoint Summary tab."""
        st.subheader("Endpoint Performance Summary")
        
        endpoint_stats = PerformanceAnalyzer.get_slowest_endpoints(df, limit=50)
        
        st.dataframe(
            endpoint_stats,
            width='stretch',
            hide_index=True
        )
        
        # Show chart with unique key for endpoint tab
        fig_endpoints, key_endpoints = ChartFactory.create_slowest_endpoints_chart(
            df, 
            limit=20, 
            key="endpoint_tab_slowest"
        )
        st.plotly_chart(fig_endpoints, width='stretch', key=key_endpoints)