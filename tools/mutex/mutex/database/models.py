from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, validator


class LockModel(BaseModel):
    """Model for lock records in the database"""
    key: str = Field(..., min_length=1, max_length=255, description="Lock key")
    holder: str = Field(..., min_length=1, max_length=255, description="Lock holder identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Lock creation timestamp")
    
    @field_validator('key', 'holder')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Value cannot be empty or whitespace only')
        return v.strip()


class LockAcquisitionRequest(BaseModel):
    """Model for lock acquisition requests"""
    key: str = Field(..., min_length=1, max_length=255)
    holder: str = Field(..., min_length=1, max_length=255)
    timeout: Optional[int] = Field(default=60, ge=1, le=3600, description="Timeout in seconds")
    
    @field_validator('key', 'holder')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Value cannot be empty or whitespace only')
        return v.strip()


class LockReleaseRequest(BaseModel):
    """Model for lock release requests"""
    key: str = Field(..., min_length=1, max_length=255)
    holder: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('key', 'holder')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Value cannot be empty or whitespace only')
        return v.strip()


class DatabaseConfig(BaseModel):
    """Model for database configuration"""
    connection_uri: str = Field(..., description="Database connection URI")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="Pool timeout in seconds")
    
    @field_validator('connection_uri')
    def validate_connection_uri(cls, v):
        if not v or not v.strip():
            raise ValueError('Connection URI cannot be empty')
        return v.strip() 