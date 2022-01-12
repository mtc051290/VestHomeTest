import sys
sys.path.append("..")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool

"""
This should not be in GitHub


Using MySQLAlchemy as a ORM for MySQL
"""
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

sql_pool = create_engine( SQLALCHEMY_DATABASE_URL, 
                        connect_args  = { 'connect_timeout' : 120 }, 
                        pool_size = 30, max_overflow = 0 )

pool_conn = sql_pool.connect()

SessionLocal = sessionmaker( autocommit  = False, 
                             autoflush   = False, 
                             bind=engine )

Base = declarative_base()

# Creates a session for database connections
def get_db():
    try:
        db=SessionLocal()
        yield db
    finally: 
        db.close()

def get_new_db():
    pool_session= sessionmaker( autocommit  = False, 
                                autoflush   = False, 
                                bind=pool_conn )
    try:
        db=pool_session()
        yield db
    finally: 
        db.close()


