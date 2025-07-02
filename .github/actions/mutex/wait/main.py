import os
import asyncio
from pathlib import Path
import sys
import asyncpg
import time

current_dir = Path(__file__).parent
utils_path = current_dir.parent.parent.parent.parent.parent / "scripts" / "python" / "utils.py"
sys.path.insert(0, str(utils_path))

# Import functions from utils.py
from utils import (
    safe_print, 
    safe_subprocess_run, 
    safe_print_info, 
    safe_print_error, 
    safe_print_success, 
    safe_print_start, 
    safe_print_done
)

async def acquire_mutex(connection, mutex_key, holder_id, timeout):
    start_time = time.time()
    
    while True:
        try:
            # Try to acquire the mutex atomically
            safe_print_info(f"🔒 Attempting to acquire mutex with holder '{holder_id}'...")
            
            # Use INSERT ... ON CONFLICT for atomic acquisition
            result = await connection.execute("""
                INSERT INTO locks (name, holder) 
                VALUES ($1, $2) 
                ON CONFLICT (name) DO NOTHING
            """, mutex_key, holder_id)
            
            if result == "INSERT 0 1":
                # Successfully acquired the mutex
                safe_print_success(f"✅ Mutex acquired with key '{mutex_key}' and holder '{holder_id}'")
                return True
            else:
                # Failed to acquire, check if it's stale
                row = await connection.fetchrow(
                    "SELECT holder, created_at FROM locks WHERE name = $1",
                    mutex_key
                )

                elapsed_time = time.time() - start_time
                
                if row:
                    safe_print_info(f"🔍 Mutex is locked by {row['holder']}, waiting again {elapsed_time:.1f}s...")
                    await asyncio.sleep(1)
                        
                    if elapsed_time > timeout:
                        safe_print_error("❌ Timeout waiting for mutex to be released")
                        return False
                else:
                    # Race condition: lock was released between our attempts
                    safe_print_info("🔄 Lock was released, retrying...")
                    await asyncio.sleep(0.1)
                    continue
        except Exception as e:
            safe_print_error(f"⚠️ Error during mutex acquisition: {e}")
            await asyncio.sleep(1)
            continue

async def main():
    mutex_key = os.getenv('MUTEX_KEY', None)
    timeout = int(os.getenv('TIMEOUT', None))
    connection_uri = os.getenv('DATABASE_CONNECTION_URI', None)
    holder_id = os.getenv('HOLDER_ID', None)

    if not mutex_key:
        raise ValueError('MUTEX_KEY environment variable is not set')

    if not timeout:
        raise ValueError('TIMEOUT environment variable is not set')

    if not connection_uri:
        raise ValueError('DATABASE_CONNECTION_URI environment variable is not set')

    if not holder_id:
        raise ValueError('HOLDER_ID environment variable is not set')
    
    safe_print_info(f"🔍 Getting mutex with key '{mutex_key}' and holder '{holder_id}'")
    
    connection = await asyncpg.connect(connection_uri)
    
    try:
        success = await acquire_mutex(connection, mutex_key, holder_id, timeout)
        if not success:
            exit(1)
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())