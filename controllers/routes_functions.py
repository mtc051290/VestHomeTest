import sys
sys.path.append("..")
from utils.exceptions import symbol_exception
import requests
from controllers.users_functions import validate_new_user
from utils import exceptions
from utils.database import get_new_db
from datetime import datetime
from controllers.auth import get_current_user
from controllers.trading_functions import num_to_money, dict_format
from utils.helper_variables import hack_headers, time_zone

"""
These are methods used to interact with the Nasdaq api
"""

def get_price_nasdaq( symbol ):
    """
    Get the last price of a company from the Nasdaq API
    """
    # Get stocks data from api.nasdaq
    my_params = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{symbol}/info"
    try:
        response = requests.get( url_quote_info, 
                            params=my_params, 
                            headers=hack_headers, 
                            timeout=10 )
    except BaseException as e:
        raise BaseException("Service Failure", e, e.args)

    data   = response.json()['data']
    status = response.json()['status']

    # Throw an error if symbol not exists or could not get data from api
    if status['rCode'] == 400:
        raise exceptions.symbol_exception()
    if status['rCode'] != 200:
        raise exceptions.nasdaq_api_exception()
    
    return float( data['primaryData']['lastSalePrice'][1:] )



def get_numbers_nasdaq( symbol ):
    """
    Get a summary for a specific company
    """
    # Get stocks data from api.nasdaq
    url_quote_info = f"https://api.nasdaq.com/api/quote/{symbol}/realtime-trades"
    try:
        response = requests.get( url_quote_info, 
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
    
    # Parsing to get High and Low prices from the day
    high_low_raw = data['topTable']['rows'][0]['todayHighLow']
    high_low = high_low_raw.split("/")
    high = float( high_low[0][1:] )
    low = float( high_low[1][1:] )
    print( f' {high} and {low}' )



def get_real_average_nasdaq( symbol ):
    """
    Since nasdaq does not report a daily average, it was necessary
    to do an iteration process that evaluates the price changes issued
    by Nasdaq and makes the calculations with said data.
    """
    # Get stocks data from api.nasdaq
    my_params = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{symbol}/chart"
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

    real_high = 0.0
    cont = 0
    sum_prices = 0
    average = 0
    real_low = 0

    # Iterate through chart, find the lowest, the highest and calculate values
    if data['chart'] is not None:
        real_low = float( data['chart'][0]['z']['value'] )
        for x in data['chart']:
            value = float( x['z']['value'] )
            if value > real_high:
                real_high = value
            if value < real_low:
                real_low = value
            sum_prices += value
            cont += 1
        average = sum_prices / cont
        print( f'High: {real_high} Low: {real_low} Sum: {sum_prices} Cont: {cont} Av: {average}' )
    else:
        msg = "Data not available at this moment, please wait until open market"
    
    """
    Double check for High/Low prices and return the Highest or the lowest
    """

    # Get stocks data from api.nasdaq
    my_params_2 = { 'assetclass' : 'stocks' }
    url_quote_info = f"https://api.nasdaq.com/api/quote/{symbol}/realtime-trades"
    try:
        response_2 = requests.get( url_quote_info, 
                            params=my_params_2, 
                            headers=hack_headers, 
                            timeout=15 )
    except BaseException as e:
        raise BaseException("Service Failure", e, e.args)

    data_2   = response_2.json()['data']
    status_2 = response_2.json()['status']

    # Throw an error if symbol not exists or could not get data from api
    if status_2['rCode'] == 400:
        raise exceptions.symbol_exception()
    if status_2['rCode'] != 200:
        raise exceptions.nasdaq_api_exception()

    high_low_recheck = data_2['topTable']['rows'][0]['todayHighLow']
    pre_high_low = high_low_recheck.split("/")
    high_recheck = float( pre_high_low[0][1:] )
    low_recheck = float( pre_high_low[1][1:] )

    if high_recheck > real_high:
        final_high = high_recheck
    else:
        final_high = real_high

    if low_recheck < real_low:
        final_low = low_recheck
    elif real_low == 0:
        final_low = low_recheck
    else:
        final_low = real_low

    if average == 0:
        average = ( final_high + final_low ) / 2
    else:
        msg = "Data in real time"

    return final_high, final_low, average, msg
