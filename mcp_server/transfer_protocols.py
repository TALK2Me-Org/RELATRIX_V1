"""
RELATRIX Transfer Protocols
System for managing agent transfers based on conversation context and triggers
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class TransferTriggerType(Enum):
    """Types of transfer triggers"""
    KEYWORD = "keyword"
    PHRASE = "phrase"
    EMOTION = "emotion"
    INTENT = "intent"
    PATTERN = "pattern"
    ESCALATION = "escalation"

@dataclass
class TransferTrigger:
    """Individual transfer trigger definition"""
    pattern: str
    target_agent: str
    trigger_type: TransferTriggerType
    confidence_threshold: float = 0.7
    description: str = ""
    priority: int = 1
    requires_confirmation: bool = False
    
    def matches(self, text: str) -> bool:
        """Check if trigger matches the given text"""
        text_lower = text.lower()
        pattern_lower = self.pattern.lower()
        
        if self.trigger_type == TransferTriggerType.KEYWORD:
            return pattern_lower in text_lower
        elif self.trigger_type == TransferTriggerType.PHRASE:
            return pattern_lower in text_lower
        elif self.trigger_type == TransferTriggerType.PATTERN:
            return bool(re.search(pattern_lower, text_lower))
        else:
            return pattern_lower in text_lower

@dataclass
class TransferContext:
    """Context information for agent transfers"""
    session_id: str
    user_id: str
    current_agent: str
    previous_agent: Optional[str] = None
    conversation_history: List[str] = field(default_factory=list)
    emotional_state: str = "neutral"
    topic: str = "general"
    urgency_level: str = "normal"
    transfer_count: int = 0
    last_transfer_time: Optional[datetime] = None

class TransferProtocol:
    """Main transfer protocol system"""
    
    def __init__(self):
        self.triggers = self._initialize_triggers()
        self.transfer_history = []
        self.agent_capabilities = self._get_agent_capabilities()
        
        logger.info(f"Transfer protocol initialized with {len(self.triggers)} triggers")
    
    def _initialize_triggers(self) -> List[TransferTrigger]:
        """Initialize all transfer triggers"""
        triggers = []
        
        # EMOTIONAL VOMIT DUMPER triggers
        emotional_triggers = [
            TransferTrigger("I need to express my emotions", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.9, "Need emotional expression"),
            TransferTrigger("I'm feeling overwhelmed", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.8, "Feeling overwhelmed"),
            TransferTrigger("I need to vent", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.9, "Need to vent"),
            TransferTrigger("emotional dump", "emotional_vomit_dumper", TransferTriggerType.KEYWORD, 0.8, "Emotional dumping"),
            TransferTrigger("I'm upset about", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.7, "Upset feelings"),
            TransferTrigger("I'm so angry", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.8, "Anger expression"),
            TransferTrigger("I'm hurt", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.7, "Hurt feelings"),
            TransferTrigger("I'm devastated", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.9, "Devastation"),
            TransferTrigger("I can't handle", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.8, "Can't handle"),
            TransferTrigger("I'm breaking down", "emotional_vomit_dumper", TransferTriggerType.PHRASE, 0.9, "Breaking down"),
        ]
        
        # SOLUTION FINDER triggers
        solution_triggers = [
            TransferTrigger("I feel better now", "solution_finder", TransferTriggerType.PHRASE, 0.8, "Ready for solutions"),
            TransferTrigger("I'm ready to talk about solutions", "solution_finder", TransferTriggerType.PHRASE, 0.9, "Ready for solutions"),
            TransferTrigger("I want to work on this", "solution_finder", TransferTriggerType.PHRASE, 0.8, "Want to work on it"),
            TransferTrigger("what should I do", "solution_finder", TransferTriggerType.PHRASE, 0.7, "Asking for action"),
            TransferTrigger("I need help with", "solution_finder", TransferTriggerType.PHRASE, 0.7, "Need help"),
            TransferTrigger("how can I fix", "solution_finder", TransferTriggerType.PHRASE, 0.8, "Want to fix"),
            TransferTrigger("I need a plan", "solution_finder", TransferTriggerType.PHRASE, 0.9, "Need planning"),
            TransferTrigger("what's my next step", "solution_finder", TransferTriggerType.PHRASE, 0.8, "Next steps"),
            TransferTrigger("I want to change", "solution_finder", TransferTriggerType.PHRASE, 0.7, "Want change"),
            TransferTrigger("help me figure out", "solution_finder", TransferTriggerType.PHRASE, 0.8, "Need figuring out"),
        ]
        
        # CONFLICT SOLVER triggers
        conflict_triggers = [
            TransferTrigger("we're fighting", "conflict_solver", TransferTriggerType.PHRASE, 0.8, "Fighting"),
            TransferTrigger("we had an argument", "conflict_solver", TransferTriggerType.PHRASE, 0.8, "Argument"),
            TransferTrigger("we're in conflict", "conflict_solver", TransferTriggerType.PHRASE, 0.9, "In conflict"),
            TransferTrigger("we can't agree", "conflict_solver", TransferTriggerType.PHRASE, 0.7, "Can't agree"),
            TransferTrigger("we need mediation", "conflict_solver", TransferTriggerType.PHRASE, 0.9, "Need mediation"),
            TransferTrigger("we're having problems", "conflict_solver", TransferTriggerType.PHRASE, 0.7, "Having problems"),
            TransferTrigger("we need to resolve", "conflict_solver", TransferTriggerType.PHRASE, 0.8, "Need resolution"),
            TransferTrigger("we're stuck", "conflict_solver", TransferTriggerType.PHRASE, 0.7, "Stuck in conflict"),
            TransferTrigger("we keep arguing", "conflict_solver", TransferTriggerType.PHRASE, 0.8, "Keep arguing"),
            TransferTrigger("we're at an impasse", "conflict_solver", TransferTriggerType.PHRASE, 0.9, "At impasse"),
        ]
        
        # COMMUNICATION SIMULATOR triggers
        communication_triggers = [
            TransferTrigger("I want to practice", "communication_simulator", TransferTriggerType.PHRASE, 0.8, "Want practice"),
            TransferTrigger("I need to rehearse", "communication_simulator", TransferTriggerType.PHRASE, 0.9, "Need rehearsal"),
            TransferTrigger("I'm worried about saying", "communication_simulator", TransferTriggerType.PHRASE, 0.8, "Worried about saying"),
            TransferTrigger("I don't know how to bring this up", "communication_simulator", TransferTriggerType.PHRASE, 0.8, "Don't know how to bring up"),
            TransferTrigger("practice conversation", "communication_simulator", TransferTriggerType.PHRASE, 0.9, "Practice conversation"),
            TransferTrigger("I'm nervous about talking", "communication_simulator", TransferTriggerType.PHRASE, 0.8, "Nervous about talking"),
            TransferTrigger("I need to prepare", "communication_simulator", TransferTriggerType.PHRASE, 0.7, "Need preparation"),
            TransferTrigger("I want to role-play", "communication_simulator", TransferTriggerType.PHRASE, 0.9, "Want role-play"),
            TransferTrigger("how should I say", "communication_simulator", TransferTriggerType.PHRASE, 0.8, "How to say"),
            TransferTrigger("I need feedback", "communication_simulator", TransferTriggerType.PHRASE, 0.7, "Need feedback"),
        ]
        
        # RELATIONSHIP UPGRADER triggers
        upgrader_triggers = [
            TransferTrigger("I want to level up", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Want to level up"),
            TransferTrigger("relationship games", "relationship_upgrader", TransferTriggerType.PHRASE, 0.9, "Relationship games"),
            TransferTrigger("fun challenges", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Fun challenges"),
            TransferTrigger("make it exciting", "relationship_upgrader", TransferTriggerType.PHRASE, 0.7, "Make exciting"),
            TransferTrigger("relationship activities", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Relationship activities"),
            TransferTrigger("we want to improve our relationship", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Want improvement"),
            TransferTrigger("I want to work on us", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Work on us"),
            TransferTrigger("relationship goals", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Relationship goals"),
            TransferTrigger("make things better", "relationship_upgrader", TransferTriggerType.PHRASE, 0.7, "Make things better"),
            TransferTrigger("strengthen our bond", "relationship_upgrader", TransferTriggerType.PHRASE, 0.8, "Strengthen bond"),
        ]
        
        # BREAKTHROUGH MANAGER triggers (crisis situations)
        breakthrough_triggers = [
            TransferTrigger("I think we should break up", "breakthrough_manager", TransferTriggerType.PHRASE, 0.9, "Breakup consideration", priority=10),
            TransferTrigger("I want to end this", "breakthrough_manager", TransferTriggerType.PHRASE, 0.8, "Want to end", priority=10),
            TransferTrigger("I can't do this anymore", "breakthrough_manager", TransferTriggerType.PHRASE, 0.8, "Can't continue", priority=10),
            TransferTrigger("relationship is over", "breakthrough_manager", TransferTriggerType.PHRASE, 0.9, "Relationship over", priority=10),
            TransferTrigger("I'm done", "breakthrough_manager", TransferTriggerType.PHRASE, 0.7, "Done with relationship", priority=9),
            TransferTrigger("I want out", "breakthrough_manager", TransferTriggerType.PHRASE, 0.8, "Want out", priority=9),
            TransferTrigger("I'm leaving", "breakthrough_manager", TransferTriggerType.PHRASE, 0.8, "Leaving", priority=10),
            TransferTrigger("this is hopeless", "breakthrough_manager", TransferTriggerType.PHRASE, 0.7, "Hopeless", priority=8),
            TransferTrigger("I give up", "breakthrough_manager", TransferTriggerType.PHRASE, 0.8, "Give up", priority=9),
            TransferTrigger("it's too late", "breakthrough_manager", TransferTriggerType.PHRASE, 0.7, "Too late", priority=8),
        ]
        
        # MISUNDERSTANDING PROTECTOR triggers (analysis needed)
        misunderstanding_triggers = [
            TransferTrigger("I don't understand", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.7, "Don't understand"),
            TransferTrigger("that's not what I meant", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.8, "Not what meant"),
            TransferTrigger("you're misunderstanding", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.8, "Misunderstanding"),
            TransferTrigger("I didn't say that", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.8, "Didn't say that"),
            TransferTrigger("that's not right", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.6, "Not right"),
            TransferTrigger("I'm confused", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.7, "Confused"),
            TransferTrigger("I need clarity", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.8, "Need clarity"),
            TransferTrigger("help me understand", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.8, "Help understand"),
            TransferTrigger("I'm lost", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.6, "Lost"),
            TransferTrigger("analyze this", "misunderstanding_protector", TransferTriggerType.PHRASE, 0.9, "Analyze"),
        ]
        
        # Combine all triggers
        all_triggers = (
            emotional_triggers +
            solution_triggers +
            conflict_triggers +
            communication_triggers +
            upgrader_triggers +
            breakthrough_triggers +
            misunderstanding_triggers
        )
        
        return all_triggers
    
    def _get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities for each agent"""
        return {
            "misunderstanding_protector": [
                "4-card analysis",
                "communication pattern analysis",
                "conflict prevention",
                "clarity improvement"
            ],
            "emotional_vomit_dumper": [
                "emotional support",
                "non-judgmental listening",
                "emotional processing",
                "stress relief"
            ],
            "conflict_solver": [
                "mediation",
                "conflict resolution",
                "perspective bridging",
                "solution negotiation"
            ],
            "solution_finder": [
                "action planning",
                "problem solving",
                "goal setting",
                "progress tracking"
            ],
            "communication_simulator": [
                "conversation practice",
                "role-playing",
                "feedback provision",
                "confidence building"
            ],
            "relationship_upgrader": [
                "relationship enhancement",
                "gamification",
                "challenge creation",
                "growth tracking"
            ],
            "breakthrough_manager": [
                "crisis support",
                "major decision help",
                "breakup support",
                "healing guidance"
            ]
        }
    
    def analyze_transfer_request(self, message: str, context: TransferContext) -> Optional[Tuple[str, TransferTrigger, float]]:
        """Analyze message for transfer triggers"""
        best_match = None
        best_score = 0.0
        best_trigger = None
        
        # Sort triggers by priority (higher priority first)
        sorted_triggers = sorted(self.triggers, key=lambda t: t.priority, reverse=True)
        
        for trigger in sorted_triggers:
            if trigger.target_agent == context.current_agent:
                continue  # Skip if already on target agent
            
            if trigger.matches(message):
                # Calculate confidence score
                confidence = self._calculate_confidence(trigger, message, context)
                
                if confidence >= trigger.confidence_threshold and confidence > best_score:
                    best_match = trigger.target_agent
                    best_score = confidence
                    best_trigger = trigger
        
        if best_match:
            return best_match, best_trigger, best_score
        
        return None
    
    def _calculate_confidence(self, trigger: TransferTrigger, message: str, context: TransferContext) -> float:
        """Calculate confidence score for a transfer trigger"""
        base_confidence = 0.5
        
        # Exact phrase match gets higher confidence
        if trigger.pattern.lower() in message.lower():
            base_confidence = 0.8
        
        # Boost confidence based on context
        if context.emotional_state == "distressed" and "emotional_vomit_dumper" in trigger.target_agent:
            base_confidence += 0.2
        
        if context.urgency_level == "high" and trigger.priority >= 8:
            base_confidence += 0.15
        
        # Reduce confidence for frequent transfers
        if context.transfer_count > 5:
            base_confidence -= 0.1
        
        # Time-based considerations
        if context.last_transfer_time:
            time_since_transfer = (datetime.now() - context.last_transfer_time).total_seconds()
            if time_since_transfer < 60:  # Less than 1 minute
                base_confidence -= 0.2
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def execute_transfer(self, from_agent: str, to_agent: str, trigger: TransferTrigger, context: TransferContext) -> Dict[str, Any]:
        """Execute agent transfer"""
        transfer_record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": context.session_id,
            "user_id": context.user_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "trigger_pattern": trigger.pattern,
            "trigger_description": trigger.description,
            "confidence": self._calculate_confidence(trigger, "", context),
            "requires_confirmation": trigger.requires_confirmation
        }
        
        self.transfer_history.append(transfer_record)
        
        # Update context
        context.previous_agent = from_agent
        context.current_agent = to_agent
        context.transfer_count += 1
        context.last_transfer_time = datetime.now()
        
        logger.info(f"Transfer executed: {from_agent} -> {to_agent} (trigger: {trigger.pattern})")
        
        return transfer_record
    
    def get_transfer_suggestion(self, message: str, context: TransferContext) -> Optional[Dict[str, Any]]:
        """Get transfer suggestion without executing"""
        result = self.analyze_transfer_request(message, context)
        
        if result:
            agent, trigger, confidence = result
            return {
                "suggested_agent": agent,
                "trigger": trigger.pattern,
                "description": trigger.description,
                "confidence": confidence,
                "requires_confirmation": trigger.requires_confirmation,
                "agent_capabilities": self.agent_capabilities.get(agent, [])
            }
        
        return None
    
    def get_transfer_history(self, session_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get transfer history"""
        if session_id:
            filtered_history = [t for t in self.transfer_history if t["session_id"] == session_id]
        else:
            filtered_history = self.transfer_history
        
        return filtered_history[-limit:]
    
    def get_agent_triggers(self, agent_id: str) -> List[TransferTrigger]:
        """Get all triggers that lead to a specific agent"""
        return [trigger for trigger in self.triggers if trigger.target_agent == agent_id]
    
    def add_custom_trigger(self, trigger: TransferTrigger) -> bool:
        """Add a custom transfer trigger"""
        try:
            self.triggers.append(trigger)
            logger.info(f"Added custom trigger: {trigger.pattern} -> {trigger.target_agent}")
            return True
        except Exception as e:
            logger.error(f"Failed to add custom trigger: {e}")
            return False
    
    def validate_transfer_chain(self, context: TransferContext) -> bool:
        """Validate if transfer chain is healthy (not stuck in loops)"""
        if context.transfer_count > 10:
            logger.warning(f"High transfer count detected: {context.transfer_count}")
            return False
        
        # Check for transfer loops
        recent_transfers = self.get_transfer_history(context.session_id, 5)
        if len(recent_transfers) >= 3:
            agents = [t["to_agent"] for t in recent_transfers]
            if len(set(agents)) <= 2:  # Bouncing between 2 agents
                logger.warning(f"Transfer loop detected: {agents}")
                return False
        
        return True
    
    def get_transfer_stats(self) -> Dict[str, Any]:
        """Get transfer statistics"""
        if not self.transfer_history:
            return {"total_transfers": 0}
        
        total_transfers = len(self.transfer_history)
        
        # Agent transfer counts
        agent_counts = {}
        for transfer in self.transfer_history:
            agent = transfer["to_agent"]
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        # Most common triggers
        trigger_counts = {}
        for transfer in self.transfer_history:
            trigger = transfer["trigger_pattern"]
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        return {
            "total_transfers": total_transfers,
            "agent_transfer_counts": agent_counts,
            "most_common_triggers": sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "average_confidence": sum(t.get("confidence", 0) for t in self.transfer_history) / total_transfers
        }

# Global transfer protocol instance
transfer_protocol = TransferProtocol()

# Convenience functions
def analyze_message_for_transfer(message: str, context: TransferContext) -> Optional[Tuple[str, TransferTrigger, float]]:
    """Analyze message for transfer triggers"""
    return transfer_protocol.analyze_transfer_request(message, context)

def get_transfer_suggestion(message: str, context: TransferContext) -> Optional[Dict[str, Any]]:
    """Get transfer suggestion"""
    return transfer_protocol.get_transfer_suggestion(message, context)

def execute_transfer(from_agent: str, to_agent: str, trigger: TransferTrigger, context: TransferContext) -> Dict[str, Any]:
    """Execute agent transfer"""
    return transfer_protocol.execute_transfer(from_agent, to_agent, trigger, context)

if __name__ == "__main__":
    # Test the transfer protocol
    print("RELATRIX Transfer Protocol Test")
    print("=" * 40)
    
    # Create test context
    test_context = TransferContext(
        session_id="test_session",
        user_id="test_user",
        current_agent="misunderstanding_protector"
    )
    
    # Test messages
    test_messages = [
        "I need to vent about my partner",
        "I'm ready to work on solutions",
        "We're having a big fight",
        "I want to practice what to say",
        "I think we should break up",
        "I want to level up our relationship"
    ]
    
    for message in test_messages:
        print(f"\nMessage: '{message}'")
        suggestion = get_transfer_suggestion(message, test_context)
        if suggestion:
            print(f"  → Suggested agent: {suggestion['suggested_agent']}")
            print(f"  → Trigger: {suggestion['trigger']}")
            print(f"  → Confidence: {suggestion['confidence']:.2f}")
        else:
            print("  → No transfer suggested")
    
    # Print statistics
    print("\nTransfer Statistics:")
    stats = transfer_protocol.get_transfer_stats()
    print(f"Total triggers: {len(transfer_protocol.triggers)}")
    print(f"Available agents: {len(transfer_protocol.agent_capabilities)}")
    
    # Print agent capabilities
    print("\nAgent Capabilities:")
    for agent, capabilities in transfer_protocol.agent_capabilities.items():
        print(f"  {agent}: {', '.join(capabilities)}")