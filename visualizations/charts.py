# visualizations/charts.py - Chart creation functions

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Tuple, Optional, List, Dict, Any, Union
import streamlit as st
from config import (
    TIMING_PHASES,
    RESPONSE_TIME_HISTOGRAM_BINS,
    COLOR_SUCCESS,
    COLOR_REDIRECT,
    COLOR_ERROR,
    COLOR_SCALE,
)


# Cache heavy chart configurations
@st.cache_resource
def get_chart_configurations():
    """Get cached chart configurations."""
    return {
        'default_layout': {
            'font': {'family': 'Arial, sans-serif', 'size': 12},
            'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
        },
        'performance_gauge_colors': {
            'excellent': '#00CC96',
            'good': '#FF6692',
            'poor': '#B6E880',
            'bad': '#FF97FF',
        },
        'status_colors': {
            'success': COLOR_SUCCESS,
            'redirect': COLOR_REDIRECT,
            'error': COLOR_ERROR,
        },
        'percentile_colors': ['green', 'lightgreen', 'yellow', 'orange', 'red'],
        'timing_colors': {
            'blocked': '#FF6692',
            'dns': '#FF97FF',
            'connect': '#B6E880',
            'send': '#19D3F3',
            'wait': '#FF6692',
            'receive': '#00CC96',
            'ssl': '#FF6692',
        }
    }


@st.cache_resource
def get_chart_templates():
    """Get cached chart templates."""
    return {
        'histogram_template': 'plotly_white',
        'pie_template': 'plotly_white',
        'bar_template': 'plotly_white',
        'scatter_template': 'plotly_white',
        'gauge_template': 'plotly_white',
    }


class ChartFactory:
    """Factory for creating Plotly charts."""
    
    @staticmethod
    def create_timing_breakdown_chart(df: pd.DataFrame, key: str = None) -> Tuple[go.Figure, str]:
        """Create timing breakdown bar chart."""
        configs = get_chart_configurations()
        avg_timings = df[TIMING_PHASES].mean()
        
        # Create custom colors for each timing phase
        colors = [configs['timing_colors'].get(phase, '#7F7F7F') for phase in avg_timings.index]
        
        fig = px.bar(
            x=avg_timings.index,
            y=avg_timings.values,
            title="Average Timing Breakdown",
            labels={'x': 'Timing Phase', 'y': 'Time (ms)'},
            color=avg_timings.index,
            color_discrete_map={phase: configs['timing_colors'].get(phase, '#7F7F7F') for phase in avg_timings.index}
        )
        
        fig.update_layout(
            showlegend=False,
            template=get_chart_templates()['bar_template'],
            **configs['default_layout']
        )
        return fig, key or "timing_breakdown"
    
    @staticmethod
    def create_response_time_histogram(df: pd.DataFrame, key: str = None) -> Tuple[go.Figure, str]:
        """Create response time distribution histogram."""
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        fig = px.histogram(
            df,
            x='total_time',
            title="Response Time Distribution",
            labels={
                'total_time': 'Response Time (ms)',
                'count': 'Number of Requests'
            },
            nbins=RESPONSE_TIME_HISTOGRAM_BINS,
            template=templates['histogram_template']
        )
        
        # Add vertical line for 1000ms threshold
        fig.add_vline(
            x=1000,
            line_dash="dash",
            line_color="red",
            annotation_text="1000ms threshold"
        )
        
        fig.update_layout(**configs['default_layout'])
        return fig, key or "response_time_histogram"
    
    @staticmethod
    def create_status_code_chart(df: pd.DataFrame, key: str = None) -> Tuple[go.Figure, str]:
        """Create status code distribution pie chart."""
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        
        # Color code based on status ranges
        colors = []
        for status in status_counts['status']:
            if status < 300:
                colors.append(configs['status_colors']['success'])
            elif status < 400:
                colors.append(configs['status_colors']['redirect'])
            else:
                colors.append(configs['status_colors']['error'])
        
        fig = px.pie(
            status_counts,
            values='count',
            names='status',
            title="Status Code Distribution",
            color_discrete_sequence=colors,
            template=templates['pie_template']
        )
        
        fig.update_layout(**configs['default_layout'])
        return fig, key or "status_code_chart"
    
    @staticmethod
    def create_slowest_endpoints_chart(df: pd.DataFrame, limit: int = 10, key: str = None) -> Tuple[go.Figure, str]:
        """Create chart showing slowest endpoints."""
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        endpoint_stats = df.groupby('endpoint').agg({
            'total_time': ['mean', 'count']
        }).round(2)
        
        endpoint_stats.columns = ['avg_response_time', 'request_count']
        endpoint_stats = endpoint_stats.reset_index()
        endpoint_stats = endpoint_stats[endpoint_stats['request_count'] >= 1]
        endpoint_stats = endpoint_stats.sort_values(
            'avg_response_time',
            ascending=False
        ).head(limit)
        
        fig = px.bar(
            endpoint_stats,
            x='avg_response_time',
            y='endpoint',
            orientation='h',
            title="Top 10 Slowest Endpoints",
            labels={
                'avg_response_time': 'Average Response Time (ms)',
                'endpoint': 'Endpoint'
            },
            color='avg_response_time',
            color_continuous_scale=COLOR_SCALE,
            template=templates['bar_template']
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            **configs['default_layout']
        )
        return fig, key or "slowest_endpoints_chart"
    
    @staticmethod
    def create_domain_performance_chart(domain_stats: pd.DataFrame, key: str = None) -> Tuple[Optional[go.Figure], Optional[str]]:
        """Create domain-wise performance breakdown chart."""
        if domain_stats.empty:
            return None, None
        
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        # Take top 15 domains by total time
        top_domains = domain_stats.head(15)
        
        fig = px.bar(
            top_domains,
            x='total_time_sum',
            y='domain',
            orientation='h',
            title="Domain Performance Impact",
            labels={
                'total_time_sum': 'Total Time (ms)',
                'domain': 'Domain'
            },
            color='time_percentage',
            color_continuous_scale=COLOR_SCALE,
            hover_data=['request_count', 'avg_time'],
            template=templates['bar_template']
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            **configs['default_layout']
        )
        return fig, key or "domain_performance_chart"
    
    @staticmethod
    def create_resource_size_chart(resource_stats: pd.DataFrame, key: str = None) -> Tuple[Optional[go.Figure], Optional[str]]:
        """Create resource size distribution by type."""
        if resource_stats.empty:
            return None, None
        
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        fig = px.pie(
            resource_stats,
            values='total_size',
            names='resource_type',
            title="Resource Size Distribution by Type",
            hole=0.3,
            template=templates['pie_template']
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        
        fig.update_layout(**configs['default_layout'])
        return fig, key or "resource_size_chart"
    
    @staticmethod
    def create_performance_score_gauge(score: int, grade: str, key: str = None) -> Tuple[go.Figure, str]:
        """Create performance score gauge chart."""
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        # Determine color based on score
        if score >= 80:
            color = configs['performance_gauge_colors']['excellent']
        elif score >= 60:
            color = configs['performance_gauge_colors']['good']
        else:
            color = configs['performance_gauge_colors']['bad']
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Performance Score: {grade}"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            template=templates['gauge_template'],
            **configs['default_layout']
        )
        return fig, key or "performance_score_gauge"
    
    @staticmethod
    def create_percentile_chart(df: pd.DataFrame, key: str = None) -> Tuple[go.Figure, str]:
        """Create percentile analysis chart."""
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        percentiles = [0.5, 0.75, 0.9, 0.95, 0.99]
        percentile_values = [df['total_time'].quantile(p) for p in percentiles]
        percentile_labels = ['P50', 'P75', 'P90', 'P95', 'P99']
        
        fig = go.Figure(data=[
            go.Bar(
                x=percentile_labels,
                y=percentile_values,
                text=[f"{v:.0f}ms" for v in percentile_values],
                textposition='auto',
                marker_color=configs['percentile_colors']
            )
        ])
        
        fig.update_layout(
            title="Response Time Percentiles",
            xaxis_title="Percentile",
            yaxis_title="Response Time (ms)",
            showlegend=False,
            template=templates['bar_template'],
            **configs['default_layout']
        )
        
        return fig, key or "percentile_chart"
    
    @staticmethod
    def create_size_vs_time_scatter(df: pd.DataFrame, key: str = None) -> Tuple[go.Figure, str]:
        """Create scatter plot of resource size vs load time."""
        # Add resource type for coloring
        from analyzers.resource_analyzer import ResourceAnalyzer
        
        configs = get_chart_configurations()
        templates = get_chart_templates()
        
        df_plot = df.copy()
        df_plot['resource_type'] = df_plot['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        fig = px.scatter(
            df_plot,
            x='response_size',
            y='total_time',
            color='resource_type',
            title="Resource Size vs Load Time Correlation",
            labels={
                'response_size': 'Resource Size (bytes)',
                'total_time': 'Load Time (ms)'
            },
            hover_data=['url'],
            template=templates['scatter_template']
        )
        
        fig.update_layout(**configs['default_layout'])
        return fig, key or "size_vs_time_scatter"
