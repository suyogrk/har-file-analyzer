# utils/validators.py - Input validation utilities

import pandas as pd
from typing import Optional, List
from utils.logger import get_logger

logger = get_logger(__name__)

# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MIN_FILE_SIZE = 100  # 100 bytes

# Required DataFrame columns
REQUIRED_COLUMNS = [
    'url', 'endpoint', 'method', 'status', 'total_time',
    'blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl'
]


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file size.
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size < MIN_FILE_SIZE:
        error = f"File too small ({file_size} bytes). Minimum size is {MIN_FILE_SIZE} bytes."
        logger.warning(error)
        return False, error
    
    if file_size > MAX_FILE_SIZE:
        error = f"File too large ({file_size / (1024*1024):.1f} MB). Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f} MB."
        logger.warning(error)
        return False, error
    
    return True, None


def validate_dataframe_schema(df: pd.DataFrame) -> tuple[bool, Optional[str]]:
    """
    Validate that DataFrame has required columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if df is None or df.empty:
        error = "DataFrame is empty or None"
        logger.error(error)
        return False, error
    
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_columns:
        error = f"Missing required columns: {', '.join(missing_columns)}"
        logger.error(error)
        return False, error
    
    return True, None


def validate_har_content(content: str) -> tuple[bool, Optional[str]]:
    """
    Basic validation of HAR file content.
    
    Args:
        content: HAR file content as string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        error = "File content is empty"
        logger.warning(error)
        return False, error
    
    # Check if it looks like JSON
    if not content.strip().startswith('{'):
        error = "File does not appear to be valid JSON"
        logger.warning(error)
        return False, error
    
    return True, None
