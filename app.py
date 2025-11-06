# app.py - Main Streamlit application

import streamlit as st
from config import PAGE_CONFIG
from parsers.har_parser import HARParser
from analyzers.performance_analyzer import PerformanceAnalyzer
from ui.metrics import MetricsDisplay
from ui.tabs import TabManager


def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    
    # Title and description
    st.title("🔍 HAR File API Performance Analyzer")
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
        # Read and parse the HAR file
        har_content = uploaded_file.read().decode('utf-8')
        
        with st.spinner('Parsing HAR file...'):
            df = HARParser.parse(har_content)
        
        if df is not None and not df.empty:
            # Identify problematic APIs
            df = PerformanceAnalyzer.identify_problematic_apis(df)
            
            # Main metrics
            st.header("📊 Overview Metrics")
            MetricsDisplay.render_overview_metrics(df)
            
            st.markdown("---")
            
            # Tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📈 Overview",
                "📋 All Requests",
                "⚠️ Problematic APIs",
                "⏱️ Timing Analysis",
                "🎯 Endpoint Summary"
            ])
            
            with tab1:
                TabManager.render_overview_tab(df)
            
            with tab2:
                TabManager.render_requests_tab(df)
            
            with tab3:
                TabManager.render_problematic_tab(df)
            
            with tab4:
                TabManager.render_timing_tab(df)
            
            with tab5:
                TabManager.render_endpoint_tab(df)


if __name__ == "__main__":
    main()
