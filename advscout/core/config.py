"""
Configuration Management for ADVScout

Handles API keys, scoring thresholds, and other configuration parameters.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

class ADVScoutConfig:
    """Configuration class for ADVScout platform"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_file: Path to YAML config file (optional)
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        
        # Default configuration
        self.config = {
            # API Configuration
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "nih_api_key": os.getenv("NIH_API_KEY", ""),
            "opencorporates_api_key": os.getenv("OPENCORPORATES_API_KEY", ""),
            
            # Scoring Configuration
            "revenue_stage_threshold": 1000000,  # $1M ARR
            "growth_rate_threshold": 0.5,  # 50% YoY growth
            "market_size_threshold": 1000000000,  # $1B market
            "employee_count_threshold": 10,  # Minimum employees
            
            # Enrichment Configuration
            "gpt_model": "gpt-4",
            "max_tokens": 2000,
            "temperature": 0.3,
            
            # API Rate Limits
            "openai_rate_limit": 60,  # requests per minute
            "nih_rate_limit": 100,
            "opencorporates_rate_limit": 50,
            
            # Output Configuration
            "output_formats": ["markdown", "csv"],
            "report_template": "templates/scout_report.md",
            "csv_delimiter": ",",
            
            # Logging Configuration
            "log_level": "INFO",
            "log_file": "advscout.log",
            
            # Data Configuration
            "data_dir": "data",
            "output_dir": "data/output",
            "cache_dir": "data/cache",
            "cache_expiry": 3600,  # 1 hour
        }
        
        # Load from YAML file if provided
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                self.config.update(file_config)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value"""
        self.config[key] = value
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Check required API keys
        if not self.config.get("openai_api_key"):
            errors.append("OpenAI API key is required")
        
        # Check numeric thresholds
        numeric_fields = [
            "revenue_stage_threshold",
            "growth_rate_threshold",
            "market_size_threshold",
            "employee_count_threshold"
        ]
        
        for field in numeric_fields:
            if not isinstance(self.config.get(field), (int, float)):
                errors.append(f"{field} must be a number")
        
        # Check directories exist
        data_dir = Path(self.config.get("data_dir", "data"))
        if not data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create data directory: {e}")
        
        return errors
    
    def save_config(self, filepath: str):
        """Save current configuration to YAML file"""
        with open(filepath, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key"""
        return self.config.get("openai_api_key", "")
    
    @property
    def scoring_thresholds(self) -> Dict:
        """Get scoring thresholds"""
        return {
            "revenue_stage": self.config.get("revenue_stage_threshold"),
            "growth_rate": self.config.get("growth_rate_threshold"),
            "market_size": self.config.get("market_size_threshold"),
            "employee_count": self.config.get("employee_count_threshold")
        }
    
    @property
    def output_config(self) -> Dict:
        """Get output configuration"""
        return {
            "formats": self.config.get("output_formats"),
            "template": self.config.get("report_template"),
            "delimiter": self.config.get("csv_delimiter"),
            "output_dir": self.config.get("output_dir")
        }

# Global configuration instance
config = ADVScoutConfig()

# Example configuration template
CONFIG_TEMPLATE = """
# ADVScout Configuration File

# API Configuration
openai_api_key: "your-openai-key-here"
nih_api_key: "your-nih-key-here"  # Optional
opencorporates_api_key: "your-opencorporates-key-here"  # Optional

# Scoring Configuration
revenue_stage_threshold: 1000000  # $1M ARR
growth_rate_threshold: 0.5  # 50% YoY growth
market_size_threshold: 1000000000  # $1B market
employee_count_threshold: 10  # Minimum employees

# Enrichment Configuration
gpt_model: "gpt-4"
max_tokens: 2000
temperature: 0.3

# Output Configuration
output_formats: ["markdown", "csv"]
report_template: "templates/scout_report.md"
csv_delimiter: ","

# Logging Configuration
log_level: "INFO"
log_file: "advscout.log"
"""