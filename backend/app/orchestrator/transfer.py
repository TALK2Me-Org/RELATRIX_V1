"""
Transfer Engine - Manages agent switching and transfer logic
"""

import logging
import re
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from .models import Agent, TransferEvent, TransferReason, SessionState
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class TransferEngine:
    """Handles agent transfer logic and trigger analysis"""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.transfer_patterns: Dict[str, List[re.Pattern]] = {}
        logger.info("Transfer Engine initialized")
    
    async def analyze_message(
        self, 
        message: str, 
        current_agent: str,
        session_state: SessionState
    ) -> Optional[Tuple[str, str, TransferReason]]:
        """
        Analyze message for transfer triggers
        Returns: (target_agent_slug, trigger_phrase, reason) or None
        """
        message_lower = message.lower().strip()
        
        # Check explicit transfer requests first
        explicit_transfer = self._check_explicit_transfer(message_lower)
        if explicit_transfer:
            return explicit_transfer[0], explicit_transfer[1], TransferReason.USER_REQUEST
        
        # Get all agents to check triggers
        agents = await self.registry.get_all_agents()
        
        # Check each agent's triggers
        for agent in agents:
            if agent.slug == current_agent:
                continue
            
            # Check trigger phrases
            for trigger in agent.transfer_triggers:
                if trigger.lower() in message_lower:
                    logger.info(f"Transfer trigger matched: '{trigger}' -> {agent.slug}")
                    return agent.slug, trigger, TransferReason.TRIGGER_MATCH
            
            # Check regex patterns if compiled
            if agent.slug in self.transfer_patterns:
                for pattern in self.transfer_patterns[agent.slug]:
                    if pattern.search(message_lower):
                        logger.info(f"Transfer pattern matched -> {agent.slug}")
                        return agent.slug, "pattern match", TransferReason.TRIGGER_MATCH
        
        # Check if current agent suggests transfer in their response
        # This would be implemented after agent responds
        
        return None
    
    def _check_explicit_transfer(self, message: str) -> Optional[Tuple[str, str]]:
        """Check for explicit transfer requests"""
        transfer_phrases = {
            "transfer me to": r"transfer (?:me )?to (?:the )?(\w+)",
            "switch to": r"switch to (?:the )?(\w+)",
            "talk to": r"(?:i want to |can i |let me )?talk to (?:the )?(\w+)",
            "connect me with": r"connect me (?:with|to) (?:the )?(\w+)"
        }
        
        for phrase, pattern in transfer_phrases.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                agent_name = match.group(1).lower()
                # Map common names to agent slugs
                agent_map = {
                    "misunderstanding": "misunderstanding_protector",
                    "emotional": "emotional_vomit_dumper",
                    "vomit": "emotional_vomit_dumper",
                    "conflict": "conflict_solver",
                    "solution": "solution_finder",
                    "communication": "communication_simulator",
                    "simulator": "communication_simulator",
                    "relationship": "relationship_upgrader",
                    "upgrader": "relationship_upgrader",
                    "breakthrough": "breakthrough_manager",
                    "crisis": "breakthrough_manager"
                }
                
                # Check if it's a known agent
                for key, slug in agent_map.items():
                    if key in agent_name:
                        return slug, phrase
                
        return None
    
    async def execute_transfer(
        self,
        session_state: SessionState,
        to_agent: str,
        reason: TransferReason,
        trigger: Optional[str] = None,
        user_message: str = ""
    ) -> TransferEvent:
        """Execute agent transfer"""
        from_agent = session_state.current_agent
        
        # Verify target agent exists
        target_agent = await self.registry.get_agent(to_agent)
        if not target_agent:
            logger.error(f"Target agent not found: {to_agent}")
            return TransferEvent(
                from_agent=from_agent,
                to_agent=to_agent,
                reason=reason,
                trigger=trigger,
                user_message=user_message,
                success=False,
                error="Target agent not found"
            )
        
        # Create transfer event
        transfer = TransferEvent(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            trigger=trigger,
            user_message=user_message,
            context={
                "session_id": session_state.session_id,
                "message_count": len(session_state.conversation_history),
                "previous_transfers": len(session_state.transfer_history)
            }
        )
        
        # Update session state
        session_state.add_transfer(transfer)
        
        logger.info(f"Transfer executed: {from_agent} -> {to_agent} (reason: {reason})")
        return transfer
    
    def compile_patterns(self, agents: List[Agent]):
        """Compile regex patterns for efficient matching"""
        for agent in agents:
            patterns = []
            
            # Add some common patterns based on agent type
            if agent.slug == "emotional_vomit_dumper":
                patterns.extend([
                    re.compile(r"\b(need to vent|feeling overwhelmed|so frustrated)\b", re.I),
                    re.compile(r"\b(can't take it|about to explode|so angry)\b", re.I)
                ])
            elif agent.slug == "conflict_solver":
                patterns.extend([
                    re.compile(r"\b(we keep arguing|constant fights?|always fighting)\b", re.I),
                    re.compile(r"\b(resolve this|find middle ground|compromise)\b", re.I)
                ])
            elif agent.slug == "breakthrough_manager":
                patterns.extend([
                    re.compile(r"\b(want to break up|end (this|it|us)|divorce)\b", re.I),
                    re.compile(r"\b(can't go on|relationship is over|we're done)\b", re.I)
                ])
            
            if patterns:
                self.transfer_patterns[agent.slug] = patterns
    
    def get_transfer_history_summary(
        self, 
        session_state: SessionState,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get summary of recent transfers"""
        recent_transfers = session_state.transfer_history[-limit:]
        
        summary = []
        for transfer in recent_transfers:
            summary.append({
                "timestamp": transfer.timestamp.isoformat(),
                "from": transfer.from_agent,
                "to": transfer.to_agent,
                "reason": transfer.reason,
                "trigger": transfer.trigger
            })
        
        return summary
    
    async def suggest_transfer(
        self,
        current_agent: str,
        conversation_context: str
    ) -> Optional[Tuple[str, str]]:
        """
        Suggest a transfer based on conversation context
        Used when agent determines a transfer would be helpful
        Returns: (target_agent_slug, suggestion_reason) or None
        """
        # This would analyze the conversation and current agent's capabilities
        # to suggest appropriate transfers
        
        # Example logic:
        if current_agent == "misunderstanding_protector":
            if "feeling overwhelmed" in conversation_context.lower():
                return "emotional_vomit_dumper", "User seems emotionally overwhelmed"
        
        elif current_agent == "emotional_vomit_dumper":
            if "what should i do" in conversation_context.lower():
                return "solution_finder", "User is ready for solutions"
        
        return None