
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from config.db.pmis_db import pmis_session
from sqlalchemy import text

router = APIRouter()

### MS SQL ###
## Get Department Employees

@router.get("/getemployees/{officeid}")
async def get_records(officeid: int, session: AsyncSession = Depends(pmis_session)):
    sql = text("select EmpName, eid from pmis.dbo.m_vwgetallemployee where isactive = 1 and Department = :officeid order by EmpName ASC")
    result = await session.execute(sql, {"officeid": officeid})
    rows = result.fetchall()  # returns list of Row objects
    # Convert to dicts if needed
    return [dict(row._mapping) for row in rows]