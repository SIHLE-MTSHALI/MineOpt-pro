from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..domain import models_core
from ..services.auth_service import AuthService
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    email: str = None

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check existing
    existing = db.query(models_core.User).filter(models_core.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = models_core.User(
        username=user.username,
        email=user.email,
        password_hash=AuthService.get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "username": new_user.username}

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find User (or create default admin if not exists for demo)
    user = db.query(models_core.User).filter(models_core.User.username == form_data.username).first()
    
    if not user:
        if form_data.username == "admin" and form_data.password == "admin":
            # Auto-create admin
            user = models_core.User(
                username="admin", 
                email="admin@mineopt.com",
                password_hash=AuthService.get_password_hash("admin")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
            
    # 2. Verify Password
    if not AuthService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    # 3. Create Token
    access_token = AuthService.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = payload.get("sub")
    user = db.query(models_core.User).filter(models_core.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {"username": user.username, "email": user.email, "roles": ["admin"]} # Mock roles for MVP
