from json import load
import sys
sys.path.append("..")
from models import models
from datetime import datetime
from utils.helper_variables import time_zone, hack_headers
from utils import exceptions
import uuid
import yaml
import requests

"""
General Methods
"""

def dict_format(val):
    return yaml.load(val, Loader=yaml.FullLoader)

def create_nasdaq_stock_if_not_exists(data, db):
    """
    Verify if user owns a stock from this company
    Create a new one with purchase information
    """
    stocks_model = db.query(models.NasdaqStocks)\
        .filter(models.NasdaqStocks.symbol == data['symbol']).first()
    if stocks_model is None:
        try:
            stocks_model_create = models.NasdaqStocks()
            stocks_model_create.symbol             = data['symbol']
            stocks_model_create.company            = data['companyName']
            stocks_model_create.created_date       = datetime.now(time_zone)
            stocks_model_create.day_price_lowest   = 0
            stocks_model_create.day_price_highest  = 0
            stocks_model_create.day_price_average  = 0
            db.add(stocks_model_create)
            db.flush()
            db.commit()
            db.refresh(stocks_model_create)
            return stocks_model_create.id
        except:
            exceptions.database_exception()
    stocks_model = db.query(models.NasdaqStocks)\
        .filter(models.NasdaqStocks.symbol == data['symbol']).first()
    return stocks_model.id


def add_shares_to_user_stocks(data, user_model, db):
    """
    Add a LOT to the user's instance
    """
    stocks_model = db.query(models.NasdaqStocks)\
        .filter(models.NasdaqStocks.symbol == data['symbol']).first()
    if stocks_model is None:
        try:
            stocks_model = models.NasdaqStocks()
            stocks_model.symbol             = data['symbol']
            stocks_model.company            = data['companyName']
            stocks_model.created_date       = datetime.now(time_zone)
            stocks_model.day_price_lowest   = 0
            stocks_model.day_price_highest  = 0
            stocks_model.day_price_average  = 0
            db.add(stocks_model)
            db.commit()
        except:
            exceptions.database_exception()


def create_list_of_shares( data, user_id, x ):
    """
    Used before creating LOTS
    """
    date_time_now=datetime.now(time_zone).strftime("%Y-%m-%d %H:%M:%f")
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False
    last_price = data['primaryData']['lastSalePrice'][1:]
    id = uuid.uuid5(uuid.NAMESPACE_DNS, f'{x}{user_id}{date_time_now}'
    )
    return {
        'uuid'         : str(id),
        'held'         : True,
        'sold'         : False,
        'bought_date'  : date_time_now,
        'bought_price' : last_price,
        'sold_date'    : '',
        'sold_price'   : 0.00,
        'profit_loss'  : 0.00,
        'difference'   : 0.00,
        'pending'      : pending
    }



def create_lot( data, user_id, qty ):
    """
        Create and return a dictionary with de new LOT.
        If market is closed, set 'pending' to True
    """
    date_time_now=datetime.now(time_zone).strftime("%Y-%m-%d %H:%M:%f")
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False
    last_price = data['primaryData']['lastSalePrice'][1:]
    id = uuid.uuid5(uuid.NAMESPACE_DNS, 
                    f'{qty}{user_id}{date_time_now}')
    total_paid = float( last_price) * int( qty )
    return {
        'uuid'          : str(id),
        'bought_date'   : date_time_now,
        'bought_price'  : last_price,
        'quantity'      : qty,
        'held_quantity' : qty,
        'total_paid'    : total_paid,
        'pending'       : pending
    }


def create_sell( data, user_id, qty, lots ):
    """
        Iterate through lots to get the real
        paid amount, change status of held shares in lots,
        calculate difference $sold - $paid and get profit/loss
        from this operation.
        If market is closed, set 'pending' to True
    """
    date_time_now=datetime.now(time_zone).strftime("%Y-%m-%d %H:%M:%f")
    pending = True
    if data['marketStatus'] != "Market Closed":
        pending = False
    last_price = data['primaryData']['lastSalePrice'][1:]
    id = uuid.uuid5(uuid.NAMESPACE_DNS, 
                    f'{qty}{user_id}{date_time_now}')

    # For FIFO
    lots.reverse()
    
    # Iterate through lots and set new data
    i = 0
    to_next_lot = 1
    total_paid = 0
    paid = 0
    missing_sold = qty

    while ( to_next_lot == 1 and i < len(lots)):
        if lots[i]['held_quantity'] > 0:
            if lots[i]['held_quantity'] < missing_sold:
                to_next_lot = 1
                qty_available = lots[i]['held_quantity']
            elif lots[i]['held_quantity'] >= missing_sold:
                qty_available = missing_sold
                to_next_lot = 0
            else:
                qty_available = missing_sold
            
            paid = qty_available * float( lots[i]['bought_price'] )
            total_paid += paid
            lots[i]['held_quantity'] -= qty_available
            missing_sold -= qty_available
        i += 1

    # DELTA = $selled - $paid
    delta = ( float(last_price) * qty ) - total_paid 
    profit_loss = delta / total_paid

    id = uuid.uuid5( uuid.NAMESPACE_DNS, 
                     f'{qty}{user_id}{date_time_now}' )
    response = {
        'uuid'          : str( id ),
        'sold_date'     : date_time_now,
        'sold_price'    : last_price,
        'sold_total'    : round(float(last_price) * qty , 4) ,
        'quantity'      : qty,
        'total_paid'    : round( total_paid, 4 ),
        'delta'         : round( delta,4 ),
        'profit_loss'   : round( profit_loss, 4 ),
        'pending'       : pending
    }
    lots.reverse()
    return response, lots


def get_num_held_shares( shares_list ):
    """
    Get the current shares holding by the user, 
    if the market is open and there is something
    pending, just change the status
    """
    num_shares_held = 0
    num_shares_held_pending = 0
    has_pending = False
    for share in shares_list:
            if share['held'] == True:
                num_shares_held += 1
            if share['pending'] == True:
                has_pending = True
                num_shares_held_pending += 1
    return num_shares_held, has_pending

def num_to_money( num ):
    num = float( num )
    if num < 0:
        return f'-$'+'{:,}'.format( num * -1 )
    return f'$'+'{:,}'.format( num )

def change_pending_status( el, pending ):
    for x in el:
        x['pending'] = True
        if x['pending'] == True and pending == False:
            x['pending'] = False
    return el

def get_hour_from_string(date):
    hour_split = date.split(" ")
    hour_lot = int(hour_split[1][:2])
    return hour_lot


def get_nasdaq_chart_from_today( symbol ):
    """
    Verify the Nasdaq realtime chart to get prices from different hours
    """
    my_params = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{symbol}/chart"
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

    # Parse for date to ensure that is today's value
    date_time_now=datetime.now(time_zone).strftime("%b %-d")
    hoy_nasdaq = data['timeAsOf']
    mes_dia_anio = hoy_nasdaq.split(",")
    if mes_dia_anio[0] == date_time_now:
        return data['chart']
    return False



    