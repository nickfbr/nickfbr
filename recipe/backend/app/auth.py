from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.errors import AppError
from app.models import User

settings = get_settings()
# pbkdf2_sha256 is pure-Python in passlib (no native bcrypt build/version
# coupling) and is a solid password hash. bcrypt hashes are still verifiable
# if present, easing future migration.
_pwd = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise AppError("UNAUTHORIZED", "Authentication required.", status_code=401)
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise AppError("UNAUTHORIZED", "Invalid or expired token.", status_code=401)

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise AppError("UNAUTHORIZED", "User no longer exists.", status_code=401)
    return user
