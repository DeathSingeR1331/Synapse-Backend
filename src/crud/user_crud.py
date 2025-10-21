from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.base import CRUDBase
from src.db import models
from src.schemas.user import UserCreate, UserUpdate
# NOTE: You will need to import your password hashing function.
# The path might be different in your project.
from src.core.security import get_password_hash

class CRUDUser(CRUDBase[models.User, UserCreate, UserUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> models.User:
        """
        Overrides the base create method to also create a user's notification
        preferences in the same transaction.
        """
        # Create the main user object
        db_obj = models.User(
            email=obj_in.email,
            username=obj_in.username,
            full_name=obj_in.full_name,
            date_of_birth=obj_in.date_of_birth,
            hashed_password=get_password_hash(obj_in.password),
        )
        db.add(db_obj)
        # Flush the session to get the generated UUID for the new user
        await db.flush()

        # Create the default notification preferences for the new user
        new_prefs = models.NotificationPreference(user_id=db_obj.uuid)
        db.add(new_prefs)

        # Commit both the user and their preferences to the database
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

# Create a pre-configured instance of the CRUD class for easy import
user = CRUDUser(models.User)