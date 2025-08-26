from fastapi import Depends
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Annotated, Generator

#URL_DATABASE = "postgresql://postgres:pgas@*153@vm_db_postgresql.pgas.ph:5432/neweps"

DATABASE_URL = URL.create(
    "postgresql+psycopg2",  # or "postgresql+psycopg"
    username="postgres",
    password="pgas@*153",  # raw; SQLAlchemy will quote it
    host="vm_db_postgresql.pgas.ph",
    port=5432,
    database="neweps",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]