# === LIBS ===
import datetime
import logging
import secrets
from anyio import run_process, run
from fastapi.staticfiles import StaticFiles
from database import engine, SessionLocal 
from fastapi import (BackgroundTasks, FastAPI, File, 
                     Form, UploadFile, Request, Response,
                     HTTPException, status, Depends)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, constr
from typing import Annotated, List
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
import requests
from datetime import datetime, timedelta



# === START UP/INIT ===

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
app.mount('/images', StaticFiles(directory='/images'), name="images")



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
db_dependency = Annotated[Session, Depends(get_db)]

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

# === GOOGLE LOGIN ENDPOINTS ===
# Base model for user data
class User(BaseModel):
    id: int
    email: str
    name: str
    image: str
    token: str
    refresh_token: str
    class Config:
        from_attributes=True

# Request model for user login
class UserIn(BaseModel):
    id_token: str
    access_token: str

# Request model for token validation
class TokenRequest(BaseModel):
    token: str
def generate_token():
    return secrets.token_urlsafe(64)

def generate_refresh_token():
    return secrets.token_urlsafe(64)

def save_image_to_filesystem(image_url: str, filename: str) -> str:
    """Download image from URL and save it to the filesystem."""
    response = requests.get(image_url)
    if response.status_code == 200:
        file_path = os.path.join('./images', filename)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    else:
        logging.error(f"Failed to fetch image from URL: {image_url}")
        raise HTTPException(status_code=400, detail="Failed to retrieve user picture")


@app.post("/api/auth/google", response_model=User)
def google_auth(token_request: UserIn, db: db_dependency):
    # Verify the ID token
    id_token_response = requests.get(
        'https://www.googleapis.com/oauth2/v3/tokeninfo',
        params={'id_token': token_request.id_token}
    )
    
    if id_token_response.status_code != 200:
        logging.error(f"Google token validation failed: {id_token_response.text}")
        raise HTTPException(status_code=400, detail="Invalid token")

    google_data = id_token_response.json()
    email = google_data.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token: no email found")

    userinfo_response = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {token_request.access_token}'}
    )

    if userinfo_response.status_code != 200:
        logging.error(f"Failed to get user info: {userinfo_response.text}")
        raise HTTPException(status_code=400, detail="Failed to retrieve user information")

    user_info = userinfo_response.json()
    name = user_info.get('name')


    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        # Create a new user if they don't exist
        picture_url = user_info.get('picture')

        # Save user picture to filesystem and store the path in the database
        picture_filename = f"{email}_profile.png" 
        save_image_to_filesystem(picture_url, picture_filename)
        refresh_token = generate_refresh_token()
        db_user = models.User(
            email=email,
            name=name,
            image=picture_filename,  
            token=token_request.id_token,
            refresh_token=refresh_token,
            token_expiry=datetime.now() + timedelta(days=1),
            refresh_token_expiry=datetime.now() + timedelta(days=7)
        )
        db.add(db_user)
    else:
        db_user.token = token_request.id_token
        db_user.token_expiry = datetime.now() + timedelta(days=1)
        db_user.refresh_token_expiry = datetime.now() + timedelta(days=7)

    db.commit()
    db.refresh(db_user)

    # Create the user response
    db_user_data = {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "image": f"http://127.0.0.1:8000/images/{db_user.image}",
        "token": db_user.token,
        "refresh_token": db_user.refresh_token
    }
    
    return db_user_data

# Refresh token
@app.post("/api/auth/refresh", response_model=User)
def refresh_tokens(token_request: TokenRequest, db: db_dependency):
    db_user = db.query(models.User).filter(models.User.refresh_token == token_request.token).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    
    if db_user.refresh_token_expiry < datetime.now():
        raise HTTPException(status_code=400, detail="Refresh token expired")

    db_user.token = generate_token()
    db_user.token_expiry = datetime.now() + timedelta(days=1)
    db.commit()
    db.refresh(db_user)
    

    user_response = User(
        id=db_user.id,
        email=db_user.email,
        name=db_user.name,
        image=f"http://127.0.0.1:8000/images/{db_user.image}",
        token=db_user.token,
        refresh_token=db_user.refresh_token,
    )
    
    return user_response

# Validate token
@app.post("/api/auth/validate", response_model=User)
def validate_token(token_request: TokenRequest, db: db_dependency):
    db_user = db.query(models.User).filter(models.User.token == token_request.token).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    if db_user.token_expiry < datetime.now():
        raise HTTPException(status_code=400, detail="Token expired")
    

    user_response = User(
        id=db_user.id,
        email=db_user.email,
        name=db_user.name,
        image=f"http://127.0.0.1:8000/images/{db_user.image}",
        token=db_user.token,
        refresh_token=db_user.refresh_token,
    )
    
    return user_response

# === MAIN ===

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        reload=True,
        # host="0.0.0.0"
    )
