from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# ✅ ADD THIS IMPORT
from sqlalchemy.orm import selectinload 
import uuid

# ✅ IMPORT the User and NotificationPreference models
from src.db.models import User, NotificationPreference
from src.schemas.user import UserCreate, ProfileCompletion
from src.core.security import get_password_hash

class UserService:
    async def get_user_by_email(self, email: str, db: AsyncSession) -> User | None:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_user_by_username(self, username: str, db: AsyncSession) -> User | None:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()

    async def get_user_by_google_id(self, google_id: str, db: AsyncSession) -> User | None:
        result = await db.execute(select(User).filter(User.google_provider_id == google_id))
        return result.scalars().first()
    
    # ✅ THIS IS THE ONLY FUNCTION THAT NEEDS TO BE CHANGED
    async def get_user_by_uuid(self, id: uuid.UUID, db: AsyncSession) -> User | None:
        """
        Gets a user by their UUID and eagerly loads their notification preferences
        to prevent lazy-loading errors.
        """
        stmt = (
            select(User)
            .where(User.uuid == id)
            .options(selectinload(User.notification_preferences))
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create_user_from_email(self, user_in: UserCreate, db: AsyncSession) -> User:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            username=user_in.username,
            full_name=user_in.full_name,
            date_of_birth=user_in.date_of_birth,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(db_user)
        
        await db.flush()
        
        db_prefs = NotificationPreference(user_id=db_user.uuid)
        db.add(db_prefs)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def create_user_from_google(
        self,
        profile_data: ProfileCompletion,
        google_id: str,
        email: str,
        full_name: str,
        db: AsyncSession
    ) -> User:
        existing_user = await self.get_user_by_email(email, db)
        if existing_user:
            raise ValueError("An account with this email already exists.")

        db_user = User(
            email=email,
            username=profile_data.username,
            full_name=full_name,
            date_of_birth=profile_data.date_of_birth,
            google_provider_id=google_id,
            is_active=True
        )
        db.add(db_user)

        await db.flush()
        
        db_prefs = NotificationPreference(user_id=db_user.uuid)
        db.add(db_prefs)
        
        await db.commit()
        await db.refresh(db_user)
        return db_user