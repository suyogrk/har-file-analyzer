# app.py - Main Streamlit application

import streamlit as st
import hashlib
from config import PAGE_CONFIG
from parsers.har_parser import HARParser
from analyzers.performance_analyzer import PerformanceAnalyzer
from analyzers.performance_benchmarking import PerformanceBenchmarking
from ui.metrics import MetricsDisplay
from ui.tabs import TabManager
from utils.validators import validate_file_size, validate_har_content
from visualizations.charts import ChartFactory


@st.cache_data(show_spinner=False)
def parse_har_file(file_content: str, file_hash: str):
    """
    Parse HAR file with caching based on file hash.
    
    Args:
        file_content: Raw HAR file content
        file_hash: Hash of file content for cache key
        
    Returns:
        Tuple of (DataFrame or None, error message or None)
    """
    return HARParser.parse(file_content)


@st.cache_data(show_spinner=False)
def analyze_performance(df_hash: str, df):
    """
    Analyze performance with caching.
    
    Args:
        df_hash: Hash for cache invalidation
        df: DataFrame to analyze
        
    Returns:
        DataFrame with analysis results
    """
    return PerformanceAnalyzer.identify_problematic_apis(df)


@st.cache_data(show_spinner=False)
def calculate_performance_score(df_hash: str, df):
    """
    Calculate performance score with caching.
    
    Args:
        df_hash: Hash for cache invalidation
        df: DataFrame to analyze
        
    Returns:
        Performance score dictionary
    """
    return PerformanceBenchmarking.calculate_performance_score(df)


def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    
    # Title and description
    st.title("🔍 HAR File Performance Analyzer")
    st.markdown("""
        Upload your HAR (HTTP Archive) file to analyze API performance, identify problematic endpoints,
        and get detailed timing breakdowns for all network requests.
    """)
    
    # Sidebar
    st.sidebar.header("📁 File Upload")
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose a HAR file",
        type=['har'],
        help="Select a .har file exported from browser DevTools"
    )
    
    if uploaded_file is not None:
        # Validate file size
        file_size = uploaded_file.size
        is_valid, error = validate_file_size(file_size)
        if not is_valid:
            st.error(f"❌ {error}")
            st.stop()
        
        # Read and parse the HAR file
        har_content = uploaded_file.read().decode('utf-8')
        
        # Validate content
        is_valid, error = validate_har_content(har_content)
        if not is_valid:
            st.error(f"❌ {error}")
            st.stop()
        
        # Generate hash for caching
        file_hash = hashlib.md5(har_content.encode()).hexdigest()
        
        with st.spinner('Parsing HAR file...'):
            df, error = parse_har_file(har_content, file_hash)
        
        # Handle parsing errors
        if error:
            st.error(f"❌ {error}")
            st.stop()
        
        if df is not None and not df.empty:
            # Identify problematic APIs (cached)
            df_hash = hashlib.md5(str(df.shape).encode()).hexdigest()
            df = analyze_performance(df_hash, df)
            
            # Calculate performance score (cached)
            perf_score = calculate_performance_score(df_hash, df)
            
            # Main metrics with performance score
            st.header("📊 Overview Metrics")
            
            # Performance score gauge
            col1, col2 = st.columns([1, 3])
            
            with col1:
                fig_gauge, key_gauge = ChartFactory.create_performance_score_gauge(
                    perf_score['score'],
                    perf_score['grade'],
                    key="performance_score_gauge"
                )
                if fig_gauge:
                    st.plotly_chart(fig_gauge, use_container_width=True, key=key_gauge)
                
                st.markdown(f"**{perf_score['summary']}**")
            
            with col2:
                MetricsDisplay.render_overview_metrics(df)
            
            st.markdown("---")
            
            # Tabs for different views
            tabs = st.tabs([
                "📈 Overview",
                "📋 All Requests",
                "⚠️ Problematic APIs",
                "⏱️ Timing Analysis",
                "🎯 Endpoint Summary",
                "🌐 Domain Analysis",
                "💡 Recommendations",
                "📦 Resource Analysis",
                "📊 Advanced Stats"
            ])
            
            with tabs[0]:
                TabManager.render_overview_tab(df)
            
            with tabs[1]:
                TabManager.render_requests_tab(df)
            
            with tabs[2]:
                TabManager.render_problematic_tab(df)
            
            with tabs[3]:
                TabManager.render_timing_tab(df)
            
            with tabs[4]:
                TabManager.render_endpoint_tab(df)
            
            with tabs[5]:
                TabManager.render_domain_analysis_tab(df)
            
            with tabs[6]:
                TabManager.render_recommendations_tab(df)
            
            with tabs[7]:
                TabManager.render_resource_analysis_tab(df)
            
            with tabs[8]:
                TabManager.render_advanced_stats_tab(df)


if __name__ == "__main__":
    main()
