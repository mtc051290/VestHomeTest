from pydantic import BaseModel, Field
from typing import Optional

"""
Models for new users and response models
"""

# Required for a new user
class CreateUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    password: str
    is_active: bool 

# Response for created user
class CreatedUser(BaseModel):
    username: str
    email: Optional[str]
    first_name: str
    last_name: str
    is_active: bool

# Asking for a new token, defaults set for an existing user
class LoginTokenUser(BaseModel):
    username: str = "mtc590"
    password: str = "test1234!"
