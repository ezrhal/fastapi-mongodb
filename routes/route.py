from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.pmis_db import pmis_session
from functions.conver_to_date import convert_date_format
from config.database import db, collection_name, cl_routed_documents
from models.RouteToEmployeeModel import PostRouteModel, RouteModel
from models.RoutedDocumentModel import DatesModel, InstructionModel, UserActionModel, StatusHistoryModel
from schema.schemas import list_serial, document_serial
from schema.routed_documents import list_rd_serial, rd_serial
from sqlalchemy import text

router = APIRouter()

@router.get("/getdocuments")
async def get_documents():
    documents = list_serial(collection_name.find())
    return documents


@router.get("/getrouteddocs/{userid}")
async def get_documents(userid: int):
    documents = list_rd_serial(cl_routed_documents.find({"toeid": userid}))

    for document in documents:
       document["dates"]["daterouted"] = convert_date_format(document["dates"]["daterouted"])
       document["dates"]["dateopened"] = convert_date_format(document["dates"]["dateopened"])

    return documents


@router.get("/getdocument/{id}")
async def get_document(id: str):
    document = document_serial(collection_name.find_one({"_id": ObjectId(id)}))

    for history in document["statushistory"]:
        history["statusdate"] = convert_date_format(history["statusdate"])

    return document

from fastapi import HTTPException
from datetime import datetime
from bson import ObjectId





## ROUT DOCUMENT TO EMPLOYEE
@router.post("/routetoemployee/")
async def post_routetoemployee(post_request: PostRouteModel):
    documents =[]
    employee_ids = [int(emp.strip()) for emp in post_request.employees.split(',')]

    for employee in employee_ids:
        document = RouteModel(
            dateinserted = datetime.now(),
            guidocid = post_request.guidocid,
            docid = post_request.docid,
            doceid = post_request.doceid,
            fromeid = post_request.fromeid,
            toeid = employee,
            isactive = 1,
            dates = post_request.dates,
            instruction = [InstructionModel(
                id = str(ObjectId()),
                from_=post_request.name,
                act=post_request.actions,
                inst=post_request.instruction
            )],
            useraction = UserActionModel (
                routed = 0,
                acted= 0,
                completed=0
            )
        )

        documents.append(document.model_dump())

    result = db["RoutedDocuments"].insert_many(documents)

    # Return the inserted ids, converting ObjectId to string
    inserted_ids = [str(inserted_id) for inserted_id in result.inserted_ids]

    return {"inserted_ids": inserted_ids}


### MS SQL ###
## Get Department Employees

@router.get("/getemployees/{officeid}")
async def get_records(officeid: int, session: AsyncSession = Depends(pmis_session)):
    sql = text("select EmpName, eid from pmis.dbo.m_vwgetallemployee where isactive = 1 and Department = :officeid order by EmpName ASC")
    result = await session.execute(sql, {"officeid": officeid})
    rows = result.fetchall()  # returns list of Row objects
    # Convert to dicts if needed
    return [dict(row._mapping) for row in rows]