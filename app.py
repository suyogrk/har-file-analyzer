# app.py - Main Streamlit application

import warnings
# Suppress known Streamlit/Plotly deprecation warnings that don't affect functionality
warnings.filterwarnings('ignore', message='.*keyword arguments have been deprecated.*')
warnings.filterwarnings('ignore', message='.*This pattern is interpreted as a regular expression.*')

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
from exceptions import HARParseError, HARValidationError, HARFileError


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


def show_error_with_solutions(error_message: str, solutions: list) -> None:
    """
    Display error message with actionable solutions.
    
    Args:
        error_message: The error message to display
        solutions: List of solutions to try
    """
    st.error(f"❌ {error_message}")
    
    with st.expander("💡 Possible Solutions"):
        for i, solution in enumerate(solutions, 1):
            st.write(f"{i}. {solution}")


def show_file_size_error(file_size: int, max_size: int) -> None:
    """
    Display file size error with specific guidance.
    
    Args:
        file_size: The actual file size
        max_size: The maximum allowed file size
    """
    size_mb = file_size / (1024 * 1024)
    max_mb = max_size / (1024 * 1024)
    
    error_message = f"File too large ({size_mb:.1f} MB). Maximum size is {max_mb:.0f} MB."
    
    solutions = [
        "Try filtering the HAR file to include only the network requests you need to analyze",
        "Generate a new HAR file with a shorter recording period",
        "Use browser DevTools to filter out unnecessary requests before exporting",
        "Consider using a HAR file splitter tool to divide large files into smaller chunks"
    ]
    
    show_error_with_solutions(error_message, solutions)


def show_parsing_error(error_message: str) -> None:
    """
    Display parsing error with specific guidance.
    
    Args:
        error_message: The parsing error message
    """
    solutions = [
        "Verify the HAR file was exported correctly from browser DevTools",
        "Try opening the HAR file in a text editor to check if it's valid JSON",
        "Generate a new HAR file with a fresh browser session",
        "Check if the HAR file was corrupted during transfer or storage"
    ]
    
    # Add specific solutions based on error type
    if "JSON" in error_message:
        solutions.insert(0, "The HAR file appears to have invalid JSON format")
    elif "entries" in error_message:
        solutions.insert(0, "The HAR file doesn't contain any network request entries")
    elif "Missing" in error_message:
        solutions.insert(0, "The HAR file is missing required fields")
    
    show_error_with_solutions(error_message, solutions)


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
            show_file_size_error(file_size, 50 * 1024 * 1024)  # 50MB max size
            st.stop()
        
        # Read and parse the HAR file
        har_content = uploaded_file.read().decode('utf-8')
        
        # Validate content
        is_valid, error = validate_har_content(har_content)
        if not is_valid:
            solutions = [
                "Ensure you're uploading a valid HAR file (not another file type)",
                "Check that the file wasn't corrupted during download or transfer",
                "Try exporting the HAR file again from your browser's DevTools",
                "Open the file in a text editor to verify it starts with '{' and contains valid JSON"
            ]
            show_error_with_solutions(error, solutions)
            st.stop()
        
        # Generate hash for caching
        file_hash = hashlib.md5(har_content.encode()).hexdigest()
        
        with st.spinner('Parsing HAR file...'):
            df, error = parse_har_file(har_content, file_hash)
        
        # Handle parsing errors
        if error:
            show_parsing_error(error)
            st.stop()
        
        if df is not None and not df.empty:
            # Export section in sidebar
            st.sidebar.markdown("---")
            st.sidebar.header("📥 Export Reports")
            
            from exporters.report_generator import ReportGenerator
            
            # CSV Export
            if st.sidebar.button("📄 Export CSV", use_container_width=True):
                csv_content = ReportGenerator.generate_csv_report(df)
                filename = ReportGenerator.create_download_filename('har_analysis', 'csv')
                st.sidebar.download_button(
                    label="⬇️ Download CSV",
                    data=csv_content,
                    file_name=filename,
                    mime='text/csv',
                    use_container_width=True
                )
            
            # JSON Export
            if st.sidebar.button("📋 Export JSON", use_container_width=True):
                json_content = ReportGenerator.generate_json_report(df)
                filename = ReportGenerator.create_download_filename('har_analysis', 'json')
                st.sidebar.download_button(
                    label="⬇️ Download JSON",
                    data=json_content,
                    file_name=filename,
                    mime='application/json',
                    use_container_width=True
                )
            
            # Text Summary Export
            if st.sidebar.button("📝 Export Summary", use_container_width=True):
                summary_content = ReportGenerator.generate_summary_report(df)
                filename = ReportGenerator.create_download_filename('har_summary', 'txt')
                st.sidebar.download_button(
                    label="⬇️ Download Summary",
                    data=summary_content,
                    file_name=filename,
                    mime='text/plain',
                    use_container_width=True
                )
            
            st.sidebar.markdown("---")
        
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
                "📊 Advanced Stats",
                "💾 Caching Analysis",
                "🔒 Security Analysis",
                "📊 Performance Budget",
                "📈 Waterfall",
                "📊 Comparative Analysis",
                "🔌 Connection Analysis",
                "💰 Business Impact"
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
            
            with tabs[9]:
                TabManager.render_caching_analysis_tab(df)
            
            with tabs[10]:
                TabManager.render_security_analysis_tab(df)
            
            with tabs[11]:
                TabManager.render_performance_budget_tab(df)
            
            with tabs[12]:
                TabManager.render_waterfall_tab(df)
            
            with tabs[13]:
                TabManager.render_comparative_analysis_tab(df)
            
            with tabs[14]:
                TabManager.render_connection_analysis_tab(df)
            
            with tabs[15]:
                TabManager.render_business_impact_tab(df)


if __name__ == "__main__":
    main()
