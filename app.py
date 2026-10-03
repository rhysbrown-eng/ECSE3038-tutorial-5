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
                            detail=f"No device called '{name}'",
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

@app.put("/devices/{name}")
def update_device(name: str, device: Device, response: Response):

    if device.name != name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Body name '{device.name}' does not match URL name '{name}'.",
        )
        # returns 409 if name indicated in uri and body disagree
        # it was chosen to return an error code instead of force agreement as the true intended name of the user is unknown.

    new_device = device.model_dump()

    result = devices.replace_one(
        {"name": name}, new_device, upsert=True
    )

    if result.upserted_id is not None:
        response.status_code = status.HTTP_201_CREATED
        # returns 201 if put created the resource

    return device # returns 200 if the resource was updated successfully


@app.delete("/devices/{name}")
def delete_device(name : str):
    result = devices.delete_one({"name": name})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, 
                                    detail=f"No device called '{name}'")

    return {"detail" : f"The device named {name} has been deleted."}

    
    
    