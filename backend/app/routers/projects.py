from fastapi import APIRouter, HTTPException

from backend.app.project.project_store import get_project, list_projects, save_project
from backend.app.schemas.project import (
    ProjectListResponse,
    ProjectPayload,
    ProjectRecord,
    ProjectSaveResponse,
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=ProjectListResponse)
def get_projects():
    return ProjectListResponse(
        success=True,
        projects=list_projects(),
    )


@router.get("/{project_id}", response_model=ProjectRecord)
def read_project(project_id: str):
    project = get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato.")

    return project


@router.post("", response_model=ProjectSaveResponse)
def create_project(payload: ProjectPayload):
    project = save_project(payload)

    return ProjectSaveResponse(
        success=True,
        message="Progetto salvato.",
        project=project,
    )


@router.put("/{project_id}", response_model=ProjectSaveResponse)
def update_project(project_id: str, payload: ProjectPayload):
    project = save_project(payload, project_id=project_id)

    return ProjectSaveResponse(
        success=True,
        message="Progetto aggiornato.",
        project=project,
    )