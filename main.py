from database import engine, SessionLocal 
from fastapi import (BackgroundTasks, FastAPI, File, 
                     Form, UploadFile, Request, Response,
                     HTTPException, status, Depends)
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr
from typing import List
from sqlalchemy.orm import Session
from subprocess import Popen, PIPE
import subprocess
import aiofiles
import asyncio
import apyio
import hashlib
import magic
import models
import time
import os
import re
import uuid
import uvicorn

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
   

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to delete files every 5 minutes (300s)
async def del_files(filesToDelete: List):
    while True:
        await asyncio.sleep(300)
        for file in filesToDelete:
            os.unlink(file)

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

# TODO: Add parameter to function for specifying format to convert to
# File upload
@app.post('/upload')
async def upload(files: UploadFile):

    # Get extension, hash, new name and write file to disk
    fileExt = str(re.search(".[^/.]+$", files.filename).group()) 
    fileRandName = str(uuid.uuid4().hex)[:16] 
    fileHash = hashlib.md5(await files.read()).hexdigest()
    filePath = "files/" + fileRandName + fileExt
    await files.seek(0)
    async with aiofiles.open(filePath, "wb") as recFile:
        await recFile.write(await files.read())

    # Run bash conv on separate thead
    process = subprocess.Popen(['./convert.sh', filePath, 'png'], stdout=PIPE, stderr=PIPE)
    # Get output from process
    stdout, stderr = process.communicate()

    # Call async taks to delete files
    asyncio.create_task(del_files([filePath, "convfiles/" + stdout.decode('ascii')]))

    # Return message with converted file name
    return {"message" : stdout.decode('ascii') }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
