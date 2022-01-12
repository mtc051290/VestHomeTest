from calendar import day_abbr
import sys
from VestApp.models.stocks import GetStocksHours
sys.path.append("..")
from sqlalchemy.sql.expression import false, null, true
from models.stocks import BuyShares, PurchaseSummary, SaleSummary, SellShares, GetStocks
import requests
from fastapi import Depends, status, APIRouter, Request, Response, Form, Header
from pydantic import Field
from models import models
from sqlalchemy.orm import Session
from utils import exceptions
from utils.database import get_db
from datetime import datetime, timedelta
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
    Token set for user 'mtc590' (No expericy)\n
    This route receives a request to buy x number of shares of a company\n
    determined by its symbol. The program gets the last price returned\n
    from the Nasdaq API and creates a new stock lot for the user.\n 
    In case the market is closed, the pending status is saved and the client\n
    is notified that the operation will be applied as soon as the market opens.
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
    Token set for user 'mtc590' (No expericy)\n\n
    The FIFO (First In First Out) procedure is applied to select the shares to be sold.\n
    The program loops through the oldest stock lots, changes their status, calculates\n
    the profit/loss, and records the sale in a sales pool. Prices bought at different\n
    times or days are taken into account and the last price recorded by Nasdaq is used \n
    to make the calculations.
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
    Token set for user 'mtc590' (No expericy)\n\n
    This route returns a detailed list of the stocks belonging to the user. \n
    You get the highest and lowest price in two ways:\n\n
    1) Reading the table issued by Nasdaq in real time and finding the highest\n
    price, lowest price and obtaining the average with that data.\n\n
    2) Check the information with the daily summary issued by Nasdaq and the program\n
    returns the highest and lowest value it finds, generally the summary has delays,\n
    so the real-time table is more reliable.
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


###################### LIST STOCKS BY HOUR ######################
@router.post("/hours", status_code = status.HTTP_201_CREATED)
async def list_by_hour( get_stocks        : GetStocksHours,
                        user              :  dict = Depends( get_current_user ),
                        db                :  Session = Depends( get_db )
                    ):
    """
    Token set for user 'mtc590' (No expericy)\n\n
    It receives the desired company symbol and obtains the Nasdaq real-time table,\n
    through iterations in the pool of lots and sales, the number of shares that exist\n
    for each hour is determined and the price is calculated at that time. It was developed\n
    this way to avoid creating threads that could clutter the application. The data is\n
    shown from when the market enters "Pre Market" and until "Post Market", so that during\n
    inactivity hours you will not be able to return a result.\n\n

    This is the section of the system that can be refactored the most.
    """

    # Check for authorization
    if user is None:
        raise exceptions.get_user_exception()

    my_params = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{get_stocks.symbol}/info"
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

     # Fetch
    user_stocks = db.query( models.UserStocks )\
        .filter( models.UserStocks.owner_id == user.get( 'id' ))\
        .filter( models.UserStocks.symbol == data[ 'symbol' ])\
        .first()

    if user_stocks is None:
        raise exceptions.not_available_stock()

    # GET Real Time Nasdaq Chart
    chart = trading_functions.get_nasdaq_chart_from_today( data['symbol'] )
    if chart == False:
        raise exceptions.nasdaq_api_exception()

    lots_list = dict_format(user_stocks.lots)
    sell_list = dict_format(user_stocks.sells)
    pre_hour = datetime.now(time_zone).strftime("%Y-%m-%d %H:%M:%f")
    post_hour = datetime.now() + timedelta(hours=2)
    lots_list.sort(key = lambda x: datetime.strptime(x['bought_date'], '%Y-%m-%d %H:%M:%f'))
    sell_list.sort(key = lambda x: datetime.strptime(x['sold_date'], '%Y-%m-%d %H:%M:%f'))
 
    # Get held shares until today
    now = datetime.now(time_zone).strftime("%Y-%m-%d %H:%M:%f")
    i = 0
    limit_datetime = datetime.now(time_zone).strftime("%Y-%m-%d 04:00:000000")
    date_compare = datetime.strptime(limit_datetime, '%Y-%m-%d %H:%M:%f')

    held_shares = 0
    ite_lots = 0
    ite_sells = 0
    while i < len(lots_list):
        if datetime.strptime(lots_list[i]['bought_date'], '%Y-%m-%d %H:%M:%f') < date_compare:
            qtyl = lots_list[ite_lots]['quantity']; print(f'L:{ite_lots} = {qtyl}')
            held_shares += lots_list[i]['quantity']
        else:
            break
        i +=1
        ite_lots +=1
    i = 0
    while i < len(sell_list):
        if datetime.strptime(sell_list[i]['sold_date'], '%Y-%m-%d %H:%M:%f') < date_compare:
            qtys = sell_list[ite_sells]['quantity']; print(f'S:{ite_sells} = {qtys}')
            held_shares -= sell_list[i]['quantity']
        else:
            break
        i +=1
        ite_sells += 1

    by_hours = list()

    # Get one hour range list
    i=0
    pre_hour1 = datetime.strptime(f"03:00:00 AM ET","%H:%M:%S %p ET")
    pre_hour2 = datetime.strptime("04:00:00 AM ET","%H:%M:%S %p ET")
    while i < len(chart):
        out = [ ele for ele in chart if 
                pre_hour1 <= datetime.strptime(ele['z']['dateTime'],'%H:%M:%S %p ET') <= pre_hour2 ]
        if len(out) == 0:
            print("sale")
            break
        out.reverse()
        pre_hour1 = pre_hour1 + timedelta(hours=1)
        pre_hour2 = pre_hour2 + timedelta(hours=1)
        i += 1
        open_price = out[0]['z']['value']
        close_price = out[-1]['z']['value']

        while ite_lots < len(lots_list):
            hour_lot = trading_functions.get_hour_from_string(lots_list[ite_lots]['bought_date'])
            hour_nas = trading_functions.get_hour_from_string(str(pre_hour2))
            if hour_lot >= hour_nas:
                break
            qtyl = lots_list[ite_lots]['quantity']; print(f'L:{ite_lots} = {qtyl}')
            held_shares += lots_list[ite_lots]['quantity']
            ite_lots += 1
  
        while ite_sells < len(sell_list):
            hour_sell = trading_functions.get_hour_from_string(sell_list[ite_sells]['sold_date'])
            hour_nas = trading_functions.get_hour_from_string(str(pre_hour2))
            if hour_sell >= hour_nas:
                break
            qtys = sell_list[ite_sells]['quantity']; print(f'S:{ite_sells} = {qtys}')
            held_shares -= sell_list[ite_sells]['quantity']
            ite_sells += 1
        
        total_open_price = float(open_price) * held_shares
        print(f'\n{pre_hour1}:{open_price} Total Price:{total_open_price}')
        hour_open = trading_functions.get_hour_from_string( str(pre_hour1) )
        total_price = held_shares * float(open_price)
        open_price = float( open_price )
        hour_response = {
            'hour': f'{hour_open}:00',
            'last_price': num_to_money( round(open_price,4) ),
            'held_shares': held_shares,
            'total_price': num_to_money( round(total_price,4) )
        }
        by_hours.append( dict(hour_response) )
        print(hour_response)

    total_open_price = float(close_price) * held_shares
    print(f'\n{pre_hour2}: {close_price} Total Price:{total_open_price}')
    hour_open = trading_functions.get_hour_from_string( str(pre_hour2) )
    total_price = held_shares * float(close_price)
    close_price = float( close_price )
    hour_response = {
        'hour': f'{hour_open}:00',
        'last_price': num_to_money( round(close_price,4) ),
        'held_shares': held_shares,
        'total_price': num_to_money( round(total_price,4) )
    }
    by_hours.append( dict(hour_response) )
 
    # Look for further information:
    while ite_lots < len(lots_list):
        qtyl = lots_list[ite_lots]['quantity']; print(f'L:{ite_lots} = {qtyl}')
        held_shares += lots_list[ite_lots]['quantity']
        ite_lots += 1
        
    # Look for further information:
    while ite_sells < len(sell_list):
        qtys = sell_list[ite_sells]['quantity']; print(f'S:{ite_sells} = {qtys}')
        held_shares -= sell_list[ite_sells]['quantity']
        ite_sells+= 1
        
    return by_hours















