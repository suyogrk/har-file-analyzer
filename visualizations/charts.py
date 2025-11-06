# visualizations/charts.py - Chart creation functions

import pandas as pd
import plotly.express as px
from config import (
    TIMING_PHASES,
    RESPONSE_TIME_HISTOGRAM_BINS,
    COLOR_SUCCESS,
    COLOR_REDIRECT,
    COLOR_ERROR,
    COLOR_SCALE,
)


class ChartFactory:
    """Factory for creating Plotly charts."""
    
    @staticmethod
    def create_timing_breakdown_chart(df: pd.DataFrame):
        """Create timing breakdown bar chart."""
        avg_timings = df[TIMING_PHASES].mean()
        
        fig = px.bar(
            x=avg_timings.index,
            y=avg_timings.values,
            title="Average Timing Breakdown",
            labels={'x': 'Timing Phase', 'y': 'Time (ms)'},
            color=avg_timings.values,
            color_continuous_scale=COLOR_SCALE
        )
        
        fig.update_layout(showlegend=False)
        return fig
    
    @staticmethod
    def create_response_time_histogram(df: pd.DataFrame):
        """Create response time distribution histogram."""
        fig = px.histogram(
            df,
            x='total_time',
            title="Response Time Distribution",
            labels={
                'total_time': 'Response Time (ms)',
                'count': 'Number of Requests'
            },
            nbins=RESPONSE_TIME_HISTOGRAM_BINS
        )
        
        # Add vertical line for 1000ms threshold
        fig.add_vline(
            x=1000,
            line_dash="dash",
            line_color="red",
            annotation_text="1000ms threshold"
        )
        
        return fig
    
    @staticmethod
    def create_status_code_chart(df: pd.DataFrame):
        """Create status code distribution pie chart."""
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        
        # Color code based on status ranges
        colors = []
        for status in status_counts['status']:
            if status < 300:
                colors.append(COLOR_SUCCESS)
            elif status < 400:
                colors.append(COLOR_REDIRECT)
            else:
                colors.append(COLOR_ERROR)
        
        fig = px.pie(
            status_counts,
            values='count',
            names='status',
            title="Status Code Distribution",
            color_discrete_sequence=colors
        )
        
        return fig
    
    @staticmethod
    def create_slowest_endpoints_chart(df: pd.DataFrame, limit: int = 10):
        """Create chart showing slowest endpoints."""
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
            color_continuous_scale=COLOR_SCALE
        )
        
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        return fig
