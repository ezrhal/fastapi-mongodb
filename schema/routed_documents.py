from xml.dom.minidom import Document

from models.RoutedDocumentModel import RoutedDocumentViewModel


def ind_rd_serial(document) -> dict:
    return {
        "id" : str(document["_id"]),
        "docid" : int(document["docid"]),
        "doceid" : int(document["doceid"]),
        "subject" : str(document["subject"]),
        "fromeid" : int(document["fromeid"]),
        "description" : str(document["description"]),
        "documenttype" : str(document["documenttype"]),
        "sourceoffice" : str(document["sourceoffice"]),
        "sender": str(document["sender"]),
        "datereceived" : str(document["datereceived"]),
        "guidocid" : str(document["guidocid"]),
        "dates": {
            "daterouted" : str(document["dates"]["daterouted"]),
            "timerouted" : str(document["dates"]["timerouted"]),
            "dateopened" : str(document["dates"]["dateopened"]),
            "timeopened" : str(document["dates"]["timeopened"]),

        } ,
        "instruction": [
            {
                "id": str(actions["id"]),
                "from": str(actions["from_"]),
                "act": str(actions["act"]),
                "inst": str(actions["inst"]),
            } for actions in document["instruction"]
        ],
        "useraction": {
            "routed": str(document["useraction"]["routed"]),
            "acted": str(document["useraction"]["acted"]),
            "completed": str(document["useraction"]["completed"]),
        },
        "statushistory": [
            {
                "id": str(history["id"]),
                "status": str(history["status"]),
                "remarks": str(history["remarks"]),
                "userid": str(history["userid"]),
                "name": str(history["name"]),
                "statusdatestr" : str(history["status"]),
                "statusdate": str(history["statusdate"]),  # Extract $date value
                "statustime": str(history["statustime"]),
            }
            for history in document["statushistory"]
        ],

    }

def list_rd_serial(routeddocs) -> list:
    return [ind_rd_serial(RoutedDocumentViewModel) for RoutedDocumentViewModel in routeddocs]

def rd_serial(RoutedDocumentViewModel) -> dict:
    return ind_rd_serial(RoutedDocumentViewModel)