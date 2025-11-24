
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
        
        # Get filter values (now includes preset_filter)
        search_term, method_filter, status_filter, preset_filter = FilterManager.render_filter_controls(df)
        
        # Apply filters
        filtered_df = FilterManager.apply_filters(
            df,
            search_term=search_term,
            method_filter=method_filter,
            status_filter=status_filter,
            preset_filter=preset_filter
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
    @staticmethod
    def render_domain_analysis_tab(df: pd.DataFrame):
        """Render the Domain Analysis tab."""
        from analyzers.domain_analyzer import DomainAnalyzer
        
        st.subheader("🌐 Domain Analysis")
        
        # Get domain statistics
        domain_stats = DomainAnalyzer.analyze_by_domain(df)
        
        if domain_stats.empty:
            st.warning("No domain data available")
            return
        
        # Third-party analysis
        third_party_analysis = DomainAnalyzer.identify_third_party_domains(df)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Domains", len(domain_stats))
        with col2:
            st.metric("Main Domain", third_party_analysis['main_domain'])
        with col3:
            st.metric("Third-Party %", f"{third_party_analysis['third_party_percentage']:.1f}%")
        
        st.markdown("---")
        
        # Domain performance chart
        fig_domain, key_domain = ChartFactory.create_domain_performance_chart(domain_stats, key="domain_analysis")
        if fig_domain:
            st.plotly_chart(fig_domain, width='stretch', key=key_domain)
        
        # CDN detection
        st.subheader("CDN Usage")
        cdn_usage = DomainAnalyzer.detect_cdn_usage(df)
        if cdn_usage:
            for cdn in cdn_usage:
                st.info(f"**{cdn['cdn_name']}**: {cdn['request_count']} requests, Avg time: {cdn['avg_time']:.1f}ms")
        else:
            st.info("No CDN usage detected")
        
        st.markdown("---")
        
        # Domain statistics table
        st.subheader("Domain Statistics")
        st.dataframe(domain_stats, width='stretch', hide_index=True)
    
    @staticmethod
    def render_recommendations_tab(df: pd.DataFrame):
        """Render the Recommendations tab."""
        from analyzers.recommendation_engine import RecommendationEngine
        
        st.subheader("💡 Performance Recommendations")
        
        recommendations = RecommendationEngine.generate_recommendations(df)
        
        if not recommendations:
            st.success("✅ No recommendations - your application is performing well!")
            return
        
        st.write(f"Found **{len(recommendations)}** recommendations to improve performance:")
        
        # Group by priority
        high_priority = [r for r in recommendations if r.priority == 'High']
        medium_priority = [r for r in recommendations if r.priority == 'Medium']
        low_priority = [r for r in recommendations if r.priority == 'Low']
        
        # Display high priority
        if high_priority:
            st.markdown("### 🔴 High Priority")
            for rec in high_priority:
                with st.expander(f"**{rec.title}** ({rec.category})"):
                    st.write(f"**Description:** {rec.description}")
                    st.write(f"**Impact:** {rec.impact}")
                    st.write(f"**Effort:** {rec.effort}")
        
        # Display medium priority
        if medium_priority:
            st.markdown("### 🟡 Medium Priority")
            for rec in medium_priority:
                with st.expander(f"**{rec.title}** ({rec.category})"):
                    st.write(f"**Description:** {rec.description}")
                    st.write(f"**Impact:** {rec.impact}")
                    st.write(f"**Effort:** {rec.effort}")
        
        # Display low priority
        if low_priority:
            st.markdown("### 🟢 Low Priority")
            for rec in low_priority:
                with st.expander(f"**{rec.title}** ({rec.category})"):
                    st.write(f"**Description:** {rec.description}")
                    st.write(f"**Impact:** {rec.impact}")
                    st.write(f"**Effort:** {rec.effort}")
    
    @staticmethod
    def render_resource_analysis_tab(df: pd.DataFrame):
        """Render the Resource Analysis tab."""
        from analyzers.resource_analyzer import ResourceAnalyzer
        
        st.subheader("📦 Resource Analysis")
        
        # Resource statistics
        resource_stats = ResourceAnalyzer.analyze_by_resource_type(df)
        
        if resource_stats.empty:
            st.warning("No resource data available")
            return
        
        # Display metrics
        total_size = resource_stats['total_size'].sum()
        total_count = resource_stats['count'].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Resources", int(total_count))
        with col2:
            st.metric("Total Size", f"{total_size / 1024:.1f} KB")
        with col3:
            avg_size = total_size / total_count if total_count > 0 else 0
            st.metric("Avg Size", f"{avg_size / 1024:.1f} KB")
        
        st.markdown("---")
        
        # Resource size chart
        col1, col2 = st.columns(2)
        
        with col1:
            fig_resource, key_resource = ChartFactory.create_resource_size_chart(resource_stats, key="resource_size")
            if fig_resource:
                st.plotly_chart(fig_resource, width='stretch', key=key_resource)
        
        with col2:
            fig_scatter, key_scatter = ChartFactory.create_size_vs_time_scatter(df, key="size_vs_time")
            if fig_scatter:
                st.plotly_chart(fig_scatter, width='stretch', key=key_scatter)
        
        st.markdown("---")
        
        # Large resources
        st.subheader("Large Resources (>100KB)")
        large_resources = ResourceAnalyzer.identify_large_resources(df)
        
        if not large_resources.empty:
            st.warning(f"Found {len(large_resources)} large resources")
            st.dataframe(large_resources, width='stretch', hide_index=True)
        else:
            st.success("✅ No large resources found")
        
        st.markdown("---")
        
        # Compression analysis
        st.subheader("Compression Opportunities")
        compression = ResourceAnalyzer.analyze_compression_opportunities(df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Compressible Size", f"{compression['compressible_size'] / 1024:.1f} KB")
        with col2:
            st.metric("Potential Savings", f"{compression['potential_savings'] / 1024:.1f} KB ({compression['savings_percentage']:.1f}%)")
        
        if compression['recommendations']:
            st.write("**Recommendations by resource type:**")
            for rec in compression['recommendations']:
                st.info(f"**{rec['resource_type']}**: {rec['file_count']} files, potential savings: {rec['estimated_savings']/1024:.1f}KB")
    
    @staticmethod
    def render_advanced_stats_tab(df: pd.DataFrame):
        """Render the Advanced Statistics tab."""
        st.subheader("📊 Advanced Statistical Analysis")
        
        # Percentile analysis
        st.markdown("### Response Time Percentiles")
        
        percentiles = {
            'P50 (Median)': df['total_time'].quantile(0.5),
            'P75': df['total_time'].quantile(0.75),
            'P90': df['total_time'].quantile(0.9),
            'P95': df['total_time'].quantile(0.95),
            'P99': df['total_time'].quantile(0.99)
        }
        
        cols = st.columns(5)
        for i, (label, value) in enumerate(percentiles.items()):
            with cols[i]:
                st.metric(label, f"{value:.0f}ms")
        
        # Percentile chart
        fig_percentile, key_percentile = ChartFactory.create_percentile_chart(df, key="percentile_chart")
        if fig_percentile:
            st.plotly_chart(fig_percentile, width='stretch', key=key_percentile)
        
        st.markdown("---")
        
        # Statistical measures
        st.markdown("### Statistical Measures")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mean", f"{df['total_time'].mean():.1f}ms")
        with col2:
            st.metric("Std Dev", f"{df['total_time'].std():.1f}ms")
        with col3:
            st.metric("Min", f"{df['total_time'].min():.1f}ms")
        with col4:
            st.metric("Max", f"{df['total_time'].max():.1f}ms")
        
        st.markdown("---")
        
        # Outlier detection
        st.markdown("### Outlier Detection")
        
        mean = df['total_time'].mean()
        std = df['total_time'].std()
        outliers = df[df['total_time'] > mean + 3 * std]
        
        if not outliers.empty:
            st.warning(f"Found {len(outliers)} outliers (>3 standard deviations from mean)")
            st.dataframe(
                outliers[['endpoint', 'total_time', 'status']],
                width='stretch',
                hide_index=True
            )
        else:
            st.success("✅ No significant outliers detected")
