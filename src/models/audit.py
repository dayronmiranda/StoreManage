from beanie import Document, Indexed
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from pymongo import IndexModel


class EventLog(Document):
    userId: Optional[str] = None
    eventType: str  # crud/auth/business
    module: str  # users/products/sales/etc
    action: str  # create/update/delete/read
    entity: str  # collection/model name
    entityId: Optional[str] = None
    oldData: Optional[Dict[str, Any]] = None
    newData: Optional[Dict[str, Any]] = None
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    eventDate: datetime = Field(default_factory=datetime.utcnow)
    successful: bool = True
    errorMessage: Optional[str] = None
    
    # Additional information
    durationMs: Optional[int] = None
    httpMethod: Optional[str] = None
    endpoint: Optional[str] = None
    
    class Settings:
        collection = "event_logs"
        indexes = [
            IndexModel([("userId", 1)]),
            IndexModel([("eventType", 1)]),
            IndexModel([("module", 1)]),
            IndexModel([("action", 1)]),
            IndexModel([("eventDate", -1)]),
            IndexModel([("entity", 1)]),
            IndexModel([("successful", 1)]),
        ]


class AccessLog(Document):
    userId: Optional[str] = None
    attemptedUsername: str
    ipAddress: str
    userAgent: Optional[str] = None
    accessType: str  # login/logout/token_refresh/password_reset
    successful: bool
    failureReason: Optional[str] = None
    attemptDate: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional security information
    country: Optional[str] = None
    city: Optional[str] = None
    device: Optional[str] = None
    
    class Settings:
        collection = "access_logs"
        indexes = [
            IndexModel([("userId", 1)]),
            IndexModel([("attemptedUsername", 1)]),
            IndexModel([("ipAddress", 1)]),
            IndexModel([("accessType", 1)]),
            IndexModel([("attemptDate", -1)]),
            IndexModel([("successful", 1)]),
        ]


class SystemLog(Document):
    level: str  # info/warning/error/critical
    message: str
    module: str
    function: Optional[str] = None
    line: Optional[int] = None
    exception: Optional[str] = None
    stackTrace: Optional[str] = None
    logDate: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional context
    context: Optional[Dict[str, Any]] = None
    server: Optional[str] = None
    processId: Optional[int] = None
    
    class Settings:
        collection = "system_logs"
        indexes = [
            IndexModel([("level", 1)]),
            IndexModel([("module", 1)]),
            IndexModel([("logDate", -1)]),
        ]