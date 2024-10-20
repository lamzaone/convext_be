# More or less the same as main, but less async
from database import engine, SessionLocal
from fastapi import (FastAPI, File, Form, UploadFile, Request, 
                     Response, HTTPException, status)
from fastapi.responses import FileResponse
import apyio
from io import BytesIO
import uuid
import aiofiles
import hashlib
import models
import os
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

'''
# FileUpload way
@app.post('/upload')
async def upload(files: UploadFile):
    filename = str(uuid.uuid4())[:8]
    filepath = "files/" + filename
    with open(filepath, "wb") as recFile:
        recFile.write(files.file.read())
    with open(filepath, "rb") as recFile:
        fileHash = hashlib.md5(recFile.read()).hexdigest()
    return fileHash
'''

# Request.stream() way with chunks
@app.post('/upload')
async def upload(request: Request):
    
    numChunk = 0

    filename = str(uuid.uuid4())[:8]
    filepath = "files/" + filename

    # Split in chunks and write to memory
    with open(filepath, "wb") as recFile:
        async for chunk in request.stream():
            if numChunk == 0:
                writeChunk = BytesIO(chunk)
                writeChunk.seek(146)
                recFile.write(writeChunk.read())
            else:
                recFile.write(chunk)
            numChunk += 1
        recFile.seek(-54, 2)
        recFile.truncate()

    # MD5 hash
    with open(filepath, "rb") as recFile:
        fileHash = hashlib.md5(recFile.read()).hexdigest()
    return fileHash

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
