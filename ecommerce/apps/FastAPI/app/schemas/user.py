from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class RecoverPasswordRequest(BaseModel):
    email: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
