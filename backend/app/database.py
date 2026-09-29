import motor.motor_asyncio
import os
import json
import uuid
import asyncio
import socket
import tempfile
from datetime import datetime
from bson import ObjectId
from .config import settings

# Helper to check if MongoDB is actually running
def is_mongodb_running(url: str) -> bool:
    try:
        host = "localhost"
        port = 27017
        if "://" in url:
            parts = url.split("://")[1].split("/")[0]
            if "@" in parts:
                parts = parts.split("@")[1]
            if ":" in parts:
                host, port_str = parts.split(":")
                port = int(port_str)
            else:
                host = parts
        
        # Test connection
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False

# Transparent collection wrapper that uses a local JSON file when MongoDB is offline
class JSONCollection:
    def __init__(self, name: str, filepath: str = "local_db.json"):
        self.name = name
        # If running on Vercel, AWS Lambda, or a read-only environment, store in writable temp directory
        target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or not os.access(target_dir, os.W_OK):
            self.filepath = os.path.join(tempfile.gettempdir(), filepath)
        else:
            self.filepath = os.path.join(target_dir, filepath)
        
    def _read_data(self):
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
            
    def _write_data(self, data):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception:
            pass

    async def insert_one(self, document: dict):
        await asyncio.sleep(0.01)
        data = self._read_data()
        if self.name not in data:
            data[self.name] = []
            
        if "_id" not in document:
            document["_id"] = str(ObjectId())
        elif isinstance(document["_id"], ObjectId):
            document["_id"] = str(document["_id"])
            
        doc_copy = json.loads(json.dumps(document, default=str))
        doc_copy["_id"] = document["_id"]
        
        data[self.name].append(doc_copy)
        self._write_data(data)
        
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return InsertOneResult(document["_id"])

    async def find_one(self, query: dict):
        await asyncio.sleep(0.01)
        data = self._read_data()
        docs = data.get(self.name, [])
        for doc in docs:
            match = True
            for k, v in query.items():
                if k == "_id":
                    val_str = str(v)
                    if str(doc.get("_id")) != val_str:
                        match = False
                        break
                else:
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                doc_copy = dict(doc)
                if "_id" in doc_copy and ObjectId.is_valid(doc_copy["_id"]):
                    doc_copy["_id"] = ObjectId(doc_copy["_id"])
                return doc_copy
        return None

    def find(self, query: dict):
        data = self._read_data()
        docs = data.get(self.name, [])
        matched_docs = []
        for doc in docs:
            match = True
            for k, v in query.items():
                if k == "_id":
                    val_str = str(v)
                    if str(doc.get("_id")) != val_str:
                        match = False
                        break
                else:
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                doc_copy = dict(doc)
                if "_id" in doc_copy and ObjectId.is_valid(doc_copy["_id"]):
                    doc_copy["_id"] = ObjectId(doc_copy["_id"])
                matched_docs.append(doc_copy)
                
        class AsyncCursor:
            def __init__(self, items):
                self.items = items
                self.index = 0
                
            def sort(self, key, direction=-1):
                try:
                    self.items.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
                except Exception:
                    pass
                return self
                
            def __aiter__(self):
                return self
                
            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                val = self.items[self.index]
                self.index += 1
                return val
                
        return AsyncCursor(matched_docs)

    async def update_one(self, query: dict, update: dict):
        await asyncio.sleep(0.01)
        data = self._read_data()
        docs = data.get(self.name, [])
        updated = False
        for doc in docs:
            match = True
            for k, v in query.items():
                if k == "_id":
                    val_str = str(v)
                    if str(doc.get("_id")) != val_str:
                        match = False
                        break
                else:
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                if "$set" in update:
                    for uk, uv in update["$set"].items():
                        doc[uk] = json.loads(json.dumps(uv, default=str))
                else:
                    for uk, uv in update.items():
                        doc[uk] = json.loads(json.dumps(uv, default=str))
                updated = True
                break
        if updated:
            self._write_data(data)
            
        class UpdateResult:
            def __init__(self, modified_count):
                self.modified_count = modified_count
        return UpdateResult(1 if updated else 0)

    async def delete_one(self, query: dict):
        await asyncio.sleep(0.01)
        data = self._read_data()
        docs = data.get(self.name, [])
        delete_idx = -1
        for idx, doc in enumerate(docs):
            match = True
            for k, v in query.items():
                if k == "_id":
                    val_str = str(v)
                    if str(doc.get("_id")) != val_str:
                        match = False
                        break
                else:
                    if doc.get(k) != v:
                        match = False
                        break
            if match:
                delete_idx = idx
                break
        if delete_idx != -1:
            docs.pop(delete_idx)
            data[self.name] = docs
            self._write_data(data)
            
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        return DeleteResult(1 if delete_idx != -1 else 0)

# Check connection status
USE_MOCKED_DB = not is_mongodb_running(settings.DATABASE_URL)

if USE_MOCKED_DB:
    print("----------------------------------------------------------------------")
    print("WARNING: MongoDB server is not running or unreachable at the configured URL.")
    print("AI Resume Analyzer is running in OFFLINE JSON mode using local_db.json.")
    print("----------------------------------------------------------------------")
    db = None
    client = None
else:
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.DATABASE_URL)
    db = client.get_default_database()

# Define helper to fetch collections
def get_collection(name: str):
    if USE_MOCKED_DB:
        return JSONCollection(name)
    return db[name]

