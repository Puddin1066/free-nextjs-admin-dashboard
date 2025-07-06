"""
Company Scoring Module

Advanced scoring algorithms to identify revenue-stage companies and assess
their investment potential based on multiple data sources.
"""

import json
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from ..core.config import config
from ..core.logger import get_logger, log_execution_time
from ..core.utils import DataProcessor

logger = get_logger(__name__)

class RevenueStage(Enum):
    """Revenue stage classification"""
    PRE_REVENUE = "pre-revenue"
    EARLY_REVENUE = "early-revenue"
    REVENUE_STAGE = "revenue-stage"
    GROWTH_STAGE = "growth-stage"
    MATURE = "mature"

class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very-high"

@dataclass
class ScoringResult:
    """Data class for scoring results"""
    company_name: str
    overall_score: float
    revenue_stage: RevenueStage
    risk_level: RiskLevel
    component_scores: Dict[str, float]
    recommendations: List[str]
    confidence: float
    metadata: Dict[str, Any]

class CompanyScoring:
    """Company scoring engine"""
    
    def __init__(self):
        """Initialize scoring engine"""
        self.data_processor = DataProcessor()
        
        # Get scoring thresholds from config
        self.thresholds = config.scoring_thresholds
        
        # Scoring weights
        self.weights = {
            'revenue_indicators': 0.25,
            'market_opportunity': 0.20,
            'technology_strength': 0.15,
            'team_quality': 0.15,
            'competitive_position': 0.10,
            'risk_factors': 0.10,
            'growth_potential': 0.05
        }
        
        logger.info("Initialized CompanyScoring")
    
    @log_execution_time
    def score_company(self, company_data: Dict, enrichment_data: Optional[Dict] = None, 
                     api_data: Optional[Dict] = None) -> ScoringResult:
        """Score a company based on available data
        
        Args:
            company_data: Basic company information
            enrichment_data: GPT enrichment results
            api_data: API collection results
            
        Returns:
            ScoringResult with detailed scoring breakdown
        """
        company_name = company_data.get('name', 'Unknown')
        logger.info(f"Scoring company: {company_name}")
        
        # Calculate component scores
        component_scores = self._calculate_component_scores(
            company_data, enrichment_data, api_data
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(component_scores)
        
        # Determine revenue stage
        revenue_stage = self._determine_revenue_stage(component_scores, company_data)
        
        # Assess risk level
        risk_level = self._assess_risk_level(component_scores, enrichment_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            component_scores, revenue_stage, risk_level
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(company_data, enrichment_data, api_data)
        
        # Compile metadata
        metadata = {
            'data_sources': self._identify_data_sources(company_data, enrichment_data, api_data),
            'scoring_weights': self.weights,
            'thresholds_used': self.thresholds,
            'total_data_points': self._count_data_points(company_data, enrichment_data, api_data)
        }
        
        result = ScoringResult(
            company_name=company_name,
            overall_score=overall_score,
            revenue_stage=revenue_stage,
            risk_level=risk_level,
            component_scores=component_scores,
            recommendations=recommendations,
            confidence=confidence,
            metadata=metadata
        )
        
        logger.info(f"Scored {company_name}: {overall_score:.2f} ({revenue_stage.value})")
        return result
    
    def _calculate_component_scores(self, company_data: Dict, enrichment_data: Optional[Dict], 
                                  api_data: Optional[Dict]) -> Dict[str, float]:
        """Calculate individual component scores
        
        Args:
            company_data: Basic company data
            enrichment_data: Enrichment results
            api_data: API collection results
            
        Returns:
            Dictionary of component scores
        """
        scores = {}
        
        # Revenue indicators score
        scores['revenue_indicators'] = self._score_revenue_indicators(
            company_data, enrichment_data, api_data
        )
        
        # Market opportunity score
        scores['market_opportunity'] = self._score_market_opportunity(
            enrichment_data, api_data
        )
        
        # Technology strength score
        scores['technology_strength'] = self._score_technology_strength(
            company_data, enrichment_data, api_data
        )
        
        # Team quality score
        scores['team_quality'] = self._score_team_quality(
            company_data, enrichment_data, api_data
        )
        
        # Competitive position score
        scores['competitive_position'] = self._score_competitive_position(
            enrichment_data, api_data
        )
        
        # Risk factors score (inverse - lower risk = higher score)
        scores['risk_factors'] = self._score_risk_factors(
            enrichment_data, api_data
        )
        
        # Growth potential score
        scores['growth_potential'] = self._score_growth_potential(
            enrichment_data, api_data
        )
        
        return scores
    
    def _score_revenue_indicators(self, company_data: Dict, enrichment_data: Optional[Dict], 
                                api_data: Optional[Dict]) -> float:
        """Score revenue indicators"""
        score = 0.0
        
        # Direct revenue data
        if company_data.get('revenue'):
            revenue = self.data_processor.parse_revenue_string(company_data['revenue'])
            if revenue > 0:
                # Score based on revenue amount
                if revenue >= self.thresholds['revenue_stage']:
                    score += 0.4  # High revenue
                elif revenue >= self.thresholds['revenue_stage'] * 0.1:
                    score += 0.3  # Medium revenue
                else:
                    score += 0.2  # Low revenue
        
        # Employee count as revenue proxy
        if company_data.get('employee_count'):
            try:
                employees = int(company_data['employee_count'])
                if employees >= self.thresholds['employee_count']:
                    score += 0.2
                elif employees >= self.thresholds['employee_count'] * 0.5:
                    score += 0.1
            except (ValueError, TypeError):
                pass
        
        # Funding information
        if company_data.get('funding'):
            funding = self.data_processor.parse_revenue_string(company_data['funding'])
            if funding > 1000000:  # >$1M funding
                score += 0.2
            elif funding > 100000:  # >$100K funding
                score += 0.1
        
        # NIH funding (from API data)
        if api_data and 'nih' in api_data:
            nih_funding = api_data['nih'].get('data', {}).get('total_funding', 0)
            if nih_funding > 0:
                score += 0.2
        
        return min(1.0, score)
    
    def _score_market_opportunity(self, enrichment_data: Optional[Dict], 
                                api_data: Optional[Dict]) -> float:
        """Score market opportunity"""
        score = 0.0
        
        if enrichment_data:
            # Market size indicators
            growth_indicators = enrichment_data.get('growth_indicators', {})
            
            # Market size
            market_size = growth_indicators.get('market_size', '')
            if 'billion' in market_size.lower():
                score += 0.4
            elif 'million' in market_size.lower():
                score += 0.3
            
            # Growth rate
            growth_rate = growth_indicators.get('growth_rate', '')
            if any(word in growth_rate.lower() for word in ['high', 'rapid', 'fast']):
                score += 0.3
            elif any(word in growth_rate.lower() for word in ['moderate', 'steady']):
                score += 0.2
            
            # Market opportunity text analysis
            market_opp = enrichment_data.get('market_opportunity', '').lower()
            positive_indicators = ['growing', 'expanding', 'increasing', 'demand', 'opportunity']
            score += min(0.3, sum(0.06 for word in positive_indicators if word in market_opp))
        
        return min(1.0, score)
    
    def _score_technology_strength(self, company_data: Dict, enrichment_data: Optional[Dict], 
                                 api_data: Optional[Dict]) -> float:
        """Score technology strength"""
        score = 0.0
        
        # Technology stack from enrichment
        if enrichment_data:
            tech_stack = enrichment_data.get('technology_stack', [])
            if tech_stack:
                # Modern tech stack indicators
                modern_techs = ['ai', 'ml', 'blockchain', 'cloud', 'api', 'saas', 'react', 'python']
                tech_score = sum(1 for tech in tech_stack if any(mt in tech.lower() for mt in modern_techs))
                score += min(0.4, tech_score * 0.1)
        
        # GitHub activity (from API data)
        if api_data and 'github' in api_data:
            github_data = api_data['github'].get('data', {})
            repos = github_data.get('public_repos', 0)
            if repos > 20:
                score += 0.3
            elif repos > 5:
                score += 0.2
            elif repos > 0:
                score += 0.1
        
        # Website technology indicators
        if api_data and 'website' in api_data:
            website_data = api_data['website'].get('data', {})
            tech_score = website_data.get('technology_score', 0)
            score += min(0.3, tech_score * 0.05)
        
        return min(1.0, score)
    
    def _score_team_quality(self, company_data: Dict, enrichment_data: Optional[Dict], 
                          api_data: Optional[Dict]) -> float:
        """Score team quality"""
        score = 0.0
        
        # Founded year (experience proxy)
        if company_data.get('founded_year'):
            try:
                founded = int(company_data['founded_year'])
                years_active = 2024 - founded
                if years_active >= 5:
                    score += 0.3
                elif years_active >= 2:
                    score += 0.2
                elif years_active >= 1:
                    score += 0.1
            except (ValueError, TypeError):
                pass
        
        # Employee count (team size)
        if company_data.get('employee_count'):
            try:
                employees = int(company_data['employee_count'])
                if employees >= 50:
                    score += 0.3
                elif employees >= 10:
                    score += 0.2
                elif employees >= 5:
                    score += 0.1
            except (ValueError, TypeError):
                pass
        
        # NIH research (indicates scientific team)
        if api_data and 'nih' in api_data:
            nih_data = api_data['nih'].get('data', {})
            if nih_data.get('total_projects', 0) > 0:
                score += 0.2
        
        # GitHub activity (indicates technical team)
        if api_data and 'github' in api_data:
            github_data = api_data['github'].get('data', {})
            if github_data.get('public_repos', 0) > 0:
                score += 0.2
        
        return min(1.0, score)
    
    def _score_competitive_position(self, enrichment_data: Optional[Dict], 
                                  api_data: Optional[Dict]) -> float:
        """Score competitive position"""
        score = 0.0
        
        if enrichment_data:
            # Competitive landscape analysis
            competitive_landscape = enrichment_data.get('competitive_landscape', '').lower()
            
            # Positive competitive indicators
            positive_indicators = ['leader', 'first', 'unique', 'differentiated', 'advantage']
            score += min(0.4, sum(0.08 for word in positive_indicators if word in competitive_landscape))
            
            # Market position
            market_position = enrichment_data.get('market_position', '').lower()
            if 'strong' in market_position:
                score += 0.3
            elif 'good' in market_position:
                score += 0.2
            elif 'weak' in market_position:
                score += 0.1
        
        # Technology differentiation
        if api_data and 'website' in api_data:
            website_data = api_data['website'].get('data', {})
            if website_data.get('technology_score', 0) > 4:
                score += 0.3
        
        return min(1.0, score)
    
    def _score_risk_factors(self, enrichment_data: Optional[Dict], 
                          api_data: Optional[Dict]) -> float:
        """Score risk factors (inverse scoring - lower risk = higher score)"""
        risk_score = 0.0  # Start with no risk
        
        if enrichment_data:
            risk_factors = enrichment_data.get('risk_factors', [])
            
            # High-risk indicators
            high_risk_keywords = ['regulatory', 'competition', 'market', 'funding', 'technology']
            for factor in risk_factors:
                for keyword in high_risk_keywords:
                    if keyword in factor.lower():
                        risk_score += 0.1
        
        # Convert risk to score (inverse)
        return max(0.0, 1.0 - min(1.0, risk_score))
    
    def _score_growth_potential(self, enrichment_data: Optional[Dict], 
                              api_data: Optional[Dict]) -> float:
        """Score growth potential"""
        score = 0.0
        
        if enrichment_data:
            # Growth indicators
            growth_indicators = enrichment_data.get('growth_indicators', {})
            
            # Scalability
            scalability = growth_indicators.get('scalability', '').lower()
            if 'high' in scalability:
                score += 0.4
            elif 'medium' in scalability:
                score += 0.3
            elif 'low' in scalability:
                score += 0.1
            
            # Key insights for growth
            key_insights = enrichment_data.get('key_insights', [])
            growth_keywords = ['growth', 'scale', 'expand', 'opportunity', 'potential']
            for insight in key_insights:
                for keyword in growth_keywords:
                    if keyword in insight.lower():
                        score += 0.1
                        break
        
        return min(1.0, score)
    
    def _calculate_overall_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate weighted overall score"""
        overall_score = 0.0
        
        for component, score in component_scores.items():
            weight = self.weights.get(component, 0.0)
            overall_score += score * weight
        
        return round(overall_score * 10, 2)  # Scale to 0-10
    
    def _determine_revenue_stage(self, component_scores: Dict[str, float], 
                               company_data: Dict) -> RevenueStage:
        """Determine revenue stage based on scores and data"""
        revenue_score = component_scores.get('revenue_indicators', 0)
        
        # Check direct revenue data
        if company_data.get('revenue'):
            revenue = self.data_processor.parse_revenue_string(company_data['revenue'])
            if revenue >= self.thresholds['revenue_stage'] * 10:
                return RevenueStage.MATURE
            elif revenue >= self.thresholds['revenue_stage']:
                return RevenueStage.GROWTH_STAGE
            elif revenue >= self.thresholds['revenue_stage'] * 0.1:
                return RevenueStage.REVENUE_STAGE
            elif revenue > 0:
                return RevenueStage.EARLY_REVENUE
        
        # Use score-based determination
        if revenue_score >= 0.8:
            return RevenueStage.GROWTH_STAGE
        elif revenue_score >= 0.6:
            return RevenueStage.REVENUE_STAGE
        elif revenue_score >= 0.4:
            return RevenueStage.EARLY_REVENUE
        else:
            return RevenueStage.PRE_REVENUE
    
    def _assess_risk_level(self, component_scores: Dict[str, float], 
                         enrichment_data: Optional[Dict]) -> RiskLevel:
        """Assess overall risk level"""
        risk_score = component_scores.get('risk_factors', 1.0)
        competitive_score = component_scores.get('competitive_position', 0.5)
        
        # Calculate combined risk
        combined_risk = (2 - risk_score - competitive_score) / 2
        
        if combined_risk <= 0.25:
            return RiskLevel.LOW
        elif combined_risk <= 0.5:
            return RiskLevel.MEDIUM
        elif combined_risk <= 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _generate_recommendations(self, component_scores: Dict[str, float], 
                                revenue_stage: RevenueStage, risk_level: RiskLevel) -> List[str]:
        """Generate investment recommendations"""
        recommendations = []
        
        # Revenue stage recommendations
        if revenue_stage == RevenueStage.REVENUE_STAGE:
            recommendations.append("Strong revenue-stage candidate for investment")
        elif revenue_stage == RevenueStage.GROWTH_STAGE:
            recommendations.append("Excellent growth-stage opportunity")
        elif revenue_stage == RevenueStage.EARLY_REVENUE:
            recommendations.append("Early revenue - monitor for growth acceleration")
        
        # Risk level recommendations
        if risk_level == RiskLevel.LOW:
            recommendations.append("Low risk profile - suitable for conservative investors")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("High risk - requires careful due diligence")
        elif risk_level == RiskLevel.VERY_HIGH:
            recommendations.append("Very high risk - proceed with extreme caution")
        
        # Component-specific recommendations
        if component_scores.get('technology_strength', 0) > 0.8:
            recommendations.append("Strong technology differentiation")
        
        if component_scores.get('market_opportunity', 0) > 0.8:
            recommendations.append("Large market opportunity identified")
        
        if component_scores.get('team_quality', 0) < 0.3:
            recommendations.append("Team quality concerns - investigate further")
        
        return recommendations
    
    def _calculate_confidence(self, company_data: Dict, enrichment_data: Optional[Dict], 
                            api_data: Optional[Dict]) -> float:
        """Calculate confidence in scoring"""
        confidence = 0.0
        
        # Base data availability
        if company_data.get('name'):
            confidence += 0.2
        if company_data.get('revenue'):
            confidence += 0.2
        if company_data.get('employee_count'):
            confidence += 0.1
        if company_data.get('website'):
            confidence += 0.1
        
        # Enrichment data
        if enrichment_data:
            confidence += 0.3
        
        # API data
        if api_data:
            confidence += 0.1 * len(api_data)
        
        return min(1.0, confidence)
    
    def _identify_data_sources(self, company_data: Dict, enrichment_data: Optional[Dict], 
                             api_data: Optional[Dict]) -> List[str]:
        """Identify available data sources"""
        sources = ['company_data']
        
        if enrichment_data:
            sources.append('gpt_enrichment')
        
        if api_data:
            sources.extend(api_data.keys())
        
        return sources
    
    def _count_data_points(self, company_data: Dict, enrichment_data: Optional[Dict], 
                         api_data: Optional[Dict]) -> int:
        """Count total data points available"""
        count = len([v for v in company_data.values() if v])
        
        if enrichment_data:
            count += len([v for v in enrichment_data.values() if v])
        
        if api_data:
            for source_data in api_data.values():
                if isinstance(source_data, dict) and 'data' in source_data:
                    count += len(source_data['data'])
        
        return count
    
    def batch_score(self, companies_data: List[Dict]) -> List[ScoringResult]:
        """Score multiple companies"""
        results = []
        
        for company_data in companies_data:
            try:
                # Extract enrichment and API data if available
                enrichment_data = company_data.get('enrichment_data')
                api_data = company_data.get('api_data')
                
                # Score the company
                result = self.score_company(company_data, enrichment_data, api_data)
                results.append(result)
                
            except Exception as e:
                company_name = company_data.get('name', 'Unknown')
                logger.error(f"Failed to score company {company_name}: {e}")
                
                # Add failed result
                results.append(ScoringResult(
                    company_name=company_name,
                    overall_score=0.0,
                    revenue_stage=RevenueStage.PRE_REVENUE,
                    risk_level=RiskLevel.VERY_HIGH,
                    component_scores={},
                    recommendations=["Scoring failed due to processing error"],
                    confidence=0.0,
                    metadata={'error': str(e)}
                ))
        
        return results
    
    def get_scoring_summary(self, results: List[ScoringResult]) -> Dict[str, Any]:
        """Generate scoring summary statistics"""
        if not results:
            return {}
        
        # Filter out failed results
        successful_results = [r for r in results if r.overall_score > 0]
        
        if not successful_results:
            return {'error': 'No successful scoring results'}
        
        # Calculate statistics
        scores = [r.overall_score for r in successful_results]
        avg_score = sum(scores) / len(scores)
        
        # Revenue stage distribution
        stage_counts = {}
        for stage in RevenueStage:
            stage_counts[stage.value] = len([r for r in successful_results if r.revenue_stage == stage])
        
        # Risk level distribution
        risk_counts = {}
        for risk in RiskLevel:
            risk_counts[risk.value] = len([r for r in successful_results if r.risk_level == risk])
        
        # Top companies
        top_companies = sorted(successful_results, key=lambda x: x.overall_score, reverse=True)[:10]
        
        return {
            'total_companies': len(results),
            'successful_scoring': len(successful_results),
            'average_score': avg_score,
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'revenue_stage_distribution': stage_counts,
            'risk_level_distribution': risk_counts,
            'top_companies': [
                {
                    'name': r.company_name,
                    'score': r.overall_score,
                    'stage': r.revenue_stage.value,
                    'risk': r.risk_level.value
                }
                for r in top_companies
            ]
        }

# Command-line interface
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Score companies for investment potential')
    parser.add_argument('--input', type=str, required=True, help='Input file with company data')
    parser.add_argument('--output', type=str, help='Output file for scoring results')
    parser.add_argument('--summary', action='store_true', help='Show summary statistics')
    
    args = parser.parse_args()
    
    # Initialize scoring engine
    scorer = CompanyScoring()
    
    # Load data
    from ..core.utils import FileManager
    
    try:
        if args.input.endswith('.csv'):
            companies_data = FileManager.load_csv(args.input)
        else:
            companies_data = FileManager.load_json(args.input)
        
        if not isinstance(companies_data, list):
            companies_data = [companies_data]
        
        # Score companies
        results = scorer.batch_score(companies_data)
        
        # Generate summary
        summary = scorer.get_scoring_summary(results)
        
        print(f"\nCompany Scoring Complete:")
        print(f"Total Companies: {summary.get('total_companies', 0)}")
        print(f"Successful Scoring: {summary.get('successful_scoring', 0)}")
        print(f"Average Score: {summary.get('average_score', 0):.2f}")
        print(f"Score Range: {summary.get('lowest_score', 0):.2f} - {summary.get('highest_score', 0):.2f}")
        
        if args.summary:
            print(f"\nRevenue Stage Distribution:")
            for stage, count in summary.get('revenue_stage_distribution', {}).items():
                print(f"  {stage}: {count}")
            
            print(f"\nRisk Level Distribution:")
            for risk, count in summary.get('risk_level_distribution', {}).items():
                print(f"  {risk}: {count}")
            
            print(f"\nTop Companies:")
            for company in summary.get('top_companies', [])[:5]:
                print(f"  {company['name']}: {company['score']:.2f} ({company['stage']})")
        
        if args.output:
            # Save results
            results_data = [
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
                for r in results
            ]
            
            FileManager.save_json(results_data, args.output)
            print(f"Results saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)