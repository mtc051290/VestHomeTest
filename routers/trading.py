from logging import exception
import sys
from typing import final

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
from utils.database import get_db
from datetime import datetime
from controllers.auth import get_current_user
from controllers import trading_functions
from controllers.trading_functions import num_to_money, dict_format
from utils.helper_variables import hack_headers, time_zone
from controllers import routes_functions
import asyncio
 

router = APIRouter(
    prefix    = "/trading",
    tags      = [ "Trading" ],
    responses = {
        201: {  "Trade"   :  "Purchase Created"  },
        401: {  "Trade"   :  "Not Authorized"    },
        404: {  "Trade"   :  "Stock Not Found"   }
    }
)

# BUY ENDPOINT
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

    #Create a new lot
    lots_list = [ trading_functions.create_lot( data, user.get('id'), buy_shares.quantity ) ]

    # If market is closed, purchase will be applied when market opens
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False

    last_price = float( data['primaryData']['lastSalePrice'][1:] )
    total_paid_shares = buy_shares.quantity * last_price
    print(total_paid_shares)
    if user_stocks is None:
        # Create new stock for user
        new_user_stock = models.UserStocks(
            owner_id           =  user.get('id'),
            nasdaq_stock_id    =  stock_id,
            company            =  data['companyName'],
            symbol             =  data['symbol'],
            created_date       =  datetime.now(time_zone),
            lots               =  str(lots_list),
            sells              =  "",
            num_held_shares    =  buy_shares.quantity,
            held_paid_shares   =  total_paid_shares,
            delta              =  0,
            has_pending        =  pending
        )
        db.add( new_user_stock )
        db.commit()
    else:
        # Update user stock list
        lots = dict_format(user_stocks.lots)
        lots_list_pre = lots
        lots_list.extend( lots_list_pre )
        user_stocks.lots = str( lots_list ) 

        # Update User Stocks
        user_stocks.num_held_shares += buy_shares.quantity
        user_stocks.held_paid_shares += total_paid_shares
        user_stocks.has_pending = pending
        db.add( user_stocks )
        db.commit()
        
    # If the market is closed, orders will be applied when it opens
    if pending == True:
        msg = "Your order will be applied as soon as the market opens"
    else: 
        msg = "Your order has been applied successfully"

    # Return purchase summary
    last_sale_price = data['primaryData']['lastSalePrice'][1:]
    total_price = (float(buy_shares.quantity) * float( last_sale_price))
    date_time_now = datetime.now( time_zone ).strftime( "%Y-%m-%d %H:%M:%f" )
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
            pending                 =  pending,
            message                 =  msg
        )
        return purchase_summary
    except BaseException as e:
        raise BaseException("Service Failure", e, e.args)



# SELL ENDPOINT
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

    # Check if user has enough shares to sell
    if user_stocks.num_held_shares < sell_shares.quantity:
        raise exceptions.not_available_stock()

    lots = dict_format(user_stocks.lots)

    #Create a new sell
    sell_list = [ trading_functions.create_sell( data, user.get('id'), sell_shares.quantity, lots ) ]
    




    return False
 











    """
    # If market is closed, purchase will be applied when market opens
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False

    last_price = float( data['primaryData']['lastSalePrice'][1:] )
    total_paid_shares = buy_shares.quantity * last_price
    print(total_paid_shares)
    if user_stocks is None:
        # Create new stock for user
        new_user_stock = models.UserStocks(
            owner_id           =  user.get('id'),
            nasdaq_stock_id    =  stock_id,
            company            =  data['companyName'],
            symbol             =  data['symbol'],
            created_date       =  datetime.now(time_zone),
            lots               =  str(lots_list),
            sells              =  "",
            num_held_shares    =  buy_shares.quantity,
            held_paid_shares   =  total_paid_shares,
            delta              =  0,
            has_pending        =  pending
        )
        db.add( new_user_stock )
        db.commit()
    else:
        # Update user stock list
        lots = dict_format(user_stocks.lots)
        lots_list_pre = lots
        lots_list.extend( lots_list_pre )
        user_stocks.lots = str( lots_list ) 

        # Update User Stocks
        user_stocks.num_held_shares += buy_shares.quantity
        user_stocks.held_paid_shares += total_paid_shares
        user_stocks.has_pending = pending
        db.add( user_stocks )
        db.commit()
        
    # If the market is closed, orders will be applied when it opens
    if pending == True:
        msg = "Your order will be applied as soon as the market opens"
    else: 
        msg = "Your order has been applied successfully"

    # Return purchase summary
    last_sale_price = data['primaryData']['lastSalePrice'][1:]
    total_price = (float(buy_shares.quantity) * float( last_sale_price))
    date_time_now = datetime.now( time_zone ).strftime( "%Y-%m-%d %H:%M:%f" )
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
            pending                 =  pending,
            message                 =  msg
        )
        return purchase_summary
    except BaseException as e:
        raise BaseException("Service Failure", e, e.args)
    """






















    """
    Aquí empieza lo feo
    
    # For FIRST IN FIRST OUT:
    shares = dict_format( user_stocks.shares )

    if not isinstance( shares, list ):
        raise exceptions.general_service_exception

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
    user_stocks.shares = str(shares)
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
        unitary_sold_price  =  num_to_money( unitary_sold_price ),
        total_sold_price    =  num_to_money( total_sold_price ),
        total_bought_price  =  num_to_money( ac_bought_price ),
        difference          =  num_to_money( round(ac_difference, 4) ),
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
    """