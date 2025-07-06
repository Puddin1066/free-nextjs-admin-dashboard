"""
Logging utilities for ADVScout

Provides centralized logging configuration and utilities.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA
    }
    
    def format(self, record):
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

class ADVScoutLogger:
    """Logger class for ADVScout platform"""
    
    def __init__(self, name: str = "advscout", log_file: Optional[str] = None, log_level: str = "INFO"):
        """Initialize logger
        
        Args:
            name: Logger name
            log_file: Path to log file (optional)
            log_level: Logging level
        """
        self.name = name
        self.log_file = log_file
        self.log_level = getattr(logging, log_level.upper())
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        console_formatter = ColoredFormatter(
            '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(self.log_level)
            
            file_formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        return self.logger
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, **kwargs)

# Global logger instance
logger = ADVScoutLogger()

def get_logger(name: str = "advscout", log_file: Optional[str] = None, log_level: str = "INFO") -> logging.Logger:
    """Get a logger instance
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        log_level: Logging level
        
    Returns:
        Logger instance
    """
    scout_logger = ADVScoutLogger(name, log_file, log_level)
    return scout_logger.get_logger()

def log_execution_time(func):
    """Decorator to log function execution time"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.info(f"Completed {func.__name__} in {execution_time:.2f}s")
            return result
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.error(f"Failed {func.__name__} after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper

def log_api_call(api_name: str, endpoint: str, response_status: int, response_time: float):
    """Log API call details
    
    Args:
        api_name: Name of the API
        endpoint: API endpoint
        response_status: HTTP response status
        response_time: Response time in seconds
    """
    if response_status == 200:
        logger.info(f"API Call - {api_name} | {endpoint} | {response_status} | {response_time:.2f}s")
    else:
        logger.warning(f"API Call - {api_name} | {endpoint} | {response_status} | {response_time:.2f}s")

def log_company_processing(company_name: str, stage: str, status: str = "started"):
    """Log company processing stages
    
    Args:
        company_name: Name of the company
        stage: Processing stage
        status: Status (started, completed, failed)
    """
    logger.info(f"Company Processing - {company_name} | {stage} | {status}")

def log_scoring_result(company_name: str, score: float, stage: str, risk_level: str):
    """Log scoring results
    
    Args:
        company_name: Name of the company
        score: Calculated score
        stage: Revenue stage
        risk_level: Risk assessment
    """
    logger.info(f"Scoring Result - {company_name} | Score: {score:.2f} | Stage: {stage} | Risk: {risk_level}")

def log_error_with_context(error: Exception, context: dict):
    """Log error with additional context
    
    Args:
        error: The exception that occurred
        context: Additional context information
    """
    context_str = " | ".join([f"{k}: {v}" for k, v in context.items()])
    logger.error(f"Error occurred: {str(error)} | Context: {context_str}")
    logger.exception("Full traceback:")

# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    test_logger = get_logger("test", "test.log", "DEBUG")
    
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    # Test decorators and utility functions
    @log_execution_time
    def test_function():
        import time
        time.sleep(1)
        return "success"
    
    result = test_function()
    
    # Test API logging
    log_api_call("OpenAI", "/v1/chat/completions", 200, 1.23)
    log_api_call("NIH", "/search", 404, 0.45)
    
    # Test company logging
    log_company_processing("TechCorp Inc", "enrichment", "started")
    log_company_processing("TechCorp Inc", "enrichment", "completed")
    
    # Test scoring logging
    log_scoring_result("TechCorp Inc", 8.5, "revenue-stage", "medium")
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error_with_context(e, {"company": "TechCorp", "module": "enrichment"})