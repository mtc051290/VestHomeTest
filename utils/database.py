import sys
sys.path.append("..")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Connect to Heroku MySQL 
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://bccf25ad9ef0b8:19d1cdea@us-cdbr-east-05.cleardb.net:3306/heroku_376a42443d2d0ac"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    try:
        db=SessionLocal()
        yield db
    finally: 
        db.close()