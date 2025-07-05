"""
Misunderstanding Protector Agent
Specialized AI agent for analyzing communication patterns and preventing misunderstandings
Uses 4-card analysis method for comprehensive communication breakdown
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.config import settings

logger = logging.getLogger(__name__)

class AnalysisCard(Enum):
    """4-card analysis types"""
    RED = "problems"      # Problems/Issues
    YELLOW = "cautions"   # Cautions/Risks
    GREEN = "positives"   # Positive Aspects
    BLUE = "actions"      # Recommendations/Actions

@dataclass
class CardAnalysis:
    """Individual card analysis"""
    card_type: AnalysisCard
    title: str
    points: List[str]
    priority: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_type": self.card_type.value,
            "title": self.title,
            "points": self.points,
            "priority": self.priority
        }

@dataclass
class CommunicationAnalysis:
    """Complete 4-card communication analysis"""
    session_id: str
    user_id: str
    message: str
    timestamp: datetime
    cards: List[CardAnalysis]
    overall_assessment: str
    transfer_recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "cards": [card.to_dict() for card in self.cards],
            "overall_assessment": self.overall_assessment,
            "transfer_recommendation": self.transfer_recommendation
        }

class MisunderstandingProtector:
    """Misunderstanding Protector Agent"""
    
    def __init__(self):
        self.agent_id = "misunderstanding_protector"
        self.name = "Misunderstanding Protector"
        self.description = "Analyzes communication patterns and prevents misunderstandings using 4-card analysis"
        
        # Analysis patterns
        self.problem_patterns = self._initialize_problem_patterns()
        self.positive_patterns = self._initialize_positive_patterns()
        self.risk_patterns = self._initialize_risk_patterns()
        
        logger.info("Misunderstanding Protector Agent initialized")
    
    def _initialize_problem_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that indicate problems"""
        return {
            "defensive_language": [
                "you always", "you never", "you're wrong", "that's not true",
                "you don't understand", "you're not listening", "whatever",
                "fine", "i don't care", "you're being ridiculous"
            ],
            "blame_shifting": [
                "it's your fault", "you made me", "because of you",
                "you're the reason", "you caused", "you started it"
            ],
            "dismissive_language": [
                "that's stupid", "that doesn't matter", "who cares",
                "so what", "big deal", "get over it", "you're overreacting"
            ],
            "emotional_escalation": [
                "i'm so angry", "i hate when", "this is ridiculous",
                "i can't believe", "this is insane", "you're crazy"
            ],
            "communication_breakdown": [
                "we're not communicating", "you don't get it",
                "i give up", "what's the point", "we're talking past each other"
            ],
            "assumptions": [
                "you probably think", "i know you think", "you obviously",
                "clearly you", "you must think", "i'm sure you"
            ]
        }
    
    def _initialize_positive_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that indicate positive communication"""
        return {
            "empathy": [
                "i understand", "i can see", "that must be",
                "i get why", "that makes sense", "i hear you"
            ],
            "ownership": [
                "i feel", "i think", "from my perspective",
                "i realize", "i notice", "i appreciate"
            ],
            "collaboration": [
                "let's work together", "what can we do", "how can we",
                "maybe we could", "what if we", "let's figure out"
            ],
            "validation": [
                "you're right", "good point", "that's fair",
                "i hadn't thought of that", "thank you for", "i'm glad you"
            ],
            "openness": [
                "help me understand", "can you explain", "what do you think",
                "how do you feel", "what would work", "i'm open to"
            ]
        }
    
    def _initialize_risk_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that indicate risks"""
        return {
            "escalation_warning": [
                "this is getting heated", "we're arguing again",
                "here we go again", "not this again", "i'm getting frustrated"
            ],
            "withdrawal_signs": [
                "i don't want to talk", "leave me alone",
                "i need space", "i'm done", "forget it"
            ],
            "misinterpretation": [
                "that's not what i meant", "you're twisting my words",
                "you misunderstood", "that's not what i said"
            ],
            "emotional_triggers": [
                "you sound like", "you're just like", "you remind me of",
                "this always happens", "every time we"
            ],
            "avoidance": [
                "we'll talk later", "not now", "i don't want to deal",
                "let's just drop it", "can we move on"
            ]
        }
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return f"""You are the {self.name}, a specialized AI agent focused on preventing and resolving communication misunderstandings in relationships.

Your primary role is to analyze communication patterns using the 4-card analysis method:

🔴 RED CARD - Problems/Issues
- Identify communication breakdowns
- Spot potential misunderstandings  
- Highlight emotional triggers
- Point out defensive patterns
- Note blame shifting or dismissive language

🟡 YELLOW CARD - Cautions/Risks
- Warning signs in communication
- Potential areas of concern
- Patterns that might escalate
- Things to be mindful of
- Emotional triggers to watch

🟢 GREEN CARD - Positive Aspects
- What's working well in communication
- Strengths to build upon
- Positive patterns to acknowledge
- Good intentions to recognize
- Empathy and understanding shown

🔵 BLUE CARD - Recommendations/Actions
- Concrete next steps
- Communication techniques to try
- Ways to prevent future issues
- Specific tools and strategies
- Alternative approaches to consider

CRITICAL INSTRUCTIONS:
1. ALWAYS format your responses with these 4 cards
2. Be specific and actionable in your recommendations
3. Focus on patterns, not just individual words
4. Consider both what's said and what's not said
5. Look for underlying needs and emotions
6. Suggest practical communication tools

TRANSFER TRIGGERS:
- If the user needs emotional support or mentions being "overwhelmed" → transfer to emotional_vomit_dumper
- If they mention "venting" or need to "express emotions" → transfer to emotional_vomit_dumper  
- If they're ready for "solutions" or "what should I do" → transfer to solution_finder
- If they mention "conflict" or "fighting" → transfer to conflict_solver

Always provide empathetic, non-judgmental analysis focused on improving communication patterns."""
    
    def analyze_communication(self, message: str, session_id: str, user_id: str) -> CommunicationAnalysis:
        """Perform 4-card analysis on communication"""
        try:
            # Initialize cards
            red_card = self._analyze_problems(message)
            yellow_card = self._analyze_risks(message)
            green_card = self._analyze_positives(message)
            blue_card = self._generate_recommendations(message, red_card, yellow_card, green_card)
            
            # Determine overall assessment
            overall_assessment = self._generate_overall_assessment(red_card, yellow_card, green_card)
            
            # Check for transfer recommendation
            transfer_recommendation = self._check_transfer_triggers(message)
            
            # Create analysis
            analysis = CommunicationAnalysis(
                session_id=session_id,
                user_id=user_id,
                message=message,
                timestamp=datetime.now(),
                cards=[red_card, yellow_card, green_card, blue_card],
                overall_assessment=overall_assessment,
                transfer_recommendation=transfer_recommendation
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze communication: {e}")
            # Return default analysis
            return self._get_default_analysis(message, session_id, user_id)
    
    def _analyze_problems(self, message: str) -> CardAnalysis:
        """Analyze problems/issues (RED CARD)"""
        problems = []
        priority = "low"
        
        message_lower = message.lower()
        
        # Check for defensive language
        defensive_count = 0
        for pattern in self.problem_patterns["defensive_language"]:
            if pattern in message_lower:
                defensive_count += 1
                problems.append(f"Defensive language detected: '{pattern}'")
        
        # Check for blame shifting
        for pattern in self.problem_patterns["blame_shifting"]:
            if pattern in message_lower:
                problems.append(f"Blame shifting pattern: '{pattern}'")
                priority = "high"
        
        # Check for dismissive language
        for pattern in self.problem_patterns["dismissive_language"]:
            if pattern in message_lower:
                problems.append(f"Dismissive language: '{pattern}'")
                priority = "medium"
        
        # Check for emotional escalation
        for pattern in self.problem_patterns["emotional_escalation"]:
            if pattern in message_lower:
                problems.append(f"Emotional escalation indicator: '{pattern}'")
                priority = "high"
        
        # Check for communication breakdown
        for pattern in self.problem_patterns["communication_breakdown"]:
            if pattern in message_lower:
                problems.append(f"Communication breakdown signal: '{pattern}'")
                priority = "high"
        
        # Check for assumptions
        for pattern in self.problem_patterns["assumptions"]:
            if pattern in message_lower:
                problems.append(f"Assumption being made: '{pattern}'")
        
        # Analyze message structure
        if "?" not in message and len(message.split()) > 20:
            problems.append("Long statement without questions - may not invite dialogue")
        
        if message.count("!") > 2:
            problems.append("High emotional intensity - multiple exclamation marks")
            priority = "medium"
        
        if message.isupper() and len(message) > 10:
            problems.append("ALL CAPS usage suggests strong emotions or shouting")
            priority = "high"
        
        # If no problems found, provide general observation
        if not problems:
            problems.append("No immediate communication problems detected in this message")
        
        return CardAnalysis(
            card_type=AnalysisCard.RED,
            title="🔴 Problems & Issues Identified",
            points=problems,
            priority=priority
        )
    
    def _analyze_risks(self, message: str) -> CardAnalysis:
        """Analyze cautions/risks (YELLOW CARD)"""
        risks = []
        priority = "low"
        
        message_lower = message.lower()
        
        # Check for escalation warnings
        for pattern in self.risk_patterns["escalation_warning"]:
            if pattern in message_lower:
                risks.append(f"Escalation warning: '{pattern}' - conversation may be heating up")
                priority = "medium"
        
        # Check for withdrawal signs
        for pattern in self.risk_patterns["withdrawal_signs"]:
            if pattern in message_lower:
                risks.append(f"Withdrawal indicator: '{pattern}' - partner may be disengaging")
                priority = "high"
        
        # Check for misinterpretation
        for pattern in self.risk_patterns["misinterpretation"]:
            if pattern in message_lower:
                risks.append(f"Misinterpretation signal: '{pattern}' - clarity needed")
        
        # Check for emotional triggers
        for pattern in self.risk_patterns["emotional_triggers"]:
            if pattern in message_lower:
                risks.append(f"Potential trigger: '{pattern}' - may activate past issues")
                priority = "medium"
        
        # Check for avoidance
        for pattern in self.risk_patterns["avoidance"]:
            if pattern in message_lower:
                risks.append(f"Avoidance pattern: '{pattern}' - issue may remain unresolved")
        
        # Analyze emotional intensity
        emotion_words = ["angry", "frustrated", "upset", "hurt", "disappointed", "annoyed"]
        emotion_count = sum(1 for word in emotion_words if word in message_lower)
        if emotion_count > 2:
            risks.append("High emotional content - may cloud rational communication")
            priority = "medium"
        
        # Check message length vs. content
        if len(message.split()) > 50:
            risks.append("Very long message - key points may get lost")
        
        # Check for absolute statements
        absolutes = ["always", "never", "every time", "all the time", "constantly"]
        for absolute in absolutes:
            if absolute in message_lower:
                risks.append(f"Absolute statement: '{absolute}' - may trigger defensiveness")
        
        # If no risks found
        if not risks:
            risks.append("Communication appears relatively stable - continue monitoring")
        
        return CardAnalysis(
            card_type=AnalysisCard.YELLOW,
            title="🟡 Cautions & Risk Factors",
            points=risks,
            priority=priority
        )
    
    def _analyze_positives(self, message: str) -> CardAnalysis:
        """Analyze positive aspects (GREEN CARD)"""
        positives = []
        priority = "medium"
        
        message_lower = message.lower()
        
        # Check for empathy
        for pattern in self.positive_patterns["empathy"]:
            if pattern in message_lower:
                positives.append(f"Empathy shown: '{pattern}' - acknowledging partner's perspective")
                priority = "high"
        
        # Check for ownership
        for pattern in self.positive_patterns["ownership"]:
            if pattern in message_lower:
                positives.append(f"Taking ownership: '{pattern}' - using 'I' statements")
        
        # Check for collaboration
        for pattern in self.positive_patterns["collaboration"]:
            if pattern in message_lower:
                positives.append(f"Collaborative approach: '{pattern}' - seeking solutions together")
                priority = "high"
        
        # Check for validation
        for pattern in self.positive_patterns["validation"]:
            if pattern in message_lower:
                positives.append(f"Validation given: '{pattern}' - acknowledging partner's worth")
                priority = "high"
        
        # Check for openness
        for pattern in self.positive_patterns["openness"]:
            if pattern in message_lower:
                positives.append(f"Openness demonstrated: '{pattern}' - willing to learn/understand")
        
        # Check for questions (engagement)
        question_count = message.count("?")
        if question_count > 0:
            positives.append(f"Asking questions ({question_count}) - showing interest in partner's perspective")
        
        # Check for gratitude/appreciation
        appreciation_words = ["thank", "appreciate", "grateful", "glad", "happy"]
        for word in appreciation_words:
            if word in message_lower:
                positives.append(f"Expressing appreciation: '{word}' - building positive connection")
                break
        
        # Check for solution focus
        solution_words = ["solve", "fix", "work on", "improve", "better", "help"]
        for word in solution_words:
            if word in message_lower:
                positives.append(f"Solution-focused language: '{word}' - oriented toward improvement")
                break
        
        # Check for calm tone (absence of negative indicators)
        if not any(indicator in message_lower for indicator in ["!", "??", "seriously", "really??"]):
            positives.append("Calm tone maintained - no obvious emotional escalation")
        
        # If no positives found, look for neutral aspects
        if not positives:
            positives.append("Message appears neutral - opportunity to add more positive elements")
            priority = "low"
        
        return CardAnalysis(
            card_type=AnalysisCard.GREEN,
            title="🟢 Positive Communication Elements",
            points=positives,
            priority=priority
        )
    
    def _generate_recommendations(self, message: str, red_card: CardAnalysis, 
                                yellow_card: CardAnalysis, green_card: CardAnalysis) -> CardAnalysis:
        """Generate actionable recommendations (BLUE CARD)"""
        recommendations = []
        priority = "medium"
        
        # Base recommendations on problems found
        if red_card.priority == "high":
            recommendations.extend([
                "🛑 URGENT: Take a 10-minute break to cool down before continuing",
                "🗣️ Use 'I feel...' statements instead of 'You...' accusations",
                "👂 Practice active listening - repeat back what you heard before responding"
            ])
            priority = "high"
        
        # Address specific problems
        red_points = " ".join(red_card.points).lower()
        if "defensive" in red_points:
            recommendations.append("💭 When feeling defensive, ask: 'What is my partner trying to tell me?'")
        
        if "blame" in red_points:
            recommendations.append("🤝 Focus on the issue, not the person - what happened, not who's at fault")
        
        if "dismissive" in red_points:
            recommendations.append("💖 Acknowledge your partner's feelings: 'I can see this matters to you'")
        
        # Address risks
        yellow_points = " ".join(yellow_card.points).lower()
        if "escalation" in yellow_points:
            recommendations.append("⏸️ Suggest a pause: 'Let's take a moment and come back to this'")
        
        if "withdrawal" in yellow_points:
            recommendations.append("🔗 Reassure commitment: 'I want to work through this with you'")
        
        if "misinterpretation" in yellow_points:
            recommendations.append("🔍 Clarify understanding: 'Let me make sure I understand...'")
        
        # Build on positives
        if green_card.priority in ["medium", "high"]:
            recommendations.append("✨ Continue using the positive communication patterns you're already showing")
        
        # General recommendations based on message analysis
        message_lower = message.lower()
        
        if "?" not in message:
            recommendations.append("❓ Add a question to invite your partner's perspective")
        
        if len(message.split()) > 30:
            recommendations.append("📝 Break long messages into smaller, digestible points")
        
        if message.count("!") > 1:
            recommendations.append("😌 Consider a calmer tone to help your partner hear your message")
        
        # Always include these core recommendations
        core_recommendations = [
            "🎯 Focus on one issue at a time rather than bringing up multiple concerns",
            "💝 Remember your shared goal: understanding each other better",
            "⏰ Choose the right time and place for important conversations"
        ]
        
        # Add core recommendations if we have space
        if len(recommendations) < 5:
            recommendations.extend(core_recommendations[:5-len(recommendations)])
        
        # If no specific recommendations, provide general guidance
        if not recommendations:
            recommendations = [
                "🗣️ Use 'I' statements to express your feelings and needs",
                "👂 Practice active listening - summarize what you heard",
                "❓ Ask open-ended questions to understand your partner's perspective",
                "⏸️ Take breaks if the conversation becomes too heated",
                "💖 Remember to acknowledge what your partner is doing well"
            ]
        
        return CardAnalysis(
            card_type=AnalysisCard.BLUE,
            title="🔵 Recommended Actions & Strategies",
            points=recommendations,
            priority=priority
        )
    
    def _generate_overall_assessment(self, red_card: CardAnalysis, yellow_card: CardAnalysis, 
                                   green_card: CardAnalysis) -> str:
        """Generate overall communication assessment"""
        
        # Determine overall risk level
        if red_card.priority == "high" or yellow_card.priority == "high":
            risk_level = "HIGH RISK"
            risk_color = "🔴"
        elif red_card.priority == "medium" or yellow_card.priority == "medium":
            risk_level = "MODERATE RISK"
            risk_color = "🟡"
        else:
            risk_level = "LOW RISK"
            risk_color = "🟢"
        
        # Count positive vs negative indicators
        positive_count = len([p for p in green_card.points if "opportunity" not in p.lower()])
        problem_count = len([p for p in red_card.points if "no immediate" not in p.lower()])
        
        if positive_count > problem_count:
            overall_tone = "Your communication shows more positive than negative patterns. Build on these strengths!"
        elif problem_count > positive_count * 2:
            overall_tone = "Several communication challenges detected. Focus on the blue card recommendations."
        else:
            overall_tone = "Mixed communication patterns observed. There's room for improvement."
        
        assessment = f"""{risk_color} **COMMUNICATION ASSESSMENT: {risk_level}**

{overall_tone}

**Summary:**
• Problems identified: {len(red_card.points)}
• Risk factors: {len(yellow_card.points)}  
• Positive elements: {len(green_card.points)}
• Recommendations provided: {len(blue_card.points) if 'blue_card' in locals() else 'N/A'}

**Next Steps:** Focus on the Blue Card recommendations to improve your communication patterns."""
        
        return assessment
    
    def _check_transfer_triggers(self, message: str) -> Optional[str]:
        """Check if message contains transfer triggers"""
        message_lower = message.lower()
        
        # Emotional vomit dumper triggers
        emotional_triggers = [
            "i need to vent", "i'm overwhelmed", "i need to express my emotions",
            "emotional dump", "i'm upset about", "i'm so angry", "i'm hurt",
            "i'm devastated", "i can't handle", "i'm breaking down"
        ]
        
        for trigger in emotional_triggers:
            if trigger in message_lower:
                return "emotional_vomit_dumper"
        
        # Solution finder triggers
        solution_triggers = [
            "what should i do", "i need help with", "how can i fix",
            "i need a plan", "what's my next step", "help me figure out"
        ]
        
        for trigger in solution_triggers:
            if trigger in message_lower:
                return "solution_finder"
        
        # Conflict solver triggers
        conflict_triggers = [
            "we're fighting", "we had an argument", "we're in conflict",
            "we can't agree", "we need mediation", "we're having problems"
        ]
        
        for trigger in conflict_triggers:
            if trigger in message_lower:
                return "conflict_solver"
        
        return None
    
    def _get_default_analysis(self, message: str, session_id: str, user_id: str) -> CommunicationAnalysis:
        """Get default analysis when main analysis fails"""
        return CommunicationAnalysis(
            session_id=session_id,
            user_id=user_id,
            message=message,
            timestamp=datetime.now(),
            cards=[
                CardAnalysis(AnalysisCard.RED, "🔴 Analysis Error", ["Unable to analyze problems at this time"], "low"),
                CardAnalysis(AnalysisCard.YELLOW, "🟡 Analysis Error", ["Unable to analyze risks at this time"], "low"),
                CardAnalysis(AnalysisCard.GREEN, "🟢 Analysis Error", ["Unable to analyze positives at this time"], "low"),
                CardAnalysis(AnalysisCard.BLUE, "🔵 General Advice", [
                    "Use 'I' statements instead of 'You' statements",
                    "Listen actively and ask clarifying questions",
                    "Take breaks if emotions run high"
                ], "medium")
            ],
            overall_assessment="⚠️ Analysis temporarily unavailable. Please try again.",
            transfer_recommendation=None
        )
    
    def format_response(self, analysis: CommunicationAnalysis) -> str:
        """Format the analysis into a readable response"""
        
        response = f"""**{self.name} Analysis** 🛡️

{analysis.overall_assessment}

---

"""
        
        # Add each card
        for card in analysis.cards:
            response += f"## {card.title}\n"
            for point in card.points:
                response += f"• {point}\n"
            response += "\n"
        
        # Add transfer recommendation if any
        if analysis.transfer_recommendation:
            response += f"---\n\n🔄 **Agent Transfer Recommended:** {analysis.transfer_recommendation}\n"
            
            transfer_messages = {
                "emotional_vomit_dumper": "It seems like you need emotional support. Let me connect you with our Emotional Vomit Dumper for a safe space to express your feelings.",
                "solution_finder": "You're ready for actionable solutions. Let me transfer you to our Solution Finder to create a concrete plan.",
                "conflict_solver": "This appears to involve relationship conflict. Our Conflict Solver specializes in mediation and resolution."
            }
            
            if analysis.transfer_recommendation in transfer_messages:
                response += f"\n{transfer_messages[analysis.transfer_recommendation]}\n"
        
        response += f"\n---\n*Analysis completed at {analysis.timestamp.strftime('%H:%M')} on {analysis.timestamp.strftime('%Y-%m-%d')}*"
        
        return response

# Global agent instance
misunderstanding_protector = MisunderstandingProtector()

# Convenience functions
def analyze_message(message: str, session_id: str, user_id: str) -> CommunicationAnalysis:
    """Analyze a message for communication patterns"""
    return misunderstanding_protector.analyze_communication(message, session_id, user_id)

def get_formatted_analysis(message: str, session_id: str, user_id: str) -> str:
    """Get formatted analysis response"""
    analysis = analyze_message(message, session_id, user_id)
    return misunderstanding_protector.format_response(analysis)

if __name__ == "__main__":
    # Test the agent
    test_messages = [
        "You never listen to me and you always interrupt!",
        "I feel hurt when our conversations get cut short. Can we find a better time to talk?",
        "Whatever, I don't care anymore. Do what you want.",
        "I understand you're busy, but I need to share something important with you.",
        "I'm so frustrated I can't even think straight right now!"
    ]
    
    print("Misunderstanding Protector Agent Test")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n**Test {i}:** '{message}'")
        analysis = analyze_message(message, f"test_session_{i}", "test_user")
        print(f"Transfer recommendation: {analysis.transfer_recommendation or 'None'}")
        print(f"Risk level: {analysis.cards[0].priority if analysis.cards else 'Unknown'}")
        print("-" * 30)
    
    print("\nAgent test completed!")