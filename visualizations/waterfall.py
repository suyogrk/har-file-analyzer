# visualizations/waterfall.py - Request waterfall visualization

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Tuple
from analyzers.resource_analyzer import ResourceAnalyzer


class WaterfallChart:
    """Creates interactive waterfall chart for request timeline visualization."""
    
    # Color scheme for timing phases
    PHASE_COLORS = {
        'blocked': '#808080',  # Gray
        'dns': '#4CAF50',      # Green
        'connect': '#2196F3',  # Blue
        'ssl': '#9C27B0',      # Purple
        'send': '#FF9800',     # Orange
        'wait': '#F44336',     # Red
        'receive': '#00BCD4'   # Cyan
    }
    
    @staticmethod
    def create_waterfall(df: pd.DataFrame, max_requests: int = 100) -> Tuple[go.Figure, str]:
        """
        Create waterfall chart showing request timeline.
        
        Args:
            df: DataFrame with HAR entries
            max_requests: Maximum number of requests to display
            
        Returns:
            Tuple of (Plotly figure, chart key)
        """
        if df.empty:
            return None, None
        
        # Limit requests for performance
        display_df = df.head(max_requests).copy()
        
        # Parse start times and calculate relative times
        display_df = WaterfallChart._calculate_relative_times(display_df)
        
        # Create figure
        fig = go.Figure()
        
        # Add bars for each timing phase
        phases = ['blocked', 'dns', 'connect', 'ssl', 'send', 'wait', 'receive']
        
        for idx, row in display_df.iterrows():
            current_time = row['relative_start']
            
            # Add each timing phase as a separate bar segment
            for phase in phases:
                if row[phase] > 0:
                    # Create hover text
                    hover_text = (
                        f"<b>{row['endpoint'][:50]}</b><br>"
                        f"Phase: {phase.upper()}<br>"
                        f"Duration: {row[phase]:.1f}ms<br>"
                        f"Start: {current_time:.1f}ms<br>"
                        f"Total: {row['total_time']:.1f}ms"
                    )
                    
                    fig.add_trace(go.Bar(
                        name=phase,
                        x=[row[phase]],
                        y=[idx],
                        orientation='h',
                        marker=dict(color=WaterfallChart.PHASE_COLORS.get(phase, '#000000')),
                        hovertemplate=hover_text + '<extra></extra>',
                        showlegend=(idx == 0),  # Only show legend for first request
                        base=current_time,
                        width=0.8
                    ))
                    
                    current_time += row[phase]
        
        # Update layout
        fig.update_layout(
            title="Request Waterfall Timeline",
            xaxis_title="Time (ms)",
            yaxis_title="Request",
            barmode='overlay',
            height=max(600, len(display_df) * 25),
            hovermode='closest',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update y-axis to show request numbers
        fig.update_yaxes(
            tickmode='linear',
            tick0=0,
            dtick=1,
            autorange='reversed'
        )
        
        return fig, "waterfall_chart"
    
    @staticmethod
    def _calculate_relative_times(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate relative start times for requests.
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            DataFrame with relative_start column
        """
        # Try to parse startedDateTime if available
        if 'started_datetime' in df.columns:
            try:
                df['start_time'] = pd.to_datetime(df['started_datetime'])
                first_start = df['start_time'].min()
                df['relative_start'] = (df['start_time'] - first_start).dt.total_seconds() * 1000
            except:
                # Fallback: use sequential ordering
                df['relative_start'] = 0
        else:
            # Fallback: use sequential ordering
            df['relative_start'] = 0
        
        return df
    
    @staticmethod
    def create_simplified_waterfall(df: pd.DataFrame, max_requests: int = 50) -> Tuple[go.Figure, str]:
        """
        Create simplified waterfall showing just total time bars.
        
        Args:
            df: DataFrame with HAR entries
            max_requests: Maximum number of requests to display
            
        Returns:
            Tuple of (Plotly figure, chart key)
        """
        if df.empty:
            return None, None
        
        # Limit requests
        display_df = df.head(max_requests).copy()
        
        # Calculate relative times
        display_df = WaterfallChart._calculate_relative_times(display_df)
        
        # Add resource type for coloring
        display_df['resource_type'] = display_df['mime_type'].apply(
            ResourceAnalyzer.classify_resource_type
        )
        
        # Create figure
        fig = go.Figure()
        
        # Color map for resource types
        color_map = {
            'JavaScript': '#FFC107',
            'CSS': '#2196F3',
            'Images': '#4CAF50',
            'HTML': '#9C27B0',
            'Fonts': '#FF5722',
            'JSON': '#00BCD4',
            'Other': '#9E9E9E'
        }
        
        for idx, row in display_df.iterrows():
            color = color_map.get(row['resource_type'], '#9E9E9E')
            
            hover_text = (
                f"<b>{row['endpoint'][:50]}</b><br>"
                f"Type: {row['resource_type']}<br>"
                f"Duration: {row['total_time']:.1f}ms<br>"
                f"Start: {row['relative_start']:.1f}ms<br>"
                f"Status: {row['status']}"
            )
            
            fig.add_trace(go.Bar(
                x=[row['total_time']],
                y=[idx],
                orientation='h',
                marker=dict(color=color),
                hovertemplate=hover_text + '<extra></extra>',
                showlegend=False,
                base=row['relative_start'],
                width=0.8
            ))
        
        # Update layout
        fig.update_layout(
            title="Simplified Request Timeline",
            xaxis_title="Time (ms)",
            yaxis_title="Request #",
            height=max(500, len(display_df) * 20),
            hovermode='closest'
        )
        
        fig.update_yaxes(
            tickmode='linear',
            tick0=0,
            dtick=1,
            autorange='reversed'
        )
        
        return fig, "simplified_waterfall"
    
    @staticmethod
    def analyze_request_patterns(df: pd.DataFrame) -> Dict:
        """
        Analyze request patterns (parallel vs sequential).
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            Dictionary with pattern analysis
        """
        if df.empty or 'started_datetime' not in df.columns:
            return {
                'total_requests': len(df),
                'analysis_available': False
            }
        
        try:
            df['start_time'] = pd.to_datetime(df['started_datetime'])
            df = df.sort_values('start_time')
            
            # Calculate end times
            df['end_time'] = df['start_time'] + pd.to_timedelta(df['total_time'], unit='ms')
            
            # Find overlapping requests (parallel)
            parallel_count = 0
            for i in range(len(df) - 1):
                current_end = df.iloc[i]['end_time']
                next_start = df.iloc[i + 1]['start_time']
                
                if next_start < current_end:
                    parallel_count += 1
            
            total_duration = (df['end_time'].max() - df['start_time'].min()).total_seconds() * 1000
            
            return {
                'total_requests': len(df),
                'parallel_requests': parallel_count,
                'sequential_requests': len(df) - parallel_count,
                'parallelization_ratio': round((parallel_count / len(df) * 100) if len(df) > 0 else 0, 2),
                'total_duration_ms': round(total_duration, 2),
                'analysis_available': True
            }
        except:
            return {
                'total_requests': len(df),
                'analysis_available': False
            }
    
    @staticmethod
    def identify_critical_path(df: pd.DataFrame) -> List[Dict]:
        """
        Identify critical path (slowest sequential chain).
        
        Args:
            df: DataFrame with HAR entries
            
        Returns:
            List of requests in critical path
        """
        if df.empty:
            return []
        
        # Sort by total time and get top 10 slowest
        critical_requests = df.nlargest(10, 'total_time')
        
        return critical_requests[['endpoint', 'total_time', 'status']].to_dict('records')
