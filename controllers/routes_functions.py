from logging import exception
import sys

from yaml.loader import FullLoader
sys.path.append("..")
from sqlalchemy.sql.expression import false, null, true
from utils.exceptions import symbol_exception
from models.stocks import BuyShares, PurchaseSummary, SaleSummary, SellShares
import requests
from fastapi import Depends, status, APIRouter, Request, Response, Form, Header
from starlette.exceptions import HTTPException
from pydantic import Field, ValidationError
from models import models
from controllers.users_functions import validate_new_user
from sqlalchemy.orm import Session
from utils.database import SessionLocal, engine
from utils import exceptions
from utils.database import get_new_db
from datetime import datetime
from controllers.auth import get_current_user
from controllers import trading_functions
from controllers.trading_functions import num_to_money, dict_format
from utils.helper_variables import hack_headers, time_zone


async def buy_shares( user, buy_shares, db ):


    my_params = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{buy_shares.company_symbol}/info"
    response = requests.get( url_quote_info, 
                            params=my_params, 
                            headers = hack_headers, 
                            timeout=5 )
    data   = response.json()['data']
    status = response.json()['status']

    # Throw an error if symbol does not exist or could not get data from api
    if status['rCode'] == 400:
        raise exceptions.symbol_exception()
    if status['rCode'] != 200:
        raise exceptions.nasdaq_api_exception()
    
    # Create stock in database if it does not exist
    stock_id = trading_functions.create_nasdaq_stock_if_not_exists( data, db )
    
    # Fetch, then create or add lots
    user_stocks = db.query( models.UserStocks )\
        .filter( models.UserStocks.owner_id == user.get('id') )\
        .filter( models.UserStocks.symbol  == data['symbol'] )\
        .first()

    create_lot_params =  data, user.get('id'), buy_shares.quantity 
    shares_list = [ trading_functions.create_lot( create_lot_params) ]


    print(shares_list)


    """
    num_shares_held, has_pending = trading_functions.get_num_held_shares( shares_list )

    if user_stocks is None:
        # Create new stock for user
        new_user_stock = models.UserStocks(
            owner_id         =  user.get('id'),
            nasdaq_stock_id  =  stock_id,
            company          =  data['companyName'],
            symbol           =  data['symbol'],
            created_date     =  datetime.now(time_zone),
            shares           =  str(shares_list),
            num_held_shares  =  num_shares_held,
            has_pending      =  has_pending
        )
        db.add( new_user_stock )
        db.commit()
    else:
        # Update user stock list
        shares = dict_format(user_stocks.shares)
        shares_list_pre = shares
        shares_list.extend( shares_list_pre )
        user_stocks.shares = str( shares_list ) 

        db.add( user_stocks )
        db.commit()
        user_stocks.shares = dict_format( user_stocks.shares )

    # If the market is closed, orders will be applied at 9:30 AM weekdays
    if has_pending == True:
        msg = "Your order will be applied as soon as the market opens"
    else: 
        msg = "Your order has been applied successfully"

    # Return purchase summary
    last_sale_price = data['primaryData']['lastSalePrice'][1:]
    total_price = (float(buy_shares.quantity) * float( last_sale_price))
    date_time_now = datetime.now( time_zone ).strftime("%Y-%m-%d %H:%M:%f")



    try:
        purchase_summary = PurchaseSummary(
            date_time_purchase      =  date_time_now,
            company                 =  data['companyName'],
            symbol                  =  data['symbol'],
            total_purchased_shares  =  buy_shares.quantity,
            unitary_price           =  num_to_money( last_sale_price ),
            total_price             =  num_to_money( round(total_price, 4) ),
            is_real_time            =  data['primaryData']['isRealTime'],
            market_status           =  data['marketStatus'],
            pending                 =  has_pending,
            message                 =  msg
        )
        return purchase_summary
    except BaseException as e:
        raise BaseException("Service Failure", e, e.args)
    """

















    purchase_summary = PurchaseSummary(
            date_time_purchase      =  "date_time_now",
            company                 =  "data['companyName']",
            symbol                  =  "data['symbol']",
            total_purchased_shares  =  1,
            unitary_price           =  "num_to_money( last_sale_price )",
            total_price             =  ",",
            is_real_time            =  True,
            market_status           =  "data['marketStatus']",
            pending                 =  True,
            message                 =  "msg"
        )
    return purchase_summary