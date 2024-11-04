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

async def del_files(filesToDelete: List):
    while True:
        await asyncio.sleep(300)
        for file in filesToDelete:
            os.unlink(file)

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

# File upload
@app.post('/upload')
async def upload(files: UploadFile):
    # Find file extension, randomize name, save file content to disk, find MD5
    # hash and send file response for download with Content-Disposition header
    # attributes 'attachement; filename='
    fileExt = str(re.search(".[^/.]+$", files.filename).group()) 
    fileRandName = str(uuid.uuid4().hex)[:16] 
    fileHash = hashlib.md5(await files.read()).hexdigest()
    filePath = "files/" + fileRandName + fileExt
    await files.seek(0)
    async with aiofiles.open(filePath, "wb") as recFile:
        await recFile.write(await files.read())
    process = subprocess.Popen(['./convert.sh', filePath, 'png'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()


    # Background task for autodeletion after response
    asyncio.create_task(del_files([filePath, "convfiles/" + stdout.decode('ascii')]))
    # bgDel = BackgroundTasks()
    # bgDel.add_task(os.unlink, filePath)
    # bgDel.add_task(os.unlink, "convfiles/" + str(stdout))

    # Bytes return as response, set headers and background task
    return {"message" : stdout.decode('ascii') }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
