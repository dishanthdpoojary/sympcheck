"""
Conversation state management for the medical chatbot
Handles session-based conversation tracking and state persistence
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ConversationManager:
    """
    Manages conversation states for different sessions
    """
    
    def __init__(self):
        # In-memory storage for conversation states
        # In production, this should be replaced with Redis or a database
        self.conversations: Dict[str, Dict[str, Any]] = {}
        
        # Conversation expiry time (24 hours)
        self.expiry_hours = 24
    
    def get_conversation(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation state for a session, create new if doesn't exist
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = self._create_new_conversation()
        else:
            # Check if conversation has expired
            conversation = self.conversations[session_id]
            if self._is_conversation_expired(conversation):
                self.conversations[session_id] = self._create_new_conversation()
        
        return self.conversations[session_id]
    
    def update_conversation(self, session_id: str, new_state: Dict[str, Any]) -> None:
        """
        Update conversation state for a session
        """
        self.conversations[session_id] = new_state.copy()
        self.conversations[session_id]['last_updated'] = datetime.utcnow().isoformat()
    
    def reset_conversation(self, session_id: str) -> None:
        """
        Reset conversation state for a session
        """
        self.conversations[session_id] = self._create_new_conversation()
    
    def _create_new_conversation(self) -> Dict[str, Any]:
        """
        Create a new conversation state
        """
        return {
            'question_number': 0,
            'is_complete': False,
            'initial_symptom': '',
            'answers': [],
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _is_conversation_expired(self, conversation: Dict[str, Any]) -> bool:
        """
        Check if a conversation has expired
        """
        try:
            last_updated = datetime.fromisoformat(conversation['last_updated'])
            expiry_time = last_updated + timedelta(hours=self.expiry_hours)
            return datetime.utcnow() > expiry_time
        except (KeyError, ValueError):
            # If we can't parse the date, consider it expired
            return True
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active conversation sessions (for debugging/admin purposes)
        """
        # Filter out expired conversations
        active_sessions = {}
        for session_id, conversation in self.conversations.items():
            if not self._is_conversation_expired(conversation):
                active_sessions[session_id] = conversation
        
        return active_sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions and return count of cleaned sessions
        """
        expired_sessions = []
        for session_id, conversation in self.conversations.items():
            if self._is_conversation_expired(conversation):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.conversations[session_id]
        
        return len(expired_sessions)
