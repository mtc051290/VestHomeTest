import sys

from sqlalchemy.sql.expression import false
sys.path.append("..")
from sqlalchemy import Boolean,Column,Integer,String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime, Float
from utils.database import Base


class VestUsers(Base):
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
    __tablename__    = "user_stocks"
    id               = Column(Integer, primary_key=True, index=True, autoincrement=True)
    owner_id         = Column(Integer, ForeignKey("vest_users.id"))
    nasdaq_stock_id  = Column(Integer, ForeignKey("nasdaq_stocks.id"))
    company          = Column(String)
    symbol           = Column(String)
    created_date     = Column(DateTime)
    shares           = Column(String)
    num_held_shares  = Column(Integer)
    has_pending      = Column(Integer, default=0)
    owner            = relationship("VestUsers", back_populates="user_stocks")
    nasdaq           = relationship("NasdaqStocks", back_populates="user_stocks")


class NasdaqStocks(Base): 
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

