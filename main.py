from database import engine, SessionLocal
from fastapi import (FastAPI, File, Form, UploadFile, Request, 
                     Response, HTTPException, status)
from fastapi.responses import FileResponse
import apyio
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
# FileUpload way - write to file and return MD5 hash
@app.post('/upload')
async def upload(files: UploadFile):
    # Get random filename and set path to files directory
    filename = str(uuid.uuid4())[:8]
    filepath = "files/" + filename
    
    with open(filepath, "wb") as recFile:
        recFile.write(files.file.read())

    # Get MD5 hash
    with open(filepath, "rb") as recFile:
        fileHash = hashlib.md5(recFile.read()).hexdigest()
    return fileHash
'''

# Request.stream() way with chunks
@app.post('/upload')
async def upload(request: Request):
    # Chunk counter
    numChunk = 0

    # Get random filename and set path to files directory
    
    filename = str(uuid.uuid4())[:8]
    filepath = "files/" + filename

    # Start reading the request.stream in chunks (128KB/chunk). The request
    # body contains some representational headers embedded between the boundary
    # strings (multipart request). The file data is between boundary strings as
    # well, just under the headers. See "https://developer.mozilla.org/en-US/
    # docs/Web/HTTP/Headers/Content-Encoding" or "https://documentation.
    # softwareag.com/webmethods/cloudstreams/wst10-5/10-5_CloudStreams_webhelp
    # /index.html#page/cloudstreams-webhelp/to-custom_connector_15.html".
    # Different clients will use different headers of different
    # length and since I don't know the right way to remove them, I will just
    # remove them by their bytes for now. The bytes for curl and httpx requests
    # are specified in their scripts. Adjust the value accordingly; make sure
    # you send the POST request with the right script. Hopefully, we will find
    # a better way to do this.
    async with aiofiles.open(filepath, "wb") as recFile:
        async for chunk in request.stream():

            # For the first chunk we remove the first n bytes (boundary string
            # and headers). We turn the chunk into into BytesIO object in RAM,
            # we seek past the bytes, write the rest to the file.
            if numChunk == 0:
                writeChunk = apyio.BytesIO(chunk)
                await writeChunk.seek(146)
                await recFile.write(await writeChunk.read())
                
            # For all the other chunks just write the directly to file, we
            # will get the end boundary string later.
            else:
                await recFile.write(chunk)

            # Move chunk counter.
            numChunk += 1

        # Seek file backwards from the end n bytes and truncate at current
        # position. We just removed the string boundary at the end.
        await recFile.seek(-54, 2)
        await recFile.truncate()

    # Get MD5 hash
    async with aiofiles.open(filepath, "rb") as recFile:
        fileHash = hashlib.md5(await recFile.read()).hexdigest()
    return fileHash

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
