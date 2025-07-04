from typing import List, Optional, Union
import asyncpg
import logging
from mutex.database.base import Database, DatabaseError, ConnectionError, QueryError
from mutex.database.record import Record, LockRecord
from mutex.database.statement import Statement
from mutex.database.models import DatabaseConfig

logger = logging.getLogger(__name__)


class PostgreSQLDatabase(Database):
    """PostgreSQL database implementation with connection pooling"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._pool = None
    
    async def connect(self) -> None:
        """Establish database connection pool"""
        try:
            self._pool = await asyncpg.create_pool(
                self.config.connection_uri,
                min_size=1,
                max_size=self.config.pool_size,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
                command_timeout=self.config.pool_timeout
            )
            self._is_connected = True
            logger.info("PostgreSQL connection pool established")
        except Exception as e:
            self._is_connected = False
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e
    
    async def disconnect(self) -> None:
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._is_connected = False
            logger.info("PostgreSQL connection pool closed")
    
    async def _get_connection(self):
        """Get a connection from the pool"""
        if not self.is_connected:
            raise ConnectionError("Database not connected")
        return await self._pool.acquire()
    
    async def _release_connection(self, conn):
        """Release a connection back to the pool"""
        await self._pool.release(conn)
    
    async def _begin_transaction(self) -> None:
        """Begin a new transaction"""
        conn = await self._get_connection()
        await conn.execute("BEGIN")
    
    async def _commit_transaction(self) -> None:
        """Commit the current transaction"""
        conn = await self._get_connection()
        await conn.execute("COMMIT")
    
    async def _rollback_transaction(self) -> None:
        """Rollback the current transaction"""
        conn = await self._get_connection()
        await conn.execute("ROLLBACK")

    async def create_table(self, statement: Statement) -> None:
        """Create a table"""
        conn = await self._get_connection()
        try:
            result = await conn.execute(statement.query, *statement.args)
            if result == "CREATE TABLE":
                logger.info(f"Table created: {statement.query}")
            else:
                logger.warning(f"Table creation failed: {result}")
        except Exception as e:
            raise QueryError(f"Failed to create table: {e}") from e
        finally:
            await self._release_connection(conn)
    
    async def fetch_many(self, statement: Statement) -> List[Record]:
        """Fetch multiple records"""
        conn = await self._get_connection()
        try:
            records = await conn.fetch(statement.query, *statement.args)
            return [Record(**dict(record)) for record in records]
        except Exception as e:
            raise QueryError(f"Failed to fetch records: {e}") from e
        finally:
            await self._release_connection(conn)
    
    async def fetch_one(self, statement: Statement) -> Optional[Record]:
        """Fetch a single record"""
        conn = await self._get_connection()
        try:
            record = await conn.fetchrow(statement.query, *statement.args)
            if record:
                return Record(**dict(record))
            return None
        except Exception as e:
            raise QueryError(f"Failed to fetch record: {e}") from e
        finally:
            await self._release_connection(conn)
    
    async def insert_many(self, statement: Statement) -> int:
        """Insert multiple records"""
        conn = await self._get_connection()
        try:
            result = await conn.execute(statement.query, *statement.args)
            # Parse result like "INSERT 0 5" to get count
            if result.startswith("INSERT"):
                parts = result.split()
                return int(parts[2]) if len(parts) > 2 else 0
            return 0
        except Exception as e:
            raise QueryError(f"Failed to insert records: {e}") from e
        finally:
            await self._release_connection(conn)
    
    async def insert_one(self, statement: Statement) -> bool:
        """Insert a single record"""
        inserted_count = await self.insert_many(statement)
        return inserted_count == 1
    
    async def update_many(self, statement: Statement) -> int:
        """Update multiple records"""
        conn = await self._get_connection()
        try:
            result = await conn.execute(statement.query, *statement.args)
            # Parse result like "UPDATE 3" to get count
            if result.startswith("UPDATE"):
                parts = result.split()
                return int(parts[1]) if len(parts) > 1 else 0
            return 0
        except Exception as e:
            raise QueryError(f"Failed to update records: {e}") from e
        finally:
            await self._release_connection(conn)
    
    async def update_one(self, statement: Statement) -> bool:
        """Update a single record"""
        updated_count = await self.update_many(statement)
        return updated_count == 1
    
    async def delete_many(self, statement: Statement) -> int:
        """Delete multiple records"""
        conn = await self._get_connection()
        try:
            result = await conn.execute(statement.query, *statement.args)
            # Parse result like "DELETE 2" to get count
            if result.startswith("DELETE"):
                parts = result.split()
                return int(parts[1]) if len(parts) > 1 else 0
            return 0
        except Exception as e:
            raise QueryError(f"Failed to delete records: {e}") from e
        finally:
            await self._release_connection(conn)
    
    async def delete_one(self, statement: Statement) -> bool:
        """Delete a single record"""
        deleted_count = await self.delete_many(statement)
        return deleted_count == 1