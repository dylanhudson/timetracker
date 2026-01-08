from pydantic import BaseModel, EmailStr, computed_field
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    # this lets us use ORM models (in this context from SQLAlchemy)
    # i.e. instead of dicts, we use the model.attribute syntax 
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class ProjectCreate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    active: bool | None = None

class ProjectResponse(BaseModel):
    id: int
    user_id: int
    name: str 
    description: str | None = None
    color: str 
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TimeEntryStart(BaseModel):
    project_id: int

class TimeEntryStop(BaseModel):
    description: str | None = None

class TimeEntryCreate(BaseModel):
    project_id: int
    start_time: datetime
    end_time: datetime 
    description: str | None = None


class TimeEntryResponse(BaseModel):
    id: int
    project_id: int
    start_time: datetime
    end_time: datetime | None = None
    description: str | None = None
    created_at: datetime

    @computed_field
    @property
    def duration_minutes(self) -> int | None:
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() // 60)
        else:
            return None
        
    class Config:
        from_attributes = True

    

