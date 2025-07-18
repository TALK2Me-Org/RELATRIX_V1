"""
Model definitions for RELATRIX
Single source of truth for all AI models
"""

# All available models organized by provider
MODELS = {
    "openai": [
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Najnowszy i najszybszy GPT-4 (128k kontekst)"},
        {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview", "description": "GPT-4 Turbo z wiedzą do kwietnia 2023"},
        {"id": "gpt-4", "name": "GPT-4", "description": "Klasyczny GPT-4 (8k kontekst)"},
        {"id": "gpt-4-32k", "name": "GPT-4 32K", "description": "GPT-4 z dużym kontekstem"},
        {"id": "gpt-4o", "name": "GPT-4 Optimized", "description": "Szybszy i tańszy GPT-4"},
        {"id": "gpt-4o-mini", "name": "GPT-4 Optimized Mini", "description": "Najszybszy wariant GPT-4"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Szybki i ekonomiczny (16k kontekst)"},
        {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K", "description": "GPT-3.5 z dużym kontekstem"}
    ],
    "bedrock": [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "description": "Najnowszy Claude, świetna równowaga mocy i szybkości"},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "description": "Najszybszy model Claude, idealny do prostych zadań"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "description": "Najpotężniejszy Claude, do złożonych zadań"},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "description": "Zbalansowany model Claude"}
    ]
}

# Mapping from simple IDs to full AWS Bedrock model IDs
BEDROCK_MODEL_MAPPING = {
    "claude-3-5-sonnet-20241022": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "claude-3-haiku-20240307": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-opus-20240229": "anthropic.claude-3-opus-20240229-v1:0",
    "claude-3-sonnet-20240229": "anthropic.claude-3-sonnet-20240229-v1:0"
}

# Default models per provider
DEFAULT_MODELS = {
    "openai": "gpt-4-turbo",
    "bedrock": "claude-3-5-sonnet-20241022"
}

def get_bedrock_model_id(simple_id: str) -> str:
    """Convert simple model ID to full AWS Bedrock model ID"""
    return BEDROCK_MODEL_MAPPING.get(simple_id, simple_id)

def get_all_models():
    """Get all available models with defaults"""
    return {
        **MODELS,
        "defaults": DEFAULT_MODELS
    }