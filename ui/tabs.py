
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
            st.plotly_chart(fig_hist, use_container_width=True, key=key_hist)
            
            fig_status, key_status = ChartFactory.create_status_code_chart(df, key="overview_status")
            st.plotly_chart(fig_status, use_container_width=True, key=key_status)
        
        with col2:
            fig_timing, key_timing = ChartFactory.create_timing_breakdown_chart(df, key="overview_timing")
            st.plotly_chart(fig_timing, use_container_width=True, key=key_timing)
            
            fig_endpoints, key_endpoints = ChartFactory.create_slowest_endpoints_chart(df, key="overview_endpoints")
            st.plotly_chart(fig_endpoints, use_container_width=True, key=key_endpoints)
    
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
        st.plotly_chart(fig_timing, use_container_width=True, key=key_timing)
        
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
        st.plotly_chart(fig_endpoints, use_container_width=True, key=key_endpoints)    
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
            st.plotly_chart(fig_domain, use_container_width=True, key=key_domain)
        
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
                st.plotly_chart(fig_resource, use_container_width=True, key=key_resource)
        
        with col2:
            fig_scatter, key_scatter = ChartFactory.create_size_vs_time_scatter(df, key="size_vs_time")
            if fig_scatter:
                st.plotly_chart(fig_scatter, use_container_width=True, key=key_scatter)
        
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
            st.plotly_chart(fig_percentile, use_container_width=True, key=key_percentile)
        
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
    
    @staticmethod
    def render_caching_analysis_tab(df: pd.DataFrame):
        """Render the Caching Analysis tab."""
        from analyzers.cache_analyzer import CacheAnalyzer
        
        st.subheader("💾 Caching Analysis")
        
        # Get caching analysis
        cache_analysis = CacheAnalyzer.analyze_caching_opportunities(df)
        repeat_savings = CacheAnalyzer.calculate_repeat_visit_savings(df)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", cache_analysis['total_requests'])
        with col2:
            st.metric("Cacheable", f"{cache_analysis['cacheable_requests']} ({cache_analysis['cacheable_percentage']:.1f}%)")
        with col3:
            st.metric("Potential Savings", f"{cache_analysis['potential_savings_kb']:.1f} KB")
        with col4:
            st.metric("Repeat Visit Savings", f"{repeat_savings['time_saved_seconds']:.1f}s")
        
        st.markdown("---")
        
        # Caching recommendations
        st.subheader("Cache Duration Recommendations")
        
        if cache_analysis['recommendations']:
            for rec in cache_analysis['recommendations']:
                priority_color = "🔴" if rec['priority'] == 'High' else "🟡"
                st.info(
                    f"{priority_color} **{rec['resource_type']}**: {rec['count']} files, "
                    f"{rec['total_size']/1024:.1f}KB - Recommended: `{rec['recommended_duration']}`"
                )
        else:
            st.success("✅ No specific caching recommendations")
        
        st.markdown("---")
        
        # Repeat visit savings breakdown
        st.subheader("Repeat Visit Performance")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Bandwidth Saved", f"{repeat_savings['bandwidth_saved_mb']:.2f} MB")
            st.metric("Time Saved", f"{repeat_savings['time_saved_seconds']:.2f} seconds")
        with col2:
            st.metric("Requests Saved", repeat_savings['requests_saved'])
            st.metric("Cache Hit Rate", f"{repeat_savings['cache_hit_rate']:.0f}%")
        
        st.markdown("---")
        
        # Non-cacheable resources
        st.subheader("Cacheable Resources")
        non_cacheable = CacheAnalyzer.get_non_cacheable_resources(df)
        
        if not non_cacheable.empty:
            st.write(f"**{len(non_cacheable)} resources** that should be cached:")
            st.dataframe(non_cacheable.head(20), width='stretch', hide_index=True)
        else:
            st.info("All cacheable resources are properly configured")
    
    @staticmethod
    def render_security_analysis_tab(df: pd.DataFrame):
        """Render the Security Analysis tab."""
        from analyzers.security_analyzer import SecurityAnalyzer
        
        st.subheader("🔒 Security Analysis")
        
        # Get security analysis
        security = SecurityAnalyzer.analyze_security(df)
        protocol_breakdown = SecurityAnalyzer.get_protocol_breakdown(df)
        
        # Security score
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # Security score gauge
            score_color = "🟢" if security['security_score'] >= 80 else "🟡" if security['security_score'] >= 60 else "🔴"
            st.metric("Security Score", f"{score_color} {security['security_score']}/100")
            st.metric("Grade", security['grade'])
        
        with col2:
            st.metric("HTTP Requests", f"{protocol_breakdown['http_count']} ({protocol_breakdown['http_percentage']:.1f}%)")
            st.metric("HTTPS Requests", f"{protocol_breakdown['https_count']} ({protocol_breakdown['https_percentage']:.1f}%)")
        
        st.markdown("---")
        
        # Security issues
        st.subheader("Security Issues")
        
        if security['issues']:
            for issue in security['issues']:
                severity_icon = "🔴" if issue['severity'] == 'High' else "🟡" if issue['severity'] == 'Medium' else "🟢"
                
                with st.expander(f"{severity_icon} **{issue['category']}** - {issue['severity']} Severity"):
                    st.write(f"**Description:** {issue['description']}")
                    st.write(f"**Impact:** {issue['impact']}")
        else:
            st.success("✅ No security issues detected!")
        
        st.markdown("---")
        
        # Security recommendations
        st.subheader("Security Recommendations")
        
        if security['recommendations']:
            for rec in security['recommendations']:
                priority_icon = "🔴" if rec['priority'] == 'High' else "🟡"
                
                with st.expander(f"{priority_icon} **{rec['title']}**"):
                    st.write(rec['description'])
        else:
            st.success("✅ No security recommendations - good job!")
        
        st.markdown("---")
        
        # Protocol breakdown chart
        st.subheader("Protocol Distribution")
        
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[
            go.Pie(
                labels=['HTTPS', 'HTTP'],
                values=[protocol_breakdown['https_count'], protocol_breakdown['http_count']],
                marker_colors=['green', 'red']
            )
        ])
        
        fig.update_layout(title="HTTP vs HTTPS Requests")
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_performance_budget_tab(df: pd.DataFrame):
        """Render the Performance Budget tab."""
        from models.performance_budget import PerformanceBudgetTracker, PerformanceBudget
        
        st.subheader("📊 Performance Budget")
        
        # Initialize budget tracker
        budget_tracker = PerformanceBudgetTracker()
        budget_check = budget_tracker.check_budget(df)
        utilization = budget_tracker.get_budget_utilization(df)
        
        # Budget health score
        col1, col2, col3 = st.columns(3)
        
        with col1:
            health_icon = "🟢" if budget_check['health_score'] >= 80 else "🟡" if budget_check['health_score'] >= 60 else "🔴"
            st.metric("Budget Health", f"{health_icon} {budget_check['health_score']}/100")
        
        with col2:
            status_icon = "✅" if budget_check['meets_budget'] else "⚠️"
            st.metric("Status", f"{status_icon} {'Pass' if budget_check['meets_budget'] else 'Fail'}")
        
        with col3:
            st.metric("Violations", budget_check['violation_count'])
        
        st.markdown("---")
        
        # Budget utilization
        st.subheader("Budget Utilization")
        
        for metric_name, metric_data in utilization.items():
            metric_label = metric_name.replace('_', ' ').title()
            utilization_pct = metric_data['utilization']
            
            # Color code based on utilization
            if utilization_pct <= 80:
                color = "🟢"
            elif utilization_pct <= 100:
                color = "🟡"
            else:
                color = "🔴"
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.progress(min(utilization_pct / 100, 1.0))
            
            with col2:
                st.write(f"{color} **{utilization_pct:.0f}%**")
            
            st.caption(f"{metric_label}: {metric_data['current']} / {metric_data['budget']}")
        
        st.markdown("---")
        
        # Budget violations
        if budget_check['violations']:
            st.subheader("⚠️ Budget Violations")
            
            for violation in budget_check['violations']:
                severity_icon = "🔴" if violation['severity'] == 'High' else "🟡" if violation['severity'] == 'Medium' else "🟢"
                
                with st.expander(f"{severity_icon} **{violation['metric']}** - {violation['severity']} Severity"):
                    st.write(f"**Current:** {violation['current']}")
                    st.write(f"**Budget:** {violation['budget']}")
                    st.write(f"**Exceeded by:** {violation['exceeded_by']}")
        else:
            st.success("✅ All metrics within budget!")
        
        st.markdown("---")
        
        # Budget configuration
        with st.expander("⚙️ Budget Configuration"):
            st.write("**Current Budget Thresholds:**")
            st.json({
                'max_requests': budget_tracker.budget.max_requests,
                'max_total_size_kb': budget_tracker.budget.max_total_size_kb,
                'max_response_time_ms': budget_tracker.budget.max_response_time_ms,
                'max_slow_requests': budget_tracker.budget.max_slow_requests,
                'max_error_rate_percent': budget_tracker.budget.max_error_rate_percent,
                'max_js_size_kb': budget_tracker.budget.max_js_size_kb,
                'max_css_size_kb': budget_tracker.budget.max_css_size_kb,
                'max_image_size_kb': budget_tracker.budget.max_image_size_kb
            })
    
    @staticmethod
    def render_waterfall_tab(df: pd.DataFrame):
        """Render the Waterfall Visualization tab."""
        from visualizations.waterfall import WaterfallChart
        
        st.subheader("📈 Request Waterfall Timeline")
        
        # Request pattern analysis
        patterns = WaterfallChart.analyze_request_patterns(df)
        
        if patterns['analysis_available']:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Requests", patterns['total_requests'])
            with col2:
                st.metric("Parallel Requests", patterns['parallel_requests'])
            with col3:
                st.metric("Sequential Requests", patterns['sequential_requests'])
            with col4:
                st.metric("Parallelization", f"{patterns['parallelization_ratio']:.1f}%")
            
            st.markdown("---")
        
        # Waterfall chart options
        chart_type = st.radio(
            "Chart Type",
            ["Detailed (Timing Phases)", "Simplified (Total Time)"],
            horizontal=True
        )
        
        max_requests = st.slider(
            "Maximum Requests to Display",
            min_value=10,
            max_value=min(200, len(df)),
            value=min(50, len(df)),
            step=10,
            help="Limit requests for better performance"
        )
        
        st.markdown("---")
        
        # Create waterfall chart
        if chart_type == "Detailed (Timing Phases)":
            fig, key = WaterfallChart.create_waterfall(df, max_requests=max_requests)
        else:
            fig, key = WaterfallChart.create_simplified_waterfall(df, max_requests=max_requests)
        
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=key)
        else:
            st.warning("Unable to generate waterfall chart")
        
        st.markdown("---")
        
        # Critical path
        st.subheader("🎯 Critical Path (Slowest Requests)")
        critical_path = WaterfallChart.identify_critical_path(df)
        
        if critical_path:
            for i, req in enumerate(critical_path, 1):
                st.write(f"**{i}.** {req['endpoint'][:60]} - {req['total_time']:.1f}ms (Status: {req['status']})")
        else:
            st.info("No critical path data available")
    
    @staticmethod
    def render_comparative_analysis_tab(df: pd.DataFrame):
        """Render the Comparative Analysis tab."""
        from analyzers.comparative_analyzer import ComparativeAnalyzer
        
        st.subheader("📊 Comparative Analysis")
        
        st.info("💡 **How to use:** Upload a second HAR file to compare with the current one. This is useful for before/after optimization analysis.")
        
        # File uploader for second HAR file
        st.markdown("### Upload Second HAR File for Comparison")
        
        comparison_file = st.file_uploader(
            "Choose a second HAR file to compare",
            type=['har'],
            help="Upload another HAR file to compare performance metrics",
            key="comparison_file_uploader"
        )
        
        if comparison_file is not None:
            # Parse the comparison file
            from parsers.har_parser import HARParser
            
            comparison_content = comparison_file.read().decode('utf-8')
            df2, error = HARParser.parse(comparison_content)
            
            if error:
                st.error(f"❌ Error parsing comparison file: {error}")
                return
            
            if df2 is None or df2.empty:
                st.error("❌ Comparison file is empty or invalid")
                return
            
            # Perform comparison
            st.success("✅ Comparison file loaded successfully!")
            
            # Get labels from user
            col1, col2 = st.columns(2)
            with col1:
                label1 = st.text_input("Label for Current File", value="Current", key="label1")
            with col2:
                label2 = st.text_input("Label for Comparison File", value="Comparison", key="label2")
            
            st.markdown("---")
            
            # Perform comparison
            comparison = ComparativeAnalyzer.compare_har_files(df, df2, label1, label2)
            
            # Display summary
            st.subheader("📋 Comparison Summary")
            
            summary = ComparativeAnalyzer.generate_comparison_summary(comparison)
            for item in summary:
                if "✅" in item:
                    st.success(item)
                elif "⚠️" in item:
                    st.warning(item)
                else:
                    st.info(item)
            
            st.markdown("---")
            
            # Performance scores
            st.subheader("🎯 Performance Scores")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                score1 = comparison['scores'][label1]
                st.metric(
                    f"{label1} Score",
                    f"{score1['score']}/100",
                    delta=None
                )
                st.caption(f"Grade: {score1['grade']}")
            
            with col2:
                score2 = comparison['scores'][label2]
                st.metric(
                    f"{label2} Score",
                    f"{score2['score']}/100",
                    delta=None
                )
                st.caption(f"Grade: {score2['grade']}")
            
            with col3:
                delta = comparison['score_delta']
                improvement = comparison['improvement']
                st.metric(
                    "Score Change",
                    f"{delta:+.0f}",
                    delta=f"{delta:+.0f} points",
                    delta_color="normal" if improvement else "inverse"
                )
                st.caption("✅ Improved" if improvement else "⚠️ Degraded")
            
            st.markdown("---")
            
            # Detailed metrics comparison
            st.subheader("📊 Detailed Metrics Comparison")
            
            comparison_df = ComparativeAnalyzer.create_comparison_dataframe(comparison)
            st.dataframe(comparison_df, width='stretch', hide_index=True)
            
            st.markdown("---")
            
            # Endpoint-level comparison
            st.subheader("🎯 Endpoint-Level Comparison")
            
            endpoint_comparison = ComparativeAnalyzer.compare_endpoints(df, df2)
            
            if not endpoint_comparison.empty:
                # Show top improved endpoints
                improved = endpoint_comparison[endpoint_comparison['improved']].head(10)
                if not improved.empty:
                    st.markdown("#### ✅ Top 10 Improved Endpoints")
                    st.dataframe(improved, width='stretch', hide_index=True)
                
                st.markdown("---")
                
                # Show top degraded endpoints
                degraded = endpoint_comparison[~endpoint_comparison['improved']].head(10)
                if not degraded.empty:
                    st.markdown("#### ⚠️ Top 10 Degraded Endpoints")
                    st.dataframe(degraded, width='stretch', hide_index=True)
            else:
                st.info("No common endpoints found between the two HAR files")
        
        else:
            st.info("👆 Upload a second HAR file above to start comparison")
            
            # Show example use cases
            with st.expander("📖 Use Cases for Comparative Analysis"):
                st.markdown("""
                **Comparative analysis is useful for:**
                
                1. **Before/After Optimization**
                   - Compare performance before and after implementing optimizations
                   - Measure the impact of code changes
                
                2. **A/B Testing**
                   - Compare different versions of your application
                   - Validate performance improvements
                
                3. **Regression Detection**
                   - Identify performance degradations
                   - Track performance over time
                
                4. **Environment Comparison**
                   - Compare production vs staging performance
                   - Compare different deployment configurations
                
                5. **Feature Impact Analysis**
                   - Measure performance impact of new features
                   - Identify bottlenecks introduced by changes
                """)
    
    @staticmethod
    def render_connection_analysis_tab(df: pd.DataFrame):
        """Render the Connection Analysis tab."""
        from analyzers.connection_analyzer import ConnectionAnalyzer
        
        st.subheader("🔌 Connection Analysis")
        
        # Get connection analysis
        analysis = ConnectionAnalyzer.analyze_connections(df)
        
        if not analysis['analysis_available']:
            st.warning("Connection analysis not available for this HAR file")
            return
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", analysis['total_requests'])
        with col2:
            st.metric("New Connections", analysis['new_connections'])
        with col3:
            st.metric("Reused Connections", analysis['reused_connections'])
        with col4:
            reuse_color = "🟢" if analysis['connection_reuse_ratio'] >= 80 else "🟡" if analysis['connection_reuse_ratio'] >= 50 else "🔴"
            st.metric("Reuse Ratio", f"{reuse_color} {analysis['connection_reuse_ratio']:.1f}%")
        
        st.markdown("---")
        
        # Connection timing
        st.subheader("⏱️ Connection Timing")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Connect Time", f"{analysis['avg_connect_time']:.1f}ms")
        with col2:
            st.metric("Avg SSL Time", f"{analysis['avg_ssl_time']:.1f}ms")
        with col3:
            st.metric("Connect Time %", f"{analysis['connect_time_percentage']:.1f}%")
        
        st.markdown("---")
        
        # Optimization opportunities
        st.subheader("💡 Optimization Opportunities")
        
        opportunities = ConnectionAnalyzer.identify_connection_opportunities(df)
        
        if opportunities:
            for opp in opportunities:
                priority_icon = "🔴" if opp['priority'] == 'High' else "🟡"
                
                with st.expander(f"{priority_icon} **{opp['title']}** ({opp['category']})"):
                    st.write(f"**Description:** {opp['description']}")
                    st.write(f"**Impact:** {opp['impact']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Current", opp['current_value'])
                    with col2:
                        st.metric("Target", opp['target_value'])
        else:
            st.success("✅ No connection optimization opportunities found - connections are well optimized!")
        
        st.markdown("---")
        
        # Connection breakdown by domain
        st.subheader("🌐 Connection Breakdown by Domain")
        
        breakdown = ConnectionAnalyzer.get_connection_breakdown(df)
        
        if not breakdown.empty:
            st.dataframe(breakdown, width='stretch', hide_index=True)
        else:
            st.info("No connection breakdown data available")
        
        st.markdown("---")
        
        # Best practices
        with st.expander("📖 Connection Optimization Best Practices"):
            st.markdown("""
            **Connection Reuse Best Practices:**
            
            1. **Enable HTTP Keep-Alive**
               - Allows multiple requests over a single connection
               - Target: >80% connection reuse ratio
            
            2. **Use Connection Pooling**
               - Reuse connections across requests
               - Reduces connection setup overhead
            
            3. **Optimize SSL/TLS**
               - Enable TLS session resumption
               - Use OCSP stapling
               - Target: <50ms SSL handshake time
            
            4. **Consider HTTP/2 or HTTP/3**
               - Multiplexing reduces connection overhead
               - Single connection for multiple requests
               - Eliminates head-of-line blocking (HTTP/3)
            
            5. **Use CDN**
               - Reduces geographic latency
               - Improves connection times
               - Target: <50ms connection time
            
            6. **Minimize New Connections**
               - Consolidate resources from same domain
               - Reduce number of third-party domains
               - Target: <20% new connections
            """)
    
    @staticmethod
    def render_business_impact_tab(df: pd.DataFrame):
        """Render the Business Impact Analysis tab."""
        from analyzers.business_analyzer import BusinessAnalyzer
        
        st.subheader("💰 Business Impact Analysis")
        
        st.info("💡 **Note:** Revenue estimates are based on industry benchmarks. Adjust parameters below for your specific business.")
        
        # Configuration inputs
        st.markdown("### Business Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            monthly_visitors = st.number_input(
                "Monthly Visitors",
                min_value=100,
                max_value=10000000,
                value=10000,
                step=1000,
                help="Average monthly website visitors"
            )
        
        with col2:
            avg_order_value = st.number_input(
                "Average Order Value ($)",
                min_value=1.0,
                max_value=10000.0,
                value=50.0,
                step=5.0,
                help="Average value per transaction"
            )
        
        with col3:
            baseline_conversion = st.number_input(
                "Baseline Conversion Rate (%)",
                min_value=0.1,
                max_value=20.0,
                value=2.0,
                step=0.1,
                help="Current conversion rate percentage"
            ) / 100
        
        st.markdown("---")
        
        # User Experience Score
        st.subheader("👤 User Experience Score")
        
        ux_score = BusinessAnalyzer.calculate_user_experience_score(df)
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            score_color = "🟢" if ux_score['score'] >= 80 else "🟡" if ux_score['score'] >= 60 else "🔴"
            st.metric("UX Score", f"{score_color} {ux_score['score']}/100")
            st.metric("Grade", ux_score['grade'])
        
        with col2:
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Avg Load Time", f"{ux_score['avg_load_time']:.0f}ms")
            with col_b:
                st.metric("Consistency (CV)", f"{ux_score['consistency_cv']:.2f}")
            with col_c:
                st.metric("Error Rate", f"{ux_score['error_rate']:.1f}%")
            with col_d:
                st.metric("Total Size", f"{ux_score['total_size_mb']:.1f}MB")
        
        st.markdown("---")
        
        # Conversion Impact
        st.subheader("📈 Conversion Rate Impact")
        
        conversion_impact = BusinessAnalyzer.estimate_conversion_impact(df, baseline_conversion)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Baseline Conversion",
                f"{conversion_impact['baseline_conversion_rate']:.2f}%"
            )
        
        with col2:
            delta = conversion_impact['estimated_conversion_rate'] - conversion_impact['baseline_conversion_rate']
            st.metric(
                "Estimated Conversion",
                f"{conversion_impact['estimated_conversion_rate']:.2f}%",
                delta=f"{delta:.2f}%",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Abandonment Rate",
                f"{conversion_impact['abandonment_rate']:.1f}%"
            )
        
        if conversion_impact['conversion_loss_percentage'] > 0:
            st.warning(f"⚠️ Performance issues may be reducing conversion by {conversion_impact['conversion_loss_percentage']:.1f}%")
        else:
            st.success("✅ Load time is optimal for conversion")
        
        st.markdown("---")
        
        # Revenue Impact
        st.subheader("💵 Revenue Impact Estimate")
        
        revenue_impact = BusinessAnalyzer.estimate_revenue_impact(
            df,
            monthly_visitors=monthly_visitors,
            average_order_value=avg_order_value,
            baseline_conversion_rate=baseline_conversion
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Current State")
            st.metric("Monthly Revenue", f"${revenue_impact['estimated_monthly_revenue']:,.2f}")
            st.metric("Annual Revenue", f"${revenue_impact['estimated_monthly_revenue'] * 12:,.2f}")
        
        with col2:
            st.markdown("#### Potential Loss")
            st.metric(
                "Monthly Loss",
                f"${revenue_impact['monthly_revenue_loss']:,.2f}",
                delta=f"-${revenue_impact['monthly_revenue_loss']:,.2f}",
                delta_color="inverse"
            )
            st.metric(
                "Annual Loss",
                f"${revenue_impact['annual_revenue_loss']:,.2f}",
                delta=f"-${revenue_impact['annual_revenue_loss']:,.2f}",
                delta_color="inverse"
            )
        
        st.markdown("---")
        
        # Optimization Potential
        st.subheader("🚀 Optimization Potential")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Potential Monthly Gain",
                f"${revenue_impact['potential_monthly_gain']:,.2f}",
                delta=f"+${revenue_impact['potential_monthly_gain']:,.2f}"
            )
        
        with col2:
            st.metric(
                "Potential Annual Gain",
                f"${revenue_impact['potential_annual_gain']:,.2f}",
                delta=f"+${revenue_impact['potential_annual_gain']:,.2f}"
            )
        
        if revenue_impact['potential_monthly_gain'] > 0:
            st.success(f"💡 Reducing load time by 1 second could increase annual revenue by ${revenue_impact['potential_annual_gain']:,.2f}")
        
        st.markdown("---")
        
        # Industry Benchmarks
        with st.expander("📊 Industry Benchmarks & Research"):
            st.markdown("""
            **Performance Impact on Business Metrics:**
            
            1. **Load Time Impact**
               - 1 second delay = 7% reduction in conversions
               - 100ms delay = 1% drop in sales (Amazon)
               - 2 second delay = 87% bounce rate increase
            
            2. **Abandonment Rates by Load Time**
               - 1 second: 7% abandon
               - 2 seconds: 11% abandon
               - 3 seconds: 16% abandon
               - 5 seconds: 32% abandon
               - 10 seconds: 53% abandon
            
            3. **Mobile Impact**
               - 53% of mobile users abandon sites taking >3s to load
               - Mobile conversion rates are 2x lower with 5s load time
            
            4. **Revenue Correlation**
               - Every 100ms improvement = 1% revenue increase (Walmart)
               - 0.1s improvement = 8% conversion increase (Mobify)
            
            **Sources:** Google, Amazon, Akamai, Kissmetrics research
            """)
