#!/usr/bin/env python3
"""
ADVScout - Complete Venture Scout Pipeline

This script runs the full venture scouting pipeline including:
1. Data enrichment with GPT
2. API data collection
3. Company scoring
4. Report generation

Usage:
    python scripts/run_full_scout.py --input companies.csv --output results/
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from core.logger import get_logger, log_execution_time
from core.utils import FileManager, create_progress_bar
from modules.enrichment import CompanyEnrichment
from modules.api_collector import APICollector
from modules.scoring import CompanyScoring

logger = get_logger(__name__)

class ADVScoutPipeline:
    """Complete ADVScout venture scouting pipeline"""
    
    def __init__(self, output_dir: str = "data/output"):
        """Initialize the pipeline
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize modules
        self.enrichment = CompanyEnrichment()
        self.api_collector = APICollector()
        self.scorer = CompanyScoring()
        
        logger.info(f"Initialized ADVScout pipeline with output directory: {output_dir}")
    
    @log_execution_time
    def run_full_pipeline(self, companies: List[Dict], 
                         enable_enrichment: bool = True,
                         enable_api_collection: bool = True,
                         enable_scoring: bool = True,
                         batch_size: int = 5) -> Dict[str, Any]:
        """Run the complete scouting pipeline
        
        Args:
            companies: List of company data dictionaries
            enable_enrichment: Whether to run GPT enrichment
            enable_api_collection: Whether to collect API data
            enable_scoring: Whether to run scoring
            batch_size: Batch size for processing
            
        Returns:
            Complete pipeline results
        """
        logger.info(f"Starting full pipeline for {len(companies)} companies")
        
        # Initialize results structure
        results = {
            'companies': [],
            'summary': {},
            'pipeline_config': {
                'enrichment_enabled': enable_enrichment,
                'api_collection_enabled': enable_api_collection,
                'scoring_enabled': enable_scoring,
                'batch_size': batch_size
            },
            'processing_times': {}
        }
        
        start_time = time.time()
        
        # Step 1: Enrichment
        enrichment_results = {}
        if enable_enrichment:
            logger.info("Step 1: Running GPT enrichment...")
            enrichment_start = time.time()
            
            try:
                enrichment_list = self.enrichment.batch_enrich(companies, batch_size)
                enrichment_results = {r.company_name: r.__dict__ for r in enrichment_list}
                
                enrichment_time = time.time() - enrichment_start
                results['processing_times']['enrichment'] = enrichment_time
                
                logger.info(f"Enrichment completed in {enrichment_time:.2f}s")
                
                # Save intermediate results
                FileManager.save_json(
                    enrichment_results, 
                    self.output_dir / "enrichment_results.json"
                )
                
            except Exception as e:
                logger.error(f"Enrichment failed: {e}")
                results['errors'] = results.get('errors', [])
                results['errors'].append(f"Enrichment failed: {str(e)}")
        
        # Step 2: API Data Collection
        api_results = {}
        if enable_api_collection:
            logger.info("Step 2: Collecting API data...")
            api_start = time.time()
            
            try:
                api_list = self.api_collector.batch_collect(companies, batch_size)
                api_results = {r['company']['name']: r for r in api_list}
                
                api_time = time.time() - api_start
                results['processing_times']['api_collection'] = api_time
                
                logger.info(f"API collection completed in {api_time:.2f}s")
                
                # Save intermediate results
                FileManager.save_json(
                    api_results,
                    self.output_dir / "api_results.json"
                )
                
            except Exception as e:
                logger.error(f"API collection failed: {e}")
                results['errors'] = results.get('errors', [])
                results['errors'].append(f"API collection failed: {str(e)}")
        
        # Step 3: Combine data and prepare for scoring
        logger.info("Step 3: Combining data...")
        combined_companies = []
        
        for company in companies:
            company_name = company.get('name', 'Unknown')
            
            # Combine all available data
            combined_company = company.copy()
            
            # Add enrichment data
            if company_name in enrichment_results:
                combined_company['enrichment_data'] = enrichment_results[company_name]
            
            # Add API data
            if company_name in api_results:
                combined_company['api_data'] = api_results[company_name].get('api_results', {})
                combined_company['api_aggregated'] = api_results[company_name].get('aggregated', {})
            
            combined_companies.append(combined_company)
        
        # Step 4: Scoring
        scoring_results = []
        if enable_scoring:
            logger.info("Step 4: Running company scoring...")
            scoring_start = time.time()
            
            try:
                scoring_results = self.scorer.batch_score(combined_companies)
                
                scoring_time = time.time() - scoring_start
                results['processing_times']['scoring'] = scoring_time
                
                logger.info(f"Scoring completed in {scoring_time:.2f}s")
                
                # Save scoring results
                scoring_data = [
                    {
                        'company_name': r.company_name,
                        'overall_score': r.overall_score,
                        'revenue_stage': r.revenue_stage.value,
                        'risk_level': r.risk_level.value,
                        'component_scores': r.component_scores,
                        'recommendations': r.recommendations,
                        'confidence': r.confidence,
                        'metadata': r.metadata
                    }
                    for r in scoring_results
                ]
                
                FileManager.save_json(
                    scoring_data,
                    self.output_dir / "scoring_results.json"
                )
                
            except Exception as e:
                logger.error(f"Scoring failed: {e}")
                results['errors'] = results.get('errors', [])
                results['errors'].append(f"Scoring failed: {str(e)}")
        
        # Step 5: Compile final results
        logger.info("Step 5: Compiling final results...")
        
        for i, company in enumerate(combined_companies):
            company_result = {
                'company_data': company,
                'enrichment': enrichment_results.get(company.get('name', ''), {}),
                'api_data': api_results.get(company.get('name', ''), {}),
                'scoring': scoring_results[i].__dict__ if i < len(scoring_results) else {}
            }
            results['companies'].append(company_result)
        
        # Generate summary
        results['summary'] = self._generate_pipeline_summary(
            companies, enrichment_results, api_results, scoring_results
        )
        
        # Total processing time
        total_time = time.time() - start_time
        results['processing_times']['total'] = total_time
        
        logger.info(f"Pipeline completed in {total_time:.2f}s")
        
        # Save complete results
        FileManager.save_json(results, self.output_dir / "complete_results.json")
        
        return results
    
    def _generate_pipeline_summary(self, companies: List[Dict], 
                                 enrichment_results: Dict,
                                 api_results: Dict,
                                 scoring_results: List) -> Dict[str, Any]:
        """Generate pipeline summary statistics"""
        
        summary = {
            'total_companies': len(companies),
            'enrichment_success': len(enrichment_results),
            'api_collection_success': len([r for r in api_results.values() if not r.get('aggregated', {}).get('error')]),
            'scoring_success': len([r for r in scoring_results if r.overall_score > 0]),
        }
        
        # Enrichment summary
        if enrichment_results:
            confidences = [r.get('confidence_score', 0) for r in enrichment_results.values()]
            summary['enrichment_avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0
        
        # API collection summary
        if api_results:
            api_sources = []
            for result in api_results.values():
                sources = result.get('aggregated', {}).get('sources', [])
                api_sources.extend(sources)
            
            from collections import Counter
            source_counts = Counter(api_sources)
            summary['top_api_sources'] = dict(source_counts.most_common(5))
        
        # Scoring summary
        if scoring_results:
            scores = [r.overall_score for r in scoring_results if r.overall_score > 0]
            if scores:
                summary['avg_score'] = sum(scores) / len(scores)
                summary['highest_score'] = max(scores)
                summary['lowest_score'] = min(scores)
            
            # Revenue stage distribution
            from collections import Counter
            stages = [r.revenue_stage.value for r in scoring_results]
            summary['revenue_stage_distribution'] = dict(Counter(stages))
            
            # Top scoring companies
            top_companies = sorted(scoring_results, key=lambda x: x.overall_score, reverse=True)[:5]
            summary['top_companies'] = [
                {
                    'name': r.company_name,
                    'score': r.overall_score,
                    'stage': r.revenue_stage.value,
                    'risk': r.risk_level.value
                }
                for r in top_companies
            ]
        
        return summary
    
    def generate_reports(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Generate markdown and CSV reports
        
        Args:
            results: Pipeline results
            
        Returns:
            Dictionary of generated report file paths
        """
        logger.info("Generating reports...")
        
        report_files = {}
        
        # Generate CSV report
        csv_data = []
        for company_result in results['companies']:
            company = company_result['company_data']
            scoring = company_result['scoring']
            
            csv_row = {
                'Company Name': company.get('name', ''),
                'Website': company.get('website', ''),
                'Industry': company.get('industry', ''),
                'Revenue': company.get('revenue', ''),
                'Employee Count': company.get('employee_count', ''),
                'Overall Score': scoring.get('overall_score', 0),
                'Revenue Stage': scoring.get('revenue_stage', ''),
                'Risk Level': scoring.get('risk_level', ''),
                'Confidence': scoring.get('confidence', 0),
                'Recommendations': '; '.join(scoring.get('recommendations', []))
            }
            csv_data.append(csv_row)
        
        csv_path = self.output_dir / "scout_report.csv"
        FileManager.save_csv(csv_data, csv_path)
        report_files['csv'] = str(csv_path)
        
        # Generate Markdown report
        markdown_content = self._generate_markdown_report(results)
        md_path = self.output_dir / "scout_report.md"
        FileManager.save_markdown(markdown_content, md_path)
        report_files['markdown'] = str(md_path)
        
        logger.info(f"Reports generated: {list(report_files.keys())}")
        return report_files
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate markdown report content"""
        
        summary = results.get('summary', {})
        processing_times = results.get('processing_times', {})
        
        markdown = f"""# ADVScout Venture Scout Report
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Companies Analyzed**: {summary.get('total_companies', 0)}
- **Successful Enrichments**: {summary.get('enrichment_success', 0)}
- **API Data Collections**: {summary.get('api_collection_success', 0)}
- **Successful Scorings**: {summary.get('scoring_success', 0)}
- **Average Score**: {summary.get('avg_score', 0):.2f}/10.0
- **Processing Time**: {processing_times.get('total', 0):.2f} seconds

## Top Investment Opportunities

"""
        
        # Add top companies
        top_companies = summary.get('top_companies', [])
        for i, company in enumerate(top_companies, 1):
            markdown += f"""### {i}. {company['name']}
- **Score**: {company['score']:.2f}/10.0
- **Revenue Stage**: {company['stage']}
- **Risk Level**: {company['risk']}

"""
        
        markdown += """## Revenue Stage Distribution

"""
        
        # Add revenue stage distribution
        stage_dist = summary.get('revenue_stage_distribution', {})
        for stage, count in stage_dist.items():
            markdown += f"- **{stage.replace('-', ' ').title()}**: {count} companies\n"
        
        markdown += """
## Processing Performance

"""
        
        # Add processing times
        for step, time_taken in processing_times.items():
            if step != 'total':
                markdown += f"- **{step.replace('_', ' ').title()}**: {time_taken:.2f}s\n"
        
        markdown += f"""
## Data Sources Used

"""
        
        # Add API sources
        api_sources = summary.get('top_api_sources', {})
        for source, count in api_sources.items():
            markdown += f"- **{source.upper()}**: {count} successful collections\n"
        
        markdown += """
## Detailed Company Analysis

"""
        
        # Add detailed company information
        for company_result in results['companies'][:10]:  # Limit to top 10
            company = company_result['company_data']
            scoring = company_result['scoring']
            
            company_name = company.get('name', 'Unknown')
            markdown += f"""### {company_name}

**Basic Information:**
- Website: {company.get('website', 'N/A')}
- Industry: {company.get('industry', 'N/A')}
- Employee Count: {company.get('employee_count', 'N/A')}

**Scoring Results:**
- Overall Score: {scoring.get('overall_score', 0):.2f}/10.0
- Revenue Stage: {scoring.get('revenue_stage', 'N/A')}
- Risk Level: {scoring.get('risk_level', 'N/A')}
- Confidence: {scoring.get('confidence', 0):.2f}

**Recommendations:**
"""
            for rec in scoring.get('recommendations', []):
                markdown += f"- {rec}\n"
            
            markdown += "\n---\n\n"
        
        markdown += """
## Methodology

This report was generated using the ADVScout platform, which combines:

1. **GPT-4 Enrichment**: AI-powered analysis of company business models, market positioning, and growth potential
2. **Multi-API Data Collection**: Automated data gathering from NIH, OpenCorporates, GitHub, and company websites
3. **Advanced Scoring**: Proprietary algorithms that evaluate companies across 7 key dimensions
4. **Risk Assessment**: Comprehensive risk analysis based on market, competitive, and operational factors

## Disclaimer

This report is generated using automated analysis and should be used as a starting point for further due diligence. All investment decisions should be based on comprehensive manual review and professional judgment.
"""
        
        return markdown

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run complete ADVScout venture scouting pipeline')
    
    # Input/Output arguments
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with company data')
    parser.add_argument('--output', type=str, default='data/output', help='Output directory for results')
    
    # Pipeline configuration
    parser.add_argument('--skip-enrichment', action='store_true', help='Skip GPT enrichment step')
    parser.add_argument('--skip-api', action='store_true', help='Skip API data collection step')
    parser.add_argument('--skip-scoring', action='store_true', help='Skip scoring step')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    
    # Report options
    parser.add_argument('--no-reports', action='store_true', help='Skip report generation')
    
    args = parser.parse_args()
    
    try:
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            logger.error("Configuration errors found:")
            for error in config_errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        
        # Load input data
        logger.info(f"Loading companies from: {args.input}")
        companies = FileManager.load_csv(args.input)
        logger.info(f"Loaded {len(companies)} companies")
        
        # Initialize pipeline
        pipeline = ADVScoutPipeline(args.output)
        
        # Run pipeline
        results = pipeline.run_full_pipeline(
            companies=companies,
            enable_enrichment=not args.skip_enrichment,
            enable_api_collection=not args.skip_api,
            enable_scoring=not args.skip_scoring,
            batch_size=args.batch_size
        )
        
        # Print summary
        summary = results['summary']
        processing_times = results['processing_times']
        
        print("\n" + "="*60)
        print("ADVScout Pipeline Complete!")
        print("="*60)
        print(f"Total Companies: {summary.get('total_companies', 0)}")
        print(f"Successful Enrichments: {summary.get('enrichment_success', 0)}")
        print(f"API Collections: {summary.get('api_collection_success', 0)}")
        print(f"Successful Scorings: {summary.get('scoring_success', 0)}")
        print(f"Average Score: {summary.get('avg_score', 0):.2f}/10.0")
        print(f"Total Processing Time: {processing_times.get('total', 0):.2f}s")
        
        # Print top companies
        top_companies = summary.get('top_companies', [])
        if top_companies:
            print("\nTop Investment Opportunities:")
            for i, company in enumerate(top_companies[:3], 1):
                print(f"  {i}. {company['name']}: {company['score']:.2f} ({company['stage']})")
        
        # Generate reports
        if not args.no_reports:
            report_files = pipeline.generate_reports(results)
            print(f"\nReports generated:")
            for report_type, file_path in report_files.items():
                print(f"  {report_type.upper()}: {file_path}")
        
        print(f"\nAll results saved to: {args.output}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()