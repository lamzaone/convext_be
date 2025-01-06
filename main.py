# === LIBS ===

import aiofiles
import anyio
import apyio
import asyncio
import hashlib
import logging
import models
import os
import re
import requests
import secrets
import subprocess
import time
import utils
import uuid
import uvicorn
import xattr
import zipfile
import zlib
from anyio import run_process, run
from cryptography.fernet import Fernet
from database import engine, SessionLocal 
from datetime import datetime, timedelta
from fastapi import (BackgroundTasks, FastAPI, File, 
                     Form, UploadFile, Request, Response,
                     HTTPException, status, Depends)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from models import FileName
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session
from subprocess import Popen, PIPE
from typing import Annotated, List


# === START UP/INIT ===

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
os.makedirs("images", exist_ok=True)
app.mount('/images', StaticFiles(directory=utils.get_project_root() /
                                 'images'), name="images")



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
async def del_files(filesToDelete: List, time: float):
    await asyncio.sleep(time)
    for file in filesToDelete:
        try:
            os.unlink(file)
        except FileNotFoundError:
            print("File " + file + " marked for deletion but not found.")

# Add number to name if file with same name exists in users directory
async def fix_filename(filePath: str, fileName: str, fileExt: str):
    counter = 1
    fileNameCopy = fileName
    while os.path.exists(filePath + fileName + fileExt):
        fileName = fileNameCopy + " (" + str(counter) + ")"
        counter += 1
    return fileName

# Function to write uploaded file to disk
async def write_uploaded_file_to_disk(file: UploadFile, filePath: str):
    # Async write file to disk and return path
    async with aiofiles.open(filePath, "wb") as recFile:
        await recFile.write(await file.read())

# Function to write converted file to disk
async def write_converted_file_to_disk(auth: bool, filePath: str, 
                                       extension: str):
    # Call conversion script in threaded subprocess
    process = subprocess.Popen(['./convert.sh', str(auth), filePath,
                                extension[1:]], stdout=PIPE, stderr=PIPE)

    # Get output from conversion script
    stdout, stderr = process.communicate()
    convFilePath = stdout.decode('ascii')
    
    # -1 if conversion failed, else create path for converted file and return
    # it
    if convFilePath == "-1":
        return "-1"
    else:
        return convFilePath 

# Function to create zip archive
async def async_create_zip(convFilePathList: List[tuple]):
    # Generate random name for archive and create path
    zipFileName = str(uuid.uuid4().hex)[:16]+ ".zip"
    zipPathDirName = os.path.dirname(convFilePathList[0][1])
    zipPath = zipPathDirName + "/" + zipFileName

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



# === GOOGLE LOGIN ENDPOINTS ===

# Base model for user data
class User(BaseModel):
    id: int
    email: str
    hashmail: str
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
            hashmail = hashlib.md5(email.encode('ascii')).hexdigest(),
            name=name,
            image=picture_filename,  
            token=token_request.id_token,
            refresh_token=refresh_token,
            token_expiry=datetime.now() + timedelta(days=1),
            refresh_token_expiry=datetime.now() + timedelta(days=7)
        )
        db.add(db_user)
        os.makedirs("users/" + db_user.hashmail, exist_ok=True)
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
        "hashmail": db_user.hashmail,
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
        hashmail=db_user.hashmail,
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
        hashmail=db_user.hashmail,
        name=db_user.name,
        image=f"http://127.0.0.1:8000/images/{db_user.image}",
        token=db_user.token,
        refresh_token=db_user.refresh_token,
    )

    return user_response



# === API ENDPOINTS ===

# http://127.0.0.1:8000/docs - to test API endpoints
@app.get('/')
async def main():
    return { "message" : "Hello world!" }

# Get shared file endpoint
@app.get('/file/{encryptedPath}')
async def get_shared_file(encryptedPath):
    # Read encryption key from disk (maybe fix hardcoding path later)
    async with aiofiles.open('key', 'rb') as keyFile:
        key = await keyFile.read()
    cipher = Fernet(key)
    # Decypher path
    decryptedPath = cipher.decrypt(encryptedPath)
    # Set up path and filename to work with
    filePath = "users/" + decryptedPath.decode()
    fileName = os.path.basename(filePath)
    # If file is missing return 404, if not sharable, return Forbbiden, else
    # just return the file
    if os.path.isfile(filePath) == False:
        raise HTTPException(status_code=404, detail="Not Found")
    elif xattr.getxattr(filePath, "user.shareable").decode() == "False":
        raise HTTPException(status_code=403, detail="Forbidden")
    else:
        return FileResponse(path=filePath, filename=fileName,
                            headers={
                                "Access-Control-Expose-Headers" : 
                                    "Content-Disposition",
                                "Content-Disposition" : 
                                    "attachment; filename =\"" + fileName +
                                    "\"" 
                                }
                            )

# Get info about all files of user
@app.post('/myfiles')
async def get_files(tokenRequest: TokenRequest, db: db_dependency):
    # Validate token and get response
    userResponse = validate_token(tokenRequest, db)
    files = {}
    if userResponse: 
        userPath = "users/" + userResponse.hashmail + "/"
        # Get data about every file
        for file in os.listdir(userPath):
            fsize = os.stat(userPath + file).st_size
            fdate = os.stat(userPath + file).st_mtime
            if (xattr.getxattr(userPath + file, "user.shareable").decode() == "True"):
                fshare = True
            else:
                fshare = False
            files[file] = {
                "size" : fsize,
                "date" : fdate,
                "share" : fshare
            }
            if (fshare == True):            
                async with aiofiles.open('key', 'rb') as keyFile:
                    key = await keyFile.read()
                cipher = Fernet(key)
                pathToEncrypt = userResponse.hashmail + "/" + file
                encryptedPath = cipher.encrypt(pathToEncrypt.encode())
                files[file]["link"] = "http://localhost:8000/file/" + encryptedPath.decode()
    #return dictionary
    return dict(sorted(files.items()))

# Allow logged user to download own files
@app.post('/myfiles/download')
async def download(tokenRequest: TokenRequest, db: db_dependency, fileNameModel:
                   FileName):
    # Validate token and get response
    userResponse = validate_token(tokenRequest, db)
    if userResponse:
        fileName = fileNameModel.filename
        userPath = "users/" + userResponse.hashmail + "/"
        return FileResponse(path=userPath + fileName, filename=fileName,
                            headers={
                                "Access-Control-Expose-Headers" : 
                                    "Content-Disposition",
                                "Content-Disposition" : 
                                    "attachment; filename =\"" + fileName +
                                    "\"" 
                                }
                            )

@app.post('/myfiles/share')
async def set_shared_file(tokenRequest: TokenRequest, db: db_dependency,
                          fileNameModel: FileName):
    # Validate token
    userResponse = validate_token(tokenRequest, db)
    if userResponse:
        fileName = fileNameModel.filename
        userPath = userResponse.hashmail + "/"
        pathToEncrypt = userPath + fileName
        pathToWorkWith = "users/" + pathToEncrypt
        # Toggle sharable state: Shared -> Not shared and Not shared -> Shared.
        # If we toggle to Shared, generate encrypted path and return it 
        if xattr.getxattr(pathToWorkWith, "user.shareable").decode() == "True":
            xattr.setxattr(pathToWorkWith, "user.shareable", "False".encode())
            return { "message" : False }
        else:
            xattr.setxattr(pathToWorkWith, "user.shareable", "True".encode())
            async with aiofiles.open('key', 'rb') as keyFile:
                key = await keyFile.read()
            cipher = Fernet(key)
            encryptedPath = cipher.encrypt(pathToEncrypt.encode())
            return { "message" : "http://127.0.0.1:8000/file/" + encryptedPath.decode() }

# Endpoint for uploading files, for both guest and logged in user
@app.post('/upload')
async def upload(db: db_dependency, tokenRequest: str = Form(None), 
                 files: List[UploadFile] = File(...), 
                 extensions: List[str] = Form(...)):

    # Set default auth state and file path
    auth = False
    filePath = "files/"

    # Check is we received a token
    if tokenRequest is not None:
        # Workaround to get tokenRequest object from string. Maybe we can
        # fix it later.
        tokenRequest = TokenRequest(token=tokenRequest)
        # Validate token
        userResponse = validate_token(tokenRequest, db)
        if userResponse:
            # Set auth state to true and change path
            auth = True
            filePath = "users/" + userResponse.hashmail + "/"

    # List of tuples with the following structure: [(converted filename,
    # converted file path)]
    convFilePathList = []

    # Iterate over list of files and a list of extensions at the same time.
    # Considered a tuple using zip()
    for file, extension in zip(files, extensions):
        # Keep a copy of the file path
        filePathCopy = filePath
        # Get filename without extension and extension separately
        fileNameNoExt, fileExt = os.path.splitext(file.filename)
        if auth:
            # Add a number to the name if converted file already exists with
            # same name
            # !!!THIS NEEDS TO BE CHANGED IN THE FUTURE!!!
            # TODO: Find a way to send labels from convert.sh instead of
            # extensions and yet have the extension ready to check if a file
            # with similiar name exist.
            # Example: 
            # Filename:    Label: 
            # file.wav     mp3@320k
            # mp3@320k should be mp3 file with 320k bitrate. Now for
            # authenticated user check if file.mp3 exists so you can
            # fix_filename() if does.
            # In other words, FIND A WAY TO GET AN EXTENSION FROM A LABEL.
            fileNameNoExt = await fix_filename(filePath, fileNameNoExt,
                                               extension)
        else:
            # Get random file name for guest user
            fileNameNoExt = str(uuid.uuid4().hex)[:16] 

        # Set up the proper file path
        filePath = filePath + fileNameNoExt + fileExt
        # Write file to disk
        await write_uploaded_file_to_disk(file, filePath)
        # Convert file from file path and get converted file path
        convFilePath = await write_converted_file_to_disk(auth, filePath,
                                                          extension)

        if auth:
            # Set async task to delete uploaded file
            asyncio.create_task(del_files([filePath], 1))
            # Set sharable extended attribute if file got converted alright,
            # else catch error
            try:
                xattr.setxattr(convFilePath, "user.shareable",
                               "False".encode())
            except FileNotFoundError:
                print(('File ' + convFilePath + ' marked for setting sharable'
                       'flag but file not found.'))
        else:
            # Set async task to delete both files in 5 minutes if guest user
            asyncio.create_task(del_files([filePath, convFilePath], 300))

        # Return -1 if missing file path for converted file
        if convFilePath == "-1":
            return { "message" : "-1" }

        # Add tuple of filename and file path to list
        convFilePathList.append((fileNameNoExt + extension, convFilePath))

        # Bring back original path for the next file
        filePath = filePathCopy

    # If we got multiple files, make a zip for them, set headers right for
    # response
    if len(convFilePathList) > 1:
        zipPath, zipFileName = await async_create_zip(convFilePathList)

        # Set extended attribute for archive if user is authenticated, else
        # mark archive for deletion in 5 minutes if user is guest
        if auth:
            xattr.setxattr(zipPath, "user.shareable", "False".encode())
        else:
            asyncio.create_task(del_files([zipPath], 300))
        
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

# TODO: Endpoint for allowing user to delete files
@app.post('/myfiles/delete')
async def delete_user_files(tokenRequest: TokenRequest, db: db_dependency,
                          fileNameModel: FileName):
    # Validate token
    userResponse = validate_token(tokenRequest, db)
    if userResponse:
        fileName = fileNameModel.filename
        userPath = userResponse.hashmail + "/"
        pathToWorkWith = "users/" + userPath + fileName
        # Delete file if exists, if not return 404
        if os.path.isfile(pathToWorkWith):
            os.unlink(pathToWorkWith)
            return { "message" : "File " + fileName + " deleted." }
        else:
            raise HTTPException(status_code=404, detail="Not Found")
    return


# === MAIN ===

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        reload=True,
        # host="0.0.0.0"
    )
