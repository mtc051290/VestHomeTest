from logging import exception
import sys
sys.path.append("..")
from sqlalchemy.sql.expression import false, true
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
from utils.database import get_db
from datetime import datetime
from controllers.auth import get_current_user
from controllers import trading_functions
from utils.helper_variables import hack_headers, time_zone
import json
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

router = APIRouter(
    prefix    = "/trading",
    tags      = [ "Trading" ],
    responses = {
        201: {  "Trade"   :  "Purchase Created"  },
        401: {  "Trade"   :  "Not Authorized"    },
        404: {  "Trade"   :  "Stock Not Found"   }
    }
)

@router.post("/buy", response_model = PurchaseSummary, status_code = status.HTTP_201_CREATED)
async def buy_shares( buy_shares  :  BuyShares,
                      user        :  dict = Depends( get_current_user ),
                      db          :  Session = Depends( get_db )
                    ):
    """
    Token set for user 'mtc590' (No expericy)
    """

    # Check for authorization
    if user is None:
        raise exceptions.get_user_exception()

    if isinstance( buy_shares.quantity, int) and buy_shares.quantity < 0:
        raise exceptions.bad_request_exception()

    # Get stocks data from api.nasdaq
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
    
    # Fetch, then create or add shares
    user_stocks = db.query( models.UserStocks )\
        .filter( models.UserStocks.owner_id == user.get('id') )\
        .filter( models.UserStocks.symbol  == data['symbol'] )\
        .first()

    shares_list = [ trading_functions.create_list_of_shares( data, user.get('id'), x )\
                    for x in range( buy_shares.quantity ) ]

    num_shares_held, has_pending = trading_functions.get_num_held_shares( shares_list )

    if user_stocks is None:
        # Create new stock for user
        new_user_stock = models.UserStocks(
            owner_id         =  user.get('id'),
            nasdaq_stock_id  =  stock_id,
            company          =  data['companyName'],
            symbol           =  data['symbol'],
            created_date     =  datetime.now(time_zone),
            shares           =  json.dumps(shares_list),
            num_held_shares  =  num_shares_held,
            has_pending      =  has_pending
        )
        db.add( new_user_stock )
        db.commit()
        print( stock_id )
    else:
        # Update user stock list
        shares_list_pre = json.loads( user_stocks.shares )
        shares_list.extend( shares_list_pre )
        user_stocks.shares = json.dumps( shares_list )
        db.add( user_stocks )
        db.commit()

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
            unitary_price           =  f'${last_sale_price}',
            total_price             =  f'${total_price}',
            is_real_time            =  data['primaryData']['isRealTime'],
            market_status           =  data['marketStatus'],
            pending                 =  has_pending,
            message                 =  msg
        )
        return purchase_summary
    except:
        raise exceptions.general_service_exception

    

@router.post( "/sell", response_model = SaleSummary, status_code = status.HTTP_200_OK )
async def sell_shares( sell_shares   : SellShares,
                       user          : dict    = Depends( get_current_user ),
                       db            : Session = Depends( get_db )
                     ):
    """
    Token set for user 'mtc590' (No expericy)
    """

    # Check for authorization
    if user is None:
        raise exceptions.get_user_exception()

    if isinstance( sell_shares.quantity, int ) and sell_shares.quantity < 0:
        raise exceptions.bad_request_exception()

    # Get stocks data from api.nasdaq
    my_params = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{sell_shares.company_symbol}/info"
    response = requests.get( url_quote_info, 
                            params=my_params, 
                            headers=hack_headers, 
                            timeout=5 )
    data   = response.json()['data']
    status = response.json()['status']

    # Throw an error if symbol not exists or could not get data from api
    if status['rCode'] == 400:
        raise exceptions.symbol_exception()
    if status['rCode'] != 200:
        raise exceptions.nasdaq_api_exception()
    
    # Fetch
    user_stocks = db.query( models.UserStocks )\
        .filter( models.UserStocks.owner_id == user.get( 'id' ))\
        .filter( models.UserStocks.symbol == data[ 'symbol' ])\
        .first()

    if user_stocks is None:
        raise exceptions.not_available_stock()

    # For FIRST IN FIRST OUT:
    shares = json.loads( user_stocks.shares )
    shares.reverse()
    for_sale = [ x for x in shares if x['sold']==False ]
    pending_for_sale = [ x for x in shares if x['pending'] == True ]
    available_shares = len( for_sale ) - len( pending_for_sale )
    print(len(for_sale))
    
    if available_shares < sell_shares.quantity:
        if len( pending_for_sale ) > 0:
            raise exceptions.not_enough_stock_and_pending()
        raise exceptions.not_enough_stock()
    
    # If the market is closed, orders will be applied at 9:30 AM weekdays
    if data[ 'marketStatus' ] == "Market Closed":
        msg = "This operation will be applied as soon as the market opens"
        pending = True
    else: 
        msg = "This operation has been applied successfully"
        pending = False

    # Apply FIFO, save the date, save sold price and market status
    count = 0
    ac_difference = 0.0
    ac_bought_price = 0.0
    for index, item in enumerate(shares):
        if count >= sell_shares.quantity :
            break
        if shares[index]['sold'] == shares[index]['pending'] == False:
            date_time_now = datetime.now( time_zone ).strftime("%Y-%m-%d %H:%M:%f")
            last_price = float( data['primaryData']['lastSalePrice'][1:] )
            bought_price = float( shares[index]['bought_price'] )
            profit_loss = ( last_price - bought_price ) / bought_price
            price_difference = last_price - bought_price
            ac_difference += price_difference
            ac_bought_price += bought_price
            shares[index]['held']         = False
            shares[index]['sold']         = True
            shares[index]['pending']      = pending
            shares[index]['sold_date']    = date_time_now
            shares[index]['sold_price']   = last_price
            shares[index]['profit_loss']  = profit_loss * 100
            shares[index]['difference']   = price_difference
            print("vender")
            count += 1

    shares.reverse()
    user_stocks.shares = json.dumps(shares)
    db.add(user_stocks)
    db.commit()
    
    ac_profit_loss     = ac_difference / ac_bought_price
    total_sold_price   = float( sell_shares.quantity ) * last_price
    unitary_sold_price = data['primaryData']['lastSalePrice'][1:]

    sell_summary = SaleSummary(
        date_time_sold      =  date_time_now,
        company             =  data['companyName'],
        symbol              =  data['symbol'],
        total_sold_shares   =  sell_shares.quantity,
        unitary_sold_price  =  f'${unitary_sold_price}',
        total_sold_price    =  f'${total_sold_price}',
        total_bought_price  =  f'${ac_bought_price}',
        difference          =  f'${round( ac_difference, 4 )}',
        profit_loss         =  f'{round( ac_profit_loss * 100, 4 )}%',
        is_real_time        =  data['primaryData']['isRealTime'],
        market_status       =  data['marketStatus'],
        pending             =  pending,
        message             =  msg
    )
    print(sell_summary)
    return sell_summary



    """

    """