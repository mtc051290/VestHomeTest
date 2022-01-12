import sys
sys.path.append("..")
from sqlalchemy import Boolean,Column,Integer,String, ForeignKey, PickleType, TEXT
from sqlalchemy.sql.sqltypes import DateTime, Float, JSON
from sqlalchemy.orm import relationship
from utils.database import Base
from sqlalchemy.ext.mutable import MutableList


class VestUsers(Base):
    # User table
    __tablename__   = "vest_users"
    id              = Column(Integer, primary_key=True)
    email           = Column(String, unique=True, index=True)
    username        = Column(String,unique=True, index=True)
    first_name      = Column(String)
    last_name       = Column(String)
    hashed_password = Column(String)
    is_active       = Column(Boolean, default=True)
    user_stocks     = relationship("UserStocks", back_populates="owner")


class UserStocks(Base):
    # Stocks with shares held by users
    __tablename__      = "user_stocks"
    id                 = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id           = Column(Integer, ForeignKey("vest_users.id"))
    nasdaq_stock_id    = Column(Integer, ForeignKey("nasdaq_stocks.id"))
    company            = Column(String)
    symbol             = Column(String)
    created_date       = Column(DateTime)
    lots               = Column(TEXT)
    sells              = Column(TEXT)
    num_held_shares    = Column(Integer)
    held_paid_shares   = Column(Float(precision=32, decimal_return_scale=None))
    total_paid_shares   = Column(Float(precision=32, decimal_return_scale=None))
    delta              = Column(Float(precision=32, decimal_return_scale=None))
    has_pending        = Column(Integer, default=0)
    owner              = relationship("VestUsers", back_populates="user_stocks")
    nasdaq             = relationship("NasdaqStocks", back_populates="user_stocks")


class NasdaqStocks(Base): 
    # Nasdaq stocks and summary
    __tablename__      = "nasdaq_stocks"
    id                 = Column(Integer, primary_key=True)
    symbol             = Column(String, unique=True, index=True)
    company            = Column(String)
    created_date       = Column(DateTime)
    day_price_lowest   = Column(Float(precision=32, decimal_return_scale=None))
    day_price_highest  = Column(Float(precision=32, decimal_return_scale=None))
    day_price_average  = Column(Float(precision=32, decimal_return_scale=None))
    user_stocks        = relationship("UserStocks", back_populates="nasdaq")
    price_changes      = relationship("PriceChanges", back_populates="nasdaq")


class PriceChanges(Base):
    __tablename__    = "price_changes"
    id               = Column(Integer, primary_key=True, index=True)
    nasdaq_stock_id  = Column(Integer, ForeignKey("nasdaq_stocks.id"))
    change_date      = Column(DateTime)
    symbol           = Column(String)
    price            = Column(Float(precision=32, decimal_return_scale=None))
    nasdaq           = relationship("NasdaqStocks", back_populates="price_changes")

