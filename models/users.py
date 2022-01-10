from pydantic import BaseModel, Field
from typing import Optional


class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str
    is_active: bool 

class CreatedUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    is_active: bool



class LoginTokenUser(BaseModel):
    username: str = "mtc590"
    password: str = "test1234!"
