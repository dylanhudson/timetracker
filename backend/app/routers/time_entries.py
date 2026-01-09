from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.db_models import TimeEntry, User, Project
from app.schemas import TimeEntryStart, TimeEntryStop, TimeEntryCreate, TimeEntryResponse
from app.auth import get_current_user

router = APIRouter(prefix="/time-entries", tags=["time entries"])


@router.post("/start", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def start_time_entry(
    entry_data: TimeEntryStart,
    current_user : User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # verify the  ownership before creating the entry 
    db_project = db.query(Project).filter(Project.id == entry_data.project_id,
                                          Project.user_id == current_user.id).first()
    if not db_project:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="project not found"
        )
    
    db_time_entry = TimeEntry(
        project_id=entry_data.project_id,
        start_time=datetime.now(),
        user_id=current_user.id
    )
    db.add(db_time_entry)

    db.commit()
    db.refresh(db_time_entry)
    return db_time_entry

@router.post("/{entry_id}/stop", response_model=TimeEntryResponse)
def stop_timer(
    entry_id : int, 
    stop_data: TimeEntryStop, 
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
):

    db_time_entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).filter(TimeEntry.user_id == current_user.id).first()

    if db_time_entry is not None:
        if db_time_entry.end_time is None:
            db_time_entry.end_time = datetime.now(timezone.utc)
            db_time_entry.description = stop_data.description
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time entry has already been stopped"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )

    db.commit()
    db.refresh(db_time_entry)
    return (db_time_entry)


@router.post("/", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
def create_time_entry(
    entry: TimeEntryCreate,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
):
    
    #verify ownership 
    db_project = db.query(Project).filter(Project.id == entry.project_id).filter(Project.user_id == current_user.id).first()
    
    if not db_project:
        raise(HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        ))
    
    
    db_time_entry = TimeEntry(
        project_id=entry.project_id,
        start_time=entry.start_time,
        end_time=entry.end_time,
        description=entry.description,
        user_id=current_user.id
    )


    db.add(db_time_entry)
    db.commit()
    db.refresh(db_time_entry)
    return db_time_entry

@router.get("/", response_model=List[TimeEntryResponse])
def get_time_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = db.query(TimeEntry).filter(TimeEntry.user_id == current_user.id).order_by(TimeEntry.start_time.desc()).all()
    return entries

@router.get("/", response_model = TimeEntryResponse)
def get_time_entry(
    entry_id : int,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
):
    db_time_entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == current_user.id).first()
    if not db_time_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )
    return db_time_entry
