import uuid
from pydantic import BaseModel

# Schema for the token response
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Schema for the data encoded within the JWT
class TokenPayload(BaseModel):
    sub: str | None = None # 'sub' is standard for subject (user identifier)