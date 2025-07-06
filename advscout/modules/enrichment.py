"""
Company Enrichment Module

Uses GPT to analyze and enrich company data with insights about business model,
market positioning, technology stack, and growth potential.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai
from ..core.config import config
from ..core.logger import get_logger, log_execution_time, log_error_with_context
from ..core.utils import DataProcessor, CacheManager, APIError

logger = get_logger(__name__)

@dataclass
class EnrichmentResult:
    """Data class for enrichment results"""
    company_name: str
    business_model: str
    market_position: str
    technology_stack: List[str]
    growth_indicators: Dict[str, Any]
    risk_factors: List[str]
    market_opportunity: str
    competitive_landscape: str
    key_insights: List[str]
    confidence_score: float
    processing_time: float

class CompanyEnrichment:
    """GPT-powered company enrichment engine"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """Initialize enrichment engine
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
        """
        self.api_key = api_key or config.get("openai_api_key")
        self.model = model or config.get("gpt_model", "gpt-4")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.3)
        
        # Initialize OpenAI client
        if self.api_key:
            openai.api_key = self.api_key
        else:
            raise ValueError("OpenAI API key is required")
        
        # Initialize cache
        cache_dir = config.get("cache_dir", "data/cache")
        cache_expiry = config.get("cache_expiry", 3600)
        self.cache = CacheManager(
            cache_dir=cache_dir if cache_dir is not None else "data/cache",
            expiry_seconds=cache_expiry if cache_expiry is not None else 3600
        )
        
        # Data processor
        self.data_processor = DataProcessor()
        
        logger.info(f"Initialized CompanyEnrichment with model: {self.model}")
    
    @log_execution_time
    def enrich_company(self, company_data: Dict) -> EnrichmentResult:
        """Enrich company data with GPT insights
        
        Args:
            company_data: Company data dictionary
            
        Returns:
            EnrichmentResult with enriched data
        """
        company_name = company_data.get('name', 'Unknown Company')
        logger.info(f"Starting enrichment for: {company_name}")
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"enrichment_{company_name}_{self.model}"
            cached_result = self.cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached enrichment for: {company_name}")
                return EnrichmentResult(**cached_result)
            
            # Prepare company context
            context = self._prepare_company_context(company_data)
            
            # Generate enrichment prompt
            prompt = self._create_enrichment_prompt(context)
            
            # Get GPT analysis
            gpt_analysis = self._get_gpt_analysis(prompt)
            
            # Parse and structure results
            enrichment_result = self._parse_gpt_response(gpt_analysis, company_name)
            
            # Add processing time
            enrichment_result.processing_time = time.time() - start_time
            
            # Cache the result
            self.cache.set(cache_key, enrichment_result.__dict__)
            
            logger.info(f"Completed enrichment for: {company_name}")
            return enrichment_result
            
        except Exception as e:
            log_error_with_context(e, {
                'company': company_name,
                'module': 'enrichment',
                'model': self.model
            })
            raise
    
    def _prepare_company_context(self, company_data: Dict) -> Dict:
        """Prepare company context for GPT analysis
        
        Args:
            company_data: Raw company data
            
        Returns:
            Structured context
        """
        context = {
            'name': company_data.get('name', ''),
            'website': company_data.get('website', ''),
            'description': company_data.get('description', ''),
            'industry': company_data.get('industry', ''),
            'founded_year': company_data.get('founded_year', ''),
            'employee_count': company_data.get('employee_count', ''),
            'revenue': company_data.get('revenue', ''),
            'funding': company_data.get('funding', ''),
            'location': company_data.get('location', ''),
            'products': company_data.get('products', []),
            'technologies': company_data.get('technologies', []),
            'keywords': company_data.get('keywords', [])
        }
        
        # Clean and process data
        if context['name']:
            context['clean_name'] = self.data_processor.clean_company_name(context['name'])
        
        if context['website']:
            context['domain'] = self.data_processor.extract_domain_from_url(context['website'])
        
        return context
    
    def _create_enrichment_prompt(self, context: Dict) -> str:
        """Create enrichment prompt for GPT
        
        Args:
            context: Company context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""
Analyze the following company and provide detailed insights for venture capital evaluation:

Company Information:
- Name: {context.get('name', 'N/A')}
- Website: {context.get('website', 'N/A')}
- Industry: {context.get('industry', 'N/A')}
- Description: {context.get('description', 'N/A')}
- Founded: {context.get('founded_year', 'N/A')}
- Employee Count: {context.get('employee_count', 'N/A')}
- Revenue: {context.get('revenue', 'N/A')}
- Funding: {context.get('funding', 'N/A')}
- Location: {context.get('location', 'N/A')}
- Products: {context.get('products', 'N/A')}
- Technologies: {context.get('technologies', 'N/A')}

Please provide a comprehensive analysis in the following JSON format:
{{
    "business_model": "Brief description of the business model",
    "market_position": "Analysis of market position and competitive advantages",
    "technology_stack": ["List", "of", "key", "technologies"],
    "growth_indicators": {{
        "market_size": "Estimated market size",
        "growth_rate": "Estimated growth rate",
        "scalability": "Scalability assessment"
    }},
    "risk_factors": ["List", "of", "key", "risks"],
    "market_opportunity": "Assessment of market opportunity",
    "competitive_landscape": "Overview of competitive landscape",
    "key_insights": ["List", "of", "key", "insights"],
    "confidence_score": 0.85
}}

Focus on:
1. Revenue potential and scalability
2. Market opportunity and timing
3. Competitive advantages
4. Technology differentiation
5. Risk assessment
6. Growth trajectory indicators

Provide specific, actionable insights based on the available information.
"""
        return prompt
    
    def _get_gpt_analysis(self, prompt: str) -> Dict:
        """Get analysis from GPT
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            GPT response
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert venture capital analyst specializing in company evaluation and market analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            raise APIError("Invalid JSON response from GPT")
        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            raise APIError(f"GPT API error: {str(e)}")
    
    def _parse_gpt_response(self, gpt_response: Dict, company_name: str) -> EnrichmentResult:
        """Parse GPT response into structured result
        
        Args:
            gpt_response: GPT analysis response
            company_name: Company name
            
        Returns:
            EnrichmentResult object
        """
        try:
            return EnrichmentResult(
                company_name=company_name,
                business_model=gpt_response.get('business_model', ''),
                market_position=gpt_response.get('market_position', ''),
                technology_stack=gpt_response.get('technology_stack', []),
                growth_indicators=gpt_response.get('growth_indicators', {}),
                risk_factors=gpt_response.get('risk_factors', []),
                market_opportunity=gpt_response.get('market_opportunity', ''),
                competitive_landscape=gpt_response.get('competitive_landscape', ''),
                key_insights=gpt_response.get('key_insights', []),
                confidence_score=gpt_response.get('confidence_score', 0.5),
                processing_time=0.0  # Will be set by caller
            )
        except Exception as e:
            logger.error(f"Failed to parse GPT response: {e}")
            # Return default result with low confidence
            return EnrichmentResult(
                company_name=company_name,
                business_model="Unable to analyze",
                market_position="Unable to analyze",
                technology_stack=[],
                growth_indicators={},
                risk_factors=["Analysis failed"],
                market_opportunity="Unable to analyze",
                competitive_landscape="Unable to analyze",
                key_insights=["Analysis failed due to processing error"],
                confidence_score=0.0,
                processing_time=0.0
            )
    
    def batch_enrich(self, companies: List[Dict], batch_size: int = 5) -> List[EnrichmentResult]:
        """Enrich multiple companies in batches
        
        Args:
            companies: List of company data dictionaries
            batch_size: Number of companies to process simultaneously
            
        Returns:
            List of enrichment results
        """
        results = []
        
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            batch_results = []
            
            for company in batch:
                try:
                    result = self.enrich_company(company)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to enrich company {company.get('name', 'Unknown')}: {e}")
                    # Add failed result
                    batch_results.append(EnrichmentResult(
                        company_name=company.get('name', 'Unknown'),
                        business_model="Processing failed",
                        market_position="Processing failed",
                        technology_stack=[],
                        growth_indicators={},
                        risk_factors=["Processing failed"],
                        market_opportunity="Processing failed",
                        competitive_landscape="Processing failed",
                        key_insights=["Processing failed"],
                        confidence_score=0.0,
                        processing_time=0.0
                    ))
            
            results.extend(batch_results)
            
            # Brief pause between batches to respect rate limits
            if i + batch_size < len(companies):
                time.sleep(1)
        
        return results
    
    def get_enrichment_summary(self, results: List[EnrichmentResult]) -> Dict:
        """Generate summary statistics for enrichment results
        
        Args:
            results: List of enrichment results
            
        Returns:
            Summary statistics
        """
        if not results:
            return {}
        
        total_companies = len(results)
        successful_analyses = len([r for r in results if r.confidence_score > 0.1])
        avg_confidence = sum(r.confidence_score for r in results) / total_companies
        avg_processing_time = sum(r.processing_time for r in results) / total_companies
        
        # Technology analysis
        all_technologies = []
        for result in results:
            all_technologies.extend(result.technology_stack)
        
        tech_frequency = {}
        for tech in all_technologies:
            tech_frequency[tech] = tech_frequency.get(tech, 0) + 1
        
        top_technologies = sorted(tech_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_companies': total_companies,
            'successful_analyses': successful_analyses,
            'success_rate': successful_analyses / total_companies if total_companies > 0 else 0,
            'average_confidence': avg_confidence,
            'average_processing_time': avg_processing_time,
            'top_technologies': top_technologies,
            'high_confidence_companies': [
                r.company_name for r in results if r.confidence_score > 0.8
            ]
        }

# Command-line interface
if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description='Enrich company data with GPT insights')
    parser.add_argument('--company', type=str, help='Company name to enrich')
    parser.add_argument('--input', type=str, help='Input CSV file with company data')
    parser.add_argument('--output', type=str, help='Output file for results')
    parser.add_argument('--model', type=str, default='gpt-4', help='GPT model to use')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Initialize enrichment engine
    enrichment = CompanyEnrichment(model=args.model)
    
    if args.company:
        # Single company enrichment
        company_data = {'name': args.company}
        result = enrichment.enrich_company(company_data)
        
        print(f"\nEnrichment Results for {result.company_name}:")
        print(f"Business Model: {result.business_model}")
        print(f"Market Position: {result.market_position}")
        print(f"Technology Stack: {', '.join(result.technology_stack)}")
        print(f"Key Insights: {', '.join(result.key_insights)}")
        print(f"Confidence Score: {result.confidence_score:.2f}")
        print(f"Processing Time: {result.processing_time:.2f}s")
        
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(result.__dict__, f, indent=2)
            print(f"Results saved to: {args.output}")
    
    elif args.input:
        # Batch enrichment
        from ..core.utils import FileManager
        
        # Load companies from CSV
        companies = FileManager.load_csv(args.input)
        
        # Enrich companies
        results = enrichment.batch_enrich(companies, args.batch_size)
        
        # Generate summary
        summary = enrichment.get_enrichment_summary(results)
        
        print(f"\nBatch Enrichment Complete:")
        print(f"Total Companies: {summary['total_companies']}")
        print(f"Successful Analyses: {summary['successful_analyses']}")
        print(f"Success Rate: {summary['success_rate']:.2%}")
        print(f"Average Confidence: {summary['average_confidence']:.2f}")
        print(f"Average Processing Time: {summary['average_processing_time']:.2f}s")
        
        if args.output:
            # Save results
            results_data = [result.__dict__ for result in results]
            FileManager.save_json(results_data, args.output)
            print(f"Results saved to: {args.output}")
    
    else:
        print("Please provide either --company or --input parameter")
        sys.exit(1)