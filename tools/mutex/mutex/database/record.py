from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import BaseModel, Field


class Record(BaseModel):
    """Database record with validation and type safety"""

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key with default"""
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Record":
        """Create record from dictionary"""
        return cls(**data)

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access"""
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        return hasattr(self, key)


class LockRecord(Record):
    """Specific record type for lock data"""

    name: str = Field(..., description="Lock name/key")
    holder: str = Field(..., description="Lock holder identifier")
    created_at: datetime = Field(..., description="Lock creation timestamp")

    @property
    def age_seconds(self) -> float:
        """Get lock age in seconds"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds()

    @property
    def is_stale(self, max_age_seconds: int = 3600) -> bool:
        """Check if lock is stale (older than max_age_seconds)"""
        return self.age_seconds > max_age_seconds
