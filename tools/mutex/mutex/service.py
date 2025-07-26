import asyncio
import logging
import time
from typing import Optional

from mutex.database.base import Database, DatabaseError
from mutex.database.models import LockAcquisitionRequest, LockReleaseRequest
from mutex.database.record import LockRecord, Record
from mutex.database.statement import StatementBuilder

logger = logging.getLogger(__name__)


class MutexService:
    """Service for managing distributed mutexes"""

    def __init__(self, database: Database):
        self._table_name = "locks"
        self._database = database
        self._default_timeout = 60  # seconds

    async def initialize(self) -> None:
        """Initialize the mutex service"""
        await self._database.connect()
        statement = StatementBuilder.create_locks_table()
        await self._database.create_table(statement)
        logger.info("Mutex service initialized")

    async def shutdown(self) -> None:
        """Shutdown the mutex service"""
        await self._database.disconnect()
        logger.info("Mutex service shutdown")

    async def acquire(self, request: LockAcquisitionRequest) -> bool:
        """Acquire a lock with timeout"""
        start_time = time.time()
        key = request.key
        holder = request.holder
        timeout_seconds = request.timeout or self._default_timeout

        insert_statement = StatementBuilder.insert_on_conflict_do_nothing(
            table=self._table_name,
            data={"key": key, "holder": holder},
            conflict_column="key",
        )

        fetch_one_statement = StatementBuilder.select(
            table=self._table_name, columns=["holder", "created_at"], where={"key": key}
        )

        while True:
            try:
                elapsed_time = time.time() - start_time

                if elapsed_time > timeout_seconds:
                    logger.error("❌ Timeout waiting for mutex to be released")
                    return False

                logger.info(f"🔒 Attempting to acquire mutex with holder '{holder}'...")

                is_inserted = await self._database.insert_one(insert_statement)

                if is_inserted:
                    logger.info(
                        f"✅ Mutex acquired with key '{key}' and holder '{holder}'"
                    )
                    return True
                else:
                    record: Optional[Record] = await self._database.fetch_one(
                        fetch_one_statement
                    )

                    if record:
                        lock_record = LockRecord(**record)
                        logger.info(
                            f"🔍 Mutex is locked by {lock_record.holder}, "
                            f"waiting again {elapsed_time:.1f}s..."
                        )
                        await asyncio.sleep(1)
                    else:
                        # Race condition: lock was released between our attempts
                        logger.info("🔄 Lock was released, retrying...")
                        await asyncio.sleep(0.1)
            except DatabaseError as e:
                logger.error(f"❌ Database error during lock acquisition: {e}")
                await asyncio.sleep(1)
                continue

    async def release(self, request: LockReleaseRequest) -> bool:
        """Release a lock"""
        key = request.key
        holder = request.holder

        select_statement = StatementBuilder.select(
            table=self._table_name, columns=["holder"], where={"key": key}
        )

        delete_statement = StatementBuilder.delete(
            table=self._table_name, where={"key": key, "holder": holder}
        )

        try:
            # Try to release the lock atomically
            is_deleted = await self._database.delete_one(delete_statement)

            if is_deleted:
                logger.info(f"✅ Mutex released with key '{key}'")
                return True
            else:
                # Check if lock exists but we don't own it
                record: Optional[Record] = await self._database.fetch_one(
                    select_statement
                )
                if record:
                    lock_record = LockRecord(**record)
                    logger.info(
                        f"⚠️ Lock '{key}' is held by '{lock_record.holder}', not by us "
                        f"(prefix: '{holder}')"
                    )
                    return False
                else:
                    logger.info(f"⚠️ No lock found for key '{key}'")
                    return True
        except DatabaseError as e:
            logger.error(f"❌Database error during lock release: {e}")
            return False

    async def cleanup(self, holder_pattern: str) -> bool:
        """Clean up all locks for a specific holder pattern"""

        select_statement = StatementBuilder.select_like(
            table=self._table_name,
            columns=["holder", "created_at"],
            where={"holder": f"{holder_pattern}%"},
        )

        delete_statement = StatementBuilder.delete_like(
            table=self._table_name, where={"holder": f"{holder_pattern}%"}
        )

        try:
            records = await self._database.fetch_many(select_statement)

            if not records:
                logger.info(f"✅ No locks found with holder pattern '{holder_pattern}'")
                return True

            lock_records = [LockRecord(**record) for record in records]

            logger.info(
                f"🔍 Found {len(records)} locks to clean with holder pattern "
                f"'{holder_pattern}':"
            )
            for lock_record in lock_records:
                elapsed = (
                    asyncio.get_event_loop().time() - lock_record.created_at.timestamp()
                )
                logger.info(
                    f"  - {lock_record.key} (held by {lock_record.holder}, "
                    f"age: {elapsed:.1f}s)"
                )

            deleted_count = await self._database.delete_many(delete_statement)

            logger.info(
                f"✅ Successfully deleted {deleted_count} locks with holder pattern "
                f"'{holder_pattern}'"
            )

            return True
        except DatabaseError as e:
            logger.error(f"❌Database error during cleanup: {e}")
            return 0
