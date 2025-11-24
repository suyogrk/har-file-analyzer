# ui/filters.py - Filter components

import streamlit as st
import pandas as pd
from typing import Tuple, Optional
from urllib.parse import urlparse


class FilterManager:
    """Manages filtering for HAR data."""
    
    # Pre-defined filter templates
    FILTER_PRESETS = {
        'All Requests': None,
        'Slow Requests (>1s)': 'slow',
        'Large Resources (>100KB)': 'large',
        'Errors Only (4xx/5xx)': 'errors',
        'Third-Party': 'third_party',
        'Blocking Resources': 'blocking'
    }
    
    @staticmethod
    def render_filter_controls(df: pd.DataFrame) -> Tuple[str, str, int, Optional[str]]:
        """
        Render filter controls in the UI.
        
        Returns:
            Tuple of (search_term, method_filter, status_filter, preset_filter)
        """
        # Filter preset dropdown
        st.subheader("Quick Filters")
        preset = st.selectbox(
            "📋 Filter Preset",
            list(FilterManager.FILTER_PRESETS.keys()),
            help="Select a pre-defined filter template"
        )
        
        st.markdown("---")
        st.subheader("Custom Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("🔍 Search URL/Endpoint")
        
        with col2:
            method_filter = st.selectbox(
                "HTTP Method",
                ['All'] + df['method'].unique().tolist()
            )
        
        with col3:
            status_filter = st.selectbox(
                "Status Code",
                ['All'] + sorted(df['status'].unique().tolist())
            )
        
        preset_filter = FilterManager.FILTER_PRESETS[preset]
        
        return search_term, method_filter, status_filter, preset_filter
    
    @staticmethod
    def apply_filters(
        df: pd.DataFrame,
        search_term: str = None,
        method_filter: str = None,
        status_filter: int = None,
        preset_filter: str = None
    ) -> pd.DataFrame:
        """Apply filters to the DataFrame."""
        filtered_df = df.copy()
        
        # Apply preset filter first
        if preset_filter:
            filtered_df = FilterManager._apply_preset_filter(filtered_df, preset_filter)
        
        # Apply custom filters
        if search_term:
            filtered_df = filtered_df[
                filtered_df['url'].str.contains(search_term, case=False, na=False) |
                filtered_df['endpoint'].str.contains(search_term, case=False, na=False)
            ]
        
        if method_filter and method_filter != 'All':
            filtered_df = filtered_df[filtered_df['method'] == method_filter]
        
        if status_filter and status_filter != 'All':
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        return filtered_df
    
    @staticmethod
    def _apply_preset_filter(df: pd.DataFrame, preset: str) -> pd.DataFrame:
        """Apply a preset filter to the DataFrame."""
        if preset == 'slow':
            # Slow requests (>1000ms)
            return df[df['total_time'] > 1000]
        
        elif preset == 'large':
            # Large resources (>100KB)
            return df[df['response_size'] > 100 * 1024]
        
        elif preset == 'errors':
            # Error responses (4xx/5xx)
            return df[df['status'] >= 400]
        
        elif preset == 'third_party':
            # Third-party resources (different domain than most common)
            if 'domain' not in df.columns:
                df['domain'] = df['url'].apply(lambda x: urlparse(x).netloc)
            
            # Get main domain (most frequent)
            main_domain = df['domain'].value_counts().index[0] if not df.empty else ''
            
            # Filter for domains not matching main domain
            return df[~df['domain'].str.contains(main_domain, na=False, regex=False)]
        
        elif preset == 'blocking':
            # Blocking resources (high wait time >500ms)
            return df[df['wait'] > 500]
        
        return df
