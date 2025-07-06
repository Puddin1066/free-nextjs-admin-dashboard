"""
Common utilities for ADVScout

Provides utility functions for data processing, API calls, and file operations.
"""

import json
import csv
import re
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd
import requests
from urllib.parse import urljoin, urlparse, parse_qs
import asyncio
import aiohttp
from tqdm import tqdm

class DataProcessor:
    """Data processing utilities"""
    
    @staticmethod
    def clean_company_name(name: str) -> str:
        """Clean and normalize company name
        
        Args:
            name: Company name to clean
            
        Returns:
            Cleaned company name
        """
        if not name:
            return ""
        
        # Remove common suffixes
        suffixes = [
            r'\s+(Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Corporation|Company|Co\.?)$',
            r'\s+(Limited|Incorporated|L\.L\.C\.?)$'
        ]
        
        cleaned = name.strip()
        for suffix in suffixes:
            cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    @staticmethod
    def extract_domain_from_url(url: str) -> str:
        """Extract domain from URL
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^a-z0-9\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def parse_revenue_string(revenue_str: str) -> float:
        """Parse revenue string to float
        
        Args:
            revenue_str: Revenue string (e.g., "$1.5M", "2.3B", "500K")
            
        Returns:
            Revenue as float
        """
        if not revenue_str:
            return 0.0
        
        # Remove currency symbols and spaces
        clean_str = re.sub(r'[^\d.KMB]', '', revenue_str.upper())
        
        # Extract number and multiplier
        match = re.match(r'([\d.]+)([KMB])?', clean_str)
        if not match:
            return 0.0
        
        number = float(match.group(1))
        multiplier = match.group(2)
        
        if multiplier == 'K':
            return number * 1000
        elif multiplier == 'M':
            return number * 1000000
        elif multiplier == 'B':
            return number * 1000000000
        else:
            return number
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity using simple matching
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        norm1 = DataProcessor.normalize_text(text1)
        norm2 = DataProcessor.normalize_text(text2)
        
        # Split into words
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

class APIClient:
    """Generic API client with rate limiting and error handling"""
    
    def __init__(self, base_url: str, rate_limit: int = 60, timeout: int = 30):
        """Initialize API client
        
        Args:
            base_url: Base URL for API
            rate_limit: Requests per minute
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.last_request_time = 0
        self.request_count = 0
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'ADVScout/1.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Check rate limit
        if self.request_count >= self.rate_limit:
            sleep_time = 60 - (current_time - self.last_request_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
    
    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """Make GET request
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response data
        """
        self._rate_limit_check()
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            start_time = time.time()
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            self.request_count += 1
            
            # Log API call (if logger is available)
            try:
                from .logger import log_api_call
                log_api_call("API", endpoint, response.status_code, response_time)
            except:
                pass
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {str(e)}")
    
    def post(self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict:
        """Make POST request
        
        Args:
            endpoint: API endpoint
            data: Request data
            headers: Additional headers
            
        Returns:
            Response data
        """
        self._rate_limit_check()
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            start_time = time.time()
            response = self.session.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            self.request_count += 1
            
            # Log API call (if logger is available)
            try:
                from .logger import log_api_call
                log_api_call("API", endpoint, response.status_code, response_time)
            except:
                pass
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {str(e)}")

class FileManager:
    """File management utilities"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]):
        """Ensure directory exists
        
        Args:
            path: Directory path
        """
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def save_json(data: Union[Dict, List], filepath: Union[str, Path]):
        """Save data to JSON file
        
        Args:
            data: Data to save
            filepath: File path
        """
        filepath = Path(filepath)
        FileManager.ensure_directory(filepath.parent)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_json(filepath: Union[str, Path]) -> Union[Dict, List]:
        """Load data from JSON file
        
        Args:
            filepath: File path
            
        Returns:
            Loaded data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_csv(data: List[Dict], filepath: Union[str, Path]):
        """Save data to CSV file
        
        Args:
            data: Data to save
            filepath: File path
        """
        if not data:
            return
        
        filepath = Path(filepath)
        FileManager.ensure_directory(filepath.parent)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def load_csv(filepath: Union[str, Path]) -> List[Dict]:
        """Load data from CSV file
        
        Args:
            filepath: File path
            
        Returns:
            Loaded data
        """
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data
    
    @staticmethod
    def save_markdown(content: str, filepath: Union[str, Path]):
        """Save content to Markdown file
        
        Args:
            content: Markdown content
            filepath: File path
        """
        filepath = Path(filepath)
        FileManager.ensure_directory(filepath.parent)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    @staticmethod
    def generate_filename(prefix: str, suffix: str = "", timestamp: bool = True) -> str:
        """Generate filename with optional timestamp
        
        Args:
            prefix: Filename prefix
            suffix: Filename suffix
            timestamp: Whether to include timestamp
            
        Returns:
            Generated filename
        """
        filename = prefix
        
        if timestamp:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename += f"_{timestamp_str}"
        
        if suffix:
            filename += f"_{suffix}"
        
        return filename

class CacheManager:
    """Simple file-based cache manager"""
    
    def __init__(self, cache_dir: Union[str, Path], expiry_seconds: int = 3600):
        """Initialize cache manager
        
        Args:
            cache_dir: Cache directory
            expiry_seconds: Cache expiry time in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.expiry_seconds = expiry_seconds
        FileManager.ensure_directory(self.cache_dir)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key
        
        Args:
            key: Cache key
            
        Returns:
            Cache file path
        """
        # Create hash of key for filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check expiry
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > timedelta(seconds=self.expiry_seconds):
                cache_path.unlink()  # Remove expired cache
                return None
            
            return cache_data['value']
        
        except (json.JSONDecodeError, KeyError, ValueError):
            # Remove corrupted cache
            cache_path.unlink()
            return None
    
    def set(self, key: str, value: Any):
        """Set cached value
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'value': value
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    def clear(self):
        """Clear all cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

class APIError(Exception):
    """Custom exception for API errors"""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_company_data(data: Dict) -> List[str]:
    """Validate company data structure
    
    Args:
        data: Company data dictionary
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Required fields
    required_fields = ['name', 'website']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate website URL
    if 'website' in data and data['website']:
        if not data['website'].startswith(('http://', 'https://')):
            errors.append("Website must be a valid URL")
    
    # Validate revenue if provided
    if 'revenue' in data and data['revenue']:
        try:
            DataProcessor.parse_revenue_string(data['revenue'])
        except:
            errors.append("Invalid revenue format")
    
    return errors

def chunk_list(items: List, chunk_size: int) -> List[List]:
    """Split list into chunks
    
    Args:
        items: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    return chunks

def create_progress_bar(total: int, description: str = "Processing") -> tqdm:
    """Create progress bar
    
    Args:
        total: Total number of items
        description: Progress bar description
        
    Returns:
        Progress bar instance
    """
    return tqdm(total=total, desc=description, unit="item")

# Example usage and testing
if __name__ == "__main__":
    # Test data processor
    processor = DataProcessor()
    
    print("Testing DataProcessor:")
    print(f"Clean name: {processor.clean_company_name('TechCorp Inc.')}")
    print(f"Domain: {processor.extract_domain_from_url('https://www.example.com/path')}")
    print(f"Revenue: {processor.parse_revenue_string('$1.5M')}")
    print(f"Similarity: {processor.calculate_similarity('TechCorp Inc', 'TechCorp LLC')}")
    
    # Test file manager
    print("\nTesting FileManager:")
    test_data = [{'name': 'TechCorp', 'revenue': 1000000}]
    FileManager.save_json(test_data, 'test_data.json')
    loaded_data = FileManager.load_json('test_data.json')
    print(f"Saved and loaded: {loaded_data}")
    
    # Test cache manager
    print("\nTesting CacheManager:")
    cache = CacheManager('test_cache', expiry_seconds=60)
    cache.set('test_key', {'data': 'test_value'})
    cached_value = cache.get('test_key')
    print(f"Cached value: {cached_value}")
    
    # Test validation
    print("\nTesting validation:")
    test_company = {'name': 'TechCorp', 'website': 'https://techcorp.com'}
    errors = validate_company_data(test_company)
    print(f"Validation errors: {errors}")
    
    # Cleanup
    Path('test_data.json').unlink(missing_ok=True)
    cache.clear()