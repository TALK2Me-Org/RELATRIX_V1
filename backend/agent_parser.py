"""
Agent parser for extracting and removing JSON from responses
Simple regex operations
"""
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def extract_agent_slug(text: str) -> Optional[str]:
    """
    Extract agent slug from JSON in text
    Looking for pattern: {"agent": "slug_name"}
    """
    try:
        # Match JSON with flexible whitespace
        match = re.search(r'{\s*"agent"\s*:\s*"([^"]+)"\s*}', text)
        if match:
            agent_slug = match.group(1)
            logger.info(f"Found agent switch request: {agent_slug}")
            return agent_slug
        return None
    except Exception as e:
        logger.error(f"Error extracting agent slug: {e}")
        return None


def remove_agent_json(text: str) -> str:
    """
    Remove agent JSON from text
    Returns clean text without JSON markers
    """
    try:
        # Remove all agent JSON patterns
        clean_text = re.sub(r'{\s*"agent"\s*:\s*"[^"]+"\s*}', '', text)
        # Clean up extra whitespace
        clean_text = ' '.join(clean_text.split())
        return clean_text.strip()
    except Exception as e:
        logger.error(f"Error removing agent JSON: {e}")
        return text