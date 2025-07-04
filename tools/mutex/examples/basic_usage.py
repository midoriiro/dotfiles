#!/usr/bin/env python3
"""
Basic usage example for the improved Mutex service
"""

import asyncio
import os
import logging
from mutex.database.models import DatabaseConfig, LockAcquisitionRequest, LockReleaseRequest
from mutex.database.postgresql import PostgreSQLDatabase
from mutex.service import MutexService
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_lock():
    """Example of basic lock acquisition and release"""
    
    # Configuration
    config = DatabaseConfig(
        connection_uri=os.getenv("DATABASE_CONNECTION_URI", "postgresql://user:pass@localhost/mutex_db"),
        pool_size=5
    )
    
    # Create database and service
    database = PostgreSQLDatabase(config)
    service = MutexService(database)
    
    try:
        # Initialize service
        await service.initialize()
        
        # Create lock acquisition request
        lock_key = "example-lock"
        holder_id = "worker-1"
        
        acquisition_request = LockAcquisitionRequest(
            key=lock_key,
            holder=holder_id,
            timeout=30
        )
        
        logger.info(f"Attempting to acquire lock: {lock_key}")
        success = await service.acquire(acquisition_request)
        
        if success:
            logger.info("Lock acquired successfully!")
            
            # Simulate some work
            await asyncio.sleep(2)
            
            # Create lock release request
            release_request = LockReleaseRequest(
                key=lock_key,
                holder=holder_id
            )
            
            # Release the lock
            await service.release(release_request)
            logger.info("Lock released")
        else:
            logger.error("Failed to acquire lock")
            
    finally:
        await service.shutdown()


async def example_context_manager():
    """Example using the context manager for automatic lock management"""
    
    config = DatabaseConfig(
        connection_uri=os.getenv("DATABASE_CONNECTION_URI", "postgresql://user:pass@localhost/mutex_db"),
        pool_size=5
    )
    
    database = PostgreSQLDatabase(config)
    service = MutexService(database)
    
    try:
        await service.initialize()
        
        # Use context manager for automatic lock management
        lock_key = "context-lock"
        holder_id = "worker-2"
        
        # Create acquisition request for context manager
        acquisition_request = LockAcquisitionRequest(
            key=lock_key,
            holder=holder_id,
            timeout=30
        )
        
        # Use context manager pattern
        try:
            success = await service.acquire(acquisition_request)
            if not success:
                raise TimeoutError("Failed to acquire lock")
            
            logger.info("Lock acquired via context manager")
            await asyncio.sleep(3)
            logger.info("Work completed, lock will be automatically released")
            
        finally:
            # Always release the lock
            release_request = LockReleaseRequest(
                key=lock_key,
                holder=holder_id
            )
            await service.release(release_request)
            logger.info("Lock released")
            
    except TimeoutError as e:
        logger.error(f"Lock acquisition failed: {e}")
    finally:
        await service.shutdown()


async def example_concurrent_workers():
    """Example with multiple concurrent workers"""
    
    config = DatabaseConfig(
        connection_uri=os.getenv("DATABASE_CONNECTION_URI", "postgresql://user:pass@localhost/mutex_db"),
        pool_size=10
    )
    
    database = PostgreSQLDatabase(config)
    service = MutexService(database)
    
    async def worker(worker_id: int):
        """Individual worker function"""
        lock_key = "shared-resource"
        holder_id = f"worker-{worker_id}"
        
        try:
            logger.info(f"Worker {worker_id} attempting to acquire lock")
            
            acquisition_request = LockAcquisitionRequest(
                key=lock_key,
                holder=holder_id,
                timeout=10
            )
            
            success = await service.acquire(acquisition_request)
            
            if success:
                logger.info(f"Worker {worker_id} acquired lock")
                await asyncio.sleep(2)  # Simulate work
                
                release_request = LockReleaseRequest(
                    key=lock_key,
                    holder=holder_id
                )
                await service.release(release_request)
                logger.info(f"Worker {worker_id} released lock")
            else:
                logger.warning(f"Worker {worker_id} failed to acquire lock")
                
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
    
    try:
        await service.initialize()
        
        # Create multiple workers
        workers = [worker(i) for i in range(3)]
        await asyncio.gather(*workers)
        
    finally:
        await service.shutdown()


async def example_cleanup():
    """Example of cleaning up locks for a specific holder pattern"""
    
    config = DatabaseConfig(
        connection_uri=os.getenv("DATABASE_CONNECTION_URI", "postgresql://user:pass@localhost/mutex_db"),
        pool_size=5
    )
    
    database = PostgreSQLDatabase(config)
    service = MutexService(database)
    
    try:
        await service.initialize()
        
        # Create some locks
        workflow_id = "workflow-123"
        for i in range(3):
            acquisition_request = LockAcquisitionRequest(
                key=f"resource-{i}",
                holder=f"{workflow_id}-task-{i}",
                timeout=30
            )
            await service.acquire(acquisition_request)
        
        # Clean up locks for this workflow
        cleaned_count = await service.cleanup(workflow_id)
        logger.info(f"Cleaned up {cleaned_count} locks for workflow {workflow_id}")
        
    finally:
        await service.shutdown()


async def example_advanced_context_manager():
    """Example of a more advanced context manager implementation"""
    
    config = DatabaseConfig(
        connection_uri=os.getenv("DATABASE_CONNECTION_URI", "postgresql://user:pass@localhost/mutex_db"),
        pool_size=5
    )
    
    database = PostgreSQLDatabase(config)
    service = MutexService(database)
    
    @asynccontextmanager
    async def lock_context(service: MutexService, key: str, holder: str, timeout: int = 30):
        """Custom context manager for lock management"""
        acquisition_request = LockAcquisitionRequest(
            key=key,
            holder=holder,
            timeout=timeout
        )
        
        success = await service.acquire(acquisition_request)
        if not success:
            raise TimeoutError(f"Failed to acquire lock '{key}'")
        
        try:
            yield
        finally:
            release_request = LockReleaseRequest(
                key=key,
                holder=holder
            )
            await service.release(release_request)
    
    try:
        await service.initialize()
        
        # Use the custom context manager
        async with lock_context(service, "advanced-lock", "worker-3", timeout=30):
            logger.info("Lock acquired via custom context manager")
            await asyncio.sleep(2)
            logger.info("Work completed, lock will be automatically released")
            
    except TimeoutError as e:
        logger.error(f"Lock acquisition failed: {e}")
    finally:
        await service.shutdown()


async def main():
    """Run all examples"""
    logger.info("Running Mutex service examples...")
    
    logger.info("\n=== Basic Lock Example ===")
    await example_basic_lock()
    
    logger.info("\n=== Context Manager Example ===")
    await example_context_manager()
    
    logger.info("\n=== Concurrent Workers Example ===")
    await example_concurrent_workers()
    
    logger.info("\n=== Cleanup Example ===")
    await example_cleanup()
    
    logger.info("\n=== Advanced Context Manager Example ===")
    await example_advanced_context_manager()
    
    logger.info("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main()) 