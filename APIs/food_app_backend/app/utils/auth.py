from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app.database import get_db

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 10080))  # 7 days

# CryptContext handles bcrypt hashing
# bcrypt automatically salts and hashes — never store plain passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer extracts the token from "Authorization: Bearer <token>" header
bearer_scheme = HTTPBearer()


# ── Password utilities ────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Converts plain text password to bcrypt hash.
    Example: "mypassword123" → "$2b$12$abc...xyz"
    The hash is what gets stored in the database.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches the stored hash.
    Used during login — bcrypt rehashes and compares internally.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT utilities ─────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    """
    Creates a JWT token containing the user's ID.
    JWT = 3 base64 parts: header.payload.signature
    The payload has: sub (user id) + exp (expiry time)
    The secret key signs it so it cannot be tampered with.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),    # 'sub' = subject = who this token belongs to
        "exp": expire            # expiry timestamp
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> str:
    """
    Decodes and validates a JWT token.
    Returns user_id string if valid, raises 401 if invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Auth dependency ───────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    FastAPI dependency — inject into any route that requires a logged-in user.
    Reads the Bearer token from the request header, validates it,
    fetches the user from DB, and returns the User object.

    Usage in a route:
        @router.get("/protected")
        def protected(current_user = Depends(get_current_user)):
            return {"hello": current_user.name}
    """
    from app.models.user import User  # imported here to avoid circular imports

    token = credentials.credentials
    user_id = decode_access_token(token)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user