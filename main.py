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


def main():
    pass


if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0"
    )
