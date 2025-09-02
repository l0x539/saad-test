from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SubjectType(str, Enum):
    EMAIL = "email"
    USERNAME = "username"
    PHONE = "phone"

class Subject(BaseModel):
    type: SubjectType
    value: str
    normalized_value: str
    key: str
    
    model_config = ConfigDict(use_enum_values=True)

class Message(BaseModel):
    ts: datetime = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    channel: str
    message_id: str
    user_id: Optional[str] = None
    user_name: str
    text: str
    mentions: List[str] = []
    urls: List[str] = []
    emotes: List[str] = []
    source: str = "twitch-irc"

class UserProfile(BaseModel):
    user_name: str
    channels_participated: List[str] = []
    message_count: int = 0
    top_keywords: List[str] = []
    last_seen: Optional[datetime] = None
    facts: Dict[str, Any] = {}

class ChannelProfile(BaseModel):
    channel: str
    unique_users: int = 0
    message_count: int = 0
    top_users: List[str] = []
    top_keywords: List[str] = []
    last_seen: Optional[datetime] = None
    streamer_signals: Dict[str, Any] = {}