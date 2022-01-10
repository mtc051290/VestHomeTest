import sys
from pydantic.fields import Field
sys.path.append("..")
from pydantic import BaseModel, validator
from typing import Optional
from utils import exceptions
from pydantic.typing import display_as_type
from starlette.responses import JSONResponse




"""
    VALIDATORS
"""
def is_number(number: str):
    return True


class CreateNasdaqStock(BaseModel):
    company             : str
    symbol              : str
    created_date        : str
    day_price_lowest    : float
    day_price_highest   : float
    day_price_average   : float


class BuyShares(BaseModel):
    quantity        : int = Field(1, gt=0, details="Must be grater than 0, no limits")
    company_symbol  : str = Field("AAPL", description="Upper o Lower cases")
    token           : str = Field("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtdGM1OTAiLCJpZCI6MTQsImV4cCI6MTY0Nzg1NDQxM30.GTobMEQn1rSDNGQHccai2nE7aHZfblJ8LK66YHV5OrA",
                description="Token set for test user 'mtc590' with password 'test1234!'")


class SellShares(BaseModel):
    quantity        : int = Field(1, gt=0, details="Must be grater than 0, no limits")
    company_symbol  : str = Field("AAPL", description="Upper o Lower cases")
    token           : str = Field("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtdGM1OTAiLCJpZCI6MTQsImV4cCI6MTY0Nzg1NDQxM30.GTobMEQn1rSDNGQHccai2nE7aHZfblJ8LK66YHV5OrA",
                description="Token set for test user 'mtc590' with password 'test1234!'")



class PurchaseSummary(BaseModel):
    date_time_purchase       : str
    company                  : str
    symbol                   : str
    total_purchased_shares   : int 
    unitary_price            : str
    total_price              : str
    is_real_time             : bool 
    market_status            : str
    pending                  : bool
    message                  : str


class SaleSummary(BaseModel):
    date_time_sold           : str
    company                  : str
    symbol                   : str
    total_sold_shares        : int 
    unitary_sold_price       : str
    total_sold_price         : str 
    total_bought_price       : str
    difference               : str
    profit_loss              : str
    is_real_time             : bool 
    market_status            : str
    pending                  : bool
    message                  : str



