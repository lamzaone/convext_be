from database import engine, SessionLocal 
from fastapi import (FastAPI, File, Form, UploadFile, Request, Response,
                     HTTPException, status, Depends)
from fastapi.responses import FileResponse
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
import aiofiles
import apyio
import hashlib
import magic
import models
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

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

# FileUpload way - write to file and return MD5 hash
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

    # Background task for autodeletion after response
    bgDel = BackgroundTasks()
    bgDel.add_task(os.unlink, filePath)

    # Bytes return as response, set headers and background task
    return FileResponse(path=filePath, headers={"Content-Disposition":
                                                "attachment; filename=" +
                                                fileRandName + fileExt},
                        media_type=files.content_type, background=bgDel)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
