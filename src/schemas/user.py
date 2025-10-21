import uuid
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any

# --- EXISTING SCHEMAS ---

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    full_name: str | None = None
    date_of_birth: date | None = None

class ProfileCompletion(BaseModel):
    username: str
    full_name: str | None = None
    date_of_birth: date | None = None

class UserPublic(BaseModel):
    uuid: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None = None
    
    class Config:
        from_attributes = True

# --- ✅ NEW SCHEMAS FOR PHASE 2 ---

class UserUpdate(BaseModel):
    """Schema for updating basic user profile info."""
    full_name: Optional[str] = None
    pfpb: Optional[str] = None # Profile Picture URL

class UserSettingsUpdate(BaseModel):
    """Schema for updating the generic JSON settings."""
    settings: Dict[str, Any]

class NotificationPreferencePublic(BaseModel):
    """Public schema for notification preferences."""
    email_enabled: bool
    push_enabled: bool
    in_app_enabled: bool

    class Config:
        from_attributes = True

class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None

class UserPublicWithDetails(UserPublic):
    """A comprehensive public user model including settings and preferences."""
    pfpb: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[NotificationPreferencePublic] = None

    class Config:
        from_attributes = True