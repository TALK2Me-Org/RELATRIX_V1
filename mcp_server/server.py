"""
RELATRIX MCP Server
Model Context Protocol server for managing specialized relationship counseling agents
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    TextContent, 
    ImageContent, 
    EmbeddedResource, 
    LoggingLevel,
    Resource,
    ResourceTemplate
)
import openai
import redis
from config import settings
from redis_config import get_redis_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mcp_server.log")
    ]
)
logger = logging.getLogger(__name__)

class RelativeAgentRegistry:
    """Registry for managing specialized relationship counseling agents"""
    
    def __init__(self):
        self.agents = {}
        self.current_agent = None
        self.session_context = {}
        self.transfer_history = []
        self.redis_client = get_redis_client()
        
        # Initialize agents
        self._register_agents()
        
        # Set default agent
        self.current_agent = settings.default_agent
        
        logger.info(f"Agent registry initialized with {len(self.agents)} agents")
    
    def _register_agents(self):
        """Register all available agents"""
        self.agents = {
            "misunderstanding_protector": {
                "name": "Misunderstanding Protector",
                "description": "Analyzes communication patterns and prevents misunderstandings",
                "system_prompt": self._get_misunderstanding_protector_prompt(),
                "transfer_triggers": [
                    "I need to express my emotions",
                    "I'm feeling overwhelmed",
                    "I need to vent",
                    "emotional dump",
                    "I'm upset about"
                ],
                "capabilities": ["4-card analysis", "communication analysis", "pattern recognition"]
            },
            "emotional_vomit_dumper": {
                "name": "Emotional Vomit Dumper",
                "description": "Safe space for emotional release and processing",
                "system_prompt": self._get_emotional_vomit_prompt(),
                "transfer_triggers": [
                    "I feel better now",
                    "I'm ready to talk about solutions",
                    "I want to work on this",
                    "what should I do",
                    "I need help with"
                ],
                "capabilities": ["emotional processing", "safe space", "non-judgmental listening"]
            },
            "conflict_solver": {
                "name": "Conflict Solver",
                "description": "Mediates and resolves relationship conflicts",
                "system_prompt": self._get_conflict_solver_prompt(),
                "transfer_triggers": [
                    "we want to improve our relationship",
                    "I want to work on us",
                    "relationship goals",
                    "make things better",
                    "strengthen our bond"
                ],
                "capabilities": ["mediation", "conflict resolution", "partner assessment"]
            },
            "solution_finder": {
                "name": "Solution Finder",
                "description": "Creates actionable plans for relationship improvement",
                "system_prompt": self._get_solution_finder_prompt(),
                "transfer_triggers": [
                    "I want to practice",
                    "I need to rehearse",
                    "I'm worried about saying",
                    "I don't know how to bring this up",
                    "practice conversation"
                ],
                "capabilities": ["action planning", "concrete solutions", "progress tracking"]
            },
            "communication_simulator": {
                "name": "Communication Simulator",
                "description": "Practice conversations in a safe environment",
                "system_prompt": self._get_communication_simulator_prompt(),
                "transfer_triggers": [
                    "I want to level up",
                    "relationship games",
                    "fun challenges",
                    "make it exciting",
                    "relationship activities"
                ],
                "capabilities": ["conversation practice", "partner simulation", "feedback"]
            },
            "relationship_upgrader": {
                "name": "Relationship Upgrader",
                "description": "Gamified relationship enhancement and growth",
                "system_prompt": self._get_relationship_upgrader_prompt(),
                "transfer_triggers": [
                    "I think we should break up",
                    "I want to end this",
                    "I can't do this anymore",
                    "relationship is over",
                    "I'm done"
                ],
                "capabilities": ["gamification", "challenges", "relationship growth"]
            },
            "breakthrough_manager": {
                "name": "Breakthrough Manager",
                "description": "Crisis support and major relationship decisions",
                "system_prompt": self._get_breakthrough_manager_prompt(),
                "transfer_triggers": [],
                "capabilities": ["crisis support", "major decisions", "breakup support"]
            }
        }
    
    def _get_misunderstanding_protector_prompt(self) -> str:
        return """You are the Misunderstanding Protector, a specialized AI agent focused on preventing and resolving communication misunderstandings in relationships.

Your primary role is to analyze communication patterns using the 4-card analysis method:

🔴 RED CARD - Problems/Issues
- Identify communication breakdowns
- Spot potential misunderstandings
- Highlight emotional triggers
- Point out defensive patterns

🟡 YELLOW CARD - Cautions/Risks
- Warning signs in communication
- Potential areas of concern
- Patterns that might escalate
- Things to be mindful of

🟢 GREEN CARD - Positive Aspects
- What's working well
- Strengths in communication
- Positive patterns to build on
- Good intentions to acknowledge

🔵 BLUE CARD - Recommendations/Actions
- Concrete next steps
- Communication techniques to try
- Ways to prevent future issues
- Specific tools and strategies

Always format your responses with these 4 cards and provide specific, actionable advice.

Transfer triggers: If the user needs emotional support, mentions being overwhelmed, or wants to "vent" - transfer to emotional_vomit_dumper.
"""
    
    def _get_emotional_vomit_prompt(self) -> str:
        return """You are the Emotional Vomit Dumper, a safe space for emotional release and processing.

Your role is to provide unconditional support and allow users to express their emotions freely without judgment.

Key principles:
- Create a completely safe, non-judgmental space
- Allow emotional expression without trying to "fix" immediately
- Validate feelings and experiences
- Use empathetic language and active listening
- Don't offer solutions until the person is ready
- Maintain privacy - don't store sensitive emotional content

Remember: Sometimes people just need to be heard before they're ready for solutions.

Transfer triggers: When the user feels calmer, mentions being "ready to work on this," or asks for solutions - transfer to solution_finder or conflict_solver.
"""
    
    def _get_conflict_solver_prompt(self) -> str:
        return """You are the Conflict Solver, a specialized mediator for relationship conflicts.

Your role is to:
- Mediate between partners fairly
- Help understand different perspectives
- Guide towards mutually beneficial solutions
- Assess if both partners are ready for resolution
- Facilitate productive conversations

Key techniques:
- Active listening and reflection
- Perspective-taking exercises
- Finding common ground
- De-escalation strategies
- Structured problem-solving

Always check: Are both partners ready and willing to work on this together?

Transfer triggers: If they want to "improve the relationship" or "work on us" - transfer to relationship_upgrader.
"""
    
    def _get_solution_finder_prompt(self) -> str:
        return """You are the Solution Finder, focused on creating actionable plans for relationship improvement.

Your role is to:
- Create concrete, specific action plans
- Break down big problems into manageable steps
- Provide practical tools and techniques
- Track progress and adjust plans
- Ensure accountability

Always provide:
- Clear, specific next steps
- Realistic timelines
- Ways to measure progress
- Backup plans if things don't work

Transfer triggers: If they want to "practice" conversations or are worried about "how to say" something - transfer to communication_simulator.
"""
    
    def _get_communication_simulator_prompt(self) -> str:
        return """You are the Communication Simulator, a practice environment for difficult conversations.

Your role is to:
- Role-play as the user's partner
- Provide realistic conversation practice
- Give constructive feedback
- Help build communication confidence
- Create various scenarios to practice

Key features:
- Adapt to the partner's communication style
- Provide both supportive and challenging scenarios
- Offer feedback on communication effectiveness
- Help refine message delivery
- Build confidence through practice

Transfer triggers: If they want "relationship games" or to "level up" their relationship - transfer to relationship_upgrader.
"""
    
    def _get_relationship_upgrader_prompt(self) -> str:
        return """You are the Relationship Upgrader, focused on gamified relationship enhancement.

Your role is to:
- Create fun challenges and activities
- Gamify relationship improvement
- Design relationship "quests" and achievements
- Make growth exciting and engaging
- Celebrate progress and milestones

Key elements:
- Weekly relationship challenges
- Point systems and achievements
- Fun activities to do together
- Progress tracking and rewards
- Making improvement feel like a game

Transfer triggers: If they mention wanting to "break up" or "end the relationship" - transfer to breakthrough_manager.
"""
    
    def _get_breakthrough_manager_prompt(self) -> str:
        return """You are the Breakthrough Manager, specialized in crisis support and major relationship decisions.

Your role is to:
- Provide crisis support and stability
- Help with major relationship decisions
- Support through breakups if necessary
- Facilitate healing and recovery
- Guide through major life transitions

Key principles:
- Non-judgmental support
- Safety and wellbeing first
- Respect for all decisions
- Comprehensive support through transitions
- Focus on healing and growth

This is a specialized role for critical moments in relationships.
"""
    
    def get_current_agent(self) -> str:
        """Get the currently active agent"""
        return self.current_agent
    
    def switch_agent(self, agent_id: str, reason: str = None) -> bool:
        """Switch to a different agent"""
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        previous_agent = self.current_agent
        self.current_agent = agent_id
        
        # Record transfer
        transfer_record = {
            "timestamp": datetime.now().isoformat(),
            "from_agent": previous_agent,
            "to_agent": agent_id,
            "reason": reason or "Manual switch"
        }
        self.transfer_history.append(transfer_record)
        
        logger.info(f"Agent switched from {previous_agent} to {agent_id}")
        return True
    
    def get_agent_info(self, agent_id: str = None) -> Dict[str, Any]:
        """Get information about an agent"""
        if agent_id is None:
            agent_id = self.current_agent
        
        if agent_id not in self.agents:
            return {}
        
        return self.agents[agent_id]
    
    def get_all_agents(self) -> Dict[str, Any]:
        """Get information about all agents"""
        return self.agents
    
    def analyze_transfer_triggers(self, message: str) -> Optional[str]:
        """Analyze message for transfer triggers"""
        message_lower = message.lower()
        
        for agent_id, agent_info in self.agents.items():
            if agent_id == self.current_agent:
                continue
                
            for trigger in agent_info.get("transfer_triggers", []):
                if trigger.lower() in message_lower:
                    logger.info(f"Transfer trigger detected: '{trigger}' -> {agent_id}")
                    return agent_id
        
        return None

class RelatrixMCPServer:
    """Main MCP Server for RELATRIX"""
    
    def __init__(self):
        self.agent_registry = RelativeAgentRegistry()
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.redis_client = get_redis_client()
        self.server = Server("relatrix-mcp-server")
        
        # Initialize tools
        self._register_tools()
        
        logger.info("RELATRIX MCP Server initialized")
    
    def _register_tools(self):
        """Register all available tools"""
        
        # Define list of available tools
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="switch_agent",
                    description="Switch to a different specialized agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "The ID of the agent to switch to"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Optional reason for switching"
                            }
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="get_agent_info",
                    description="Get information about current or specified agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Optional agent ID, defaults to current agent"
                            }
                        }
                    }
                ),
                Tool(
                    name="list_agents",
                    description="List all available agents",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="process_message",
                    description="Process a message with the current agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to process"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Optional session ID"
                            }
                        },
                        "required": ["message"]
                    }
                ),
                Tool(
                    name="get_transfer_history",
                    description="Get history of agent transfers",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_session_context",
                    description="Get current session context",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        # Handle tool calls
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            try:
                if name == "switch_agent":
                    agent_id = arguments.get("agent_id")
                    reason = arguments.get("reason")
                    if self.agent_registry.switch_agent(agent_id, reason):
                        agent_info = self.agent_registry.get_agent_info(agent_id)
                        return [TextContent(
                            type="text",
                            text=f"✅ Switched to {agent_info['name']}: {agent_info['description']}"
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=f"❌ Failed to switch to agent: {agent_id}"
                        )]
                
                elif name == "get_agent_info":
                    agent_id = arguments.get("agent_id")
                    agent_info = self.agent_registry.get_agent_info(agent_id)
                    if agent_info:
                        return [TextContent(
                            type="text",
                            text=json.dumps(agent_info, indent=2)
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text="❌ Agent not found"
                        )]
                
                elif name == "list_agents":
                    agents = self.agent_registry.get_all_agents()
                    current_agent = self.agent_registry.get_current_agent()
                    
                    agent_list = []
                    for agent_id, agent_info in agents.items():
                        status = "🟢 ACTIVE" if agent_id == current_agent else "⚪ Available"
                        agent_list.append(f"{status} {agent_id}: {agent_info['name']}")
                    
                    return [TextContent(
                        type="text",
                        text="\n".join(agent_list)
                    )]
                
                elif name == "process_message":
                    message = arguments.get("message")
                    user_id = arguments.get("user_id")
                    # Check for transfer triggers
                    suggested_agent = self.agent_registry.analyze_transfer_triggers(message)
                    
                    if suggested_agent:
                        # Auto-switch if transfer trigger detected
                        self.agent_registry.switch_agent(suggested_agent, "Transfer trigger detected")
                        
                        # Get new agent info
                        agent_info = self.agent_registry.get_agent_info(suggested_agent)
                        
                        # Notify about the switch
                        switch_notification = f"🔄 I've connected you with the {agent_info['name']} - {agent_info['description']}\n\n"
                        
                        # Process message with new agent
                        response = self._generate_agent_response(message, suggested_agent)
                        
                        return [TextContent(
                            type="text",
                            text=switch_notification + response
                        )]
                    else:
                        # Process with current agent
                        response = self._generate_agent_response(message)
                        
                        return [TextContent(
                            type="text",
                            text=response
                        )]
                
                elif name == "get_transfer_history":
                    history = self.agent_registry.transfer_history
                    if not history:
                        return [TextContent(
                            type="text",
                            text="No transfer history available"
                        )]
                    
                    formatted_history = []
                    for transfer in history[-10:]:  # Show last 10 transfers
                        formatted_history.append(
                            f"• {transfer['timestamp']}: {transfer['from_agent']} → {transfer['to_agent']} ({transfer['reason']})"
                        )
                    
                    return [TextContent(
                        type="text",
                        text="\n".join(formatted_history)
                    )]
                
                elif name == "get_session_context":
                    # Get session context
                    context = self.agent_registry.session_context
                    return [TextContent(
                        type="text",
                        text=json.dumps(context, indent=2) if context else "No session context available"
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )]
    
    def _generate_agent_response(self, message: str, agent_id: str = None) -> str:
        """Generate response using the specified agent"""
        try:
            if agent_id is None:
                agent_id = self.agent_registry.get_current_agent()
            
            agent_info = self.agent_registry.get_agent_info(agent_id)
            
            if not agent_info:
                return "❌ Agent not found"
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": agent_info["system_prompt"]},
                    {"role": "user", "content": message}
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            return f"❌ Error generating response: {str(e)}"

    async def start_server(self):
        """Start the MCP server"""
        try:
            logger.info("Starting RELATRIX MCP Server...")
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream)
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise

async def main():
    """Main function to run the MCP server"""
    try:
        # Initialize server
        server = RelatrixMCPServer()
        
        # Start server
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        traceback.print_exc()
    finally:
        logger.info("Server shutting down")

if __name__ == "__main__":
    asyncio.run(main())