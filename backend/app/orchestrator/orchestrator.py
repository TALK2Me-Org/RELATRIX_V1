"""
Main Orchestrator - Coordinates all components
"""

import logging
from typing import AsyncGenerator, Optional, Dict, Any
from datetime import datetime
import asyncio
import uuid

from .registry import AgentRegistry
from .transfer import TransferEngine
from .memory import MemoryCoordinator
from .streaming import StreamingHandler
from .models import (
    SessionState, Message, StreamChunk, 
    TransferReason, OrchestratorStatus
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator for multi-agent system"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.transfer_engine = TransferEngine(self.registry)
        self.memory = MemoryCoordinator()
        self.streaming = StreamingHandler()
        
        # Metrics
        self.start_time = datetime.now()
        self.total_transfers = 0
        self.active_sessions: Dict[str, SessionState] = {}
        
        logger.info("Orchestrator initialized")
    
    async def initialize(self):
        """Initialize all components"""
        # Load agents
        await self.registry.load_agents()
        
        # Initialize memory
        await self.memory.initialize()
        
        # Compile transfer patterns
        agents = await self.registry.get_all_agents()
        self.transfer_engine.compile_patterns(agents)
        
        logger.info("Orchestrator fully initialized")
    
    async def create_session(
        self, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        initial_agent: str = "misunderstanding_protector"
    ) -> SessionState:
        """Create new orchestrator session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check for existing session
        existing = await self.memory.load_session_state(session_id)
        if existing:
            self.active_sessions[session_id] = existing
            return existing
        
        # Create new session
        session = SessionState(
            session_id=session_id,
            user_id=user_id,
            current_agent=initial_agent,
            metadata={
                "created_by": "orchestrator",
                "version": "1.0.0"
            }
        )
        
        # Save to memory
        await self.memory.save_session_state(session)
        self.active_sessions[session_id] = session
        
        # Session created successfully
        
        logger.info(f"Created session {session_id} with agent {initial_agent}")
        return session
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Process user message and stream response
        Main entry point for chat interactions
        """
        logger.info(f"process_message: session_id={session_id}, user_id={user_id}")
        # Get or create session
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self.create_session(session_id, user_id)
        
        # Update user_id if provided
        if user_id and not session.user_id:
            session.user_id = user_id
        
        # Add user message to history
        user_msg = Message(
            role="user",
            content=message,
            metadata={"session_id": session_id}
        )
        session.add_message(user_msg)
        
        # Check for transfer triggers
        transfer_check = await self.transfer_engine.analyze_message(
            message, 
            session.current_agent,
            session
        )
        
        # Handle transfer if needed
        if transfer_check:
            target_agent, trigger, reason = transfer_check
            
            # Execute transfer
            transfer_event = await self.transfer_engine.execute_transfer(
                session,
                target_agent,
                reason,
                trigger,
                message
            )
            
            if transfer_event.success:
                self.total_transfers += 1
                
                # Get new agent
                new_agent = await self.registry.get_agent(target_agent)
                if new_agent:
                    # Send transfer notification
                    old_agent = await self.registry.get_agent(transfer_event.from_agent)
                    yield await self.streaming.generate_transfer_notification(
                        old_agent, new_agent, trigger
                    )
        
        # Get current agent
        current_agent = await self.registry.get_agent(session.current_agent)
        if not current_agent:
            yield StreamChunk(
                type="error",
                content="Agent not found",
                metadata={"agent_id": session.current_agent}
            )
            return
        
        # Get memories from Mem0 if user is logged in
        memories = []
        if session.user_id:
            memories = await self.memory.search(message, session.user_id, limit=5)
            logger.info(f"Retrieved {len(memories)} memories for user {session.user_id}")
        
        # Format messages for OpenAI API
        api_messages = [{
            "role": "system",
            "content": current_agent.system_prompt
        }]
        
        # Add memories as context if available
        if memories:
            memory_text = "Relevant user context:\n"
            for mem in memories:
                memory_content = mem.get('memory', mem.get('content', str(mem)))
                memory_text += f"- {memory_content}\n"
            api_messages.append({
                "role": "system",
                "content": memory_text
            })
        
        # Add current user message
        api_messages.append({
            "role": "user",
            "content": message
        })
        
        # Stream response
        logger.info(f"Starting OpenAI stream for session {session_id}")
        response_content = ""
        async for chunk in self.streaming.stream_response(
            current_agent,
            api_messages,
            session_id,
            on_transfer_suggestion=self._handle_transfer_suggestion
        ):
            # Accumulate response
            if chunk.type == "content":
                response_content += chunk.content
            
            # Yield chunk to caller
            yield chunk
        
        # Add assistant message to history
        if response_content:
            assistant_msg = Message(
                role="assistant",
                content=response_content,
                agent_id=current_agent.slug,
                metadata={"session_id": session_id}
            )
            session.add_message(assistant_msg)
        
        # Save session state
        await self.memory.save_session_state(session)
        
        # Save to Mem0 if user is logged in and we have both messages
        if session.user_id and response_content:
            messages_to_save = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response_content}
            ]
            memory_id = await self.memory.add(
                messages=messages_to_save,
                user_id=session.user_id,
                agent_id=current_agent.slug,
                run_id=session.session_id
            )
            if memory_id:
                logger.info(f"Saved conversation to Mem0: {memory_id}")
    
    async def _handle_transfer_suggestion(self, response: str) -> Optional[tuple]:
        """Handle transfer suggestions from agent responses"""
        # Extract suggested transfer from response
        # This is a simplified implementation
        suggestions = {
            "emotional_vomit_dumper": ["vent", "emotional support", "overwhelmed"],
            "solution_finder": ["find solutions", "action plan", "what to do"],
            "conflict_solver": ["resolve conflict", "mediation", "both partners"]
        }
        
        response_lower = response.lower()
        for agent, keywords in suggestions.items():
            if any(keyword in response_lower for keyword in keywords):
                return agent, "Agent suggested transfer"
        
        return None
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session status"""
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self.memory.load_session_state(session_id)
        
        if not session:
            return None
        
        current_agent = await self.registry.get_agent(session.current_agent)
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "current_agent": {
                "slug": current_agent.slug,
                "name": current_agent.name,
                "description": current_agent.description
            } if current_agent else None,
            "message_count": len(session.conversation_history),
            "transfer_count": len(session.transfer_history),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
    
    async def manual_transfer(
        self,
        session_id: str,
        target_agent: str,
        reason: str = "Manual transfer requested"
    ) -> Dict[str, Any]:
        """Manually transfer to a different agent"""
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self.memory.load_session_state(session_id)
        
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Execute transfer
        transfer_event = await self.transfer_engine.execute_transfer(
            session,
            target_agent,
            TransferReason.USER_REQUEST,
            "manual",
            reason
        )
        
        if transfer_event.success:
            self.total_transfers += 1
            await self.memory.save_session_state(session)
            
            return {
                "success": True,
                "from_agent": transfer_event.from_agent,
                "to_agent": transfer_event.to_agent,
                "timestamp": transfer_event.timestamp.isoformat()
            }
        else:
            return {
                "success": False,
                "error": transfer_event.error
            }
    
    async def get_status(self) -> OrchestratorStatus:
        """Get orchestrator status"""
        agents = await self.registry.get_all_agents()
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return OrchestratorStatus(
            healthy=True,
            agents_loaded=len(agents),
            active_sessions=len(self.active_sessions),
            total_transfers=self.total_transfers,
            uptime_seconds=uptime,
            last_reload=self.registry.last_loaded
        )
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload agents from database"""
        try:
            agents = await self.registry.reload_agents()
            
            # Recompile transfer patterns
            self.transfer_engine.compile_patterns(list(agents.values()))
            
            return {
                "success": True,
                "agents_loaded": len(agents),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error reloading agents: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_sessions(self, inactive_hours: int = 24):
        """Clean up inactive sessions"""
        cutoff = datetime.now().timestamp() - (inactive_hours * 3600)
        removed = 0
        
        for session_id in list(self.active_sessions.keys()):
            session = self.active_sessions[session_id]
            if session.updated_at.timestamp() < cutoff:
                del self.active_sessions[session_id]
                removed += 1
        
        if removed:
            logger.info(f"Cleaned up {removed} inactive sessions")
        
        # Also trigger Redis cleanup
        await self.memory.cleanup_old_sessions()


# Global orchestrator instance (lazy initialization)
_orchestrator = None

def get_orchestrator() -> Orchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

# For backward compatibility
orchestrator = get_orchestrator()