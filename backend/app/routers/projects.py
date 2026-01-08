from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.db_models import Project, User
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
def get_projects(active_only: bool = True, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Project).filter(Project.user_id == current_user.id)
    if active_only:
        query = query.filter(Project.active == True)
    projects = query.order_by(Project.created_at.desc()).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_project = Project(
        name = project.name, 
        description = project.description,
        color = project.color,
        user_id = current_user.id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):

    db_project = db.query(Project).filter(Project.id == project_id, 
                                          Project.user_id == current_user.id).first()
    if not db_project:
        raise HTTPException(

            status_code = status.HTTP_404_NOT_FOUND,
            detail="Project Not found"
        )



    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.commit()
    db.refresh(db_project)

    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id : int,
    current_user: User = Depends(get_current_user),
    db : Session = Depends(get_db)
):

    db_project = db.query(Project).filter(Project.id == project_id, 
                                          Project.user_id == current_user.id).first()
    
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    db_project.active = False
    db.commit()

    return None


