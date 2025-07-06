"""
API Collector Module

Collects data from free APIs like NIH, OpenCorporates, and other public data sources
to enrich company information.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from ..core.config import config
from ..core.logger import get_logger, log_execution_time, log_api_call
from ..core.utils import APIClient, DataProcessor, CacheManager, APIError

logger = get_logger(__name__)

@dataclass
class APIResult:
    """Data class for API collection results"""
    company_name: str
    source: str
    data: Dict[str, Any]
    confidence: float
    timestamp: float

class APICollector:
    """Free API data collector"""
    
    def __init__(self):
        """Initialize API collector"""
        self.data_processor = DataProcessor()
        
        # Initialize cache
        cache_dir = config.get("cache_dir", "data/cache")
        cache_expiry = config.get("cache_expiry", 3600)
        self.cache = CacheManager(
            cache_dir=cache_dir if cache_dir is not None else "data/cache",
            expiry_seconds=cache_expiry if cache_expiry is not None else 3600
        )
        
        # Initialize API clients
        nih_rate_limit = config.get("nih_rate_limit", 100)
        opencorp_rate_limit = config.get("opencorporates_rate_limit", 50)
        
        self.nih_client = APIClient(
            base_url="https://api.nih.gov",
            rate_limit=nih_rate_limit if nih_rate_limit is not None else 100
        )
        
        self.opencorporates_client = APIClient(
            base_url="https://api.opencorporates.com",
            rate_limit=opencorp_rate_limit if opencorp_rate_limit is not None else 50
        )
        
        logger.info("Initialized APICollector")
    
    @log_execution_time
    def collect_company_data(self, company_data: Dict) -> Dict[str, APIResult]:
        """Collect data from multiple APIs for a company
        
        Args:
            company_data: Company information
            
        Returns:
            Dictionary of API results by source
        """
        company_name = company_data.get('name', 'Unknown')
        logger.info(f"Collecting API data for: {company_name}")
        
        results = {}
        
        # Check cache first
        cache_key = f"api_data_{company_name}"
        cached_results = self.cache.get(cache_key)
        
        if cached_results:
            logger.info(f"Using cached API data for: {company_name}")
            return {k: APIResult(**v) for k, v in cached_results.items()}
        
        # Collect from NIH
        try:
            nih_result = self.collect_nih_data(company_data)
            if nih_result:
                results['nih'] = nih_result
        except Exception as e:
            logger.error(f"NIH API collection failed for {company_name}: {e}")
        
        # Collect from OpenCorporates
        try:
            opencorp_result = self.collect_opencorporates_data(company_data)
            if opencorp_result:
                results['opencorporates'] = opencorp_result
        except Exception as e:
            logger.error(f"OpenCorporates API collection failed for {company_name}: {e}")
        
        # Collect from other free APIs
        try:
            other_results = self.collect_other_apis(company_data)
            results.update(other_results)
        except Exception as e:
            logger.error(f"Other APIs collection failed for {company_name}: {e}")
        
        # Cache results
        cache_data = {k: v.__dict__ for k, v in results.items()}
        self.cache.set(cache_key, cache_data)
        
        logger.info(f"Collected data from {len(results)} sources for: {company_name}")
        return results
    
    def collect_nih_data(self, company_data: Dict) -> Optional[APIResult]:
        """Collect data from NIH APIs
        
        Args:
            company_data: Company information
            
        Returns:
            APIResult or None
        """
        company_name = company_data.get('name', '')
        
        if not company_name:
            return None
        
        try:
            # Search NIH RePORTER for grants
            params = {
                'criteria': {
                    'org_names': [company_name],
                    'fiscal_years': [2020, 2021, 2022, 2023, 2024]
                },
                'include_fields': [
                    'ApplId', 'SubprojectId', 'FiscalYear', 'Organization',
                    'ProjectTitle', 'ProjectStartDate', 'ProjectEndDate',
                    'AwardAmount', 'ContactPiName'
                ],
                'offset': 0,
                'limit': 50
            }
            
            # NIH RePORTER API
            response = requests.post(
                "https://api.reporter.nih.gov/v2/projects/search",
                json=params,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Process NIH data
                nih_data = {
                    'total_projects': data.get('meta', {}).get('total', 0),
                    'projects': data.get('results', [])[:10],  # Limit to top 10
                    'total_funding': 0,
                    'active_projects': 0,
                    'research_areas': set()
                }
                
                # Calculate metrics
                for project in data.get('results', []):
                    if project.get('AwardAmount'):
                        nih_data['total_funding'] += project['AwardAmount']
                    
                    # Check if project is active
                    if project.get('ProjectEndDate'):
                        # Simple check - could be improved with date parsing
                        if '2024' in str(project['ProjectEndDate']):
                            nih_data['active_projects'] += 1
                    
                    # Extract research areas from title
                    title = project.get('ProjectTitle', '').lower()
                    research_keywords = [
                        'cancer', 'diabetes', 'cardiovascular', 'neuroscience',
                        'infectious disease', 'mental health', 'genetics',
                        'biotechnology', 'drug development', 'clinical trial'
                    ]
                    
                    for keyword in research_keywords:
                        if keyword in title:
                            nih_data['research_areas'].add(keyword)
                
                # Convert set to list for JSON serialization
                nih_data['research_areas'] = list(nih_data['research_areas'])
                
                confidence = min(1.0, nih_data['total_projects'] / 10)  # More projects = higher confidence
                
                return APIResult(
                    company_name=company_name,
                    source='nih',
                    data=nih_data,
                    confidence=confidence,
                    timestamp=time.time()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"NIH API error for {company_name}: {e}")
            return None
    
    def collect_opencorporates_data(self, company_data: Dict) -> Optional[APIResult]:
        """Collect data from OpenCorporates API
        
        Args:
            company_data: Company information
            
        Returns:
            APIResult or None
        """
        company_name = company_data.get('name', '')
        
        if not company_name:
            return None
        
        try:
            # Clean company name for search
            clean_name = self.data_processor.clean_company_name(company_name)
            
            # Search OpenCorporates
            params = {
                'q': clean_name,
                'format': 'json',
                'per_page': 5
            }
            
            # Add API key if available
            api_key = config.get("opencorporates_api_key")
            if api_key:
                params['api_token'] = api_key
            
            response = requests.get(
                "https://api.opencorporates.com/v0.4/companies/search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                companies = data.get('results', {}).get('companies', [])
                
                if companies:
                    # Take the first/best match
                    best_match = companies[0].get('company', {})
                    
                    opencorp_data = {
                        'name': best_match.get('name', ''),
                        'jurisdiction': best_match.get('jurisdiction_code', ''),
                        'incorporation_date': best_match.get('incorporation_date', ''),
                        'company_type': best_match.get('company_type', ''),
                        'status': best_match.get('current_status', ''),
                        'address': best_match.get('registered_address_in_full', ''),
                        'opencorporates_url': best_match.get('opencorporates_url', ''),
                        'total_matches': len(companies)
                    }
                    
                    # Calculate confidence based on name similarity
                    similarity = self.data_processor.calculate_similarity(
                        company_name, opencorp_data['name']
                    )
                    
                    return APIResult(
                        company_name=company_name,
                        source='opencorporates',
                        data=opencorp_data,
                        confidence=similarity,
                        timestamp=time.time()
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"OpenCorporates API error for {company_name}: {e}")
            return None
    
    def collect_other_apis(self, company_data: Dict) -> Dict[str, APIResult]:
        """Collect data from other free APIs
        
        Args:
            company_data: Company information
            
        Returns:
            Dictionary of API results
        """
        company_name = company_data.get('name', '')
        website = company_data.get('website', '')
        results = {}
        
        # Collect from company website (if available)
        if website:
            try:
                website_result = self.collect_website_data(website, company_name)
                if website_result:
                    results['website'] = website_result
            except Exception as e:
                logger.error(f"Website data collection failed for {company_name}: {e}")
        
        # Collect from GitHub (if tech company)
        try:
            github_result = self.collect_github_data(company_name)
            if github_result:
                results['github'] = github_result
        except Exception as e:
            logger.error(f"GitHub data collection failed for {company_name}: {e}")
        
        return results
    
    def collect_website_data(self, website: str, company_name: str) -> Optional[APIResult]:
        """Collect basic data from company website
        
        Args:
            website: Company website URL
            company_name: Company name
            
        Returns:
            APIResult or None
        """
        try:
            # Basic website info
            response = requests.get(website, timeout=10, headers={
                'User-Agent': 'ADVScout/1.0.0 (Research Bot)'
            })
            
            if response.status_code == 200:
                # Extract basic info
                content = response.text.lower()
                
                # Look for technology indicators
                tech_indicators = {
                    'react': 'react' in content,
                    'python': 'python' in content,
                    'javascript': 'javascript' in content,
                    'api': 'api' in content,
                    'saas': 'saas' in content or 'software as a service' in content,
                    'ai': 'artificial intelligence' in content or 'machine learning' in content,
                    'blockchain': 'blockchain' in content or 'crypto' in content,
                    'cloud': 'cloud' in content or 'aws' in content or 'azure' in content
                }
                
                # Count technology mentions
                tech_count = sum(1 for v in tech_indicators.values() if v)
                
                website_data = {
                    'url': website,
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'technology_indicators': tech_indicators,
                    'technology_score': tech_count,
                    'has_careers_page': 'careers' in content or 'jobs' in content,
                    'has_contact_info': 'contact' in content or 'email' in content,
                    'has_pricing': 'pricing' in content or 'plans' in content
                }
                
                confidence = min(1.0, tech_count / 5)  # Normalize to 0-1
                
                return APIResult(
                    company_name=company_name,
                    source='website',
                    data=website_data,
                    confidence=confidence,
                    timestamp=time.time()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Website data collection error: {e}")
            return None
    
    def collect_github_data(self, company_name: str) -> Optional[APIResult]:
        """Collect data from GitHub API
        
        Args:
            company_name: Company name
            
        Returns:
            APIResult or None
        """
        try:
            # Search for organization
            clean_name = self.data_processor.clean_company_name(company_name)
            
            response = requests.get(
                f"https://api.github.com/search/users",
                params={
                    'q': f"{clean_name} type:org",
                    'per_page': 5
                },
                headers={'User-Agent': 'ADVScout/1.0.0'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('items'):
                    # Take the first match
                    org = data['items'][0]
                    
                    # Get organization details
                    org_response = requests.get(
                        org['url'],
                        headers={'User-Agent': 'ADVScout/1.0.0'},
                        timeout=10
                    )
                    
                    if org_response.status_code == 200:
                        org_data = org_response.json()
                        
                        github_data = {
                            'login': org_data.get('login', ''),
                            'name': org_data.get('name', ''),
                            'description': org_data.get('description', ''),
                            'public_repos': org_data.get('public_repos', 0),
                            'followers': org_data.get('followers', 0),
                            'following': org_data.get('following', 0),
                            'created_at': org_data.get('created_at', ''),
                            'updated_at': org_data.get('updated_at', ''),
                            'html_url': org_data.get('html_url', ''),
                            'blog': org_data.get('blog', ''),
                            'location': org_data.get('location', ''),
                            'company': org_data.get('company', '')
                        }
                        
                        # Calculate confidence based on name similarity and activity
                        name_similarity = self.data_processor.calculate_similarity(
                            company_name, github_data['name'] or github_data['login']
                        )
                        
                        # Activity score (more repos and followers = higher confidence)
                        activity_score = min(1.0, (github_data['public_repos'] + github_data['followers']) / 100)
                        
                        confidence = (name_similarity + activity_score) / 2
                        
                        return APIResult(
                            company_name=company_name,
                            source='github',
                            data=github_data,
                            confidence=confidence,
                            timestamp=time.time()
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"GitHub data collection error: {e}")
            return None
    
    def aggregate_results(self, results: Dict[str, APIResult]) -> Dict[str, Any]:
        """Aggregate results from multiple API sources
        
        Args:
            results: Dictionary of API results
            
        Returns:
            Aggregated data summary
        """
        if not results:
            return {}
        
        aggregated = {
            'sources': list(results.keys()),
            'total_sources': len(results),
            'average_confidence': sum(r.confidence for r in results.values()) / len(results),
            'data_summary': {},
            'recommendations': []
        }
        
        # Process each source
        for source, result in results.items():
            aggregated['data_summary'][source] = {
                'confidence': result.confidence,
                'data_points': len(result.data),
                'key_fields': list(result.data.keys())[:5]  # Top 5 fields
            }
        
        # Generate recommendations
        if 'nih' in results and results['nih'].data.get('total_projects', 0) > 0:
            aggregated['recommendations'].append("Company has NIH research funding - indicates R&D activity")
        
        if 'opencorporates' in results and results['opencorporates'].confidence > 0.8:
            aggregated['recommendations'].append("High confidence company registration match found")
        
        if 'github' in results and results['github'].data.get('public_repos', 0) > 10:
            aggregated['recommendations'].append("Active open-source development - tech-focused company")
        
        if 'website' in results and results['website'].data.get('technology_score', 0) > 3:
            aggregated['recommendations'].append("Strong technology presence on website")
        
        return aggregated
    
    def batch_collect(self, companies: List[Dict], batch_size: int = 3) -> List[Dict]:
        """Collect data for multiple companies in batches
        
        Args:
            companies: List of company data
            batch_size: Number of companies to process simultaneously
            
        Returns:
            List of results with aggregated data
        """
        all_results = []
        
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            batch_results = []
            
            for company in batch:
                try:
                    # Collect API data
                    api_results = self.collect_company_data(company)
                    
                    # Aggregate results
                    aggregated = self.aggregate_results(api_results)
                    
                    # Combine with original company data
                    result = {
                        'company': company,
                        'api_results': {k: v.__dict__ for k, v in api_results.items()},
                        'aggregated': aggregated
                    }
                    
                    batch_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to collect data for {company.get('name', 'Unknown')}: {e}")
                    # Add failed result
                    batch_results.append({
                        'company': company,
                        'api_results': {},
                        'aggregated': {'error': str(e)}
                    })
            
            all_results.extend(batch_results)
            
            # Rate limiting pause between batches
            if i + batch_size < len(companies):
                time.sleep(2)
        
        return all_results

# Command-line interface
if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description='Collect company data from free APIs')
    parser.add_argument('--company', type=str, help='Company name to collect data for')
    parser.add_argument('--website', type=str, help='Company website URL')
    parser.add_argument('--input', type=str, help='Input CSV file with company data')
    parser.add_argument('--output', type=str, help='Output file for results')
    parser.add_argument('--batch-size', type=int, default=3, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Initialize API collector
    collector = APICollector()
    
    if args.company:
        # Single company collection
        company_data = {
            'name': args.company,
            'website': args.website or ''
        }
        
        results = collector.collect_company_data(company_data)
        aggregated = collector.aggregate_results(results)
        
        print(f"\nAPI Collection Results for {args.company}:")
        print(f"Sources: {', '.join(aggregated.get('sources', []))}")
        print(f"Total Sources: {aggregated.get('total_sources', 0)}")
        print(f"Average Confidence: {aggregated.get('average_confidence', 0):.2f}")
        print(f"Recommendations: {', '.join(aggregated.get('recommendations', []))}")
        
        if args.output:
            from ..core.utils import FileManager
            result_data = {
                'company': company_data,
                'api_results': {k: v.__dict__ for k, v in results.items()},
                'aggregated': aggregated
            }
            FileManager.save_json(result_data, args.output)
            print(f"Results saved to: {args.output}")
    
    elif args.input:
        # Batch collection
        from ..core.utils import FileManager
        
        # Load companies from CSV
        companies = FileManager.load_csv(args.input)
        
        # Collect data
        results = collector.batch_collect(companies, args.batch_size)
        
        print(f"\nBatch Collection Complete:")
        print(f"Total Companies: {len(results)}")
        print(f"Successful Collections: {len([r for r in results if not r['aggregated'].get('error')])}")
        
        if args.output:
            FileManager.save_json(results, args.output)
            print(f"Results saved to: {args.output}")
    
    else:
        print("Please provide either --company or --input parameter")
        sys.exit(1)