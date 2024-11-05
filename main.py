from database import engine, SessionLocal 
from fastapi import (BackgroundTasks, FastAPI, File, 
                     Form, UploadFile, Request, Response,
                     HTTPException, status, Depends)
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr
from typing import List
from sqlalchemy.orm import Session
from subprocess import Popen, PIPE
from anyio import run_process, run
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
    await asyncio.sleep(300)
    for file in filesToDelete:
        os.unlink(file)

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

# File upload; convExt gets extension to convert to from frontend
@app.post('/upload')
async def upload(files: UploadFile, convExt: str):

    # Get extension, hash, new name and write file to disk
    fileExt = str(re.search(".[^/.]+$", files.filename).group()) 
    fileRandName = str(uuid.uuid4().hex)[:16] 
    fileHash = hashlib.md5(await files.read()).hexdigest()
    filePath = "files/" + fileRandName + fileExt
    await files.seek(0)
    async with aiofiles.open(filePath, "wb") as recFile:
        await recFile.write(await files.read())


    # (?) Alternative way for async running (?)
    # process = await run_process(['./convert.sh', filePath, 'png'])

    # Run bash conv on separate thead
    process = subprocess.Popen(['./convert.sh', filePath, convExt], 
                               stdout=PIPE,
                               stderr=PIPE)

    # Get output from process; don't use at all for first variant just add
    # process. to stdout in return
    stdout, stderr = process.communicate()


    # Call async taks to delete files; if using first variant async add
    # process. before stdout
    asyncio.create_task(del_files([filePath, "convfiles/" +
                                   stdout.decode('ascii')]))

    # Return message with converted file name; if first variant => process.
    # before stdout
    return {"message" : stdout.decode('ascii') }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
