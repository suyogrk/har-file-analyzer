# parsers/har_parser.py - HAR file parsing

import json
import pandas as pd
from urllib.parse import urlparse
from typing import List, Optional, Tuple, Iterator
from utils.logger import get_logger
from exceptions import HARParseError, HARValidationError, HARFileError

from models.har_entry import HAREntry, HARTiming

# Initialize logger
logger = get_logger(__name__)

# Configuration for chunked processing
CHUNK_SIZE = 1000  # Process entries in chunks of 1000
LARGE_FILE_THRESHOLD = 10000  # Files with more than 10k entries are considered large


def safe_time(value: float | None) -> float:
    """Safely convert timing value to float, handling None and negative values."""
    try:
        if value is None or not isinstance(value, (int, float)):
            return 0.0
        return max(value, 0.0)
    except (TypeError, ValueError):
        return 0.0


class HARParser:
    """Parser for HAR (HTTP Archive) files."""
    
    @staticmethod
    def parse(har_content: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Parse HAR file content and return DataFrame.
        
        Args:
            har_content: Raw HAR file content as string
            
        Returns:
            Tuple of (DataFrame with parsed entries or None, error message or None)
        """
        try:
            # Validate input
            if not har_content or not har_content.strip():
                raise HARValidationError("HAR file content is empty", field="content")
            
            # Parse JSON
            try:
                har_data = json.loads(har_content)
            except json.JSONDecodeError as e:
                raise HARParseError(
                    f"Invalid JSON format in HAR file: {str(e)}",
                    line_number=getattr(e, 'lineno', None),
                    details=f"JSON error at position {getattr(e, 'pos', 'unknown')}"
                )
            
            # Validate HAR structure
            if not isinstance(har_data, dict):
                raise HARValidationError("HAR file must be a JSON object", field="root")
            
            if 'log' not in har_data:
                raise HARValidationError("Missing 'log' field in HAR file", field="log")
            
            log_data = har_data['log']
            if not isinstance(log_data, dict):
                raise HARValidationError("'log' field must be an object", field="log")
            
            # Get entries
            entries = log_data.get('entries', [])
            if not entries:
                raise HARValidationError("No entries found in HAR file", field="log.entries")
            
            if not isinstance(entries, list):
                raise HARValidationError("'entries' field must be an array", field="log.entries")
            
            # Check if we should use chunked processing for large files
            if len(entries) > LARGE_FILE_THRESHOLD:
                logger.info(f"Large HAR file detected ({len(entries)} entries), using chunked processing")
                return HARParser._parse_large_file(entries)
            else:
                return HARParser._parse_standard_file(entries)
                
        except (HARParseError, HARValidationError) as e:
            # Re-raise our custom exceptions
            logger.error(f"HAR parsing failed: {str(e)}")
            return None, str(e)
        except Exception as e:
            # Catch any other unexpected exceptions
            error_msg = f"Unexpected error parsing HAR file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
    
    @staticmethod
    def _parse_standard_file(entries: List[dict]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Parse a standard-sized HAR file.
        
        Args:
            entries: List of HAR entries
            
        Returns:
            Tuple of (DataFrame with parsed entries or None, error message or None)
        """
        parsed_entries = []
        parse_errors = []
        
        for i, entry in enumerate(entries):
            try:
                har_entry = HARParser._parse_entry(entry)
                if har_entry:
                    parsed_entries.append(har_entry.to_dict())
            except HARParseError as e:
                parse_errors.append(f"Entry {i}: {str(e)}")
                logger.warning(f"Failed to parse entry {i}: {str(e)}")
            except Exception as e:
                parse_errors.append(f"Entry {i}: Unexpected error - {str(e)}")
                logger.warning(f"Unexpected error parsing entry {i}: {str(e)}")
        
        # Check if we have any valid entries
        if not parsed_entries:
            if parse_errors:
                raise HARParseError(
                    "No valid entries could be parsed from HAR file",
                    details=f"Parse errors: {'; '.join(parse_errors[:5])}"
                )
            else:
                raise HARParseError("No valid entries could be parsed from HAR file")
        
        # Log warnings for any parse errors
        if parse_errors:
            logger.warning(f"Encountered {len(parse_errors)} parse errors while parsing HAR file")
            logger.debug(f"Parse errors: {'; '.join(parse_errors[:10])}")
        
        # Create DataFrame
        try:
            df = pd.DataFrame(parsed_entries)
            logger.info(f"Successfully parsed {len(parsed_entries)} entries from HAR file")
            return df, None
        except Exception as e:
            raise HARParseError(
                f"Failed to create DataFrame from parsed entries: {str(e)}",
                details="This may indicate a data type inconsistency in parsed entries"
            )
    
    @staticmethod
    def _parse_large_file(entries: List[dict]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Parse a large HAR file using chunked processing to reduce memory usage.
        
        Args:
            entries: List of HAR entries
            
        Returns:
            Tuple of (DataFrame with parsed entries or None, error message or None)
        """
        logger.info(f"Processing {len(entries)} entries in chunks of {CHUNK_SIZE}")
        
        # Process entries in chunks
        chunk_dfs = []
        total_parsed = 0
        total_errors = 0
        
        for chunk_start in range(0, len(entries), CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, len(entries))
            chunk = entries[chunk_start:chunk_end]
            
            logger.debug(f"Processing chunk {chunk_start//CHUNK_SIZE + 1}: entries {chunk_start}-{chunk_end-1}")
            
            # Parse this chunk
            chunk_entries = []
            chunk_errors = 0
            
            for i, entry in enumerate(chunk):
                try:
                    har_entry = HARParser._parse_entry(entry)
                    if har_entry:
                        chunk_entries.append(har_entry.to_dict())
                except HARParseError as e:
                    chunk_errors += 1
                    logger.debug(f"Failed to parse entry {chunk_start + i}: {str(e)}")
                except Exception as e:
                    chunk_errors += 1
                    logger.debug(f"Unexpected error parsing entry {chunk_start + i}: {str(e)}")
            
            # Create DataFrame for this chunk
            if chunk_entries:
                chunk_df = pd.DataFrame(chunk_entries)
                chunk_dfs.append(chunk_df)
                total_parsed += len(chunk_entries)
            
            total_errors += chunk_errors
            
            # Log progress
            if (chunk_start // CHUNK_SIZE + 1) % 10 == 0:  # Every 10 chunks
                logger.info(f"Processed {chunk_end}/{len(entries)} entries ({chunk_end/len(entries)*100:.1f}%)")
        
        # Combine all chunks
        if not chunk_dfs:
            raise HARParseError(
                "No valid entries could be parsed from HAR file",
                details=f"Total errors: {total_errors}"
            )
        
        try:
            # Concatenate all chunk DataFrames
            df = pd.concat(chunk_dfs, ignore_index=True)
            
            logger.info(f"Successfully parsed {total_parsed} entries from HAR file with {total_errors} errors")
            return df, None
        except Exception as e:
            raise HARParseError(
                f"Failed to combine chunked DataFrames: {str(e)}",
                details="This may indicate a data type inconsistency between chunks"
            )
    
    @staticmethod
    def _parse_entry(entry: dict) -> Optional[HAREntry]:
        """Parse a single HAR entry."""
        try:
            # Validate entry structure
            if not isinstance(entry, dict):
                raise HARParseError("Entry must be a JSON object")
            
            # Extract required fields with validation
            request = entry.get('request')
            if not request or not isinstance(request, dict):
                raise HARParseError("Missing or invalid 'request' field in entry")
            
            response = entry.get('response')
            if not response or not isinstance(response, dict):
                raise HARParseError("Missing or invalid 'response' field in entry")
            
            timings = entry.get('timings', {})
            if not isinstance(timings, dict):
                raise HARParseError("Invalid 'timings' field in entry")
            
            # Parse URL to get endpoint
            url = request.get('url', '')
            if not url:
                raise HARParseError("Missing 'url' in request")
            
            try:
                parsed_url = urlparse(url)
                if not parsed_url.netloc:
                    raise HARParseError(f"Invalid URL format: {url}")
                endpoint = f"{parsed_url.netloc}{parsed_url.path}"
            except Exception as e:
                raise HARParseError(f"Failed to parse URL '{url}': {str(e)}")
            
            # Create timing object
            try:
                timing = HARTiming(
                    blocked=safe_time(timings.get('blocked')),
                    dns=safe_time(timings.get('dns')),
                    connect=safe_time(timings.get('connect')),
                    send=safe_time(timings.get('send')),
                    wait=safe_time(timings.get('wait')),
                    receive=safe_time(timings.get('receive')),
                    ssl=safe_time(timings.get('ssl')),
                )
            except Exception as e:
                raise HARParseError(f"Failed to parse timing data: {str(e)}")
            
            # Create entry object
            try:
                har_entry = HAREntry(
                    url=url,
                    endpoint=endpoint,
                    method=request.get('method', 'GET'),
                    status=response.get('status', 0),
                    status_text=response.get('statusText', ''),
                    total_time=entry.get('time', 0),
                    timing=timing,
                    started_datetime=entry.get('startedDateTime', ''),
                    response_size=response.get('content', {}).get('size', 0),
                    mime_type=response.get('content', {}).get('mimeType', ''),
                )
            except Exception as e:
                raise HARParseError(f"Failed to create HAR entry: {str(e)}")
            
            return har_entry
            
        except HARParseError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap other exceptions in HARParseError
            raise HARParseError(f"Unexpected error parsing entry: {str(e)}")
