import os
import asyncio
import asyncpg
import time

async def acquire_mutex(connection, mutex_key, holder_id, timeout):
    start_time = time.time()
    
    while True:
        try:
            # Try to acquire the mutex atomically
            print(f"🔒 Attempting to acquire mutex with holder '{holder_id}'...")
            
            # Use INSERT ... ON CONFLICT for atomic acquisition
            result = await connection.execute("""
                INSERT INTO locks (name, holder) 
                VALUES ($1, $2) 
                ON CONFLICT (name) DO NOTHING
            """, mutex_key, holder_id)
            
            if result == "INSERT 0 1":
                # Successfully acquired the mutex
                print(f"✅ Mutex acquired with key '{mutex_key}' and holder '{holder_id}'")
                return True
            else:
                # Failed to acquire, check if it's stale
                row = await connection.fetchrow(
                    "SELECT holder, created_at FROM locks WHERE name = $1",
                    mutex_key
                )

                elapsed_time = time.time() - start_time
                
                if row:
                    print(f"🔍 Mutex is locked by {row['holder']}, waiting again {elapsed_time:.1f}s...")
                    await asyncio.sleep(1)
                        
                    if elapsed_time > timeout:
                        print("❌ Timeout waiting for mutex to be released")
                        return False
                else:
                    # Race condition: lock was released between our attempts
                    print("🔄 Lock was released, retrying...")
                    await asyncio.sleep(0.1)
                    continue
        except Exception as e:
            print(f"⚠️ Error during mutex acquisition: {e}")
            await asyncio.sleep(1)
            continue

async def main():
    mutex_key = os.getenv('MUTEX_KEY', None)
    timeout = int(os.getenv('TIMEOUT', None))
    connection_uri = os.getenv('DATABASE_CONNECTION_URI', None)
    job_id = os.getenv('JOB_ID', None)
    run_id = os.getenv('RUN_ID', None)

    if not mutex_key:
        raise ValueError('MUTEX_KEY environment variable is not set')

    if not timeout:
        raise ValueError('TIMEOUT environment variable is not set')

    if not connection_uri:
        raise ValueError('DATABASE_CONNECTION_URI environment variable is not set')

    if not job_id:
        raise ValueError('JOB_ID environment variable is not set')

    if not run_id:
        raise ValueError('RUN_ID environment variable is not set')
    
    # Create unique holder ID
    holder_id = f"{job_id}-{run_id}"
    
    print(f"🔍 Getting mutex with key '{mutex_key}'")
    
    connection = await asyncpg.connect(connection_uri)
    
    try:
        success = await acquire_mutex(connection, mutex_key, holder_id, timeout)
        if not success:
            exit(1)
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())