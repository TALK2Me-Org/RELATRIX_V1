"""
RELATRIX MCP Tools
Comprehensive tool set for the MCP server including agent management,
memory operations, session handling, and telemetry
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.types import Tool, TextContent
from transfer_protocols import (
    TransferContext, 
    get_transfer_suggestion, 
    execute_transfer,
    transfer_protocol
)
from memory_manager import (
    MemoryType,
    store_memory,
    retrieve_memories,
    get_relevant_memories,
    add_message_to_context,
    memory_manager
)
from redis_config import get_redis_client, CacheKeys, CacheTTL
from backend.app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Session information"""
    session_id: str
    user_id: str
    current_agent: str
    start_time: datetime
    last_activity: datetime
    message_count: int = 0
    transfer_count: int = 0
    total_tokens: int = 0
    status: str = "active"

@dataclass
class TelemetryEvent:
    """Telemetry event data"""
    event_id: str
    event_type: str
    timestamp: datetime
    session_id: str
    user_id: str
    agent_id: str
    data: Dict[str, Any]

class MCPTools:
    """Collection of tools for the MCP server"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.active_sessions = {}
        self.telemetry_events = []
        
        logger.info("MCP Tools initialized")
    
    # =============================================================================
    # SESSION MANAGEMENT TOOLS
    # =============================================================================
    
    def create_session_tool(self) -> Tool:
        """Create session management tool"""
        return Tool(
            name="create_session",
            description="Create a new conversation session",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User identifier"},
                    "agent_id": {"type": "string", "description": "Initial agent", "default": "misunderstanding_protector"}
                },
                "required": ["user_id"]
            }
        )
    
    async def create_session(self, user_id: str, agent_id: str = "misunderstanding_protector") -> List[TextContent]:
        """Create a new session"""
        try:
            session_id = str(uuid.uuid4())
            
            session_info = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                current_agent=agent_id,
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
            
            # Store session info
            cache_key = CacheKeys.format_key(CacheKeys.USER_SESSION, user_id=user_id)
            self.redis_client.setex(
                cache_key,
                CacheTTL.SESSION,
                json.dumps(asdict(session_info), default=str)
            )
            
            # Track in active sessions
            self.active_sessions[session_id] = session_info
            
            # Record telemetry
            await self._record_telemetry("session_created", session_id, user_id, agent_id, {
                "initial_agent": agent_id
            })
            
            logger.info(f"Session created: {session_id} for user {user_id}")
            
            return [TextContent(
                type="text",
                text=f"✅ Session created: {session_id}\n🤖 Active agent: {agent_id}"
            )]
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to create session: {str(e)}"
            )]
    
    def get_session_tool(self) -> Tool:
        """Get session info tool"""
        return Tool(
            name="get_session",
            description="Get information about a session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier"}
                },
                "required": ["session_id"]
            }
        )
    
    async def get_session(self, session_id: str) -> List[TextContent]:
        """Get session information"""
        try:
            # Check active sessions first
            if session_id in self.active_sessions:
                session_info = self.active_sessions[session_id]
                
                return [TextContent(
                    type="text",
                    text=json.dumps(asdict(session_info), indent=2, default=str)
                )]
            
            # Check Redis
            pattern = CacheKeys.USER_SESSION.replace("{user_id}", "*")
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                session_data = self.redis_client.get(key)
                if session_data:
                    session_info_dict = json.loads(session_data)
                    if session_info_dict["session_id"] == session_id:
                        return [TextContent(
                            type="text",
                            text=json.dumps(session_info_dict, indent=2)
                        )]
            
            return [TextContent(
                type="text",
                text=f"❌ Session not found: {session_id}"
            )]
            
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error getting session: {str(e)}"
            )]
    
    # =============================================================================
    # AGENT SWITCHING TOOLS
    # =============================================================================
    
    def switch_agent_tool(self) -> Tool:
        """Agent switching tool"""
        return Tool(
            name="switch_agent",
            description="Switch to a different specialized agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier"},
                    "agent_id": {"type": "string", "description": "Target agent identifier"},
                    "reason": {"type": "string", "description": "Reason for switching", "default": "Manual switch"}
                },
                "required": ["session_id", "agent_id"]
            }
        )
    
    async def switch_agent(self, session_id: str, agent_id: str, reason: str = "Manual switch") -> List[TextContent]:
        """Switch to a different agent"""
        try:
            # Get session info
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                return [TextContent(
                    type="text",
                    text=f"❌ Session not found: {session_id}"
                )]
            
            previous_agent = session_info.current_agent
            
            # Create transfer context
            transfer_context = TransferContext(
                session_id=session_id,
                user_id=session_info.user_id,
                current_agent=previous_agent,
                transfer_count=session_info.transfer_count
            )
            
            # Execute switch
            session_info.current_agent = agent_id
            session_info.transfer_count += 1
            session_info.last_activity = datetime.now()
            
            # Record telemetry
            await self._record_telemetry("agent_switched", session_id, session_info.user_id, agent_id, {
                "from_agent": previous_agent,
                "to_agent": agent_id,
                "reason": reason,
                "transfer_count": session_info.transfer_count
            })
            
            logger.info(f"Agent switched: {previous_agent} -> {agent_id} (session: {session_id})")
            
            return [TextContent(
                type="text",
                text=f"✅ Switched from {previous_agent} to {agent_id}\n📝 Reason: {reason}"
            )]
            
        except Exception as e:
            logger.error(f"Failed to switch agent: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to switch agent: {str(e)}"
            )]
    
    def analyze_transfer_tool(self) -> Tool:
        """Transfer analysis tool"""
        return Tool(
            name="analyze_transfer",
            description="Analyze message for potential agent transfers",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to analyze"},
                    "session_id": {"type": "string", "description": "Session identifier"},
                    "current_agent": {"type": "string", "description": "Current agent"}
                },
                "required": ["message", "session_id", "current_agent"]
            }
        )
    
    async def analyze_transfer(self, message: str, session_id: str, current_agent: str) -> List[TextContent]:
        """Analyze message for transfer opportunities"""
        try:
            # Get session info
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                return [TextContent(
                    type="text",
                    text=f"❌ Session not found: {session_id}"
                )]
            
            # Create transfer context
            transfer_context = TransferContext(
                session_id=session_id,
                user_id=session_info.user_id,
                current_agent=current_agent,
                transfer_count=session_info.transfer_count
            )
            
            # Get transfer suggestion
            suggestion = get_transfer_suggestion(message, transfer_context)
            
            if suggestion:
                return [TextContent(
                    type="text",
                    text=json.dumps(suggestion, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text="ℹ️ No transfer suggested for this message"
                )]
                
        except Exception as e:
            logger.error(f"Failed to analyze transfer: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to analyze transfer: {str(e)}"
            )]
    
    # =============================================================================
    # MEMORY MANAGEMENT TOOLS
    # =============================================================================
    
    def store_memory_tool(self) -> Tool:
        """Memory storage tool"""
        return Tool(
            name="store_memory",
            description="Store information in memory system",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to store"},
                    "memory_type": {"type": "string", "description": "Type of memory", "enum": [
                        "conversation", "relationship_pattern", "communication_style",
                        "emotional_state", "conflict_history", "solution_history",
                        "preference", "context"
                    ]},
                    "user_id": {"type": "string", "description": "User identifier"},
                    "session_id": {"type": "string", "description": "Session identifier"},
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Memory tags"},
                    "metadata": {"type": "object", "description": "Additional metadata"}
                },
                "required": ["content", "memory_type", "user_id", "session_id", "agent_id"]
            }
        )
    
    async def store_memory_content(self, content: str, memory_type: str, user_id: str, 
                                  session_id: str, agent_id: str, tags: List[str] = None, 
                                  metadata: Dict[str, Any] = None) -> List[TextContent]:
        """Store content in memory"""
        try:
            # Convert string to MemoryType enum
            memory_type_enum = MemoryType(memory_type)
            
            # Store memory
            memory_id = await store_memory(
                content=content,
                memory_type=memory_type_enum,
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            # Record telemetry
            await self._record_telemetry("memory_stored", session_id, user_id, agent_id, {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "content_length": len(content)
            })
            
            return [TextContent(
                type="text",
                text=f"✅ Memory stored with ID: {memory_id}"
            )]
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to store memory: {str(e)}"
            )]
    
    def retrieve_memories_tool(self) -> Tool:
        """Memory retrieval tool"""
        return Tool(
            name="retrieve_memories",
            description="Retrieve stored memories",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User identifier"},
                    "session_id": {"type": "string", "description": "Session identifier (optional)"},
                    "memory_type": {"type": "string", "description": "Memory type filter (optional)"},
                    "limit": {"type": "integer", "description": "Maximum number of memories", "default": 10}
                },
                "required": ["user_id"]
            }
        )
    
    async def retrieve_memories_content(self, user_id: str, session_id: str = None, 
                                       memory_type: str = None, limit: int = 10) -> List[TextContent]:
        """Retrieve memories"""
        try:
            # Convert string to MemoryType enum if provided
            memory_type_enum = MemoryType(memory_type) if memory_type else None
            
            # Retrieve memories
            memories = await retrieve_memories(user_id, session_id, memory_type_enum, limit)
            
            if not memories:
                return [TextContent(
                    type="text",
                    text="ℹ️ No memories found"
                )]
            
            # Format memories
            formatted_memories = []
            for memory in memories:
                formatted_memories.append({
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.memory_type.value,
                    "timestamp": memory.timestamp.isoformat(),
                    "agent": memory.agent_id,
                    "importance": memory.importance,
                    "tags": memory.tags
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(formatted_memories, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to retrieve memories: {str(e)}"
            )]
    
    def search_memories_tool(self) -> Tool:
        """Memory search tool"""
        return Tool(
            name="search_memories",
            description="Search for relevant memories",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "user_id": {"type": "string", "description": "User identifier"},
                    "session_id": {"type": "string", "description": "Session identifier (optional)"},
                    "limit": {"type": "integer", "description": "Maximum results", "default": 5}
                },
                "required": ["query", "user_id"]
            }
        )
    
    async def search_memories(self, query: str, user_id: str, session_id: str = None, 
                             limit: int = 5) -> List[TextContent]:
        """Search for relevant memories"""
        try:
            # Search memories
            relevant_memories = await get_relevant_memories(query, user_id, session_id, limit)
            
            if not relevant_memories:
                return [TextContent(
                    type="text",
                    text=f"ℹ️ No relevant memories found for: '{query}'"
                )]
            
            # Format results
            results = []
            for memory in relevant_memories:
                results.append({
                    "content": memory.content,
                    "type": memory.memory_type.value,
                    "relevance": memory.importance,
                    "timestamp": memory.timestamp.isoformat()
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to search memories: {str(e)}"
            )]
    
    # =============================================================================
    # CONVERSATION CONTEXT TOOLS
    # =============================================================================
    
    def add_message_tool(self) -> Tool:
        """Add message to context tool"""
        return Tool(
            name="add_message",
            description="Add message to conversation context",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier"},
                    "user_id": {"type": "string", "description": "User identifier"},
                    "role": {"type": "string", "description": "Message role (user/assistant)"},
                    "content": {"type": "string", "description": "Message content"},
                    "importance": {"type": "number", "description": "Importance score (1.0-3.0)", "default": 1.0}
                },
                "required": ["session_id", "user_id", "role", "content"]
            }
        )
    
    async def add_message(self, session_id: str, user_id: str, role: str, content: str, 
                         importance: float = 1.0) -> List[TextContent]:
        """Add message to conversation context"""
        try:
            # Add to context
            await add_message_to_context(session_id, user_id, role, content, importance)
            
            # Update session activity
            if session_id in self.active_sessions:
                session_info = self.active_sessions[session_id]
                session_info.message_count += 1
                session_info.last_activity = datetime.now()
            
            # Record telemetry
            await self._record_telemetry("message_added", session_id, user_id, "system", {
                "role": role,
                "content_length": len(content),
                "importance": importance
            })
            
            return [TextContent(
                type="text",
                text=f"✅ Message added to context (importance: {importance})"
            )]
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to add message: {str(e)}"
            )]
    
    def get_context_tool(self) -> Tool:
        """Get conversation context tool"""
        return Tool(
            name="get_context",
            description="Get conversation context for session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier"},
                    "user_id": {"type": "string", "description": "User identifier"}
                },
                "required": ["session_id", "user_id"]
            }
        )
    
    async def get_context(self, session_id: str, user_id: str) -> List[TextContent]:
        """Get conversation context"""
        try:
            # Get context from memory manager
            context = await memory_manager.get_conversation_context(session_id, user_id)
            
            context_info = {
                "session_id": context.session_id,
                "current_agent": context.current_agent,
                "message_count": len(context.messages),
                "token_count": context.token_count,
                "has_compressed_context": context.compressed_context is not None,
                "last_compression": context.last_compression.isoformat() if context.last_compression else None,
                "recent_messages": context.messages[-5:]  # Last 5 messages
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(context_info, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to get context: {str(e)}"
            )]
    
    # =============================================================================
    # TELEMETRY TOOLS
    # =============================================================================
    
    def record_telemetry_tool(self) -> Tool:
        """Record telemetry event tool"""
        return Tool(
            name="record_telemetry",
            description="Record a telemetry event",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {"type": "string", "description": "Type of event"},
                    "session_id": {"type": "string", "description": "Session identifier"},
                    "user_id": {"type": "string", "description": "User identifier"},
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "data": {"type": "object", "description": "Event data"}
                },
                "required": ["event_type", "session_id", "user_id", "agent_id"]
            }
        )
    
    async def _record_telemetry(self, event_type: str, session_id: str, user_id: str, 
                               agent_id: str, data: Dict[str, Any] = None) -> str:
        """Record telemetry event"""
        try:
            event_id = str(uuid.uuid4())
            
            telemetry_event = TelemetryEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(),
                session_id=session_id,
                user_id=user_id,
                agent_id=agent_id,
                data=data or {}
            )
            
            # Store in memory
            self.telemetry_events.append(telemetry_event)
            
            # Store in Redis
            cache_key = f"telemetry:{datetime.now().strftime('%Y-%m-%d')}"
            existing_events = self.redis_client.get(cache_key)
            events = json.loads(existing_events) if existing_events else []
            events.append(asdict(telemetry_event, dict_factory=lambda x: {k: v.isoformat() if isinstance(v, datetime) else v for k, v in x}))
            
            self.redis_client.setex(cache_key, CacheTTL.COSTS, json.dumps(events))
            
            logger.debug(f"Telemetry recorded: {event_type} ({event_id})")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to record telemetry: {e}")
            return ""
    
    def get_telemetry_tool(self) -> Tool:
        """Get telemetry data tool"""
        return Tool(
            name="get_telemetry",
            description="Get telemetry data",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session identifier (optional)"},
                    "event_type": {"type": "string", "description": "Event type filter (optional)"},
                    "limit": {"type": "integer", "description": "Maximum events", "default": 50}
                }
            }
        )
    
    async def get_telemetry(self, session_id: str = None, event_type: str = None, 
                           limit: int = 50) -> List[TextContent]:
        """Get telemetry data"""
        try:
            # Filter events
            filtered_events = []
            for event in self.telemetry_events[-limit:]:
                if session_id and event.session_id != session_id:
                    continue
                if event_type and event.event_type != event_type:
                    continue
                filtered_events.append(event)
            
            # Format events
            formatted_events = []
            for event in filtered_events:
                formatted_events.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "session_id": event.session_id,
                    "user_id": event.user_id,
                    "agent_id": event.agent_id,
                    "data": event.data
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(formatted_events, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Failed to get telemetry: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Failed to get telemetry: {str(e)}"
            )]
    
    # =============================================================================
    # UTILITY TOOLS
    # =============================================================================
    
    def health_check_tool(self) -> Tool:
        """Health check tool"""
        return Tool(
            name="health_check",
            description="Check system health",
            inputSchema={"type": "object", "properties": {}}
        )
    
    async def health_check(self) -> List[TextContent]:
        """Check system health"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "mcp_server": "healthy",
                "redis_connection": "unknown",
                "memory_manager": "unknown",
                "active_sessions": len(self.active_sessions),
                "telemetry_events": len(self.telemetry_events)
            }
            
            # Test Redis connection
            try:
                self.redis_client.ping()
                health_status["redis_connection"] = "healthy"
            except:
                health_status["redis_connection"] = "error"
            
            # Test memory manager
            try:
                test_summary = await memory_manager.get_memory_summary("health_check_user")
                health_status["memory_manager"] = "healthy"
            except:
                health_status["memory_manager"] = "error"
            
            return [TextContent(
                type="text",
                text=json.dumps(health_status, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Health check failed: {str(e)}"
            )]
    
    def get_all_tools(self) -> List[Tool]:
        """Get all available tools"""
        return [
            self.create_session_tool(),
            self.get_session_tool(),
            self.switch_agent_tool(),
            self.analyze_transfer_tool(),
            self.store_memory_tool(),
            self.retrieve_memories_tool(),
            self.search_memories_tool(),
            self.add_message_tool(),
            self.get_context_tool(),
            self.record_telemetry_tool(),
            self.get_telemetry_tool(),
            self.health_check_tool()
        ]

# Global tools instance
mcp_tools = MCPTools()

# Tool execution mapping
TOOL_FUNCTIONS = {
    "create_session": mcp_tools.create_session,
    "get_session": mcp_tools.get_session,
    "switch_agent": mcp_tools.switch_agent,
    "analyze_transfer": mcp_tools.analyze_transfer,
    "store_memory": mcp_tools.store_memory_content,
    "retrieve_memories": mcp_tools.retrieve_memories_content,
    "search_memories": mcp_tools.search_memories,
    "add_message": mcp_tools.add_message,
    "get_context": mcp_tools.get_context,
    "record_telemetry": mcp_tools._record_telemetry,
    "get_telemetry": mcp_tools.get_telemetry,
    "health_check": mcp_tools.health_check
}

async def execute_tool(tool_name: str, **kwargs) -> List[TextContent]:
    """Execute a tool by name"""
    if tool_name not in TOOL_FUNCTIONS:
        return [TextContent(
            type="text",
            text=f"❌ Unknown tool: {tool_name}"
        )]
    
    try:
        return await TOOL_FUNCTIONS[tool_name](**kwargs)
    except Exception as e:
        logger.error(f"Tool execution failed ({tool_name}): {e}")
        return [TextContent(
            type="text",
            text=f"❌ Tool execution failed: {str(e)}"
        )]

if __name__ == "__main__":
    # Test the tools
    import asyncio
    
    async def test_tools():
        print("RELATRIX MCP Tools Test")
        print("=" * 40)
        
        # Test session creation
        result = await mcp_tools.create_session("test_user", "misunderstanding_protector")
        print(f"Session creation: {result[0].text}")
        
        # Test health check
        result = await mcp_tools.health_check()
        print(f"Health check: {result[0].text}")
        
        # Test memory storage
        result = await mcp_tools.store_memory_content(
            content="Test memory content",
            memory_type="conversation",
            user_id="test_user",
            session_id="test_session",
            agent_id="test_agent",
            tags=["test"],
            metadata={"test": True}
        )
        print(f"Memory storage: {result[0].text}")
        
        print("Tools test completed")
    
    asyncio.run(test_tools())