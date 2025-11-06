# models/har_entry.py - Data models

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class HARTiming:
    """Represents timing information for a request."""
    blocked: float = 0.0
    dns: float = 0.0
    connect: float = 0.0
    send: float = 0.0
    wait: float = 0.0
    receive: float = 0.0
    ssl: float = 0.0
    
    @property
    def total(self) -> float:
        """Calculate total timing."""
        return sum([self.blocked, self.dns, self.connect, 
                   self.send, self.wait, self.receive, self.ssl])


@dataclass
class HAREntry:
    """Represents a single HAR entry (HTTP request/response)."""
    url: str
    endpoint: str
    method: str
    status: int
    status_text: str
    total_time: float
    timing: HARTiming
    started_datetime: str
    response_size: int
    mime_type: str
    
    # Dynamic fields added during analysis
    problems: List[str] = field(default_factory=list)
    is_problematic: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame compatibility."""
        return {
            'url': self.url,
            'endpoint': self.endpoint,
            'method': self.method,
            'status': self.status,
            'status_text': self.status_text,
            'total_time': self.total_time,
            'blocked': self.timing.blocked,
            'dns': self.timing.dns,
            'connect': self.timing.connect,
            'send': self.timing.send,
            'wait': self.timing.wait,
            'receive': self.timing.receive,
            'ssl': self.timing.ssl,
            'started_datetime': self.started_datetime,
            'response_size': self.response_size,
            'mime_type': self.mime_type,
            'problems': ', '.join(self.problems) if self.problems else 'No Issues',
            'is_problematic': self.is_problematic,
        }
