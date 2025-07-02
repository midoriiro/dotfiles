import os
import asyncio
import asyncpg

async def release_mutex(connection, mutex_key, job_id, run_id):
    try:
        expected_prefix = f"{job_id}-{run_id}"
        
        # Try to release the lock atomically
        result = await connection.execute("""
            DELETE FROM locks 
            WHERE name = $1 AND holder LIKE $2
        """, mutex_key, f"{expected_prefix}%")
        
        if result == "DELETE 1":
            print(f"✅ Mutex released with key '{mutex_key}'")
            return True
        elif result == "DELETE 0":
            # Check if lock exists but we don't own it
            row = await connection.fetchrow(
                "SELECT holder FROM locks WHERE name = $1",
                mutex_key
            )
            
            if row:
                print(f"⚠️ Lock '{mutex_key}' is held by '{row['holder']}', not by us (prefix: '{expected_prefix}')")
                return False
            else:
                print(f"⚠️ No lock found for key '{mutex_key}'")
                return True
        else:
            print(f"⚠️ Unexpected DELETE result: {result}")
            return False
            
    except Exception as e:
        print(f"⚠️ Error during mutex release: {e}")
        return False

async def main():
    mutex_key = os.getenv('MUTEX_KEY', None)
    connection_uri = os.getenv('DATABASE_CONNECTION_URI', None)
    job_id = os.getenv('JOB_ID', None)
    run_id = os.getenv('RUN_ID', None)

    if not mutex_key:
        raise ValueError('MUTEX_KEY environment variable is not set')

    if not connection_uri:
        raise ValueError('DATABASE_CONNECTION_URI environment variable is not set')

    if not job_id:
        raise ValueError('JOB_ID environment variable is not set')

    if not run_id:
        raise ValueError('RUN_ID environment variable is not set')
    
    connection = await asyncpg.connect(connection_uri)
    
    try:
        success = await release_mutex(connection, mutex_key, job_id, run_id)
        if not success:
            exit(1)
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())