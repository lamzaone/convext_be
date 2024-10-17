from database import engine, SessionLocal
import models
from fastapi import FastAPI
import uvicorn

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/test")
def test():
    return {"message": "Hello World"}
#  http://127.0.0.1:8000/docs - to test API endpoints

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        # host="0.0.0.0"
    )
