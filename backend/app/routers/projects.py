from fastapi import APIRouter, Depends, HTTPException

from backend.app.routers.auth import get_current_user
from backend.app.project.project_store import get_project, list_projects, save_project
from backend.app.schemas.project import (
    ProjectListResponse,
    ProjectPayload,
    ProjectRecord,
    ProjectSaveResponse,
)

router = APIRouter(prefix="/api/projects", tags=["Projects"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=ProjectListResponse)
def get_projects(current_user=Depends(get_current_user)):
    return ProjectListResponse(
        success=True,
        projects=list_projects(current_user["id"]),
    )


@router.get("/{project_id}", response_model=ProjectRecord)
def read_project(project_id: str, current_user=Depends(get_current_user)):
    project = get_project(project_id, current_user["id"])

    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato.")

    return project


@router.post("", response_model=ProjectSaveResponse)
def create_project(payload: ProjectPayload, current_user=Depends(get_current_user)):
    project = save_project(payload, current_user["id"])

    return ProjectSaveResponse(
        success=True,
        message="Progetto salvato.",
        project=project,
    )


@router.put("/{project_id}", response_model=ProjectSaveResponse)
def update_project(project_id: str, payload: ProjectPayload, current_user=Depends(get_current_user)):
    project = save_project(payload, current_user["id"], project_id=project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="Progetto non trovato.")

    return ProjectSaveResponse(
        success=True,
        message="Progetto aggiornato.",
        project=project,
    )
