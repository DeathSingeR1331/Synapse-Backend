import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.dependencies import get_current_active_user
from src.db import models
from src.db.database import get_db_session
from src.schemas.user import (
    UserPublicWithDetails,
    UserUpdate,
    UserSettingsUpdate,
    NotificationPreferenceUpdate,
)

router = APIRouter()

@router.get(
    "/me",
    response_model=UserPublicWithDetails,
    summary="Get current user's detailed profile"
)
async def read_users_me(
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Fetch the current authenticated user's profile, including settings and notification preferences.
    """
    # Eager load related notification preferences to avoid a separate query
    result = await session.get(
        models.User,
        current_user.uuid,
        options=[selectinload(models.User.notification_preferences)],
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@router.patch(
    "/me",
    response_model=UserPublicWithDetails,
    summary="Update current user's profile"
)
async def update_user_me(
    user_in: UserUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update the current user's full_name or profile picture URL.
    """
    user_data = user_in.model_dump(exclude_unset=True)
    for field, value in user_data.items():
        setattr(current_user, field, value)
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.patch(
    "/me/settings",
    response_model=UserPublicWithDetails,
    summary="Update current user's generic settings"
)
async def update_user_settings_me(
    settings_in: UserSettingsUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update the JSON settings field for the user. Merges new settings with existing ones.
    """
    if current_user.settings is None:
        current_user.settings = {}
    
    # Merge new settings into the existing dictionary
    current_user.settings.update(settings_in.settings)
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.patch(
    "/me/notifications",
    response_model=UserPublicWithDetails,
    summary="Update current user's notification preferences"
)
async def update_user_notification_prefs(
    prefs_in: NotificationPreferenceUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update notification preferences for the current user.
    """
    prefs = await session.get(
        models.NotificationPreference,
        current_user.uuid,
        options=[selectinload(models.NotificationPreference.user)]
    )
    if not prefs:
        # If user has no preferences yet, create them
        prefs = models.NotificationPreference(user_id=current_user.uuid)

    prefs_data = prefs_in.model_dump(exclude_unset=True)
    for field, value in prefs_data.items():
        setattr(prefs, field, value)

    session.add(prefs)
    await session.commit()
    await session.refresh(current_user)
    
    # Re-fetch the user with the updated preferences loaded
    refreshed_user = await session.get(
        models.User,
        current_user.uuid,
        options=[selectinload(models.User.notification_preferences)],
    )
    return refreshed_user
@router.patch(
    "/me/notifications",
    response_model=UserPublicWithDetails,
    summary="Update current user's notification preferences"
)
async def update_user_notification_prefs(
    prefs_in: NotificationPreferenceUpdate,
    current_user: Annotated[models.User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Update notification preferences for the current user.
    """
    # ✅ CORRECTED QUERY: Fetch preferences based on the user_id foreign key
    stmt = select(models.NotificationPreference).where(
        models.NotificationPreference.user_id == current_user.uuid
    )
    result = await session.execute(stmt)
    prefs = result.scalars().first()

    if not prefs:
        # This logic is correct: if no prefs exist, create them.
        prefs = models.NotificationPreference(user_id=current_user.uuid)

    prefs_data = prefs_in.model_dump(exclude_unset=True)
    for field, value in prefs_data.items():
        setattr(prefs, field, value)

    session.add(prefs)
    await session.commit()
    
    # Refresh the top-level user object to get the updated relationship
    await session.refresh(current_user, attribute_names=['notification_preferences'])
    
    return current_user