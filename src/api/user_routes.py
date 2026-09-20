from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from service.user_service import authenticate_user, register_new_user

router = APIRouter(prefix="/api/users", tags=["users"])


class RegisterUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class RegisterUserResponse(BaseModel):
    user_id: str
    message: str = "User registered successfully"


class LoginUserRequest(BaseModel):
    username_or_email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    user_id: str
    username: str
    display_name: str
    email: str


@router.post(
    "/register",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(request: RegisterUserRequest) -> RegisterUserResponse:
    user_id = register_new_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    return RegisterUserResponse(user_id=user_id)


@router.post("/login", response_model=UserResponse)
def login(request: LoginUserRequest) -> UserResponse:
    user = authenticate_user(
        username_or_email=request.username_or_email,
        password=request.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
        )
    return UserResponse(**user)
