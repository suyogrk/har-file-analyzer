import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.parse import urlparse
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="HAR File Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🔍 HAR File API Performance Analyzer")
st.markdown("""
Upload your HAR (HTTP Archive) file to analyze API performance, identify problematic endpoints, 
and get detailed timing breakdowns for all network requests.
""")

# Sidebar
st.sidebar.header("📁 File Upload")

def safe_time(value):
    try:
        if value is None or not isinstance(value, (int, float)):
            return 0
        return max(value, 0)
    except:
        return 0

def parse_har_file(har_content):
    """Parse HAR file and extract relevant data"""
    try:
        har_data = json.loads(har_content)
        entries = har_data.get('log', {}).get('entries', [])
        
        parsed_data = []
        for entry in entries:
            request = entry.get('request', {})
            response = entry.get('response', {})
            timings = entry.get('timings', {})
            
            # Parse URL to get endpoint
            url = request.get('url', '')
            parsed_url = urlparse(url)
            endpoint = f"{parsed_url.netloc}{parsed_url.path}"
            
            # Calculate total time
            total_time = entry.get('time', 0)
            
            # Extract timing components
            blocked = safe_time(timings.get('blocked'))
            dns = safe_time(timings.get('dns'))
            connect = safe_time(timings.get('connect'))
            send = safe_time(timings.get('send'))
            wait = safe_time(timings.get('wait'))
            receive = safe_time(timings.get('receive'))
            ssl = safe_time(timings.get('ssl'))
            
            parsed_data.append({
                'url': url,
                'endpoint': endpoint,
                'method': request.get('method', 'GET'),
                'status': response.get('status', 0),
                'status_text': response.get('statusText', ''),
                'total_time': total_time,
                'blocked': blocked,
                'dns': dns,
                'connect': connect,
                'send': send,
                'wait': wait,
                'receive': receive,
                'ssl': ssl,
                'started_datetime': entry.get('startedDateTime', ''),
                'response_size': response.get('content', {}).get('size', 0),
                'mime_type': response.get('content', {}).get('mimeType', '')
            })
        
        return pd.DataFrame(parsed_data)
    
    except Exception as e:
        st.error(f"Error parsing HAR file: {str(e)}")
        return None

def identify_problematic_apis(df):
    """Identify problematic APIs based on performance criteria"""
    if df.empty:
        return df
    
    problems = []
    for idx, row in df.iterrows():
        issues = []
        
        # Slow response (>1000ms)
        if row['total_time'] > 1000:
            issues.append('Slow Response')
        
        # High server wait time (>500ms)
        if row['wait'] > 500:
            issues.append('High Server Wait')
        
        # Error status codes
        if row['status'] >= 400:
            issues.append('Error Response')
        
        # Connection issues
        if row['connect'] > 1000:
            issues.append('Connection Delay')
        
        # DNS issues
        if row['dns'] > 100:
            issues.append('DNS Delay')
        
        problems.append(', '.join(issues) if issues else 'No Issues')
    
    df['problems'] = problems
    df['is_problematic'] = df['problems'] != 'No Issues'
    
    return df

def create_timing_breakdown_chart(df):
    """Create timing breakdown chart"""
    # Calculate average timing for each phase
    timing_cols = ['blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl']
    avg_timings = df[timing_cols].mean()
    
    fig = px.bar(
        x=avg_timings.index,
        y=avg_timings.values,
        title="Average Timing Breakdown",
        labels={'x': 'Timing Phase', 'y': 'Time (ms)'},
        color=avg_timings.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(showlegend=False)
    return fig

def create_response_time_histogram(df):
    """Create response time distribution histogram"""
    fig = px.histogram(
        df, 
        x='total_time',
        title="Response Time Distribution",
        labels={'total_time': 'Response Time (ms)', 'count': 'Number of Requests'},
        nbins=50
    )
    
    # Add vertical line for 1000ms threshold
    fig.add_vline(x=1000, line_dash="dash", line_color="red", 
                  annotation_text="1000ms threshold")
    
    return fig

def create_status_code_chart(df):
    """Create status code distribution chart"""
    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    
    # Color code based on status ranges
    colors = []
    for status in status_counts['status']:
        if status < 300:
            colors.append('green')
        elif status < 400:
            colors.append('orange')
        else:
            colors.append('red')
    
    fig = px.pie(
        status_counts,
        values='count',
        names='status',
        title="Status Code Distribution",
        color_discrete_sequence=colors
    )
    
    return fig

def create_slowest_endpoints_chart(df):
    """Create chart showing slowest endpoints"""
    endpoint_stats = df.groupby('endpoint').agg({
        'total_time': ['mean', 'count']
    }).round(2)
    
    endpoint_stats.columns = ['avg_response_time', 'request_count']
    endpoint_stats = endpoint_stats.reset_index()
    
    # Filter endpoints with at least 2 requests and sort by response time
    endpoint_stats = endpoint_stats[endpoint_stats['request_count'] >= 1]
    endpoint_stats = endpoint_stats.sort_values('avg_response_time', ascending=False).head(10)
    
    fig = px.bar(
        endpoint_stats,
        x='avg_response_time',
        y='endpoint',
        orientation='h',
        title="Top 10 Slowest Endpoints",
        labels={'avg_response_time': 'Average Response Time (ms)', 'endpoint': 'Endpoint'},
        color='avg_response_time',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return fig

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Choose a HAR file",
    type=['har'],
    help="Select a .har file exported from browser DevTools"
)

if uploaded_file is not None:
    # Read and parse the HAR file
    har_content = uploaded_file.read().decode('utf-8')
    
    with st.spinner('Parsing HAR file...'):
        df = parse_har_file(har_content)
    
    if df is not None and not df.empty:
        # Identify problematic APIs
        df = identify_problematic_apis(df)
        
        # Main metrics
        st.header("📊 Overview Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", len(df))
        
        with col2:
            unique_endpoints = df['endpoint'].nunique()
            st.metric("Unique Endpoints", unique_endpoints)
        
        with col3:
            error_rate = (df['status'] >= 400).mean() * 100
            st.metric("Error Rate", f"{error_rate:.1f}%")
        
        with col4:
            avg_response_time = df['total_time'].mean()
            st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Overview", 
            "📋 All Requests", 
            "⚠️ Problematic APIs", 
            "⏱️ Timing Analysis", 
            "🎯 Endpoint Summary"
        ])
        
        with tab1:
            st.subheader("Performance Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = create_response_time_histogram(df)
                st.plotly_chart(fig_hist, use_container_width=True)
                
                fig_status = create_status_code_chart(df)
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                fig_timing = create_timing_breakdown_chart(df)
                st.plotly_chart(fig_timing, use_container_width=True)
                
                fig_endpoints = create_slowest_endpoints_chart(df)
                st.plotly_chart(fig_endpoints, use_container_width=True)
        
        with tab2:
            st.subheader("All Requests")
            
            # Search and filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("🔍 Search URL/Endpoint")
            
            with col2:
                method_filter = st.selectbox("HTTP Method", ['All'] + df['method'].unique().tolist())
            
            with col3:
                status_filter = st.selectbox("Status Code", ['All'] + sorted(df['status'].unique().tolist()))
            
            # Apply filters
            filtered_df = df.copy()
            
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['url'].str.contains(search_term, case=False, na=False) |
                    filtered_df['endpoint'].str.contains(search_term, case=False, na=False)
                ]
            
            if method_filter != 'All':
                filtered_df = filtered_df[filtered_df['method'] == method_filter]
            
            if status_filter != 'All':
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            
            # Display results
            st.write(f"Showing {len(filtered_df)} of {len(df)} requests")
            
            # Select columns to display
            display_cols = ['method', 'endpoint', 'status', 'total_time', 'wait', 'receive', 'problems']
            st.dataframe(
                filtered_df[display_cols].sort_values('total_time', ascending=False),
                use_container_width=True,
                column_config={
                    'total_time': st.column_config.NumberColumn('Total Time (ms)', format="%.1f"),
                    'wait': st.column_config.NumberColumn('Wait (ms)', format="%.1f"),
                    'receive': st.column_config.NumberColumn('Receive (ms)', format="%.1f"),
                    'problems': st.column_config.TextColumn('Issues')
                }
            )
        
        with tab3:
            st.subheader("⚠️ Problematic APIs")
            
            problematic_df = df[df['is_problematic']].copy()
            
            if not problematic_df.empty:
                st.write(f"Found {len(problematic_df)} problematic requests out of {len(df)} total")
                
                # Problem type breakdown
                problem_counts = {}
                for problems in problematic_df['problems']:
                    for problem in problems.split(', '):
                        problem_counts[problem] = problem_counts.get(problem, 0) + 1
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Problem Type Breakdown:**")
                    for problem, count in sorted(problem_counts.items(), key=lambda x: x[1], reverse=True):
                        st.write(f"• {problem}: {count} requests")
                
                with col2:
                    # Problem severity chart
                    problem_df = pd.DataFrame(list(problem_counts.items()), columns=['Problem', 'Count'])
                    fig = px.bar(problem_df, x='Count', y='Problem', orientation='h',
                                title="Problem Types Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed problematic requests table
                st.write("**Detailed Problematic Requests:**")
                display_cols = ['method', 'endpoint', 'status', 'total_time', 'wait', 'problems']
                st.dataframe(
                    problematic_df[display_cols].sort_values('total_time', ascending=False),
                    use_container_width=True,
                    column_config={
                        'total_time': st.column_config.NumberColumn('Total Time (ms)', format="%.1f"),
                        'wait': st.column_config.NumberColumn('Wait (ms)', format="%.1f"),
                        'problems': st.column_config.TextColumn('Issues')
                    }
                )
            else:
                st.success("🎉 No problematic APIs found! All requests performed within acceptable limits.")
        
        with tab4:
            st.subheader("⏱️ Timing Analysis")
            
            # Detailed timing breakdown
            timing_cols = ['blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Average Timing Breakdown (ms):**")
                timing_stats = df[timing_cols].describe().round(2)
                st.dataframe(timing_stats)
            
            with col2:
                # Box plot for timing distribution
                timing_data = []
                for col in timing_cols:
                    for val in df[col]:
                        if val > 0:  # Only include positive values
                            timing_data.append({'Phase': col, 'Time': val})
                
                timing_df = pd.DataFrame(timing_data)
                if not timing_df.empty:
                    fig = px.box(timing_df, x='Phase', y='Time', 
                                title="Timing Phase Distribution")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Waterfall chart for slowest request
            st.write("**Slowest Request Timing Breakdown:**")
            slowest_idx = df['total_time'].idxmax()
            slowest_request = df.loc[slowest_idx]
            
            phases = ['blocked', 'dns', 'connect', 'send', 'wait', 'receive']
            values = [slowest_request[phase] for phase in phases if slowest_request[phase] > 0]
            labels = [phase.capitalize() for phase, val in zip(phases, [slowest_request[phase] for phase in phases]) if val > 0]
            
            if values:
                fig = go.Figure(go.Waterfall(
                    name="Timing Phases",
                    orientation="v",
                    measure=["relative"] * len(values),
                    x=labels,
                    y=values,
                    text=[f"{v:.1f}ms" for v in values],
                    textposition="outside"
                ))
                
                fig.update_layout(
                    title=f"Timing Breakdown for Slowest Request ({slowest_request['total_time']:.1f}ms total)",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.write(f"**URL:** {slowest_request['url']}")
        
        with tab5:
            st.subheader("🎯 Endpoint Summary")
            
            # Aggregate statistics by endpoint
            endpoint_stats = df.groupby('endpoint').agg({
                'total_time': ['mean', 'min', 'max', 'std'],
                'wait': 'mean',
                'status': lambda x: (x >= 400).sum(),  # Error count
                'url': 'count'  # Request count
            }).round(2)
            
            endpoint_stats.columns = ['avg_time', 'min_time', 'max_time', 'std_time', 'avg_wait', 'error_count', 'request_count']
            endpoint_stats = endpoint_stats.reset_index()
            
            # Calculate error rate
            endpoint_stats['error_rate'] = (endpoint_stats['error_count'] / endpoint_stats['request_count'] * 100).round(1)
            
            # Sort by average response time
            endpoint_stats = endpoint_stats.sort_values('avg_time', ascending=False)
            
            st.dataframe(
                endpoint_stats,
                use_container_width=True,
                column_config={
                    'avg_time': st.column_config.NumberColumn('Avg Time (ms)', format="%.1f"),
                    'min_time': st.column_config.NumberColumn('Min Time (ms)', format="%.1f"),
                    'max_time': st.column_config.NumberColumn('Max Time (ms)', format="%.1f"),
                    'std_time': st.column_config.NumberColumn('Std Dev (ms)', format="%.1f"),
                    'avg_wait': st.column_config.NumberColumn('Avg Wait (ms)', format="%.1f"),
                    'error_rate': st.column_config.NumberColumn('Error Rate (%)', format="%.1f"),
                    'request_count': st.column_config.NumberColumn('Requests', format="%d"),
                    'error_count': st.column_config.NumberColumn('Errors', format="%d")
                }
            )
            
            # Export functionality
            if st.button("📥 Export Endpoint Summary as CSV"):
                csv = endpoint_stats.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="endpoint_summary.csv",
                    mime="text/csv"
                )
    
    else:
        st.error("Failed to parse HAR file. Please ensure it's a valid HAR file.")

else:
    st.info("👆 Please upload a HAR file to begin analysis")
    
    # Instructions
    st.markdown("""
    ### How to generate a HAR file:
    
    1. **Chrome DevTools:**
       - Open DevTools (F12)
       - Go to Network tab
       - Perform the actions you want to analyze
       - Right-click in the Network tab
       - Select "Save all as HAR with content"
    
    2. **Firefox DevTools:**
       - Open DevTools (F12)
       - Go to Network tab
       - Perform the actions you want to analyze
       - Click the gear icon
       - Select "Save All As HAR"
    
    3. **Safari:**
       - Enable Develop menu in Safari preferences
       - Open Web Inspector
       - Go to Network tab
       - Perform actions
       - Export HAR file
    """)

# Sidebar information
st.sidebar.markdown("""
### 📋 Analysis Features:
- **API Endpoint Analysis**: Count and performance per endpoint
- **Timing Breakdown**: DNS, connect, wait, receive phases
- **Problem Detection**: Slow APIs, errors, timeouts
- **Performance Metrics**: Response times, error rates
- **Interactive Charts**: Visual analysis tools
- **Export Options**: Download filtered results

### ⚠️ Problem Detection Criteria:
- **Slow Response**: > 1000ms total time
- **High Server Wait**: > 500ms wait time
- **Error Response**: 4xx/5xx status codes
- **Connection Delay**: > 1000ms connect time
- **DNS Delay**: > 100ms DNS lookup
""")