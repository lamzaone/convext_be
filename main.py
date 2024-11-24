# === LIBS ===
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
import anyio
import hashlib
import models
import time
import os
import re
import uuid
import uvicorn



# === START UP/INIT ===

models.Base.metadata.create_all(bind=engine)
app = FastAPI()



# === CORS MIDDLEWARE ===

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# === FUNCTIONS ===

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
        try:
            os.unlink(file)
        except FileNotFoundError:
            print("File " + file + " marked for deletion but not found.");

# Function to write uploaded file to disk
async def write_uploaded_file_to_disk(file: UploadFile, fileExt: str):
    # Generate random name for file and create path
    fileRandName = str(uuid.uuid4().hex)[:16] 
    filePath = "files/" + fileRandName + fileExt

    # Async write file to disk and return path
    async with aiofiles.open(filePath, "wb") as recFile:
        await recFile.write(await file.read())
    return filePath

# Function to write converted file to disk
async def write_converted_file_to_disk(filePath: str, extension: str):
    # Call conversion script in threaded subprocess
    process = subprocess.Popen(['./convert.sh', filePath, extension[1:]],
                               stdout=PIPE, stderr=PIPE)

    # Get output from conversion script
    stdout, stderr = process.communicate()
    convFileName = stdout.decode('ascii')

    # -1 if conversion failed, else create path for converted file and return it
    if convFileName == "-1":
        return "-1"
    else:
        return "convfiles/" + convFileName 

# Function to create zip archive
async def async_create_zip(convFilePathList: List[tuple]):
    # Generate random name for archive and create path
    zipFileName = str(uuid.uuid4().hex)[:16]+ ".zip"
    zipPath = "convfiles/" + zipFileName

    # Separate thread to create zip archive
    await anyio.to_thread.run_sync(create_zip_sync, convFilePathList, zipPath)

    # Return zip path and filename
    return zipPath, zipFileName

# Synchronous function to create the zip file
def create_zip_sync(convFilePathList: List[tuple], zipPath: str):
    # Write converted files to archive with original name
    with zipfile.ZipFile(zipPath, "w", zipfile.ZIP_DEFLATED) as zipDescriptor:
        for convFileName, convFilePath in convFilePathList:
            zipDescriptor.write(convFilePath, convFileName)



# === API ENDPOINTS ===

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

@app.post('/upload')
async def upload(files: List[UploadFile] = File(...), 
                 extensions: List[str] = Form(...)):

    # List of tuples with the following structure: [(converted filename,
    # converted file path)]
    convFilePathList = []

    # Iterate over list of files and a list of extensions at the same time.
    # Considered a tuple using zip()
    for file, extension in zip(files, extensions):
        # Get filename without extension and extension separately
        fileNameNoExt, fileExt = os.path.splitext(file.filename)

        # Write file to disk and get path
        filePath = await write_uploaded_file_to_disk(file, fileExt)
        # Convert file from file path and get converted file path
        convFilePath = await write_converted_file_to_disk(filePath, extension)

        # Return -1 if missing file path for converted file
        if convFilePath == "-1":
            return { "message" : "-1" }

        # Set async task to delete both files
        asyncio.create_task(del_files([filePath, convFilePath]))
        
        # Add tuple of filename and file path to list
        convFilePathList.append((fileNameNoExt + extension, convFilePath))

    # If we got multiple files, make a zip for them, set headers right for
    # response
    if len(convFilePathList) > 1:
        zipPath, zipFileName = await async_create_zip(convFilePathList)

        # Set async task to delete archive
        asyncio.create_task(del_files([zipPath]))
        
        return FileResponse(path=zipPath, filename=zipFileName, 
                            headers={
                                "Access-Control-Expose-Headers" : 
                                    "Content-Disposition",
                                "Content-Disposition" : 
                                    "attachment; filename =\"" + zipFileName +
                                    "\"" 
                                }
                            )
    # Just return the file and set headers
    else:
        return FileResponse(path=convFilePathList[0][1],
                            filename=convFilePathList[0][0], 
                            headers={
                                "Access-Control-Expose-Headers" :
                                    "Content-Disposition", 
                                "Content-Disposition" :
                                    "attachment; filename =\"" +
                                    convFilePathList[0][0] + "\"" 
                                }
                            )



# === MAIN ===

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
