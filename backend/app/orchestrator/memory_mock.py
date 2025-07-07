"""Mock Mem0 functionality for testing without API key"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MockMem0Client:
    """Mock Mem0 client for testing memory operations"""
    
    def __init__(self):
        # Simple in-memory storage
        self.memories: Dict[str, List[Dict]] = {}
        logger.info("MockMem0Client initialized for testing")
    
    def add(self, messages: List[Dict], user_id: str, metadata: Dict = None) -> Dict:
        """Mock memory addition"""
        if user_id not in self.memories:
            self.memories[user_id] = []
        
        memory = {
            "id": f"mock-mem-{len(self.memories[user_id])}",
            "content": messages[0]["content"] if messages else "",
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        self.memories[user_id].append(memory)
        
        logger.debug(f"[MOCK] Added memory for user {user_id}: {memory['id']}")
        
        return {
            "memories": [memory]
        }
    
    def search(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """Mock memory search"""
        user_memories = self.memories.get(user_id, [])
        
        # Simple keyword matching
        query_lower = query.lower()
        matching = [
            mem for mem in user_memories 
            if query_lower in mem.get("content", "").lower()
        ]
        
        # Return last N memories if no matches
        if not matching:
            matching = user_memories[-limit:]
        
        logger.debug(f"[MOCK] Searched memories for user {user_id}, found {len(matching)} matches")
        
        return {
            "memories": matching[:limit]
        }
    
    def get_all(self, user_id: str) -> Dict:
        """Get all memories for a user"""
        return {
            "memories": self.memories.get(user_id, [])
        }


def get_mock_user_profile(user_id: str) -> Dict[str, Any]:
    """Generate mock user profile for testing"""
    return {
        "user_id": user_id,
        "name": f"Test User {user_id[-3:]}",
        "conversation_count": 5,
        "common_topics": ["komunikacja", "związek", "uczucia"],
        "relationship_status": "w związku",
        "communication_style": "bezpośredni",
        "last_session": datetime.now().isoformat()
    }


def get_mock_context(user_id: str, query: str = None) -> Dict[str, Any]:
    """Generate mock context for testing"""
    return {
        "memories": [
            {
                "id": "mock-1",
                "content": "Partner często nie słucha gdy mówię o uczuciach",
                "created": "2025-01-01T10:00:00"
            },
            {
                "id": "mock-2", 
                "content": "Mamy problemy z komunikacją od 2 lat",
                "created": "2025-01-02T15:30:00"
            },
            {
                "id": "mock-3",
                "content": "Chciałabym nauczyć się lepiej wyrażać swoje potrzeby",
                "created": "2025-01-03T09:15:00"
            }
        ],
        "profile": get_mock_user_profile(user_id),
        "mock": True
    }