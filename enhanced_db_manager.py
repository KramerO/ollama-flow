"""
Enhanced Database Manager with Redis for better performance and stability
Replaces SQLite with Redis for faster, more reliable message handling
"""
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import queue
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

@dataclass
class Message:
    """Enhanced message structure with better type safety"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: str
    content: str
    request_id: Optional[str] = None
    timestamp: float = None
    status: str = "pending"
    retry_count: int = 0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.id is None:
            self.id = str(uuid.uuid4())

class EnhancedDBManager:
    """
    Enhanced database manager with Redis backend and fallback to in-memory storage
    Provides better performance, stability, and error handling
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0, use_fallback=True):
        self.use_redis = False
        self.redis_client = None
        self.fallback_storage = {}  # In-memory fallback
        self.message_queue = queue.Queue()
        self.lock = threading.RLock()
        self.use_fallback = use_fallback
        self._setup_logging()
        
        # Try to connect to Redis first
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                self.logger.info("✅ Connected to Redis for enhanced performance")
            except Exception as e:
                self.logger.warning(f"⚠️ Redis connection failed: {e}")
                if not use_fallback:
                    raise
        
        if not self.use_redis:
            self.logger.info("🔄 Using high-performance in-memory storage as fallback")
            self._init_fallback_storage()
    
    def _setup_logging(self):
        """Setup logging for database operations"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _init_fallback_storage(self):
        """Initialize in-memory storage structures"""
        with self.lock:
            self.fallback_storage = {
                'messages': {},
                'pending_by_receiver': {},
                'processed_messages': set(),
                'stats': {
                    'total_messages': 0,
                    'processed_messages': 0,
                    'failed_messages': 0
                }
            }
    
    def _serialize_message(self, message: Message) -> str:
        """Safely serialize message to JSON"""
        try:
            return json.dumps(asdict(message), ensure_ascii=False, separators=(',', ':'))
        except Exception as e:
            self.logger.error(f"❌ Message serialization failed: {e}")
            # Create safe fallback
            safe_message = {
                'id': message.id,
                'sender_id': str(message.sender_id),
                'receiver_id': str(message.receiver_id),
                'message_type': str(message.message_type),
                'content': str(message.content)[:1000],  # Truncate if too long
                'request_id': str(message.request_id) if message.request_id else None,
                'timestamp': message.timestamp,
                'status': message.status,
                'retry_count': message.retry_count
            }
            return json.dumps(safe_message, ensure_ascii=False, separators=(',', ':'))
    
    def _deserialize_message(self, data: str) -> Message:
        """Safely deserialize message from JSON"""
        try:
            msg_dict = json.loads(data)
            return Message(**msg_dict)
        except Exception as e:
            self.logger.error(f"❌ Message deserialization failed: {e}")
            raise ValueError(f"Invalid message format: {e}")
    
    def insert_message(self, sender_id: str, receiver_id: str, message_type: str, 
                      content: str, request_id: str = None) -> str:
        """
        Insert message with enhanced error handling and type validation
        Returns message ID for tracking
        """
        try:
            # Validate input parameters
            if not all([sender_id, receiver_id, message_type]):
                raise ValueError("sender_id, receiver_id, and message_type are required")
            
            # Create message with validation
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=str(sender_id),
                receiver_id=str(receiver_id),
                message_type=str(message_type),
                content=str(content) if content is not None else "",
                request_id=str(request_id) if request_id else None
            )
            
            if self.use_redis:
                return self._insert_message_redis(message)
            else:
                return self._insert_message_fallback(message)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to insert message: {e}")
            raise
    
    def _insert_message_redis(self, message: Message) -> str:
        """Insert message using Redis backend"""
        try:
            pipe = self.redis_client.pipeline()
            serialized = self._serialize_message(message)
            
            # Store message
            pipe.hset(f"msg:{message.id}", mapping={
                'data': serialized,
                'status': message.status,
                'timestamp': message.timestamp
            })
            
            # Add to receiver's pending queue
            pipe.lpush(f"pending:{message.receiver_id}", message.id)
            
            # Update stats
            pipe.incr("stats:total_messages")
            
            pipe.execute()
            return message.id
            
        except Exception as e:
            self.logger.error(f"❌ Redis insert failed: {e}")
            if self.use_fallback:
                return self._insert_message_fallback(message)
            raise
    
    def _insert_message_fallback(self, message: Message) -> str:
        """Insert message using in-memory fallback"""
        with self.lock:
            # Store message
            self.fallback_storage['messages'][message.id] = message
            
            # Add to receiver's pending queue
            if message.receiver_id not in self.fallback_storage['pending_by_receiver']:
                self.fallback_storage['pending_by_receiver'][message.receiver_id] = []
            self.fallback_storage['pending_by_receiver'][message.receiver_id].append(message.id)
            
            # Update stats
            self.fallback_storage['stats']['total_messages'] += 1
            
            return message.id
    
    def get_pending_messages(self, receiver_id: str) -> List[Dict[str, Any]]:
        """Get pending messages for receiver with enhanced error handling"""
        try:
            if self.use_redis:
                return self._get_pending_messages_redis(receiver_id)
            else:
                return self._get_pending_messages_fallback(receiver_id)
        except Exception as e:
            self.logger.error(f"❌ Failed to get pending messages for {receiver_id}: {e}")
            return []
    
    def _get_pending_messages_redis(self, receiver_id: str) -> List[Dict[str, Any]]:
        """Get pending messages using Redis backend"""
        try:
            message_ids = self.redis_client.lrange(f"pending:{receiver_id}", 0, -1)
            messages = []
            
            for msg_id in message_ids:
                try:
                    msg_data = self.redis_client.hget(f"msg:{msg_id}", 'data')
                    if msg_data:
                        message = self._deserialize_message(msg_data)
                        if message.status == 'pending':
                            messages.append(asdict(message))
                except Exception as e:
                    self.logger.warning(f"⚠️ Skipping corrupted message {msg_id}: {e}")
                    continue
            
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ Redis get pending failed: {e}")
            if self.use_fallback:
                return self._get_pending_messages_fallback(receiver_id)
            raise
    
    def _get_pending_messages_fallback(self, receiver_id: str) -> List[Dict[str, Any]]:
        """Get pending messages using in-memory fallback"""
        with self.lock:
            messages = []
            pending_ids = self.fallback_storage['pending_by_receiver'].get(receiver_id, [])
            
            for msg_id in pending_ids:
                message = self.fallback_storage['messages'].get(msg_id)
                if message and message.status == 'pending':
                    messages.append(asdict(message))
            
            return messages
    
    def mark_message_as_processed(self, message_id: str) -> bool:
        """Mark message as processed with error handling"""
        try:
            if self.use_redis:
                return self._mark_processed_redis(message_id)
            else:
                return self._mark_processed_fallback(message_id)
        except Exception as e:
            self.logger.error(f"❌ Failed to mark message {message_id} as processed: {e}")
            return False
    
    def _mark_processed_redis(self, message_id: str) -> bool:
        """Mark message as processed using Redis"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.hset(f"msg:{message_id}", 'status', 'processed')
            pipe.incr("stats:processed_messages")
            
            # Remove from all pending queues (cleanup)
            for key in self.redis_client.scan_iter(match="pending:*"):
                pipe.lrem(key, 0, message_id)
            
            pipe.execute()
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Redis mark processed failed: {e}")
            if self.use_fallback:
                return self._mark_processed_fallback(message_id)
            return False
    
    def _mark_processed_fallback(self, message_id: str) -> bool:
        """Mark message as processed using in-memory fallback"""
        with self.lock:
            message = self.fallback_storage['messages'].get(message_id)
            if message:
                message.status = 'processed'
                self.fallback_storage['processed_messages'].add(message_id)
                self.fallback_storage['stats']['processed_messages'] += 1
                
                # Remove from pending queues
                for receiver_id in self.fallback_storage['pending_by_receiver']:
                    if message_id in self.fallback_storage['pending_by_receiver'][receiver_id]:
                        self.fallback_storage['pending_by_receiver'][receiver_id].remove(message_id)
                
                return True
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if self.use_redis:
                return {
                    'backend': 'redis',
                    'total_messages': int(self.redis_client.get("stats:total_messages") or 0),
                    'processed_messages': int(self.redis_client.get("stats:processed_messages") or 0),
                    'connected': True,
                    'memory_usage': self.redis_client.info('memory').get('used_memory_human', 'unknown')
                }
            else:
                with self.lock:
                    stats = self.fallback_storage['stats'].copy()
                    stats['backend'] = 'in-memory'
                    stats['connected'] = True
                    return stats
        except Exception as e:
            self.logger.error(f"❌ Failed to get stats: {e}")
            return {'backend': 'unknown', 'connected': False, 'error': str(e)}
    
    def cleanup_old_messages(self, max_age_hours: int = 24) -> int:
        """Clean up old processed messages"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            if self.use_redis:
                return self._cleanup_redis(cutoff_time)
            else:
                return self._cleanup_fallback(cutoff_time)
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")
            return 0
    
    def _cleanup_redis(self, cutoff_time: float) -> int:
        """Cleanup old messages in Redis"""
        cleaned = 0
        try:
            for key in self.redis_client.scan_iter(match="msg:*"):
                msg_data = self.redis_client.hgetall(key)
                if msg_data and float(msg_data.get('timestamp', 0)) < cutoff_time:
                    if msg_data.get('status') == 'processed':
                        self.redis_client.delete(key)
                        cleaned += 1
        except Exception as e:
            self.logger.error(f"❌ Redis cleanup failed: {e}")
        
        return cleaned
    
    def _cleanup_fallback(self, cutoff_time: float) -> int:
        """Cleanup old messages in fallback storage"""
        cleaned = 0
        with self.lock:
            to_remove = []
            for msg_id, message in self.fallback_storage['messages'].items():
                if message.timestamp < cutoff_time and message.status == 'processed':
                    to_remove.append(msg_id)
            
            for msg_id in to_remove:
                del self.fallback_storage['messages'][msg_id]
                self.fallback_storage['processed_messages'].discard(msg_id)
                cleaned += 1
        
        return cleaned

    def clear_all_messages(self):
        """Clear all messages from the database on startup for a fresh start"""
        try:
            if self.use_redis and self.redis_client:
                # Clear Redis database
                self.redis_client.flushdb()
                self.logger.info("✅ Redis database cleared - Fresh start for ollama-flow")
            else:
                # Clear fallback storage
                with self.lock:
                    self.fallback_storage = {
                        'messages': {},
                        'processed_messages': set(),
                        'stats': {
                            'total_messages': 0,
                            'processed_messages': 0,
                            'failed_messages': 0
                        }
                    }
                self.logger.info("✅ In-memory database cleared - Fresh start for ollama-flow")
        except Exception as e:
            self.logger.error(f"❌ Failed to clear database: {e}")
            # Fallback to in-memory clear
            with self.lock:
                self.fallback_storage = {
                    'messages': {},
                    'processed_messages': set(),
                    'stats': {
                        'total_messages': 0,
                        'processed_messages': 0,
                        'failed_messages': 0
                    }
                }
            self.logger.info("✅ Fallback database cleared - Fresh start for ollama-flow")
    
    def close(self):
        """Gracefully close database connections"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.close()
                self.logger.info("✅ Redis connection closed gracefully")
        except Exception as e:
            self.logger.warning(f"⚠️ Error closing Redis connection: {e}")
        
        # Clear fallback storage
        with self.lock:
            self.fallback_storage.clear()
            self.logger.info("✅ In-memory storage cleared")

# Convenience function for backward compatibility
def create_db_manager(**kwargs) -> EnhancedDBManager:
    """Create database manager with optimal settings"""
    return EnhancedDBManager(**kwargs)

if __name__ == '__main__':
    # Test the enhanced database manager
    print("🧪 Testing Enhanced Database Manager...")
    
    db = EnhancedDBManager()
    
    # Test message insertion
    msg_id = db.insert_message("agent_a", "agent_b", "task", "Test message")
    print(f"✅ Inserted message: {msg_id}")
    
    # Test retrieval
    pending = db.get_pending_messages("agent_b")
    print(f"📋 Pending messages: {len(pending)}")
    
    # Test processing
    if pending:
        db.mark_message_as_processed(pending[0]['id'])
        print("✅ Marked message as processed")
    
    # Show stats
    stats = db.get_stats()
    print(f"📊 Stats: {stats}")
    
    # Cleanup
    db.close()
    print("✅ Database manager test completed")