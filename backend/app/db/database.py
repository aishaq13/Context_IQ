"""Database connection and models."""

import logging
from typing import Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extensions import connection as db_connection
from app.utils.config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL connections with connection pooling."""
    
    def __init__(self):
        self.pool: Optional[SimpleConnectionPool] = None
        self.min_connections = 2
        self.max_connections = 20
    
    async def initialize(self) -> None:
        """Initialize the connection pool."""
        try:
            self.pool = SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                config.DATABASE_URL,
                connect_timeout=10
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database pool closed")
    
    def get_connection(self) -> db_connection:
        """Get a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool.getconn()
    
    def return_connection(self, conn: db_connection) -> None:
        """Return a connection to the pool."""
        if self.pool:
            self.pool.putconn(conn)
    
    def execute_query(
        self,
        query: str,
        params: tuple = ()
    ) -> list:
        """Execute a SELECT query and return results."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def execute_insert(
        self,
        query: str,
        params: tuple = ()
    ) -> Optional[int]:
        """Execute an INSERT query and return the last inserted ID."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            # Get the last inserted ID if available
            if "RETURNING" in query:
                last_id = cursor.fetchone()[0]
            else:
                last_id = None
            
            cursor.close()
            return last_id
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Insert execution error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def execute_update(
        self,
        query: str,
        params: tuple = ()
    ) -> int:
        """Execute an UPDATE query and return the number of affected rows."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Update execution error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)


# Global database manager instance
db_manager = DatabaseManager()
