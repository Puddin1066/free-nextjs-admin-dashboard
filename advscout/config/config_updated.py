"""
Updated ADVScout Configuration with OpenRouter Integration and Pricing Tiers

This configuration file supports:
- Multiple AI providers (OpenAI, OpenRouter)
- Tiered pricing structure (Free, Professional, Enterprise)
- Dynamic cost optimization
- Client-specific configurations
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from ..core.config import config as base_config

class TieredConfig:
    """Configuration manager with pricing tier support"""
    
    def __init__(self, client_name: str = "default", tier: str = "free"):
        """Initialize configuration with tier support
        
        Args:
            client_name: Name of the client
            tier: Pricing tier (free, professional, enterprise)
        """
        self.client_name = client_name
        self.tier = tier
        self.config_dir = Path(__file__).parent
        
        # Load configurations
        self.pricing_config = self._load_pricing_config()
        self.client_config = self._load_client_config()
        self.base_config = base_config
        
        # Validate tier
        if tier not in self.pricing_config.get("pricing_tiers", {}):
            raise ValueError(f"Invalid tier: {tier}")
    
    def _load_pricing_config(self) -> Dict[str, Any]:
        """Load pricing configuration"""
        pricing_file = self.config_dir / "pricing_tiers.yaml"
        
        if pricing_file.exists():
            with open(pricing_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_client_config(self) -> Dict[str, Any]:
        """Load client-specific configuration"""
        client_file = self.config_dir / "clients" / f"{self.client_name}.yaml"
        
        if client_file.exists():
            with open(client_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def get_tier_config(self) -> Dict[str, Any]:
        """Get configuration for current tier"""
        return self.pricing_config.get("pricing_tiers", {}).get(self.tier, {})
    
    def get_enabled_apis(self) -> Dict[str, Any]:
        """Get enabled APIs for current tier"""
        tier_config = self.get_tier_config()
        return tier_config.get("apis", {})
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration for current tier"""
        tier_config = self.get_tier_config()
        openrouter_config = tier_config.get("apis", {}).get("openrouter", {})
        
        return {
            "openrouter_enabled": openrouter_config.get("enabled", False),
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
            "openrouter_models": openrouter_config.get("models", []),
            "openrouter_default_model": openrouter_config.get("default_model", "openai/gpt-4o-mini"),
            "max_cost_per_analysis": openrouter_config.get("max_cost_per_analysis", 0.50),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "ai_cost_optimization": True,  # Always optimize for contractors
            "ai_max_retries": 3
        }
    
    def get_usage_limits(self) -> Dict[str, Any]:
        """Get usage limits for current tier"""
        tier_config = self.get_tier_config()
        
        return {
            "max_companies_per_month": tier_config.get("max_companies_per_month", 50),
            "max_api_calls_per_day": tier_config.get("max_api_calls_per_day", 1000),
            "max_ai_cost_per_month": tier_config.get("max_ai_cost_per_month", 25.00)
        }
    
    def get_features(self) -> list:
        """Get available features for current tier"""
        tier_config = self.get_tier_config()
        return tier_config.get("features", [])
    
    def get_limitations(self) -> list:
        """Get limitations for current tier"""
        tier_config = self.get_tier_config()
        return tier_config.get("limitations", [])
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis for current tier"""
        cost_config = self.pricing_config.get("cost_analysis", {})
        contractor_margins = cost_config.get("contractor_margins", {})
        
        return contractor_margins.get(f"{self.tier}_tier", {})
    
    def is_api_enabled(self, api_name: str) -> bool:
        """Check if API is enabled for current tier"""
        enabled_apis = self.get_enabled_apis()
        return enabled_apis.get(api_name, {}).get("enabled", False)
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """Get configuration for specific API"""
        enabled_apis = self.get_enabled_apis()
        return enabled_apis.get(api_name, {})
    
    def get_monthly_cost(self) -> float:
        """Get monthly cost for current tier"""
        tier_config = self.get_tier_config()
        return tier_config.get("monthly_cost", 0.0)
    
    def get_client_fee(self) -> float:
        """Get client fee for current tier"""
        cost_analysis = self.get_cost_analysis()
        return cost_analysis.get("client_fee", 0.0)
    
    def get_contractor_profit(self) -> float:
        """Get contractor profit for current tier"""
        cost_analysis = self.get_cost_analysis()
        return cost_analysis.get("contractor_profit", 0.0)
    
    def get_profit_margin(self) -> str:
        """Get profit margin for current tier"""
        cost_analysis = self.get_cost_analysis()
        return cost_analysis.get("profit_margin", "0%")
    
    def validate_usage(self, companies_analyzed: int, api_calls_made: int, ai_cost_incurred: float) -> Dict[str, Any]:
        """Validate usage against tier limits"""
        limits = self.get_usage_limits()
        
        validation = {
            "within_limits": True,
            "warnings": [],
            "overages": []
        }
        
        # Check company limit
        if companies_analyzed > limits["max_companies_per_month"]:
            validation["within_limits"] = False
            validation["overages"].append({
                "metric": "companies",
                "limit": limits["max_companies_per_month"],
                "actual": companies_analyzed,
                "overage": companies_analyzed - limits["max_companies_per_month"]
            })
        
        # Check API calls
        if api_calls_made > limits.get("max_api_calls_per_day", 1000):
            validation["within_limits"] = False
            validation["overages"].append({
                "metric": "api_calls",
                "limit": limits["max_api_calls_per_day"],
                "actual": api_calls_made,
                "overage": api_calls_made - limits["max_api_calls_per_day"]
            })
        
        # Check AI costs
        if ai_cost_incurred > limits["max_ai_cost_per_month"]:
            validation["within_limits"] = False
            validation["overages"].append({
                "metric": "ai_costs",
                "limit": limits["max_ai_cost_per_month"],
                "actual": ai_cost_incurred,
                "overage": ai_cost_incurred - limits["max_ai_cost_per_month"]
            })
        
        return validation
    
    def get_upgrade_recommendation(self) -> Optional[str]:
        """Get tier upgrade recommendation"""
        current_tier = self.tier
        
        if current_tier == "free":
            return "professional"
        elif current_tier == "professional":
            return "enterprise"
        
        return None
    
    def get_tier_comparison(self) -> Dict[str, Any]:
        """Get comparison between tiers"""
        tiers = self.pricing_config.get("pricing_tiers", {})
        
        comparison = {}
        for tier_name, tier_config in tiers.items():
            comparison[tier_name] = {
                "name": tier_config.get("name", ""),
                "monthly_cost": tier_config.get("monthly_cost", 0),
                "max_companies": tier_config.get("max_companies_per_month", 0),
                "feature_count": len(tier_config.get("features", [])),
                "api_count": len([api for api in tier_config.get("apis", {}).values() if api.get("enabled", False)])
            }
        
        return comparison

# Global configuration instances for different tiers
configs = {
    "free": lambda client="default": TieredConfig(client, "free"),
    "professional": lambda client="default": TieredConfig(client, "professional"),
    "enterprise": lambda client="default": TieredConfig(client, "enterprise")
}

# Helper functions for easy access
def get_config(tier: str = "free", client: str = "default") -> TieredConfig:
    """Get configuration for specific tier and client"""
    return TieredConfig(client, tier)

def get_ai_config(tier: str = "free", client: str = "default") -> Dict[str, Any]:
    """Get AI configuration for specific tier and client"""
    config = get_config(tier, client)
    return config.get_ai_config()

def get_enabled_apis(tier: str = "free", client: str = "default") -> Dict[str, Any]:
    """Get enabled APIs for specific tier and client"""
    config = get_config(tier, client)
    return config.get_enabled_apis()

def get_usage_limits(tier: str = "free", client: str = "default") -> Dict[str, Any]:
    """Get usage limits for specific tier and client"""
    config = get_config(tier, client)
    return config.get_usage_limits()

def get_cost_analysis(tier: str = "free", client: str = "default") -> Dict[str, Any]:
    """Get cost analysis for specific tier and client"""
    config = get_config(tier, client)
    return config.get_cost_analysis()

# Configuration validation
def validate_tier_config(tier: str, client: str = "default") -> Dict[str, Any]:
    """Validate configuration for specific tier"""
    try:
        config = get_config(tier, client)
        ai_config = config.get_ai_config()
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required API keys
        if not ai_config.get("openrouter_api_key") and not ai_config.get("openai_api_key"):
            validation["valid"] = False
            validation["errors"].append("No AI provider API keys configured")
        
        # Check tier configuration
        if not config.get_tier_config():
            validation["valid"] = False
            validation["errors"].append(f"Tier '{tier}' not found in configuration")
        
        # Check enabled APIs
        enabled_apis = config.get_enabled_apis()
        if not enabled_apis:
            validation["warnings"].append("No APIs enabled for this tier")
        
        return validation
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": []
        }

# Example usage configurations
EXAMPLE_CONFIGS = {
    "free_tier_demo": {
        "client": "demo_client",
        "tier": "free",
        "environment": "development",
        "max_companies": 10,
        "ai_model": "openai/gpt-4o-mini",
        "max_ai_cost": 0.25
    },
    
    "professional_client": {
        "client": "advantary",
        "tier": "professional",
        "environment": "production",
        "max_companies": 200,
        "ai_model": "openai/gpt-4o-mini",
        "max_ai_cost": 0.75
    },
    
    "enterprise_client": {
        "client": "large_firm",
        "tier": "enterprise",
        "environment": "production",
        "max_companies": 500,
        "ai_model": "openai/gpt-4",
        "max_ai_cost": 1.00
    }
}

# Export main configuration class
__all__ = ['TieredConfig', 'get_config', 'get_ai_config', 'get_enabled_apis', 'get_usage_limits', 'get_cost_analysis', 'validate_tier_config']