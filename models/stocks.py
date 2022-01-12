import sys
from pydantic.fields import Field
sys.path.append("..")
from pydantic import BaseModel
from fastapi import Response

"""
Models for Request
For this test, all requests are made in JSON, so it is
easier to test with other services such as PostMan
"""

def is_number(number: str):
    return True

# If something goes wrong with the response
class ErrorResponse(Response, Exception):
    message: str

# When could not find users or stocks
class NotFoundResponse(ErrorResponse):
    def status_code(self) -> int:
        return 404

# Response for a new Nasdaq Stock
class CreateNasdaqStock(BaseModel):
    company             : str
    symbol              : str
    created_date        : str
    day_price_lowest    : float
    day_price_highest   : float
    day_price_average   : float

# Fields required for purchases and validations
class BuyShares(BaseModel):
    quantity        : int = Field(1, gt=0, details="Must be grater than 0, no limits")
    company_symbol  : str = Field("AAPL", description="Upper o Lower cases")
    token           : str = Field("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtdGM1OTAiLCJpZCI6MTQsImV4cCI6MTY0Nzg1NDQxM30.GTobMEQn1rSDNGQHccai2nE7aHZfblJ8LK66YHV5OrA",
                description="Token set for test user 'mtc590' with password 'test1234!'")

# Fields required for sells and validations
class SellShares(BaseModel):
    quantity        : int = Field(1, gt=0, details="Must be grater than 0, no limits")
    company_symbol  : str = Field("AAPL", description="Upper o Lower cases")
    token           : str = Field("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtdGM1OTAiLCJpZCI6MTQsImV4cCI6MTY0Nzg1NDQxM30.GTobMEQn1rSDNGQHccai2nE7aHZfblJ8LK66YHV5OrA",
                description="Token set for test user 'mtc590' with password 'test1234!'")


# Fields required for getting stocks
class GetStocks(BaseModel):
    token           : str = Field("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtdGM1OTAiLCJpZCI6MTQsImV4cCI6MTY0Nzg1NDQxM30.GTobMEQn1rSDNGQHccai2nE7aHZfblJ8LK66YHV5OrA",
                description="Token set for test user 'mtc590' with password 'test1234!'")

# Required fields to obtain stock list
class GetStocksHours(BaseModel):
    symbol          : str = Field("AAPL", description="Upper o Lower cases")
    token           : str = Field("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtdGM1OTAiLCJpZCI6MTQsImV4cCI6MTY0Nzg1NDQxM30.GTobMEQn1rSDNGQHccai2nE7aHZfblJ8LK66YHV5OrA",
                description="Token set for test user 'mtc590' with password 'test1234!'")


# Purchase data generated
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


# Sells data generated
class SaleSummary(BaseModel):
    date_time_sold           : str
    company                  : str
    symbol                   : str
    total_sold_shares        : int 
    unitary_sold_price       : str
    total_sold_amount        : str 
    total_bought_amount      : str
    difference               : str
    profit_loss              : str
    is_real_time             : bool 
    market_status            : str
    pending                  : bool
    message                  : str