from anyio import run_process, run
from database import engine, SessionLocal 
from fastapi import (BackgroundTasks, FastAPI, File, 
                     Form, UploadFile, Request, Response,
                     HTTPException, status, Depends)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr
from typing import List
from sqlalchemy.orm import Session
from subprocess import Popen, PIPE
import zipfile
import subprocess
import aiofiles
import asyncio
import apyio
import hashlib
import models
import time
import os
import re
import uuid
import uvicorn

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
   


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to delete files every 5 minutes (300s)
async def del_files(filesToDelete: List):
    await asyncio.sleep(300)
    os.unlink(filesToDelete[0])
    os.unlink(filesToDelete[1])

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

# File upload; convExt gets extension to convert to from frontend
# get list of files, get list of extensions, got through files, convert each
# one with sh script and add path of converted file to a new list. 
# If multiple files got converted, 
#    make zip, return zip
# else 
#   just return converted file
@app.post('/upload')
async def upload(files: List[UploadFile] = File(...), 
                 extensions: List[str] = Form(...)):

    # List of converted file names
    convFilePathList = []

    # Get extension, new name and write file to disk
    for extIndex, file in enumerate(files):
        fileExt = str(re.search(".[^/.]+$", file.filename).group()) 
        fileRandName = str(uuid.uuid4().hex)[:16] 
        filePath = "files/" + fileRandName + fileExt
        convExt = extensions[extIndex]
        async with aiofiles.open(filePath, "wb") as recFile:
            await recFile.write(await file.read())


        # (?) Alternative way for async running (?)
        # process = await run_process(['./convert.sh', filePath, 'png'])

        # Run bash conv on separate thead
        process = subprocess.Popen(['./convert.sh', filePath, convExt], 
                                   stdout=PIPE,
                                   stderr=PIPE)

        # Get output from process; don't use at all for first variant just add
        # process. to stdout in return
        stdout, stderr = process.communicate()

        
        # Converted file name
        convFileName = stdout.decode('ascii')

        # If something break, return error code -1
        if convFileName == "-1":
            return { "message" : "-1" }

        # Call async taks to delete files; if using first variant async add
        # process. before stdout
        asyncio.create_task(del_files([filePath, "convfiles/" + convFileName]))
        
        # Add converted file name to list
        convFilePathList.append("convfiles/" + convFileName)

    # If we got multiple files, make a zip for them, set headers right for
    # response
    # !!!IMPORTANT!!!
    # TODO: FIND ASYNC WAY TO MAKE ZIP
    # !!!
    if len(convFilePathList) > 1:
        zipFileName = str(uuid.uuid4().hex)[:16] + ".zip"
        zipDescriptor = zipfile.ZipFile("convfiles/" + zipFileName, "w",
                                        zipfile.ZIP_DEFLATED)
        for convFilePath in convFilePathList:
            zipDescriptor.write(convFilePath, os.path.basename(convFilePath))
        return FileResponse(path="convfiles/" + zipFileName,
                            filename=zipFileName,
                            headers={ "Access-Control-Expose-Headers" :
                                     "Content-Disposition",
                                     "Content-Disposition" : 
                                     "attachment; filename =\"" + zipFileName
                                        + "\"" 
                                     }
                            )

    # Just return the file and set headers
    else:
        convFilePathList[0]
        convFileName
        return FileResponse(path=convFilePathList[0],
                            filename=convFileName,
                            headers={ "Access-Control-Expose-Headers" :
                                     "Content-Disposition",
                                     "Content-Disposition" : 
                                     "attachment; filename =\"" + convFileName
                                        + "\"" 
                                     }
                            )


# @app.post("/upload")
# async def upload_files(
#     files: List[UploadFile] = File(...)
# ):
#     file_info = []
# 
#     for i, file in enumerate(files):
#         extension = file.filename.split(".").pop()          # Get file extension
#         filename = f"{uuid.uuid4().hex[:8]}.{extension}"    # Generate random filename
#         filepath = f"files/{filename}"                      # Path to save the file
# 
#         # Write the file in chunks to the specified path
#         async with aiofiles.open(filepath, "wb") as out_file:
#             while content := await file.read(1024 * 1024):  # 1MB chunk size
#                 await out_file.write(content)               # Write the chunk to the file
# 
#         # Calculate MD5 hash of the saved file
#         async with aiofiles.open(filepath, "rb") as out_file:   
#             file_hash = hashlib.md5(await out_file.read()).hexdigest()  # Calculate MD5 hash
# 
#         # Collect file information
#         file_info.append({
#             "filename": filename,
#             "hash": file_hash,
#         })
# 
#     # TODO: Add the conversion logic here
# 
#     return {"files": file_info}


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
