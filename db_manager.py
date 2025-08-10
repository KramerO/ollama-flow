import sqlite3
import asyncio
import json
from typing import List, Dict, Any

class MessageDBManager:
    def __init__(self, db_path: str = 'messages.db'):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                request_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)
        self.conn.commit()

    def clear_all_messages(self):
        """Clear all messages from the database on startup for a fresh start"""
        if self.conn is None:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages")
        self.conn.commit()
        
        # Reset auto-increment counter
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='messages'")
        self.conn.commit()
        
        print("✅ Database cleared - Fresh start for ollama-flow")

    def insert_message(self, sender_id: str, receiver_id: str, type: str, content: str, request_id: str = None) -> int:
        # Ensure connection is active
        if self.conn is None:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, type, content, request_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sender_id, receiver_id, type, content, request_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_pending_messages(self, receiver_id: str) -> List[Dict[str, Any]]:
        # Ensure connection is active
        if self.conn is None:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM messages
            WHERE receiver_id = ? AND status = 'pending'
            ORDER BY timestamp ASC
            """,
            (receiver_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def mark_message_as_processed(self, message_id: int):
        # Ensure connection is active
        if self.conn is None:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE messages
            SET status = 'processed'
            WHERE id = ?
            """,
            (message_id,)
        )
        self.conn.commit()

    def delete_processed_messages(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            DELETE FROM messages
            WHERE status = 'processed'
            """
        )
        self.conn.commit()

    def get_all_messages(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages ORDER BY timestamp ASC")
        return [dict(row) for row in cursor.fetchall()]

if __name__ == '__main__':
    # Example Usage (in-memory database for testing)
    db_manager = MessageDBManager(db_path=':memory:')
    print("Database created and table initialized.")

    # Insert some messages
    db_manager.insert_message("agent_a", "agent_b", "task", "Hello from A to B", "req-1")
    db_manager.insert_message("agent_b", "agent_a", "response", "Hello from B to A", "req-1")
    db_manager.insert_message("agent_a", "agent_c", "info", "Info for C", "req-2")

    print("\nAll messages:")
    for msg in db_manager.get_all_messages():
        print(msg)

    print("\nPending messages for agent_b:")
    pending_b = db_manager.get_pending_messages("agent_b")
    for msg in pending_b:
        print(msg)
        db_manager.mark_message_as_processed(msg['id'])

    print("\nPending messages for agent_b after processing:")
    print(db_manager.get_pending_messages("agent_b"))

    print("\nAll messages after processing some:")
    for msg in db_manager.get_all_messages():
        print(msg)

    db_manager.close()
    print("\nDatabase connection closed.")
