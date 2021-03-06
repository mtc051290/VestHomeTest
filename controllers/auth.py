import sys
from sqlalchemy.sql.expression import false
sys.path.append("..")
from fastapi import Request
from typing import Optional
from models import models
from controllers.users_functions import validate_new_user
from passlib.context import CryptContext
from utils import exceptions
from utils.database import get_db
from datetime import datetime, timedelta
from jose import jwt,JWTError

"""
This contains the main features to authenticate the user
"""

#MySecret Key
SECRET_KEY="THISISATESTFORVEST" # Used in encryption
ALGORITHM="HS256"
bcrypt_context= CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """
    Password is stored in the database as a hashed crypt
    """
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password,hashed_password)


def authenticate_user(username: str, password: str,db):
    """
    Verify the user's credentials and generate a new token, which
    is the only thing required to make requests to the API.
    """
    user=db.query(models.VestUsers).filter(models.VestUsers.username==username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username:str, user_id:int, 
                        expires_delta: Optional[timedelta]=None):
    """
    Generates a JWT Token
    """
    encode={
        "sub":username,
        "id": user_id
    }
    if expires_delta:
        expire=datetime.utcnow()+expires_delta
    else:
        expire=datetime.utcnow()+timedelta(weeks=10)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user( request: Request):
    """
    Decrypts the token and validates if the user has permissions
     and if the token has not expired
    """
    body = await request.json()
    token = body['token']
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise exceptions.get_user_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise exceptions.get_user_exception()