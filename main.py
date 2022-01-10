from fastapi import FastAPI, status
import models.users
from models import models
from utils.database import engine
from routers import auth, users, trading
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi import Depends, HTTPException, status, Request
from starlette.responses import JSONResponse



description = """
    Requirements:
    This is necesary blab 

    Token expires every 20 minutes
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

@app.exception_handler(BadRequestData)
async def negative_number_exception_handler(request: Request,
                                            exception: BadRequestData):
    return JSONResponse(
        status_code=400,
        content={"message": f"Bad Request"}
    )

#app.include_router(auth.router)
app.include_router(users.router)
app.include_router(trading.router)
