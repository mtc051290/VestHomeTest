
import sys
from models.models import UserStocks
sys.path.append("..")
from models import models
from datetime import datetime, timedelta
from utils.helper_variables import time_zone
from utils import exceptions
import base64
import uuid
import json

def create_nasdaq_stock_if_not_exists(data, db):
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
    print(user_model)
    print(data)


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


def get_num_held_shares( shares_list ):
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
