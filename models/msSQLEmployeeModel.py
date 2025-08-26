from typing import Optional
from sqlmodel import SQLModel


class User(SQLModel, table=True):
    eid: int
    EmpName: str

class UserOffices(SQLModel, table=True):
    eid: int
    officeid : int