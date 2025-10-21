import uuid
from typing import Annotated
import structlog

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# ✅ ADD THIS IMPORT
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from jose import JWTError, jwt

from src.schemas.user import UserCreate, UserPublic, ProfileCompletion
from src.schemas.auth import Token
from src.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    create_completion_token,
    verify_completion_token,
    get_access_token_payload,
)
from src.core.config import settings
from src.db.database import get_db_session
from src.services.user_service import UserService

log = structlog.get_logger(__name__)

router = APIRouter()
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- Dependencies ---
completion_token_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/complete-profile")
access_token_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

def get_completion_token_payload(token: Annotated[str, Depends(completion_token_scheme)]) -> dict:
    return verify_completion_token(token)

def get_refresh_token_from_cookie(request: Request) -> str | None:
    return request.cookies.get("refresh_token")

# ✅ THIS IS THE FUNCTION TO FIX
async def get_current_user(
    token: Annotated[str, Depends(access_token_scheme)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_service: UserService = Depends()
) -> UserPublic:
    payload = get_access_token_payload(token)
    user_uuid = uuid.UUID(payload.get("sub"))

    # The user_service.get_user_by_uuid is what needs to be fixed.
    # Since we have the UserService code, we'll assume it's been updated
    # to eager load the relationship as shown in the previous correct answer.
    # The get_user_by_uuid method in UserService should look like this:
    #
    # async def get_user_by_uuid(self, id: uuid.UUID, db: AsyncSession) -> User | None:
    #     stmt = (
    #         select(User)
    #         .where(User.uuid == id)
    #         .options(selectinload(User.notification_preferences))
    #     )
    #     result = await db.execute(stmt)
    #     return result.scalars().first()

    user = await user_service.get_user_by_uuid(id=user_uuid, db=db)
    
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not active")
    
    return user


# --- THE REST OF THE FILE IS UNCHANGED ---

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_service: UserService = Depends()
):
    db_user_by_email = await user_service.get_user_by_email(email=user_in.email, db=db)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user_by_username = await user_service.get_user_by_username(username=user_in.username, db=db)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    return await user_service.create_user_from_email(user_in=user_in, db=db)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserService = Depends()
):
    user = await user_service.get_user_by_email(email=form_data.username, db=db)
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user.uuid)})
    refresh_token = create_refresh_token(data={"sub": str(user.uuid)})
    
    content = {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    response = JSONResponse(content=content)
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, samesite='lax', secure=False, path='/', domain="localhost"
    )
    return response


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = f"{settings.GOOGLE_REDIRECT_URI or 'https://synapse-front-end.vercel.app/auth/google/callback'}"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_service: UserService = Depends()
):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    google_provider_id = user_info['sub']
    user = await user_service.get_user_by_google_id(google_id=google_provider_id, db=db)

    if user:
        frontend_url = "https://synapse-front-end.vercel.app"
        redirect_response = RedirectResponse(url=f"{frontend_url}/dashboard")
        refresh_token = create_refresh_token(data={"sub": str(user.uuid)})
        redirect_response.set_cookie(
            key="refresh_token", value=refresh_token, httponly=True, samesite='lax', secure=True, path='/'
        )
        return redirect_response

    completion_token = create_completion_token(
        data={"google_provider_id": google_provider_id, "email": user_info['email'], "full_name": user_info.get('name')}
    )
    frontend_url = "https://synapse-front-end.vercel.app"
    redirect_url = f"{frontend_url}/auth/google/callback?token={completion_token}"
    return RedirectResponse(url=redirect_url)


@router.patch("/complete-profile", response_model=Token)
async def complete_google_user_profile(
    profile_data: ProfileCompletion,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    payload: Annotated[dict, Depends(get_completion_token_payload)],
    user_service: UserService = Depends()
):
    if await user_service.get_user_by_username(username=profile_data.username, db=db):
        raise HTTPException(status_code=400, detail="Username is already taken")
    
    user = await user_service.create_user_from_google(
        profile_data=profile_data, google_id=payload.get("google_provider_id"),
        email=payload.get("email"), full_name=payload.get("full_name"), db=db
    )
    
    access_token = create_access_token(data={"sub": str(user.uuid)})
    refresh_token = create_refresh_token(data={"sub": str(user.uuid)})
    
    content = {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    response = JSONResponse(content=content)
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, samesite='lax', secure=False, path='/', domain="localhost"
    )
    return response


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user_service: UserService = Depends(),
    refresh_token: Annotated[str | None, Depends(get_refresh_token_from_cookie)] = None
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

    try:
        payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_uuid_str: str = payload.get("sub")
        if user_uuid_str is None: raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = await user_service.get_user_by_uuid(id=uuid.UUID(user_uuid_str), db=db)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
        
    new_access_token = create_access_token(data={"sub": str(user.uuid)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.uuid)})

    content = {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    response = JSONResponse(content=content)
    response.set_cookie(
        key="refresh_token", value=new_refresh_token, httponly=True, samesite='lax', secure=False, path='/', domain="localhost"
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Successfully logged out"})
    response.delete_cookie("refresh_token", path='/', domain="localhost")
    return response