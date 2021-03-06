import sys
from sqlalchemy.sql.expression import false

from models.stocks import BuyShares
sys.path.append("..")
from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form, Header
from pydantic import BaseModel
from typing import Optional
from models import models, users
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from utils.database import SessionLocal, engine
from utils import exceptions
from utils.database import get_db
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt,JWTError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from controllers.auth import get_password_hash, verify_password, authenticate_user, create_access_token
from controllers.auth import SECRET_KEY, ALGORITHM


"""
SECURITY FIRST, so I've implemented OAuth2 authentication and JWT
"""

# This gets all the authorization data from headers
oauth2_bearer=OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {
            "user": "Not Authorized"
        }
    }
)


# Get user with the token 
async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()
        return {"username": username, "id": user_id}
    except JWTError:
        raise get_user_exception()



# Create a new user
@router.post("/create/user", response_model=users.CreatedUser, status_code=status.HTTP_201_CREATED)
async def create_new_user(create_user: users.CreateUser,db: Session=Depends(get_db)):
    """
    When creating a new user it is required to make a request to "users / token"\n
    to obtain a new token and to be able to interact with the backend with a new user
    """
    try:
        created_user=create_user
        create_user_model=models.VestUsers()
        create_user_model.email=create_user.email
        create_user_model.username=create_user.username
        create_user_model.first_name=create_user.first_name
        create_user_model.last_name=create_user.last_name
        hash_password = get_password_hash(create_user.password)
        create_user_model.hashed_password=hash_password
        create_user_model.is_active=True
        db.add(create_user_model)
        db.commit()
        return  created_user
    except:
        raise exceptions.bad_user_create_request_exception()

# Login to get a new token
@router.post("/token")
async def login_for_access_token(user_to_login: users.LoginTokenUser,
                                db: Session = Depends(get_db)):
    """
    Create a new JWT token, the token is required for all requests
    """
    user = authenticate_user(user_to_login.username, user_to_login.password, db)
    if not user:
        raise token_exception()
    #token_expires = timedelta(minutes=20)
    token_expires = timedelta(weeks=10)
    token = create_access_token(user.username,
                                user.id,
                                expires_delta=token_expires)
    return {"token": token}

# If the user tries to use a non valid token
def get_user_exception():
    credential_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentiales",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return credential_exception

# Also for user authentication
def token_exception():
    token_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return token_exception

# If the user puts something wrong in the request
def bad_user_create_request_exception():
    exception_response=HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid user data",
        headers={"X-Error": "Invalid user data"},
    )
    return exception_response