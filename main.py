from fastapi import FastAPI, status
import models.users
from models import models
from utils.database import engine
from routers import auth, users, trading
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi import Depends, status, Request
from starlette.responses import JSONResponse


description = """
    Working on documentation...
    """

models.Base.metadata.create_all(bind=engine)

class BadRequestData(Exception):
    def __init__(self, books_to_return):
        self.books_to_return = books_to_return

app = FastAPI(
    title="Vest | Backend Engineer - Take Home Test",
    description=description,
    version="1.0",
    contact={
        "name": "Miguel Jesús Torres Cárdenas",
        "GitHub": "https://github.com/mtc051290/VestTestApp",
        "email": "mtc590@gmail.com",
    }
)

app.include_router(users.router)
app.include_router(trading.router)