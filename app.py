import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from pymongo import MongoClient

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["ecse3038"]
devices = db["tutorial5"]

app = FastAPI()


class Device(BaseModel):
    name: str
    room: str
    temp: float
    online: bool

@app.get("/devices")
def get_devices(response : Response):
    response.headers["Cache-Control"] = "no-cache"
    return list(devices.find({}, {"_id": 0}))