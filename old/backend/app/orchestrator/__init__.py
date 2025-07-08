"""
RELATRIX Simple Orchestrator
Minimal and direct!
"""

from .registry import AgentRegistry
from .orchestrator import SimpleOrchestrator, get_orchestrator

__all__ = [
    'AgentRegistry',
    'SimpleOrchestrator',
    'get_orchestrator'
]