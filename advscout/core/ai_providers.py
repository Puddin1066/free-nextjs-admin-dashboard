"""
AI Provider Management Module

Supports multiple AI providers including OpenAI and OpenRouter with automatic
failover, cost optimization, and model selection based on task requirements.
"""

import json
import time
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Handle OpenAI import gracefully
try:
    import openai
except ImportError:
    openai = None

from ..core.config import config
from ..core.logger import get_logger, log_execution_time, log_error_with_context
from ..core.utils import APIError

logger = get_logger(__name__)

class AIProvider(Enum):
    """Available AI providers"""
    OPENAI = "openai"
    OPENROUTER = "openrouter"

class TaskType(Enum):
    """Different types of AI tasks with specific requirements"""
    ENRICHMENT = "enrichment"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"

@dataclass
class ModelConfig:
    """Configuration for AI models"""
    provider: AIProvider
    model_name: str
    cost_per_1k_tokens: float
    max_tokens: int
    temperature: float
    best_for_tasks: List[TaskType]
    api_endpoint: str
    headers_template: Dict[str, str]

@dataclass
class AIResponse:
    """Standardized AI response"""
    content: str
    model_used: str
    provider: AIProvider
    cost_estimate: float
    tokens_used: int
    processing_time: float
    confidence: float

class AIProviderManager:
    """Manages multiple AI providers with cost optimization and failover"""
    
    def __init__(self):
        """Initialize AI provider manager"""
        self.providers = {}
        self.model_configs = {}
        self.fallback_order = []
        self.cost_optimization = config.get("ai_cost_optimization", True)
        self.max_retries = config.get("ai_max_retries", 3)
        
        # Initialize providers
        self._initialize_providers()
        self._setup_model_configs()
        
        logger.info(f"Initialized AI providers: {list(self.providers.keys())}")
    
    def _initialize_providers(self):
        """Initialize available AI providers"""
        # OpenAI
        openai_key = config.get("openai_api_key")
        if openai_key and openai is not None:
            self.providers[AIProvider.OPENAI] = {
                'api_key': openai_key,
                'client': openai,
                'available': True
            }
            openai.api_key = openai_key
        
        # OpenRouter
        openrouter_key = config.get("openrouter_api_key")
        if openrouter_key:
            self.providers[AIProvider.OPENROUTER] = {
                'api_key': openrouter_key,
                'base_url': "https://openrouter.ai/api/v1",
                'available': True
            }
        
        # Set fallback order based on cost optimization
        if self.cost_optimization:
            self.fallback_order = [AIProvider.OPENROUTER, AIProvider.OPENAI]
        else:
            self.fallback_order = [AIProvider.OPENAI, AIProvider.OPENROUTER]
    
    def _setup_model_configs(self):
        """Setup model configurations for different providers"""
        
        # OpenAI Models
        self.model_configs.update({
            "gpt-4": ModelConfig(
                provider=AIProvider.OPENAI,
                model_name="gpt-4",
                cost_per_1k_tokens=0.03,
                max_tokens=8192,
                temperature=0.3,
                best_for_tasks=[TaskType.ENRICHMENT, TaskType.ANALYSIS],
                api_endpoint="https://api.openai.com/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}"}
            ),
            
            "gpt-4o-mini": ModelConfig(
                provider=AIProvider.OPENAI,
                model_name="gpt-4o-mini",
                cost_per_1k_tokens=0.00015,
                max_tokens=16384,
                temperature=0.1,
                best_for_tasks=[TaskType.ANALYSIS, TaskType.SYNTHESIS, TaskType.CLASSIFICATION],
                api_endpoint="https://api.openai.com/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}"}
            ),
            
            "gpt-3.5-turbo": ModelConfig(
                provider=AIProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                cost_per_1k_tokens=0.0015,
                max_tokens=4096,
                temperature=0.2,
                best_for_tasks=[TaskType.EXTRACTION, TaskType.CLASSIFICATION],
                api_endpoint="https://api.openai.com/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}"}
            )
        })
        
        # OpenRouter Models
        self.model_configs.update({
            "openrouter/gpt-4o-mini": ModelConfig(
                provider=AIProvider.OPENROUTER,
                model_name="openai/gpt-4o-mini",
                cost_per_1k_tokens=0.00015,
                max_tokens=16384,
                temperature=0.1,
                best_for_tasks=[TaskType.ANALYSIS, TaskType.SYNTHESIS],
                api_endpoint="https://openrouter.ai/api/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}", "HTTP-Referer": "https://advscout.ai"}
            ),
            
            "openrouter/claude-3-haiku": ModelConfig(
                provider=AIProvider.OPENROUTER,
                model_name="anthropic/claude-3-haiku",
                cost_per_1k_tokens=0.00025,
                max_tokens=4096,
                temperature=0.2,
                best_for_tasks=[TaskType.ENRICHMENT, TaskType.ANALYSIS],
                api_endpoint="https://openrouter.ai/api/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}", "HTTP-Referer": "https://advscout.ai"}
            ),
            
            "openrouter/llama-3-70b": ModelConfig(
                provider=AIProvider.OPENROUTER,
                model_name="meta-llama/llama-3-70b-instruct",
                cost_per_1k_tokens=0.0004,
                max_tokens=8192,
                temperature=0.3,
                best_for_tasks=[TaskType.SYNTHESIS, TaskType.CLASSIFICATION],
                api_endpoint="https://openrouter.ai/api/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}", "HTTP-Referer": "https://advscout.ai"}
            ),
            
            "openrouter/gemini-pro": ModelConfig(
                provider=AIProvider.OPENROUTER,
                model_name="google/gemini-pro",
                cost_per_1k_tokens=0.000125,
                max_tokens=2048,
                temperature=0.2,
                best_for_tasks=[TaskType.EXTRACTION, TaskType.CLASSIFICATION],
                api_endpoint="https://openrouter.ai/api/v1/chat/completions",
                headers_template={"Authorization": "Bearer {api_key}", "HTTP-Referer": "https://advscout.ai"}
            )
        })
    
    def get_optimal_model(self, task_type: TaskType, max_cost: Optional[float] = None) -> str:
        """Get the optimal model for a specific task type
        
        Args:
            task_type: Type of AI task
            max_cost: Maximum cost per 1k tokens (optional)
            
        Returns:
            Model name
        """
        # Filter models by task type and cost
        suitable_models = []
        
        for model_name, config in self.model_configs.items():
            if task_type in config.best_for_tasks:
                if max_cost is None or config.cost_per_1k_tokens <= max_cost:
                    if config.provider in self.providers and self.providers[config.provider]['available']:
                        suitable_models.append((model_name, config))
        
        if not suitable_models:
            # Fallback to any available model
            for model_name, config in self.model_configs.items():
                if config.provider in self.providers and self.providers[config.provider]['available']:
                    suitable_models.append((model_name, config))
        
        if not suitable_models:
            raise APIError("No AI models available")
        
        # Sort by cost (ascending) if cost optimization is enabled
        if self.cost_optimization:
            suitable_models.sort(key=lambda x: x[1].cost_per_1k_tokens)
        else:
            # Sort by capability (descending cost as proxy for capability)
            suitable_models.sort(key=lambda x: x[1].cost_per_1k_tokens, reverse=True)
        
        selected_model = suitable_models[0][0]
        logger.info(f"Selected model {selected_model} for task {task_type.value}")
        return selected_model
    
    @log_execution_time
    def complete(self, prompt: str, system_prompt: Optional[str] = None, 
                task_type: TaskType = TaskType.ANALYSIS,
                model_name: Optional[str] = None, max_cost: Optional[float] = None,
                response_format: str = "json") -> AIResponse:
        """Complete an AI task with automatic provider selection and failover
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            task_type: Type of AI task
            model_name: Specific model to use (optional)
            max_cost: Maximum cost per 1k tokens
            response_format: Response format ("json" or "text")
            
        Returns:
            AIResponse object
        """
        start_time = time.time()
        
        # Select model
        if model_name is None:
            model_name = self.get_optimal_model(task_type, max_cost)
        
        model_config = self.model_configs.get(model_name)
        if not model_config:
            raise APIError(f"Model {model_name} not found")
        
        # Try primary model first, then fallback
        models_to_try = [model_name]
        
        # Add fallback models
        for fallback_model in self.model_configs.keys():
            if fallback_model != model_name and fallback_model not in models_to_try:
                fallback_config = self.model_configs[fallback_model]
                if fallback_config.provider in self.providers and self.providers[fallback_config.provider]['available']:
                    models_to_try.append(fallback_model)
        
        last_error = None
        
        for attempt_model in models_to_try:
            try:
                response = self._make_api_call(
                    prompt, system_prompt, attempt_model, response_format
                )
                
                # Calculate cost estimate
                model_config = self.model_configs[attempt_model]
                cost_estimate = (response.tokens_used / 1000) * model_config.cost_per_1k_tokens
                
                return AIResponse(
                    content=response.content,
                    model_used=attempt_model,
                    provider=model_config.provider,
                    cost_estimate=cost_estimate,
                    tokens_used=response.tokens_used,
                    processing_time=time.time() - start_time,
                    confidence=response.confidence
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Model {attempt_model} failed: {e}")
                continue
        
        # All models failed
        raise APIError(f"All AI models failed. Last error: {last_error}")
    
    def _make_api_call(self, prompt: str, system_prompt: Optional[str], 
                      model_name: str, response_format: str) -> AIResponse:
        """Make API call to specific model
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            model_name: Model to use
            response_format: Response format
            
        Returns:
            AIResponse object
        """
        model_config = self.model_configs[model_name]
        provider_config = self.providers[model_config.provider]
        
        if model_config.provider == AIProvider.OPENAI:
            return self._call_openai(prompt, system_prompt, model_config, response_format)
        elif model_config.provider == AIProvider.OPENROUTER:
            return self._call_openrouter(prompt, system_prompt, model_config, response_format)
        else:
            raise APIError(f"Unsupported provider: {model_config.provider}")
    
    def _call_openai(self, prompt: str, system_prompt: Optional[str], 
                    model_config: ModelConfig, response_format: str) -> AIResponse:
        """Call OpenAI API"""
        
        if openai is None:
            raise APIError("OpenAI library not available")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        request_params = {
            "model": model_config.model_name,
            "messages": messages,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature
        }
        
        if response_format == "json":
            request_params["response_format"] = {"type": "json_object"}
        
        try:
            response = openai.ChatCompletion.create(**request_params)
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return AIResponse(
                content=content,
                model_used=model_config.model_name,
                provider=model_config.provider,
                cost_estimate=0.0,  # Will be calculated by caller
                tokens_used=tokens_used,
                processing_time=0.0,  # Will be calculated by caller
                confidence=0.9  # High confidence for OpenAI
            )
            
        except Exception as e:
            raise APIError(f"OpenAI API call failed: {e}")
    
    def _call_openrouter(self, prompt: str, system_prompt: Optional[str], 
                        model_config: ModelConfig, response_format: str) -> AIResponse:
        """Call OpenRouter API"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.providers[AIProvider.OPENROUTER]['api_key']}",
            "HTTP-Referer": "https://advscout.ai",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model_config.model_name,
            "messages": messages,
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature
        }
        
        if response_format == "json":
            data["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(
                model_config.api_endpoint,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code != 200:
                raise APIError(f"OpenRouter API returned status {response.status_code}: {response.text}")
            
            response_data = response.json()
            
            content = response_data["choices"][0]["message"]["content"]
            tokens_used = response_data.get("usage", {}).get("total_tokens", 0)
            
            return AIResponse(
                content=content,
                model_used=model_config.model_name,
                provider=model_config.provider,
                cost_estimate=0.0,  # Will be calculated by caller
                tokens_used=tokens_used,
                processing_time=0.0,  # Will be calculated by caller
                confidence=0.85  # Good confidence for OpenRouter
            )
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"OpenRouter API request failed: {e}")
        except KeyError as e:
            raise APIError(f"OpenRouter API response missing key: {e}")
    
    def get_cost_estimate(self, text: str, model_name: Optional[str] = None, 
                         task_type: TaskType = TaskType.ANALYSIS) -> float:
        """Estimate cost for processing text
        
        Args:
            text: Text to process
            model_name: Specific model (optional)
            task_type: Task type for model selection
            
        Returns:
            Estimated cost in USD
        """
        if model_name is None:
            model_name = self.get_optimal_model(task_type)
        
        model_config = self.model_configs.get(model_name)
        if not model_config:
            return 0.0
        
        # Rough token estimation (4 characters per token)
        estimated_tokens = len(text) / 4
        
        # Add response tokens estimate
        estimated_tokens += model_config.max_tokens * 0.3  # Assume 30% of max tokens for response
        
        return (estimated_tokens / 1000) * model_config.cost_per_1k_tokens
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers
        
        Returns:
            Dictionary with provider status information
        """
        status = {}
        
        for provider, config in self.providers.items():
            status[provider.value] = {
                'available': config['available'],
                'models': [
                    {
                        'name': model_name,
                        'cost_per_1k_tokens': model_config.cost_per_1k_tokens,
                        'max_tokens': model_config.max_tokens,
                        'best_for_tasks': [task.value for task in model_config.best_for_tasks]
                    }
                    for model_name, model_config in self.model_configs.items()
                    if model_config.provider == provider
                ]
            }
        
        return status

# Global instance
ai_provider = AIProviderManager()