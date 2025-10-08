from collections import defaultdict
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from config.db.pmis_db import pmis_session
from config.db.postgres import get_db

router = APIRouter()

@router.get("/offices")
async def get_calendar(
    session: AsyncSession = Depends(pmis_session),   # async MSSQL session
):
    sql = text("""
            SELECT officeid, eid, officehead, officename FROM [pmis].[dbo].[m_vwGetOfficeHead_NoAddOns]
        """)

    result = await session.execute(sql)
    mssql_rows = result.mappings().all()  # List[RowMapping]

    return mssql_rows