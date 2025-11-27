# types.py - Common type definitions for HAR Analyzer

from typing import Dict, List, Tuple, Optional, Union, Any, TypedDict, Protocol
from dataclasses import dataclass
import pandas as pd
import plotly.graph_objects as go


# Common type aliases
DataFrame = pd.DataFrame
Figure = go.Figure
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
TimingPhase = str
Endpoint = str
Domain = str
ResourceType = str
Method = str
StatusCode = int
FileSize = int
TimeInMs = float
Percentage = float


# TypedDict definitions for structured data
class HAREntryDict(TypedDict):
    """Type definition for HAR entry dictionary."""
    url: str
    endpoint: str
    method: str
    status: int
    status_text: str
    total_time: float
    blocked: float
    dns: float
    connect: float
    send: float
    wait: float
    receive: float
    ssl: float
    started_datetime: str
    response_size: int
    mime_type: str
    problems: str
    is_problematic: bool


class PerformanceStatsDict(TypedDict):
    """Type definition for performance statistics."""
    total_requests: int
    unique_endpoints: int
    error_rate: float
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    problematic_count: int


class EndpointStatsDict(TypedDict):
    """Type definition for endpoint statistics."""
    endpoint: str
    avg_response_time: float
    request_count: int


class DomainStatsDict(TypedDict):
    """Type definition for domain statistics."""
    domain: str
    request_count: int
    total_time_sum: float
    avg_time: float
    time_percentage: float


class ResourceStatsDict(TypedDict):
    """Type definition for resource statistics."""
    resource_type: str
    count: int
    total_size: int
    avg_size: float


class SecurityIssueDict(TypedDict):
    """Type definition for security issues."""
    category: str
    severity: str
    description: str
    impact: str


class RecommendationDict(TypedDict):
    """Type definition for recommendations."""
    title: str
    category: str
    priority: str
    description: str
    impact: str
    effort: str


class PerformanceScoreDict(TypedDict):
    """Type definition for performance score."""
    score: int
    grade: str
    summary: str


class CacheAnalysisDict(TypedDict):
    """Type definition for cache analysis."""
    total_requests: int
    cacheable_requests: int
    cacheable_percentage: float
    potential_savings_kb: float


class ConnectionAnalysisDict(TypedDict):
    """Type definition for connection analysis."""
    total_requests: int
    new_connections: int
    reused_connections: int
    connection_reuse_ratio: float
    avg_connect_time: float
    avg_ssl_time: float
    connect_time_percentage: float


class BusinessImpactDict(TypedDict):
    """Type definition for business impact analysis."""
    estimated_monthly_revenue: float
    monthly_revenue_loss: float
    annual_revenue_loss: float
    potential_monthly_gain: float
    potential_annual_gain: float


class ComparisonDict(TypedDict):
    """Type definition for HAR file comparison."""
    scores: Dict[str, PerformanceScoreDict]
    score_delta: float
    improvement: bool
    metrics: Dict[str, Dict[str, float]]


# Protocol definitions for interfaces
class ParserProtocol(Protocol):
    """Protocol for HAR parsers."""
    
    def parse(self, content: str) -> Tuple[Optional[DataFrame], Optional[str]]:
        """Parse HAR content into DataFrame."""
        ...


class AnalyzerProtocol(Protocol):
    """Protocol for data analyzers."""
    
    def analyze(self, df: DataFrame) -> Dict[str, Any]:
        """Analyze DataFrame and return results."""
        ...


class VisualizerProtocol(Protocol):
    """Protocol for data visualizers."""
    
    def create_chart(self, df: DataFrame, **kwargs) -> Tuple[Optional[Figure], Optional[str]]:
        """Create a chart from DataFrame."""
        ...


# Dataclass definitions for structured data
@dataclass
class TimingInfo:
    """Dataclass for timing information."""
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
class RequestInfo:
    """Dataclass for request information."""
    url: str
    endpoint: str
    method: str
    status: int
    status_text: str
    total_time: float
    timing: TimingInfo
    started_datetime: str
    response_size: int
    mime_type: str
    problems: List[str]
    is_problematic: bool = False


@dataclass
class PerformanceThresholds:
    """Dataclass for performance thresholds."""
    slow_response_ms: float = 1000.0
    high_wait_ms: float = 500.0
    connection_delay_ms: float = 1000.0
    dns_delay_ms: float = 100.0


@dataclass
class ChartConfig:
    """Dataclass for chart configuration."""
    title: str
    x_label: str
    y_label: str
    color_scale: str = "Reds"
    height: int = 400
    width: int = 800


# Union types for common parameters
FilterValue = Union[str, List[str], None]
ChartKey = Optional[str]
AnalysisResult = Dict[str, Any]
ExportFormat = str  # 'csv', 'json', 'txt', etc.


# Function type signatures
ParseFunction = callable[[str], Tuple[Optional[DataFrame], Optional[str]]]
AnalysisFunction = callable[[DataFrame], AnalysisResult]
ChartFunction = callable[[DataFrame, ChartKey], Tuple[Optional[Figure], Optional[str]]]
FilterFunction = callable[[DataFrame, FilterValue, FilterValue, FilterValue, FilterValue], DataFrame]
