import sys
sys.path.append("..")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.exceptions import database_exception


SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Miguel.01@127.0.0.1:3306/vest_mtc"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    try:
        db=SessionLocal()
        yield db
    finally: 
        db.close()