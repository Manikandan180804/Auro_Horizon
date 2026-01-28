from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship

class Recommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    category: str
    image_url: str
    url: Optional[str] = Field(default=None)

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str # 'user' or 'ai'
    content: str

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interests: str = Field(default="") # Comma-separated interests
