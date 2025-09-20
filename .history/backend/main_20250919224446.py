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
    

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)