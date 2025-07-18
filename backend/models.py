"""
Model definitions for RELATRIX
Single source of truth for all AI models
"""

# All available models organized by provider
MODELS = {
    "openai": [
        # GPT-4.1 Series (2025)
        {"id": "gpt-4.1", "name": "GPT-4.1"},
        {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini"},
        {"id": "gpt-4.1-nano", "name": "GPT-4.1 Nano"},
        
        # GPT-4.5
        {"id": "gpt-4.5-preview", "name": "GPT-4.5 Preview"},
        
        # O-series (Reasoning models)
        {"id": "o1", "name": "O1"},
        {"id": "o3", "name": "O3"},
        {"id": "o3-mini", "name": "O3 Mini"},
        {"id": "o3-pro", "name": "O3 Pro"},
        {"id": "o4-mini", "name": "O4 Mini"},
        
        # GPT-4o Series
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4o-2024-08-06", "name": "GPT-4o (08-2024)"},
        {"id": "gpt-4o-2024-05-13", "name": "GPT-4o (05-2024)"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "gpt-4o-mini-2024-07-18", "name": "GPT-4o Mini (07-2024)"},
        {"id": "chatgpt-4o-latest", "name": "ChatGPT-4o Latest"},
        
        # GPT-4 Turbo
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
        {"id": "gpt-4-turbo-2024-04-09", "name": "GPT-4 Turbo (04-2024)"},
        {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview"},
        
        # GPT-4 Standard
        {"id": "gpt-4", "name": "GPT-4"},
        {"id": "gpt-4-32k", "name": "GPT-4 32K"},
        {"id": "gpt-4-0125-preview", "name": "GPT-4 (01-2025)"},
        {"id": "gpt-4-1106-preview", "name": "GPT-4 (11-2024)"},
        
        # GPT-3.5 Turbo
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K"},
        {"id": "gpt-3.5-turbo-0125", "name": "GPT-3.5 Turbo (01-2025)"},
        {"id": "gpt-3.5-turbo-1106", "name": "GPT-3.5 Turbo (11-2024)"},
        {"id": "gpt-3.5-turbo-instruct", "name": "GPT-3.5 Turbo Instruct"}
    ],
    "bedrock": [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
        {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"}
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