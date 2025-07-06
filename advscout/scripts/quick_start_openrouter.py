#!/usr/bin/env python3
"""
ADVScout Quick Start with OpenRouter Integration

This script demonstrates the enhanced ADVScout platform with:
- OpenRouter AI integration for cost-effective analysis
- Tiered pricing structure (Free, Professional, Enterprise)
- Client-specific configurations
- Usage tracking and cost optimization

Usage:
    python scripts/quick_start_openrouter.py --tier free --client demo
    python scripts/quick_start_openrouter.py --tier professional --client advantary
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_environment():
    """Setup environment variables for demo"""
    # Set demo API keys (replace with real keys)
    demo_keys = {
        "OPENROUTER_API_KEY": "sk-or-demo-key-here",
        "OPENAI_API_KEY": "sk-demo-key-here",
        "GITHUB_TOKEN": "ghp_demo_token_here",
        "NEWSAPI_KEY": "demo_news_api_key"
    }
    
    for key, value in demo_keys.items():
        if not os.getenv(key):
            os.environ[key] = value
            print(f"📝 Set demo {key}")

def display_tier_info(tier: str, client: str):
    """Display tier information and pricing"""
    from config.config_updated import get_config
    
    config = get_config(tier, client)
    tier_config = config.get_tier_config()
    cost_analysis = config.get_cost_analysis()
    
    print(f"\n🎯 {tier_config.get('name', tier.title())} Configuration")
    print("=" * 60)
    print(f"Monthly Cost: ${tier_config.get('monthly_cost', 0)}")
    print(f"Client Fee: ${cost_analysis.get('client_fee', 0)}")
    print(f"Contractor Profit: ${cost_analysis.get('contractor_profit', 0)}")
    print(f"Profit Margin: {cost_analysis.get('profit_margin', '0%')}")
    print(f"Max Companies/Month: {tier_config.get('max_companies_per_month', 0)}")
    
    print(f"\n📋 Features ({len(config.get_features())} total):")
    for feature in config.get_features()[:5]:  # Show first 5
        print(f"  ✅ {feature}")
    if len(config.get_features()) > 5:
        print(f"  ... and {len(config.get_features()) - 5} more")
    
    print(f"\n🔌 Enabled APIs ({len([a for a in config.get_enabled_apis().values() if a.get('enabled')])}) total):")
    for api_name, api_config in config.get_enabled_apis().items():
        if api_config.get('enabled'):
            cost = api_config.get('cost', 0)
            cost_str = f"${cost}/month" if cost > 0 else "Free"
            print(f"  🔗 {api_name.upper()}: {cost_str}")

def display_ai_config(tier: str, client: str):
    """Display AI configuration"""
    from config.config_updated import get_ai_config
    
    ai_config = get_ai_config(tier, client)
    
    print(f"\n🤖 AI Configuration")
    print("=" * 40)
    print(f"OpenRouter Enabled: {ai_config.get('openrouter_enabled', False)}")
    print(f"Cost Optimization: {ai_config.get('ai_cost_optimization', True)}")
    print(f"Max Cost/Analysis: ${ai_config.get('max_cost_per_analysis', 0.50)}")
    
    if ai_config.get('openrouter_models'):
        print(f"\nAvailable Models:")
        for model in ai_config['openrouter_models']:
            print(f"  🎯 {model}")
        print(f"\nDefault Model: {ai_config.get('openrouter_default_model', 'N/A')}")

def demo_company_analysis(tier: str, client: str):
    """Demonstrate company analysis with the enhanced platform"""
    print(f"\n🔍 Demo Company Analysis")
    print("=" * 50)
    
    # Demo company data
    demo_companies = [
        {
            "name": "TechCorp Inc",
            "website": "https://techcorp.com",
            "industry": "Software",
            "description": "AI-powered business intelligence platform"
        },
        {
            "name": "BioTech Solutions",
            "website": "https://biotech-solutions.com", 
            "industry": "Biotechnology",
            "description": "Novel drug discovery using machine learning"
        }
    ]
    
    print(f"Analyzing {len(demo_companies)} companies with {tier} tier...")
    
    # Simulate analysis results
    for i, company in enumerate(demo_companies, 1):
        print(f"\n📊 Company {i}: {company['name']}")
        print(f"   Industry: {company['industry']}")
        print(f"   AI Model Used: openai/gpt-4o-mini")
        print(f"   Analysis Cost: $0.25")
        print(f"   Overall Score: {7.5 + i * 0.3:.1f}/10.0")
        print(f"   Investment Potential: {'High' if i == 1 else 'Medium'}")
        print(f"   Service Opportunity: {'Go-to-market advisory' if i == 1 else 'Strategic consulting'}")

def show_cost_comparison():
    """Show cost comparison between tiers"""
    from config.config_updated import get_config
    
    print(f"\n💰 Tier Cost Comparison")
    print("=" * 60)
    
    tiers = ["free", "professional", "enterprise"]
    
    print(f"{'Tier':<15} {'Monthly Cost':<12} {'Client Fee':<12} {'Profit':<10} {'Margin':<8}")
    print("-" * 60)
    
    for tier in tiers:
        config = get_config(tier, "demo")
        cost_analysis = config.get_cost_analysis()
        
        monthly_cost = config.get_monthly_cost()
        client_fee = cost_analysis.get('client_fee', 0)
        profit = cost_analysis.get('contractor_profit', 0)
        margin = cost_analysis.get('profit_margin', '0%')
        
        print(f"{tier.title():<15} ${monthly_cost:<11} ${client_fee:<11} ${profit:<9} {margin:<8}")

def validate_configuration(tier: str, client: str):
    """Validate configuration for the specified tier"""
    from config.config_updated import validate_tier_config
    
    print(f"\n✅ Configuration Validation")
    print("=" * 40)
    
    validation = validate_tier_config(tier, client)
    
    if validation['valid']:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors:")
        for error in validation['errors']:
            print(f"   • {error}")
    
    if validation['warnings']:
        print("⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   • {warning}")

def show_usage_example(tier: str, client: str):
    """Show usage example for the tier"""
    print(f"\n📝 Usage Example")
    print("=" * 40)
    
    print(f"# Set up environment")
    print(f"export OPENROUTER_API_KEY='your-openrouter-key'")
    print(f"export GITHUB_TOKEN='your-github-token'")
    print(f"export NEWSAPI_KEY='your-news-api-key'")
    print(f"")
    print(f"# Run analysis with {tier} tier")
    print(f"python scripts/run_full_scout.py \\")
    print(f"  --tier {tier} \\")
    print(f"  --client {client} \\")
    print(f"  --input companies.csv \\")
    print(f"  --output results/")
    print(f"")
    print(f"# Check usage and costs")
    print(f"python scripts/check_usage.py --tier {tier} --client {client}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ADVScout Quick Start with OpenRouter')
    
    parser.add_argument('--tier', type=str, default='free', 
                       choices=['free', 'professional', 'enterprise'],
                       help='Pricing tier to demonstrate')
    parser.add_argument('--client', type=str, default='demo',
                       help='Client name for configuration')
    parser.add_argument('--setup-env', action='store_true',
                       help='Setup demo environment variables')
    parser.add_argument('--validate', action='store_true',
                       help='Validate configuration only')
    parser.add_argument('--compare-tiers', action='store_true',
                       help='Show tier comparison')
    
    args = parser.parse_args()
    
    # Setup environment if requested
    if args.setup_env:
        setup_environment()
    
    # Show header
    print("\n🚀 ADVScout Enhanced Platform Demo")
    print("=" * 60)
    print("Multi-provider AI • Tiered Pricing • Cost Optimization")
    
    try:
        # Show tier information
        display_tier_info(args.tier, args.client)
        
        # Show AI configuration
        display_ai_config(args.tier, args.client)
        
        # Validate configuration
        if args.validate:
            validate_configuration(args.tier, args.client)
            return
        
        # Show tier comparison
        if args.compare_tiers:
            show_cost_comparison()
            return
        
        # Demo analysis
        demo_company_analysis(args.tier, args.client)
        
        # Show usage example
        show_usage_example(args.tier, args.client)
        
        # Show tier comparison
        show_cost_comparison()
        
        print(f"\n🎉 Demo Complete!")
        print(f"Ready to analyze companies with {args.tier} tier configuration.")
        print(f"Estimated cost per company: $0.25-0.75 depending on tier")
        print(f"Contractor profit margin: 46-89% depending on tier")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Make sure configuration files are set up correctly.")
        sys.exit(1)

if __name__ == "__main__":
    main()