import sys
sys.path.append("..")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Connect to Heroku MySQL 
db_user     = "bccf25ad9ef0b8"
db_pass     = "19d1cdea"
db_host     = "us-cdbr-east-05.cleardb.net"
db_database = "heroku_376a42443d2d0ac"
db_port     = "3306"
db_url      = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_database}"

SQLALCHEMY_DATABASE_URL = db_url

engine = create_engine( SQLALCHEMY_DATABASE_URL, 
                        connect_args  = { 'connect_timeout' : 120 }, 
                        pool_pre_ping = True )

SessionLocal = sessionmaker( autocommit  = False, 
                             autoflush   = False, 
                             bind=engine )

Base = declarative_base()

def get_db():
    try:
        db=SessionLocal()
        yield db
    finally: 
        db.close()