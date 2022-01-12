import sys
from sqlalchemy.sql.expression import false
sys.path.append("..")
from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Form
from pydantic import BaseModel
from typing import Optional
from models import models, users
from controllers.users_functions import validate_new_user
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



"""
Never used
"""


templates=Jinja2Templates(directory="templates")

#MySecret Key
SECRET_KEY="MyLittleDogIsKoa"
ALGORITHM="HS256"
bcrypt_context= CryptContext(schemes=["bcrypt"], deprecated="auto")

# This gets all the authorization data from headers
oauth2_bearer=OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {
            "user": "Not Authorized"
        }
    }
)

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request=request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username=form.get("email")
        self.password=form.get("password")



def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password,hashed_password)

def authenticate_user(username: str, password: str,db):
    user=db.query(models.Users).filter(models.Users.username==username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(username:str, user_id:int, 
                        expires_delta: Optional[timedelta]=None):
    encode={
        "sub":username,
        "id": user_id
    }
    if expires_delta:
        expire=datetime.utcnow()+expires_delta
    else:
        expire=datetime.utcnow()+timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)



#async def get_current_user(token: str = Depends(oauth2_bearer)):
async def get_current_user(request: Request):
    try: 
        token=request.cookies.get("access_token")
        if token is None:
            return None
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username:str=payload.get("sub")
        user_id: int=payload.get("id")
        if username is None or user_id is None:
            #raise get_user_exception()
            logout(request)
        return {
            "username": username,
            "id": user_id
        }
    except JWTError:
        raise get_user_exception()



@router.post("/create/user", response_model=users.CreatedUser, status_code=status.HTTP_201_CREATED)
async def create_new_user(create_user: users.CreateUser,db: Session=Depends(get_db)):
    try:
        if validate_new_user():
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


@router.post("/token")
async def login_for_access_token(response: Response,
                                form_data: OAuth2PasswordRequestForm=Depends(),
                                db: Session=Depends(get_db)):
    user=authenticate_user(form_data.username,form_data.password,db)
    if not user:
        return False
    token_expires=timedelta(minutes=60)
    token=create_access_token(user.username, user.id, expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True




# Exceptions not used in FullStack
def get_user_exception():
    credential_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentiales",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return credential_exception


def token_exception():
    token_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )
    return token_exception

def bad_user_create_request_exception():
    exception_response=HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid user data",
        headers={"X-Error": "Invalid user data"},
    )
    return exception_response