# parsers/har_parser.py - HAR file parsing

import json
import pandas as pd
from urllib.parse import urlparse
from typing import List, Optional, Tuple
from utils.logger import get_logger

from models.har_entry import HAREntry, HARTiming

# Initialize logger
logger = get_logger(__name__)


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
            har_data = json.loads(har_content)
            entries = har_data.get('log', {}).get('entries', [])
            
            if not entries:
                logger.warning("No entries found in HAR file")
                return None, "No entries found in HAR file"
            
            parsed_entries = []
            for entry in entries:
                har_entry = HARParser._parse_entry(entry)
                if har_entry:
                    parsed_entries.append(har_entry.to_dict())
            
            if not parsed_entries:
                logger.warning("No valid entries could be parsed from HAR file")
                return None, "No valid entries could be parsed from HAR file"
            
            logger.info(f"Successfully parsed {len(parsed_entries)} entries from HAR file")
            return pd.DataFrame(parsed_entries), None
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in HAR file: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except KeyError as e:
            error_msg = f"Missing required field in HAR file: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Error parsing HAR file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg
    
    @staticmethod
    def _parse_entry(entry: dict) -> Optional[HAREntry]:
        """Parse a single HAR entry."""
        try:
            request = entry.get('request', {})
            response = entry.get('response', {})
            timings = entry.get('timings', {})
            
            # Parse URL to get endpoint
            url = request.get('url', '')
            parsed_url = urlparse(url)
            endpoint = f"{parsed_url.netloc}{parsed_url.path}"
            
            # Create timing object
            timing = HARTiming(
                blocked=safe_time(timings.get('blocked')),
                dns=safe_time(timings.get('dns')),
                connect=safe_time(timings.get('connect')),
                send=safe_time(timings.get('send')),
                wait=safe_time(timings.get('wait')),
                receive=safe_time(timings.get('receive')),
                ssl=safe_time(timings.get('ssl')),
            )
            
            # Create entry object
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
            
            return har_entry
            
        except Exception as e:
            logger.debug(f"Failed to parse entry: {str(e)}")
            return None
