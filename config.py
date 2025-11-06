# config.py - Configuration constants

# Performance thresholds
SLOW_RESPONSE_THRESHOLD_MS = 1000
HIGH_WAIT_TIME_THRESHOLD_MS = 500
CONNECTION_DELAY_THRESHOLD_MS = 1000
DNS_DELAY_THRESHOLD_MS = 100

# Chart settings
RESPONSE_TIME_HISTOGRAM_BINS = 50
TOP_ENDPOINTS_LIMIT = 10

# Timing phases
TIMING_PHASES = ['blocked', 'dns', 'connect', 'send', 'wait', 'receive', 'ssl']

# HTTP status code ranges
STATUS_SUCCESS_RANGE = (200, 299)
STATUS_REDIRECT_RANGE = (300, 399)
STATUS_CLIENT_ERROR_RANGE = (400, 499)
STATUS_SERVER_ERROR_RANGE = (500, 599)

# UI Colors
COLOR_SUCCESS = 'green'
COLOR_REDIRECT = 'orange'
COLOR_ERROR = 'red'
COLOR_SCALE = 'Reds'

# Page configuration
PAGE_CONFIG = {
    'page_title': 'HAR File Analyzer',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}
