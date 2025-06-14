from pymongo import AsyncMongoClient
from app.core.globals import MONGODB_URL, DB_NAME

class MongoDB:
    def __init__(self):
        self.client: AsyncMongoClient = AsyncMongoClient(MONGODB_URL)   
        self.db = self.client[DB_NAME]
        
    def get_collection(self, collection_name: str):
        return self.db[collection_name]
    
    def close(self):
        self.client.close()
    

def get_collection(collection_name: str):
    return lambda: MongoDB().get_collection(collection_name)