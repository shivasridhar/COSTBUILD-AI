"""
FastAPI Authentication Router for BuildCost AI — JWT Auth & User Management.

Implements registration, login, profile inspection, password hashing (bcrypt),
and JWT bearer token validation dependencies.
"""

import os
import sqlite3
import datetime
from typing import Optional, Dict, Any

import jwt
import bcrypt
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

from src.optimization.bom_optimizer import DEFAULT_DB_PATH

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "buildcost-secret-key-change-in-production-2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ---------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------

class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address", example="engineer@buildcost.ai")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)", example="SecurePass123!")
    name: Optional[str] = Field(None, description="Full name or display name", example="Priya Sharma")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address", example="engineer@buildcost.ai")
    password: str = Field(..., description="Password", example="SecurePass123!")


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hashes plaintext password using bcrypt with automatic salt (truncated to 72 bytes)."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext password against stored bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


# ---------------------------------------------------------------------
# Auth Dependency: get_current_user
# ---------------------------------------------------------------------

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency extracting and validating JWT bearer token from Authorization header.
    Returns authenticated user dict or raises HTTP 401.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims: missing sub.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user_id = int(user_id_raw)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    conn = get_db_connection()
    try:
        user_row = conn.execute("SELECT id, email, name, created_at FROM users WHERE id = ?;", (user_id,)).fetchone()
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return {
            "id": user_row["id"],
            "email": user_row["email"],
            "name": user_row["name"],
            "created_at": user_row["created_at"]
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register New Engineer Account")
def register(payload: UserRegisterRequest):
    """
    Registers a new user with hashed password and immediately returns a signed JWT access token.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existing = cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?);", (payload.email,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )

        hashed_pwd = hash_password(payload.password)
        now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        cursor.execute(
            """
            INSERT INTO users (email, hashed_password, name, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (payload.email.lower().strip(), hashed_pwd, payload.name, now_iso)
        )
        user_id = cursor.lastrowid
        conn.commit()

        user_resp = UserResponse(
            id=user_id,
            email=payload.email.lower().strip(),
            name=payload.name,
            created_at=now_iso
        )

        token = create_access_token(data={"sub": str(user_id), "email": user_resp.email})
        return TokenResponse(access_token=token, token_type="bearer", user=user_resp)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register account: {str(e)}"
        )
    finally:
        conn.close()


@router.post("/login", response_model=TokenResponse, summary="Login & Issue JWT Access Token")
def login(payload: UserLoginRequest):
    """
    Verifies user credentials and returns a JWT access token.
    Uses generic error message ("Invalid email or password") to prevent user enumeration.
    """
    conn = get_db_connection()
    try:
        user_row = conn.execute(
            "SELECT id, email, hashed_password, name, created_at FROM users WHERE LOWER(email) = LOWER(?);",
            (payload.email.strip(),)
        ).fetchone()

        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

        if not user_row:
            raise generic_error

        if not verify_password(payload.password, user_row["hashed_password"]):
            raise generic_error

        user_resp = UserResponse(
            id=user_row["id"],
            email=user_row["email"],
            name=user_row["name"],
            created_at=user_row["created_at"]
        )

        token = create_access_token(data={"sub": str(user_resp.id), "email": user_resp.email})
        return TokenResponse(access_token=token, token_type="bearer", user=user_resp)
    finally:
        conn.close()


@router.get("/me", response_model=UserResponse, summary="Get Current User Profile")
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns profile information for the authenticated user based on JWT bearer token.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        created_at=current_user["created_at"]
    )
