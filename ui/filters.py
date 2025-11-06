# ui/filters.py - Filter components

import streamlit as st
import pandas as pd
from typing import Tuple


class FilterManager:
    """Manages filtering for HAR data."""
    
    @staticmethod
    def render_filter_controls(df: pd.DataFrame) -> Tuple[str, str, int]:
        """
        Render filter controls in the UI.
        
        Returns:
            Tuple of (search_term, method_filter, status_filter)
        """
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
        
        return search_term, method_filter, status_filter
    
    @staticmethod
    def apply_filters(
        df: pd.DataFrame,
        search_term: str = None,
        method_filter: str = None,
        status_filter: int = None
    ) -> pd.DataFrame:
        """Apply filters to the DataFrame."""
        filtered_df = df.copy()
        
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
