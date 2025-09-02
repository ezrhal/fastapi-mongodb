from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.db.mongodb import db
from config.db.pmis_db import pmis_session
from functions.conver_to_date import convert_date_format1, convert_date_format
from models.DTS.ActionTaken import ActionTakenModel
from models.DTS.RouteToEmployee import PostRouteModel, RouteModel
from models.DTS.RoutedDocument import InstructionModel, UserActionModel
from models.DTS.Document import StatusHistoryModel

from bson import  ObjectId

from schema.routed_documents import list_rd_serial
from security.token_verify import verify_access_token

router = APIRouter()

## region DOC ROUTE

@router.post("/routetoemployee/")
async def post_routetoemployee(post_request: PostRouteModel):
    documents = []
    #employee_ids = [int(emp.strip()) for emp in post_request.employees.split(',')]



    for employee in post_request.employees:
        # Check if the document is already routed to the employee

        existing_document = db["RoutedDocuments"].find_one({
            "guidocid": post_request.guidocid,
            "docid": post_request.docid,
            "toeid": int(employee.key),
            "isactive": 1
        })

        # If the document exists, update it with the new instruction
        if existing_document:
            # Update the document with a new instruction

            updated_document = db["RoutedDocuments"].update_one(
                {"_id": existing_document["_id"]},
                {
                    "$push": {
                        "instruction": InstructionModel(
                            id=str(ObjectId()),
                            from_=post_request.name,
                            act=post_request.actions,
                            inst=post_request.instruction
                        ).model_dump()
                    }
                }
            )

            update_status = db["Documents"].update_one(
                {"_id": ObjectId(post_request.guidocid)},
                {
                    "$push": {
                        "statushistory": StatusHistoryModel(
                            id=str(ObjectId()),
                            status="Action",
                            remarks="Instruction update for " + employee.value,
                            userid=post_request.fromeid,
                            name=post_request.name,
                            statusdate= datetime.now(),
                            statustime=post_request.dates.timerouted,
                            officeid=72
                        ).model_dump()
                    }
                }
            )

            # Check if the update was successful
            if updated_document.modified_count == 0:
                raise HTTPException(status_code=404, detail="Failed to update the document.")
            documents.append(existing_document["_id"])

        else:
            # If the document doesn't exist, create a new one
            document = RouteModel(
                dateinserted=datetime.now(),
                guidocid=post_request.guidocid,
                docid=post_request.docid,
                doceid=post_request.doceid,
                fromeid=post_request.fromeid,
                toeid= int(employee.key),
                isactive=1,
                dates=post_request.dates,
                instruction=[InstructionModel(
                    id=str(ObjectId()),
                    from_=post_request.name,
                    act=post_request.actions,
                    inst=post_request.instruction
                )],
                useraction=UserActionModel(
                    routed=0,
                    acted=0,
                    completed=0
                )
            )

            # Insert the new document
            result = db["RoutedDocuments"].insert_one(document.model_dump())
            documents.append(result.inserted_id)

            update_status = db["Documents"].update_one(
                {"_id": ObjectId(post_request.guidocid)},
                {
                    "$push": {
                        "statushistory": StatusHistoryModel(
                            id=str(ObjectId()),
                            status="Action",
                            remarks="Routed to " + employee.value,
                            userid=post_request.fromeid,
                            name=post_request.name,
                            statusdate=datetime.now(),
                            statustime=post_request.dates.timerouted,
                            officeid=72
                        ).model_dump()
                    }
                }
            )

    print(post_request.useraction.completed)
    update_action = db["RoutedDocuments"].update_one(
        {"guidocid": post_request.guidocid,
         "toeid": post_request.fromeid,},
        {
            "$set" : {
                "useraction" : {
                    "routed": 1,
                    "acted": 1,
                    "completed": post_request.useraction.completed,
                }
            }
        }
    )

    # Return the inserted or updated document ids
    inserted_ids = [str(doc_id) for doc_id in documents]
    return {"inserted_ids": inserted_ids}


## endregion

## region GET ROUTED DOCUMENT

@router.get("/getrouteddocuments/{userid}/{status}")
async def get_document(userid: int, status: str, session: AsyncSession = Depends(pmis_session), claims = Depends(verify_access_token)):


    action = "routed"
    actionid = 0

    useraction = {
        "routed": 0,
        "acted": 0,
        "completed": 0,
    }

    match_query = {
        "toeid": userid,
        "useraction.routed" : 0,
        "useraction.acted" : 0,

    }

    if status == "acted":
        match_query = {
            "toeid": userid,
            "useraction.acted": 1,
            "useraction.completed": 0,
        }
    elif status == "completed":
        match_query = {
            "toeid": userid,
            "useraction.acted": 1,
            "useraction.completed": 1,
        }

    pipeline = [
        {"$match": match_query},

        {
            "$project": {
                "_id": 1,
                "toeid": 1,
                "fromeid": 1,
                "sourceoffice": 1,
                "dates" : 1,
                "datereceived": 1,
                "guidocid": 1,
                "docid": 1,
                "doceid": 1,
                "instruction": 1,
                "useraction": 1,
                "sender": 1,
                "documenttype": 1,
                "subject": 1,
                "description": 1,
                "statushistory": {
                    "$sortArray": {"input": "$statushistory", "sortBy": {"statusdate": -1}}
                }
            }
        }
    ]
    documents = list_rd_serial(db["RDocView"].aggregate(pipeline).to_list())

    combined = []
    for document in documents:
        for status in document["statushistory"]:
            status["statusdatestr"] = convert_date_format1(status["statusdate"])

        pipeline = [
            {"$match": {
                "guidocid": document["guidocid"],
                "fromeid": userid,
            }},

            {
                "$project": {
                    "_id": 1,
                    "guidocid": 1,
                    "toeid": 1,
                    "daterouted": "$dates.daterouted",
                    "useraction": 1
                }
            }
        ]

        employees_routed = db["RoutedDocuments"].aggregate(pipeline).to_list()

        if len(employees_routed) > 0:
            sql = text(
                "select eid, EmpName from pmis.dbo.m_vwgetallemployee where isactive = 1  order by EmpName ASC")
            # result = await session.execute(sql, {"officeid": 72})
            result = await session.execute(sql)
            rows = result.fetchall()  # returns list of Row objects

            sql_dict = {
                row.eid: {
                    "EmpName": row.EmpName
                }
                for row in rows
            }

            for doc in employees_routed:
                eid = doc["toeid"]
                sql_data = sql_dict.get(eid, {})
                combined.append({
                    "guidocid": doc["guidocid"],
                    "id": str(doc["_id"]),  # better to stringify ObjectId
                    "daterouted": convert_date_format(doc["daterouted"]),
                    "eid": eid,
                    "name": sql_data.get("EmpName"),
                    "useraction": doc["useraction"],
                })

       
        document["routedemployees"] = combined


    # for document in documents:
    #     for item in document.get("statushistory", []):
    #         dt = item.get("statusdate")
    #         if isinstance(dt, datetime):
    #             item["statusdatestr"] = dt.strftime("%b %d, %Y %H:%M")

    #for document in documents:
    #    for status in document["statushistory"]:
    #        status[""]

    return  documents
    #result = list(db["RDocView"].aggregate(pipeline).to_list(length=100))
    #return result[0] if result else {"error": "Document not found"}
## endregion

## region GET EMPLOYEES ROUTED

@router.get("/getemployeesrouted/{userid}/{docid}")
async def get_employees_routed(userid: int, docid: str, session: AsyncSession = Depends(pmis_session)):
    pipeline = [
        {"$match": {
            "guidocid": docid,
            "fromeid": userid,
        }},

        {
            "$project": {
                "_id": 1,
                "guidocid": 1,
                "toeid": 1,
                "daterouted" : "$dates.daterouted",
                "acted" : "$useraction.acted",
                "completed" : "$useraction.completed",
            }
        }
    ]

    employees_routed = db["RoutedDocuments"].aggregate(pipeline).to_list()


    sql = text(
        "select eid, EmpName from pmis.dbo.m_vwgetallemployee where isactive = 1  order by EmpName ASC")
    #result = await session.execute(sql, {"officeid": 72})
    result = await session.execute(sql)
    rows = result.fetchall()  # returns list of Row objects

    sql_dict = {
        row.eid: {
            "EmpName": row.EmpName
        }
        for row in rows
    }


    combined = []
    for doc in employees_routed:
        eid = doc["toeid"]
        sql_data = sql_dict.get(eid, {})
        combined.append({
            "guidocid": doc["guidocid"],
            "id": str(doc["_id"]),  # better to stringify ObjectId
            "daterouted" : convert_date_format(doc["daterouted"]),
            "eid": eid,
            "name": sql_data.get("EmpName"),
        })

    return combined

## endregion

## region SET ACTION TAKEN

@router.post("/saveactiontaken")
async def save_action_taken(post_request: ActionTakenModel):
    new_status = StatusHistoryModel(
        id=str(ObjectId()),
        status="Action",
        remarks=post_request.remarks,
        userid=post_request.userid,
        name=post_request.name,
        statusdate=datetime.now(),
        statustime=post_request.statustime,
        officeid=post_request.officeid,
    ).model_dump()

    update_action = db["Documents"].update_one(
        {"_id": ObjectId(post_request.guidocid)},
        {
            "$push": {
                "statushistory": new_status
            }
        }
    )

    update_status = db["RoutedDocuments"].update_one(
        {"guidocid": post_request.guidocid,
         "toeid": post_request.userid},
        {
            "$set" : {
                "useraction": {
                    "routed" : post_request.useraction.routed,
                    "acted" : 1,
                "completed" : post_request.useraction.completed,}
            }
        }
    )

    if post_request.useraction.completed == 1:

        routed_docs = db["RDocView"].find(
            {
                "$or": [
                    {
                        "guidocid": post_request.guidocid,
                        "from": post_request.fromeid,
                        "useraction.completed": 0,
                    },
                    {
                        "guidocid": post_request.guidocid,
                        "toeid": post_request.fromeid,
                        "useraction.completed": 0,
                    }
                ]
            }).to_list(None)

        if len(routed_docs) == 1:

            db["RoutedDocuments"].update_one(
                {"guidocid": post_request.guidocid,
                 "toeid": post_request.fromeid},{
                    "$set" : {
                        "useraction": {
                            "routed" : routed_docs[0]["useraction"]["routed"],
                            "acted" : routed_docs[0]["useraction"]["acted"],
                            "completed" : 1
                        }
                    }
                }
            )

    new_status["statusdatestr"] = convert_date_format1(str(new_status["statusdate"]))
    return {"new_status": new_status}

## endregion

## region DELETE ROUTED EMPLOYEE

@router.post("/deleteroutedemployee")
async def delete_routed_employee(guidocid: str =Body(..., embed=True),
                                 id: str = Body(..., embed=True),
                                 userId: int = Body(..., embed=True),
                                 name: str = Body(..., embed=True),
                                 officeId: int = Body(..., embed=True),):
    deleted_routed_employee = db["RoutedDocuments"].delete_one({
        "_id" : ObjectId(id),
    })

    if deleted_routed_employee.deleted_count == 1:

        new_status = StatusHistoryModel(
            id=str(ObjectId()),
            status="Action",
            remarks="Employee removed from list ",
            userid=userId,
            name=name,
            statusdate=datetime.now(),
            statustime=datetime.now().strftime("%H:%M"),
            officeid=officeId,
        ).model_dump()

        update_action = db["Documents"].update_one(
            {"_id": ObjectId(guidocid)},
            {
                "$push": {
                    "statushistory": new_status
                }
            }
        )

    return {"result": "success"}

## endregion

