"""
SQLite Conversation Repository Implementation.
Handles conversation and message persistence using SQLite.
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiosqlite

from app.core.ports.repository_port import ConversationRepositoryPort
from app.core.entities.conversation import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


class SQLiteConversationRepository(ConversationRepositoryPort):
    """
    SQLite implementation of conversation repository.
    Handles conversation and message persistence.
    """
    
    def __init__(self, db_path: str = "prompt_lab.db"):
        """
        Initialize SQLite conversation repository.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
    
    async def _ensure_initialized(self) -> None:
        """Ensure database tables are created."""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            # Create conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Create messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations (updated_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)")
            
            await db.commit()
        
        self._initialized = True
    
    async def save_conversation(self, conversation: Conversation) -> None:
        """Save or update conversation."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Insert or update conversation
                await db.execute("""
                    INSERT OR REPLACE INTO conversations 
                    (id, user_id, title, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    conversation.id,
                    conversation.user_id,
                    conversation.title,
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                    json.dumps(conversation.metadata)
                ))
                
                # Delete existing messages for this conversation
                await db.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (conversation.id,)
                )
                
                # Insert all messages
                for message in conversation.messages:
                    await db.execute("""
                        INSERT INTO messages 
                        (id, conversation_id, role, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        message.id,
                        conversation.id,
                        message.role.value,
                        message.content,
                        message.timestamp.isoformat(),
                        json.dumps(message.metadata)
                    ))
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save conversation {conversation.id}: {e}")
            raise
    
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get conversation
                async with db.execute("""
                    SELECT id, user_id, title, created_at, updated_at, metadata
                    FROM conversations WHERE id = ?
                """, (conversation_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    # Get messages for this conversation
                    messages = await self._get_messages_for_conversation(db, conversation_id)
                    
                    # Create conversation object
                    return Conversation(
                        id=row[0],
                        user_id=row[1],
                        title=row[2],
                        created_at=datetime.fromisoformat(row[3]),
                        updated_at=datetime.fromisoformat(row[4]),
                        messages=messages,
                        metadata=json.loads(row[5]) if row[5] else {}
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Conversation]:
        """Get user's conversations with pagination."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get conversations for user
                async with db.execute("""
                    SELECT id, user_id, title, created_at, updated_at, metadata
                    FROM conversations 
                    WHERE user_id = ? 
                    ORDER BY updated_at DESC 
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset)) as cursor:
                    rows = await cursor.fetchall()
                    
                    conversations = []
                    for row in rows:
                        # Get messages for each conversation
                        messages = await self._get_messages_for_conversation(db, row[0])
                        
                        conversation = Conversation(
                            id=row[0],
                            user_id=row[1],
                            title=row[2],
                            created_at=datetime.fromisoformat(row[3]),
                            updated_at=datetime.fromisoformat(row[4]),
                            messages=messages,
                            metadata=json.loads(row[5]) if row[5] else {}
                        )
                        conversations.append(conversation)
                    
                    return conversations
                    
        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation by ID."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Delete messages first (foreign key constraint)
                await db.execute(
                    "DELETE FROM messages WHERE conversation_id = ?",
                    (conversation_id,)
                )
                
                # Delete conversation
                cursor = await db.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (conversation_id,)
                )
                
                await db.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise
    
    async def search_conversations(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by content."""
        await self._ensure_initialized()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Search in conversation titles and message content
                search_pattern = f"%{query}%"
                
                async with db.execute("""
                    SELECT DISTINCT c.id, c.user_id, c.title, c.created_at, c.updated_at, c.metadata
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    WHERE c.user_id = ? 
                    AND (c.title LIKE ? OR m.content LIKE ?)
                    ORDER BY c.updated_at DESC
                    LIMIT ?
                """, (user_id, search_pattern, search_pattern, limit)) as cursor:
                    rows = await cursor.fetchall()
                    
                    conversations = []
                    for row in rows:
                        # Get messages for each conversation
                        messages = await self._get_messages_for_conversation(db, row[0])
                        
                        conversation = Conversation(
                            id=row[0],
                            user_id=row[1],
                            title=row[2],
                            created_at=datetime.fromisoformat(row[3]),
                            updated_at=datetime.fromisoformat(row[4]),
                            messages=messages,
                            metadata=json.loads(row[5]) if row[5] else {}
                        )
                        conversations.append(conversation)
                    
                    return conversations
                    
        except Exception as e:
            logger.error(f"Failed to search conversations for user {user_id}: {e}")
            raise
    
    async def _get_messages_for_conversation(
        self, 
        db: aiosqlite.Connection, 
        conversation_id: str
    ) -> List[Message]:
        """Get all messages for a conversation."""
        try:
            async with db.execute("""
                SELECT id, role, content, timestamp, metadata
                FROM messages 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
            """, (conversation_id,)) as cursor:
                rows = await cursor.fetchall()
                
                messages = []
                for row in rows:
                    message = Message(
                        id=row[0],
                        role=MessageRole(row[1]),
                        content=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        metadata=json.loads(row[4]) if row[4] else {}
                    )
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            return []
