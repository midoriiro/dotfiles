import os
import asyncio
import asyncpg

async def main():
    connection_uri = os.getenv('DATABASE_CONNECTION_URI')

    if not connection_uri:
        raise ValueError('DATABASE_CONNECTION_URI environment variable is not set')

    connection = await asyncpg.connect(connection_uri)

    try:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS locks (
            name VARCHAR(255) PRIMARY KEY,
            holder VARCHAR(255),
            created_at TIMESTAMP DEFAULT now()
            );
        """)
    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())