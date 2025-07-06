"""
Example Configuration File for ADVScout

Copy this file to config.py and update with your API keys and preferences.
"""

# API Configuration
OPENAI_API_KEY = "your-openai-api-key-here"
NIH_API_KEY = ""  # Optional - NIH API is free but may require registration
OPENCORPORATES_API_KEY = ""  # Optional - for higher rate limits

# Scoring Configuration
REVENUE_STAGE_THRESHOLD = 1000000  # $1M ARR threshold for revenue-stage classification
GROWTH_RATE_THRESHOLD = 0.5  # 50% YoY growth threshold
MARKET_SIZE_THRESHOLD = 1000000000  # $1B market size threshold
EMPLOYEE_COUNT_THRESHOLD = 10  # Minimum employee count for established companies

# Enrichment Configuration
GPT_MODEL = "gpt-4"  # or "gpt-3.5-turbo" for faster/cheaper processing
MAX_TOKENS = 2000
TEMPERATURE = 0.3  # Lower = more focused, Higher = more creative

# API Rate Limits (requests per minute)
OPENAI_RATE_LIMIT = 60
NIH_RATE_LIMIT = 100
OPENCORPORATES_RATE_LIMIT = 50

# Output Configuration
OUTPUT_FORMATS = ["markdown", "csv"]
REPORT_TEMPLATE = "templates/scout_report.md"
CSV_DELIMITER = ","

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "advscout.log"

# Data Configuration
DATA_DIR = "data"
OUTPUT_DIR = "data/output"
CACHE_DIR = "data/cache"
CACHE_EXPIRY = 3600  # Cache expiry in seconds (1 hour)

# Advanced Configuration
BATCH_SIZE = 5  # Default batch size for processing
TIMEOUT = 30  # API timeout in seconds
MAX_RETRIES = 3  # Maximum API retry attempts