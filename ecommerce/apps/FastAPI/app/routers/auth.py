from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.FastAPI.app.auth_utils import create_access_token, hash_password, verify_password
from apps.FastAPI.app.deps import get_session
from apps.FastAPI.app.schemas.user import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RecoverPasswordRequest,
    RegisterRequest,
    UserResponse,
)
from packages.core.infrastructure.db.models import UserModel

router = APIRouter(prefix="/v1/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]


def _to_auth_response(user_model: UserModel) -> AuthResponse:
    access_token = create_access_token(
        subject=user_model.id,
        email=user_model.email,
        is_admin=user_model.is_admin,
    )
    return AuthResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_model.id,
            email=user_model.email,
            is_admin=user_model.is_admin,
        ),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: SessionDep) -> AuthResponse:
    email = payload.email.strip().lower()
    existing = session.scalar(select(UserModel).where(UserModel.email == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_model = UserModel(
        id=str(uuid4()),
        email=email,
        hashed_password=hash_password(payload.password),
        is_admin=False,
    )
    session.add(user_model)
    session.commit()
    session.refresh(user_model)

    return _to_auth_response(user_model)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, session: SessionDep) -> AuthResponse:
    email = payload.email.strip().lower()
    user_model = session.scalar(select(UserModel).where(UserModel.email == email))

    if user_model is None or not verify_password(payload.password, user_model.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return _to_auth_response(user_model)


@router.post("/recover-password", response_model=MessageResponse)
def recover_password(payload: RecoverPasswordRequest, session: SessionDep) -> MessageResponse:
    email = payload.email.strip().lower()
    user_model = session.scalar(select(UserModel).where(UserModel.email == email))

    if user_model is not None:
        user_model.hashed_password = hash_password(payload.new_password)
        session.add(user_model)
        session.commit()

    return MessageResponse(message="If the account exists, password has been updated.")
