from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, LargeBinary
from sqlalchemy.orm import relationship
from pydantic import BaseModel, constr
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashmail = Column(String, unique=True, index=True)
    name = Column(String)
    image = Column(String)  # Store image path
    token = Column(String)
    refresh_token = Column(String)
    token_expiry = Column(DateTime)
    refresh_token_expiry = Column(DateTime)

class FileName(BaseModel):
    filename: str
