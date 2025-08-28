from bson import ObjectId
from pymongo import MongoClient

client = MongoClient('mongodb+srv://ezrhal:xmqUSDS4FkXAjdGP@imscluster0.9ecljtn.mongodb.net/', 27017)

#client = MongoClient('mongodb://192.168.101.50', 27017)

db = client.DTS

collection_name = db["Documents"]
cl_routed_documents = db["RDocView"]