import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from mutex.database.models import LockModel

logger = logging.getLogger(__name__)


@dataclass
class Statement:
    """SQL statement with parameters"""

    query: str
    args: tuple = ()

    def __str__(self):
        return self.query.format(*self.args)


class StatementBuilder:
    """Builder pattern for creating SQL statements"""

    @staticmethod
    def select(
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Statement:
        """Build SELECT statement"""
        cols = "*" if not columns else ", ".join(columns)
        query = f"SELECT {cols} FROM {table}"
        args = ()

        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = ${len(args) + 1}")
                args += (value,)
            query += f" WHERE {' AND '.join(conditions)}"

        return Statement(query, args)

    @staticmethod
    def select_like(
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Statement:
        """Build SELECT statement with LIKE"""
        cols = "*" if not columns else ", ".join(columns)
        query = f"SELECT {cols} FROM {table}"
        args = ()

        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} LIKE ${len(args) + 1}")
                args += (value,)
            query += f" WHERE {' AND '.join(conditions)}"

        return Statement(query, args)

    @staticmethod
    def insert(
        table: str, data: Dict[str, Any], on_conflict: Optional[str] = None
    ) -> Statement:
        """Build INSERT statement"""
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]

        query = f"""INSERT INTO {table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})"""
        args = tuple(data.values())

        if on_conflict:
            query += f" ON CONFLICT {on_conflict}"

        return Statement(query, args)

    @staticmethod
    def update(
        table: str, data: Dict[str, Any], where: Optional[Dict[str, Any]] = None
    ) -> Statement:
        """Build UPDATE statement"""
        set_clause = ", ".join([f"{col} = ${i+1}" for i, col in enumerate(data.keys())])
        query = f"UPDATE {table} SET {set_clause}"
        args = tuple(data.values())

        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = ${len(args) + 1}")
                args += (value,)
            query += f" WHERE {' AND '.join(conditions)}"

        return Statement(query, args)

    @staticmethod
    def delete(table: str, where: Optional[Dict[str, Any]] = None) -> Statement:
        """Build DELETE statement"""
        query = f"DELETE FROM {table}"
        args = ()

        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = ${len(args) + 1}")
                args += (value,)
            query += f" WHERE {' AND '.join(conditions)}"

        return Statement(query, args)

    @staticmethod
    def delete_like(table: str, where: Optional[Dict[str, Any]] = None) -> Statement:
        """Build DELETE statement"""
        query = f"DELETE FROM {table}"
        args = ()

        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} LIKE ${len(args) + 1}")
                args += (value,)
            query += f" WHERE {' AND '.join(conditions)}"

        return Statement(query, args)

    @staticmethod
    def insert_on_conflict_do_nothing(
        table: str, data: Dict[str, Any], conflict_column: str
    ) -> Statement:
        """Build INSERT ... ON CONFLICT DO NOTHING statement"""
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]

        query = f"""INSERT INTO {table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON CONFLICT ({conflict_column}) DO NOTHING"""
        args = tuple(data.values())

        return Statement(query, args)

    @staticmethod
    def create_table(table: str, columns: List[str]) -> Statement:
        """Build CREATE TABLE statement"""
        columns_str = ", ".join([f"{col} TEXT" for col in columns])
        query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_str})"
        return Statement(query)

    @staticmethod
    def create_table_from_model(
        table_name: str, model_class, primary_keys: Optional[List[str]] = None
    ) -> Statement:
        """Build CREATE TABLE statement from a Pydantic model"""
        columns = []

        for field_name, field_info in model_class.model_fields.items():
            field_type = field_info.annotation

            # Map Python types to SQL types
            if field_type == str:
                max_length = getattr(field_info, "max_length", 255)
                sql_type = f"VARCHAR({max_length})"
            elif field_type == int:
                sql_type = "INTEGER"
            elif field_type == float:
                sql_type = "REAL"
            elif field_type == bool:
                sql_type = "BOOLEAN"
            elif field_type == datetime:
                sql_type = "TIMESTAMP"
            else:
                sql_type = "TEXT"

            # Handle default values
            if hasattr(field_info, "default_factory") and field_info.default_factory:
                if field_info.default_factory == datetime.now(timezone.utc):
                    sql_type += " DEFAULT CURRENT_TIMESTAMP"
                else:
                    sql_type += " DEFAULT NULL"
            elif field_info.default is not None:
                sql_type += f" DEFAULT {field_info.default}"
            elif not field_info.is_required():
                sql_type += " DEFAULT NULL"
            else:
                sql_type += " NOT NULL"

            columns.append(f"{field_name} {sql_type}")

        # Add primary key constraint if specified
        if primary_keys:
            columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

        columns_str = ", ".join(columns)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
        return Statement(query)

    @staticmethod
    def create_locks_table() -> Statement:
        """Create the locks table based on LockModel"""
        return StatementBuilder.create_table_from_model(
            "locks", LockModel, primary_keys=["name", "holder"]
        )
