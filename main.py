from database import engine, SessionLocal
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from typing import List
from zipfile import ZipFile
import models
import os
import uvicorn

# commented database part for now
# models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

@app.get("/test")
def test():
    return {"message": "Hello World"}
#  http://127.0.0.1:8000/docs - to test API endpoints

# very quick, hacky and primitive first try
# TODO: Fix hardcoded paths
@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)): # files is a list of file objects
    for file in files: # parsing through the list and reading in chunks 
        try: 
            with open("files/" + file.filename, 'wb') as f: # write to file folder
                while contents := file.file.read(1024 * 1024): # 1MB chunks
                    f.write(contents) 
        except Exception: 
            return {"message": "There was an error uploading the file(s)"} 
        finally:
            file.file.close()
    return {"message": f"Successfuly uploaded {[file.filename for file in files]}"}

@app.post("/download")
async def download(files: List[str] = File(...)): #downloading from a list of strings (paths)
    # list is actually stored as a string with commas inbetween in the first element of the list
    # we can split the string into a an actual list and then move it back to file
    files = list(files[0].split(',')) 

    if len(files) < 2: # if we have just one item just return it
        try:
            return FileResponse("files/" + files[0])
        except Exception: 
            return {"message": "There was an error downloading the file"} 
    
    else: # on multiple items we create a zip archive and append the files
        with ZipFile("dfiles/dzip.zip", 'a') as zip_object: 
            for file in files:
                 zip_object.write("files/" + file) 
        
        # return archive 
        return FileResponse(path="dfiles/dzip.zip", filename="dzip.zip")

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
