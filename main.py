from fastapi import FastAPI
import models.users
from models import models
from utils.database import engine
from routers import users, trading
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

description =   """
                Vest Test
                """

# Generate tables
models.Base.metadata.create_all(bind=engine)

# Defines an exception for bad request
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
        title      =  "Vest | Backend Engineer - Take Home Test",
        version    =  "1.1",
        contact    =  {
            "name"    :  "ISDR Miguel Jesús Torres Cárdenas",
            "GitHub"  :  "https://github.com/mtc051290/VestTestApp",
            "email"   :  "mtc590@gmail.com",
        },
        description = "API developed with FastAPI, MySQL and authentication tools for a trading application",
        routes = app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url" : "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi