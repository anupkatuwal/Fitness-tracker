"""Registration and JWT login (OAuth2 password bearer flow)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import User
from app.schemas import Token, UserCreate, UserGoalsUpdate, UserRead
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession) -> Token:
    email = payload.email.lower()
    username = payload.username.strip()

    existing = db.scalar(
        select(User).where(
            (func.lower(User.email) == email) | (func.lower(User.username) == username.lower())
        )
    )
    if existing is not None:
        field = "Email" if existing.email.lower() == email else "Username"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"{field} is already registered."
        )

    user = User(
        email=email,
        username=username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return Token(access_token=create_access_token(str(user.id)), user=UserRead.model_validate(user))


@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    """OAuth2 password flow. ``username`` accepts either a username or an email."""
    identifier = form_data.username.strip().lower()
    user = db.scalar(
        select(User).where(
            (func.lower(User.email) == identifier) | (func.lower(User.username) == identifier)
        )
    )

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled.")

    return Token(access_token=create_access_token(str(user.id)), user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(payload: UserGoalsUpdate, current_user: CurrentUser, db: DbSession) -> User:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
