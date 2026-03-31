import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.db.models.user import User

# Optional bearer — does not reject missing tokens
_bearer_optional = HTTPBearer(auto_error=False)
# Required bearer — rejects missing tokens
_bearer_required = HTTPBearer(auto_error=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_required),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require a valid JWT. Returns the authenticated User."""
    from app.services.auth_service import decode_access_token, get_user_by_id

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional auth — returns User if token present and valid, None otherwise."""
    if not credentials:
        return None

    from app.services.auth_service import decode_access_token, get_user_by_id

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None

    return await get_user_by_id(db, uuid.UUID(payload["sub"]))


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to be an admin."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
