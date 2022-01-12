from asyncio.events import set_event_loop
import sys
sys.path.append("..")
from sqlalchemy.sql.expression import false, null, true
from models.stocks import BuyShares, PurchaseSummary, SaleSummary, SellShares, GetStocks
import requests
from fastapi import Depends, status, APIRouter, Request, Response, Form, Header
from pydantic import Field
from models import models
from controllers.users_functions import validate_new_user
from sqlalchemy.orm import Session
from utils import exceptions
from utils.database import get_db
from datetime import datetime
from controllers.auth import get_current_user
from controllers import trading_functions
from controllers.trading_functions import num_to_money, dict_format
from utils.helper_variables import hack_headers, time_zone 
from controllers import routes_functions

router = APIRouter(
    prefix    = "/trading",
    tags      = [ "Trading" ],
    responses = {
        201: {    "Trade"   :  "Purchase Created"       },
        401: {    "Trade"   :  "Not Authorized"         },
        404: {    "Trade"   :  "Stock Not Found"        },
        422: {    "Trade"   :  "Unprocessable Entity"   },
    }
)


###################### BUY ENDPOINT ######################
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
    try:
        response = requests.get( url_quote_info, 
                            params=my_params, 
                            headers = hack_headers, 
                            timeout=15 )
    except:
        raise exceptions.nasdaq_api_exception

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

    data['primaryData']['lastSalePrice']="$172.66" #Testing
    #Create a new lot
    lots_list = [ trading_functions.create_lot( data, user.get('id'), buy_shares.quantity ) ]

    # If market is closed, purchase will be applied when market opens
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False

    last_price = float( data['primaryData']['lastSalePrice'][1:] )
    total_paid_shares = buy_shares.quantity * last_price

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
            total_paid_shares   =  total_paid_shares,
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
        lots_list = trading_functions.change_pending_status( lots_list, pending )
        user_stocks.lots = str( lots_list ) 

        # Update User Stocks
        user_stocks.num_held_shares += buy_shares.quantity
        user_stocks.held_paid_shares += total_paid_shares
        user_stocks.total_paid_shares += total_paid_shares
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



###################### SELL ENDPOINT ######################
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
    try:
        response = requests.get( url_quote_info, 
                            params=my_params, 
                            headers=hack_headers, 
                            timeout=15 )
    except BaseException as e:
        raise BaseException("Service Failure", e, e.args)

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
        raise exceptions.not_enough_stock()

    lots = dict_format(user_stocks.lots)

    # If market is closed, purchase will be applied when market opens
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False

    #Create a new sell
    sell_list, lots   = trading_functions.create_sell( data, user.get('id'), sell_shares.quantity, lots )
    final_sell_list   = [ dict(sell_list) ]
    pre_sell_list = []
    if len(user_stocks.sells) > 0:
        pre_sell_list     = dict_format(user_stocks.sells)

    final_sell_list.extend( pre_sell_list )
    final_sell_list = trading_functions.change_pending_status( final_sell_list, pending )

    # If the market is closed, orders will be applied when it opens
    if sell_list['pending'] == True:
        msg = "Your order will be applied as soon as the market opens"
    else: 
        msg = "Your order has been applied successfully"

    profit_loss = sell_list['profit_loss'] * 100
    sell_summary = SaleSummary(
        date_time_sold      =  sell_list['sold_date'],
        company             =  data['companyName'],
        symbol              =  data['symbol'],
        total_sold_shares   =  sell_shares.quantity,
        unitary_sold_price  =  num_to_money( sell_list['sold_price'] ),
        total_sold_amount   =  num_to_money( sell_list['sold_total'] ),
        total_bought_amount =  num_to_money( sell_list['total_paid'] ),
        difference          =  num_to_money( sell_list['delta'] ),
        profit_loss         =  f'{profit_loss}%',
        is_real_time        =  data['primaryData']['isRealTime'],
        market_status       =  data['marketStatus'],
        pending             =  sell_list['pending'],
        message             =  msg
    )

    # Update User Stock, shares held, delta, total paid amount
    user_stocks.num_held_shares -= sell_shares.quantity
    user_stocks.held_paid_shares -= sell_list['total_paid']
    user_stocks.delta += sell_list['delta']
    user_stocks.has_pending = sell_list['pending']
    user_stocks.lots = str( lots )
    user_stocks.sells = str( final_sell_list )

    db.add( user_stocks )
    db.commit()
    return sell_summary




###################### LIST STOCKS ######################
@router.post("/stocks", status_code = status.HTTP_201_CREATED)
async def stock_list( get_stocks        : GetStocks,
                      user              :  dict = Depends( get_current_user ),
                      db                :  Session = Depends( get_db )
                    ):
    """
    As a POST so you can modify token easily 
    Token set for user 'mtc590' (No expericy)
    Get a list of the stocks you are holding
    """
    # Check for authorization
    if user is None:
        raise exceptions.get_user_exception()

    # Fetch
    user_stocks = db.query( models.UserStocks )\
        .filter( models.UserStocks.owner_id == user.get( 'id' ))\
        .all()

    stocks_response = []
    for stock in user_stocks:
        last_price = routes_functions.get_price_nasdaq( stock.symbol )
        final_high, final_low, average, msg = routes_functions.get_real_average_nasdaq( stock.symbol )
        shares_current_value = stock.num_held_shares * last_price
        profit_loss = stock.delta + shares_current_value - stock.held_paid_shares
        profit_loss = profit_loss / stock.total_paid_shares * 100
        profit_loss = round( profit_loss,4 )
        stock_element = {
            'company'               : stock.company,
            'symbol'                : stock.symbol,
            'last_price'            : num_to_money( last_price ),
            'held_shares'           : str( stock.num_held_shares),
            'shares_current_value'  : num_to_money( round( shares_current_value, 4) ),
            'today_lowest_price'    : num_to_money( round( final_low, 4) ),
            'today_highest_price'   : num_to_money( round( final_high, 4) ),
            'today_average_price'   : num_to_money( round( average, 4) ),
            'profit_loss'           : f'{profit_loss}%'
        }
        for_list_stock = [ stock_element ]
        stocks_response.extend( for_list_stock )

    return stocks_response



