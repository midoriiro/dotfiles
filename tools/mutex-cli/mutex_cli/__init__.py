from enum import Enum
import typer
from mutex.database.models import DatabaseConfig, LockAcquisitionRequest, LockReleaseRequest
from mutex.database.postgresql import PostgreSQLDatabase
from mutex.service import MutexService

class DatabaseType(str, Enum):
    POSTGRE = "postgres"
    # MARIADB = "mariadb"
    # MYSQL = "mysql"
    # SQLITE = "sqlite"
    # REDIS = "redis"
    # MEMORY = "memory"
    # MONGODB = "mongodb"
    # COUCHBASE = "couchbase"
    # ORACLE = "oracle"
    # SQLSERVER = "sqlserver"


app = typer.Typer(
    name="mutex",
    help="A CLI for mutex in CICD pipelines using database as a lock store.",
    no_args_is_help=True, 
    add_completion=False
)

def __get_service(
    database_type: str,
    database_connection_uri: str, 
    database_pool_size: int, 
    database_max_overflow: int, 
    database_pool_timeout: int
) -> MutexService:
    database_config = DatabaseConfig(
        connection_uri=database_connection_uri,
        pool_size=database_pool_size,
        max_overflow=database_max_overflow,
        pool_timeout=database_pool_timeout
    )
    
    database = PostgreSQLDatabase(database_config)
    service = MutexService(database)
    return service

@app.callback()
def callback(
    ctx: typer.Context,
    database_type: DatabaseType = typer.Option(DatabaseType.POSTGRE, envvar="DATABASE_TYPE", help="The type of the database."),
    database_connection_uri: str = typer.Option(..., envvar="DATABASE_URI", help="The connection URI of the database."),
    database_pool_size: int = typer.Option(10, envvar="DATABASE_POOL_SIZE", help="The pool size of the database."),
    database_max_overflow: int = typer.Option(20, envvar="DATABASE_MAX_OVERFLOW", help="The maximum overflow of the database."),
    database_pool_timeout: int = typer.Option(30, envvar="DATABASE_POOL_TIMEOUT", help="The pool timeout of the database.")
):
    ctx.obj = __get_service(
        database_type, 
        database_connection_uri, 
        database_pool_size, 
        database_max_overflow, 
        database_pool_timeout
    )

@app.command(
    name="acquire",
    help="Acquire a lock.", 
    no_args_is_help=True
)
async def acquire(
    ctx: typer.Context,
    key: str = typer.Option(..., help="The key of the lock."),
    holder: str = typer.Option(..., help="The holder of the lock."),
    timeout: int = typer.Option(60, help="The timeout in seconds.")
):
    request = LockAcquisitionRequest(key, holder, timeout)
    service = ctx.obj

    try:
        await service.initialize()
        success = await service.acquire(request)
        if success:
            typer.Exit(0)
        else:
            typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error acquiring lock: {e}", err=True)
        raise typer.Exit(2)


@app.command(
    name="release",
    help="Release a lock.", 
    no_args_is_help=True
)
async def release(
    ctx: typer.Context,
    key: str = typer.Option(..., help="The key of the lock."),
    holder: str = typer.Option(..., help="The holder of the lock.")
):
    request = LockReleaseRequest(key, holder)
    service = ctx.obj

    try:
        await service.initialize()
        success = await service.release(request)
        if success:
            typer.Exit(0)
        else:
            typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error releasing lock: {e}", err=True)
        raise typer.Exit(2)


@app.command(
    name="cleanup",
    help="Cleanup locks.", 
    no_args_is_help=True
)
async def cleanup(
    ctx: typer.Context,
    holder_pattern: str = typer.Option(..., help="The holder pattern of the locks to cleanup.")
):
    service = ctx.obj

    try:
        await service.initialize()
        success = await service.cleanup(holder_pattern)
        if success:
            typer.Exit(0)
        else:
            typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error cleaning up locks: {e}", err=True)
        raise typer.Exit(2)