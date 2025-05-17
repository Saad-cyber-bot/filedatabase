from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    data = Column(LargeBinary)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine('sqlite:///files.db')
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
