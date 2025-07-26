import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional

from mutex.database.models import DatabaseConfig
from mutex.database.record import Record
from mutex.database.statement import Statement

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations"""

    pass


class ConnectionError(DatabaseError):
    """Exception raised when connection fails"""

    pass


class QueryError(DatabaseError):
    """Exception raised when query execution fails"""

    pass


class Database(ABC):
    """Abstract base class for database operations"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected and self._connection is not None

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection"""
        pass

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions"""
        if not self.is_connected:
            raise ConnectionError("Database not connected")

        try:
            await self._begin_transaction()
            yield self
            await self._commit_transaction()
        except Exception as e:
            await self._rollback_transaction()
            raise QueryError(f"Transaction failed: {e}") from e

    @abstractmethod
    async def _begin_transaction(self) -> None:
        """Begin a new transaction"""
        pass

    @abstractmethod
    async def _commit_transaction(self) -> None:
        """Commit the current transaction"""
        pass

    @abstractmethod
    async def _rollback_transaction(self) -> None:
        """Rollback the current transaction"""
        pass

    @abstractmethod
    async def create_table(self, statement: Statement) -> None:
        """Create a table"""
        pass

    @abstractmethod
    async def fetch_many(self, statement: Statement) -> List[Record]:
        """Fetch multiple records"""
        pass

    @abstractmethod
    async def fetch_one(self, statement: Statement) -> Optional[Record]:
        """Fetch a single record"""
        pass

    @abstractmethod
    async def insert_many(self, statement: Statement) -> int:
        """Insert multiple records"""
        pass

    @abstractmethod
    async def insert_one(self, statement: Statement) -> bool:
        """Insert a single record"""
        pass

    @abstractmethod
    async def update_many(self, statement: Statement) -> int:
        """Update multiple records"""
        pass

    @abstractmethod
    async def update_one(self, statement: Statement) -> bool:
        """Update a single record"""
        pass

    @abstractmethod
    async def delete_many(self, statement: Statement) -> int:
        """Delete multiple records"""
        pass

    @abstractmethod
    async def delete_one(self, statement: Statement) -> bool:
        """Delete a single record"""
        pass
