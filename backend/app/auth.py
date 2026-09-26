import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User

SECRET = os.environ['JWT_SECRET']
ALGORITHM = 'HS256'
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2 = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

def hash_password(value: str) -> str:
    return pwd.hash(value)

def verify_password(value: str, hashed: str) -> bool:
    return pwd.verify(value, hashed)

def create_token(user: User) -> str:
    payload = {'sub': str(user.id), 'role': user.role, 'exp': datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        data = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user = db.get(User, int(data['sub']))
    except (JWTError, KeyError, ValueError):
        user = None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='Invalid authentication')
    return user
