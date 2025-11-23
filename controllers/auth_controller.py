import os
import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database.database import SessionLocal
from models.user import User
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme")
JWT_ALGORITHM = "HS256"
JWT_EXP_DAYS = 30


class UserRegister(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    if len(user.password) > 72:
        raise HTTPException(
            status_code=400, detail="Password cannot be longer than 72 characters"
        )
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    new_user = User(
        id=uuid.uuid4(),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=hashed_password,
        role="user",
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # Generar token JWT igual que en login
    payload = {
        "user_id": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXP_DAYS),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return {
        "msg": "User registered successfully",
        "access_token": token,
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "role": new_user.role,
            "created_at": (
                new_user.created_at.isoformat() if new_user.created_at else None
            ),
        },
    }


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not bcrypt.checkpw(
        user.password.encode("utf-8"), db_user.password.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    payload = {
        "user_id": str(db_user.id),
        "email": db_user.email,
        "role": db_user.role,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXP_DAYS),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return {
        "msg": "Login successful",
        "access_token": token,
        "user_id": str(db_user.id),
        "role": db_user.role,
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "first_name": db_user.first_name,
            "last_name": db_user.last_name,
            "role": db_user.role,
            "created_at": (
                db_user.created_at.isoformat() if db_user.created_at else None
            ),
        },
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    import jwt
    import os

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme")
    JWT_ALGORITHM = "HS256"
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
