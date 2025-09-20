from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import base64

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProcessRequest(BaseModel):
    image: str

currid = 0

@app.post("/processImage")
async def processfunction(request: ProcessRequest):
    image = request.image
    image = image[image.find(",")+1:]

    global currid
    path = f"backend/images/{currid}.jpg"
    currid += 1

    print("start read")
    try:
        with open(path, "wb") as f:
            f.write(base64.b64decode(image))
    except:
        raise HTTPException(422, "File Loading Failed.")

    print(f"img with id {currid} saved")

    code, output = analyze.analyze(path)

    if (code == 0):
        return output
    elif (code == -1):
        raise HTTPException(422, output)

    if os.path.exists(path):
        os.remove(path)
    else:
        print("file does not exist????? how")

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)