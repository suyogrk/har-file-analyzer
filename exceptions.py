# exceptions.py - Custom exception classes for HAR Analyzer

class HARError(Exception):
    """Base exception class for all HAR Analyzer errors."""
    pass


class HARParseError(HARError):
    """Exception raised when HAR file parsing fails."""
    
    def __init__(self, message: str, line_number: int = None, details: str = None):
        super().__init__(message)
        self.line_number = line_number
        self.details = details
        
    def __str__(self):
        if self.line_number:
            return f"Parse error at line {self.line_number}: {super().__str__()}"
        return super().__str__()


class HARValidationError(HARError):
    """Exception raised when HAR file validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(message)
        self.field = field
        self.value = value
        
    def __str__(self):
        if self.field:
            return f"Validation error for field '{self.field}': {super().__str__()}"
        return super().__str__()


class HARAnalysisError(HARError):
    """Exception raised when HAR data analysis fails."""
    
    def __init__(self, message: str, operation: str = None, details: str = None):
        super().__init__(message)
        self.operation = operation
        self.details = details
        
    def __str__(self):
        if self.operation:
            return f"Analysis error in '{self.operation}': {super().__str__()}"
        return super().__str__()


class HARFileError(HARError):
    """Exception raised when HAR file operations fail."""
    
    def __init__(self, message: str, file_path: str = None, file_size: int = None):
        super().__init__(message)
        self.file_path = file_path
        self.file_size = file_size
        
    def __str__(self):
        if self.file_path:
            return f"File error with '{self.file_path}': {super().__str__()}"
        return super().__str__()


class HARVisualizationError(HARError):
    """Exception raised when HAR data visualization fails."""
    
    def __init__(self, message: str, chart_type: str = None, details: str = None):
        super().__init__(message)
        self.chart_type = chart_type
        self.details = details
        
    def __str__(self):
        if self.chart_type:
            return f"Visualization error for '{self.chart_type}': {super().__str__()}"
        return super().__str__()
