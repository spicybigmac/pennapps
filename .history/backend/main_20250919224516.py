from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import dotenv
dotenv.load_dotenv()
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


@app.post("/getPositions")
async def processfunction(request: ProcessRequest):
    

if (__name__ == "__main__"):
    uvicorn.run("main:app", reload=True)