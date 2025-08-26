from xml.dom.minidom import Document


def individual_serial(document) -> dict:
    return {
        "id" : str(document["_id"]),
        "subject" : str(document["subject"]),
        "description" : str(document["description"]),
        "sourceoffice" : str(document["sourceoffice"]),
        "statushistory": [
            {
                "id": str(history["_id"]),
                "status": str(history["status"]),
                "statusid": int(history["statusid"]),
                "remarks": str(history["remarks"]),
                "userid": str(history["userid"]),
                "name": str(history["name"]),
                "statusdate": str(history["statusdate"]),  # Extract $date value
                "statustime": str(history["statustime"]),
            }
            for history in document["statushistory"]
        ],

    }

def list_serial(documents) -> list:
    return [individual_serial(DocumentModel) for DocumentModel in documents]

def document_serial(DocumentModel) -> dict:
    return individual_serial(DocumentModel)