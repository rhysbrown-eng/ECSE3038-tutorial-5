import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from urllib.parse import quote

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

devices.create_index("name", unique=True)

@app.get("/devices")
def get_devices(response : Response):
    response.headers["Cache-Control"] = "no-cache"
    return list(devices.find({}, {"_id": 0}))

@app.get("/devices/{name}")
def get_single_device(name :str, response : Response):
    response.headers["Cache-Control"] = "no-cache"

    device = devices.find_one({"name": name}, {"_id": 0})
    if device is None:
        raise HTTPException(status_code=404, 
                            detail="No device called " + name,
                            headers={"Cache-Control": "no-cache"})

    return device


@app.post("/devices", status_code=201)
def create_device(device: Device, response : Response):
    new_device = device.model_dump()

    try:
        devices.insert_one(new_device)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A device named '{device.name}' already exists."
        )

    new_device.pop("_id")
    response.headers["Location"] = f"/devices/{quote(device.name, safe='')}"
    return new_device