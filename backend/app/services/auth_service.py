"""
Authentication service.

Handles user registration, login, and current-user retrieval.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.auth import TokenResponse, UserRegisterRequest, UserResponse

logger = get_logger(__name__)
security_scheme = HTTPBearer()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: UserRegisterRequest) -> TokenResponse:
        """Register a new user.

        Raises:
            HTTPException: If email is already registered.
        """
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        # Create user
        user = User(
            email=request.email,
            full_name=request.full_name,
            hashed_password=hash_password(request.password),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"New user registered: id={user.id}")

        # Generate token
        token = create_access_token({"sub": str(user.id), "email": user.email})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user and return a JWT token.

        Raises:
            HTTPException: If credentials are invalid.
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated.",
            )

        logger.info(f"User logged in: id={user.id}")

        token = create_access_token({"sub": str(user.id), "email": user.email})
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


# =============================================================================
# FastAPI Dependencies
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that extracts and validates the current user from JWT.

    Raises:
        HTTPException: If token is missing, invalid, or user not found.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    service = AuthService(db)
    user = await service.get_user_by_id(int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    return user
