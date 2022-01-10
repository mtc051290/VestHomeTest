from fastapi import FastAPI, status
import models.users
from models import models
from utils.database import engine
from routers import users, trading
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi import Depends, HTTPException, status, Request
from starlette.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware



description =   """
                Testing in real time...
                """

models.Base.metadata.create_all(bind=engine)

class BadRequestData(Exception):
    def __init__(self, books_to_return):
        self.books_to_return = books_to_return


app = FastAPI()

app.include_router( users.router )
app.include_router( trading.router )

# Used for documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema =  get_openapi(
        title      =  "Vest | Senior Backend Engineer - Take Home Test",
        version    =  "1.1",
        contact    =  {
            "name"    :  "ISDR Miguel Jesús Torres Cárdenas",
            "GitHub"  :  "https://github.com/mtc051290/VestTestApp",
            "email"   :  "mtc590@gmail.com",
        },
        description = "Making changes for Open Market hours",
        routes = app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url" : "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi