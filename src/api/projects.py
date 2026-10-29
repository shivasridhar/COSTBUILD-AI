"""
FastAPI Router for BuildCost AI - Project Management & Project-Scoped Forecasting.
Includes JWT authentication dependencies and per-engineer project ownership checks (403 on mismatch).
"""

import json
import sqlite3
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator

from src.optimization.bom_optimizer import (
    optimize_procurement,
    DEFAULT_DB_PATH
)
from src.optimization.storage_advisor import evaluate_storage_procurement_strategy
from src.api.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])

ALLOWED_MATERIALS = {"steel", "cement", "sand", "brick", "bricks", "gravel", "wiring"}
VALID_STATUSES = {"planning", "in_progress", "completed", "archived"}


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., description="Project name (e.g. 'Priya — Coimbatore House')", example="Priya — Coimbatore House")
    sqft: float = Field(..., gt=0, description="Project size in square feet", example=1500)
    target_materials: List[str] = Field(
        default=["steel", "cement", "sand", "brick", "gravel", "wiring"],
        description="Target materials included in BOM calculation"
    )
    region: Optional[str] = Field(None, description="Geographic region", example="Tamil Nadu")
    notes: Optional[str] = Field(None, description="Free text notes")

    @field_validator("target_materials")
    def validate_materials(cls, value):
        if value is not None:
            if len(value) == 0:
                raise ValueError("target_materials list cannot be empty. Please select at least one material.")
            invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
            if invalid:
                raise ValueError(
                    f"Invalid target material(s): {invalid}. Allowed options are: {sorted(list(ALLOWED_MATERIALS))}"
                )
        return value


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    sqft: Optional[float] = Field(None, gt=0, description="Project size in square feet")
    target_materials: Optional[List[str]] = Field(None, description="Target materials")
    region: Optional[str] = Field(None, description="Geographic region")
    status: Optional[str] = Field(None, description="Project status ('planning', 'in_progress', 'completed', 'archived')")
    notes: Optional[str] = Field(None, description="Free text notes")

    @field_validator("target_materials")
    def validate_materials(cls, value):
        if value is not None:
            if len(value) == 0:
                raise ValueError("target_materials list cannot be empty. Please select at least one material.")
            invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
            if invalid:
                raise ValueError(
                    f"Invalid target material(s): {invalid}. Allowed options are: {sorted(list(ALLOWED_MATERIALS))}"
                )
        return value

    @field_validator("status")
    def validate_status(cls, value):
        if value is not None and value.lower() not in VALID_STATUSES:
            raise ValueError(f"Invalid status: '{value}'. Allowed options: {sorted(list(VALID_STATUSES))}")
        return value.lower() if value else value


class ProjectResponse(BaseModel):
    id: int
    name: str
    sqft: float
    target_materials: List[str]
    region: Optional[str]
    created_at: str
    updated_at: str
    status: str
    notes: Optional[str]
    user_id: Optional[int] = None


def _parse_materials(val: Any) -> List[str]:
    if not val:
        return []
    if isinstance(val, list):
        return [str(m).strip(' "[]\'') for m in val if str(m).strip(' "[]\'')]
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(m).strip(' "[]\'') for m in parsed if str(m).strip(' "[]\'')]
            if isinstance(parsed, str):
                return [m.strip(' "[]\'') for m in parsed.split(",") if m.strip(' "[]\'')]
        except Exception:
            pass
        return [m.strip(' "[]\'') for m in val.split(",") if m.strip(' "[]\'')]
    return []


def _format_project_row(row: sqlite3.Row) -> Dict[str, Any]:
    # Support database rows with or without user_id column
    row_keys = row.keys() if hasattr(row, 'keys') else []
    user_id = row["user_id"] if "user_id" in row_keys else None
    return {
        "id": row["id"],
        "name": row["name"],
        "sqft": row["sqft"],
        "target_materials": _parse_materials(row["target_materials"]),
        "region": row["region"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "status": row["status"],
        "notes": row["notes"],
        "user_id": user_id
    }


def _get_db_connection():
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_project_and_verify_ownership(conn: sqlite3.Connection, project_id: int, current_user_id: int) -> sqlite3.Row:
    """
    Fetches project from DB and enforces strict project ownership scoping.

    SECURITY RULE:
    - If project does NOT exist in DB -> returns 404 Not Found.
    - If project EXISTS but project.user_id != current_user_id (including legacy NULL user_id) -> returns 403 Forbidden.
      Returning 403 instead of 404 prevents leaking whether a project ID exists.
    """
    row = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found."
        )

    # Check ownership
    row_keys = row.keys() if hasattr(row, 'keys') else []
    user_id = row["user_id"] if "user_id" in row_keys else None

    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project."
        )
    return row


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create a Persistent Project")
def create_project(
    payload: ProjectCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Creates a new persistent project entity associated with the authenticated user ID.
    """
    now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    materials_json = json.dumps(payload.target_materials)

    conn = _get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (name, sqft, target_materials, region, created_at, updated_at, status, notes, user_id)
            VALUES (?, ?, ?, ?, ?, ?, 'planning', ?, ?);
            """,
            (payload.name, payload.sqft, materials_json, payload.region, now_iso, now_iso, payload.notes, current_user["id"])
        )
        project_id = cursor.lastrowid
        conn.commit()

        row = cursor.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
        return _format_project_row(row)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create project: {str(e)}")
    finally:
        conn.close()


@router.get("", response_model=List[ProjectResponse], summary="List User Projects")
def list_projects(
    status_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieves all projects owned by the currently authenticated user (`user_id == current_user.id`),
    with optional filter by `status` (e.g. `?status_filter=planning`).
    """
    conn = _get_db_connection()
    try:
        if status_filter:
            if status_filter.lower() not in VALID_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status filter. Options: {sorted(list(VALID_STATUSES))}"
                )
            rows = conn.execute(
                "SELECT * FROM projects WHERE user_id = ? AND LOWER(status) = LOWER(?) ORDER BY updated_at DESC;",
                (current_user["id"], status_filter)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC;",
                (current_user["id"],)
            ).fetchall()

        return [_format_project_row(r) for r in rows]
    finally:
        conn.close()


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get Single Project Details")
def get_project(
    project_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Fetches stored details for a single project by ID (scoped to authenticated owner).
    """
    conn = _get_db_connection()
    try:
        row = _get_project_and_verify_ownership(conn, project_id, current_user["id"])
        return _format_project_row(row)
    finally:
        conn.close()


@router.patch("/{project_id}", response_model=ProjectResponse, summary="Update Project Details")
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates mutable project attributes (name, sqft, target_materials, region, status, notes).
    Bumps `updated_at`. Enforces ownership verification.
    """
    conn = _get_db_connection()
    try:
        row = _get_project_and_verify_ownership(conn, project_id, current_user["id"])
        current = _format_project_row(row)

        new_name = payload.name if payload.name is not None else current["name"]
        new_sqft = payload.sqft if payload.sqft is not None else current["sqft"]
        new_materials = payload.target_materials if payload.target_materials is not None else current["target_materials"]
        new_region = payload.region if payload.region is not None else current["region"]
        new_status = payload.status if payload.status is not None else current["status"]
        new_notes = payload.notes if payload.notes is not None else current["notes"]

        now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        materials_json = json.dumps(new_materials)

        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE projects
            SET name = ?, sqft = ?, target_materials = ?, region = ?, status = ?, notes = ?, updated_at = ?
            WHERE id = ?;
            """,
            (new_name, new_sqft, materials_json, new_region, new_status, new_notes, now_iso, project_id)
        )
        conn.commit()

        updated_row = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
        return _format_project_row(updated_row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update project: {str(e)}")
    finally:
        conn.close()


@router.delete("/{project_id}", response_model=ProjectResponse, summary="Soft Delete (Archive) Project")
def delete_project(
    project_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Soft-deletes a project owned by the user by setting `status = 'archived'`.
    """
    conn = _get_db_connection()
    try:
        _get_project_and_verify_ownership(conn, project_id, current_user["id"])
        now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE projects SET status = 'archived', updated_at = ? WHERE id = ?;",
            (now_iso, project_id)
        )
        conn.commit()

        updated_row = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
        return _format_project_row(updated_row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to archive project: {str(e)}")
    finally:
        conn.close()


@router.get("/{project_id}/forecast", summary="Get Forecast for Stored Project")
def get_project_forecast(
    project_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Evaluates 12-month procurement forecast trajectories using stored project parameters.
    """
    conn = _get_db_connection()
    try:
        row = _get_project_and_verify_ownership(conn, project_id, current_user["id"])
        proj = _format_project_row(row)
    finally:
        conn.close()

    try:
        raw_res = optimize_procurement(
            sqft=int(proj["sqft"]),
            target_materials=proj["target_materials"],
            region=proj["region"],
            project_id=proj["id"],
            db_path=DEFAULT_DB_PATH
        )

        metadata = {
            "forecast_method": "naive_plus_drift",
            "project_id": proj["id"],
            "project_name": proj["name"],
            "model_limitation_note": (
                "Phase 3 evaluation revealed that complex ML models provided only a marginal, "
                "unreliable edge over naive baseline forecasts. Therefore, this procurement engine uses "
                "a simple, transparent naive + recent drift extrapolation to estimate near-term cost trajectories "
                "rather than presenting a fragile model as more capable than it is."
            ),
            "methodology_note": (
                "Wiring cost (wiring_cost_rs) includes 4 electrical components: (1) PVC insulated copper wire, "
                "(2) rigid PVC conduit, (3) modular switch boxes & faceplates, and (4) discrete DB/MCB distribution panel step-function lookup."
            )
        }

        return {
            "anchor_conversion": raw_res['anchor_conversion'],
            "forecast": raw_res['forecast_table'],
            "bom_cost_by_month": raw_res['bom_cost_table'],
            "recommendation": raw_res['recommendation'],
            "metadata": metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Procurement engine error: {str(e)}")


# =====================================================================
# PROJECT PHASES API ENDPOINTS (STAGED PROCUREMENT)
# =====================================================================

VALID_PHASE_STATUSES = {"upcoming", "active", "completed"}


class PhaseCreateRequest(BaseModel):
    phase_name: str = Field(..., description="Phase name (e.g. 'Foundation')", example="Foundation")
    materials: List[str] = Field(..., description="Subset of project target materials")
    expected_start_month: int = Field(default=0, ge=0, description="Months from project start when phase begins")
    sequence_order: int = Field(default=1, ge=1, description="Phase display order")

    @field_validator("materials")
    def validate_materials(cls, value):
        if not value or len(value) == 0:
            raise ValueError("materials list cannot be empty.")
        invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
        if invalid:
            raise ValueError(f"Invalid material(s): {invalid}. Allowed options: {sorted(list(ALLOWED_MATERIALS))}")
        return value


class PhaseUpdateRequest(BaseModel):
    phase_name: Optional[str] = Field(None, description="Phase name")
    materials: Optional[List[str]] = Field(None, description="Subset of materials")
    expected_start_month: Optional[int] = Field(None, ge=0, description="Start month offset")
    status: Optional[str] = Field(None, description="Phase status ('upcoming', 'active', 'completed')")
    sequence_order: Optional[int] = Field(None, ge=1, description="Sequence order")

    @field_validator("materials")
    def validate_materials(cls, value):
        if value is not None:
            if len(value) == 0:
                raise ValueError("materials list cannot be empty.")
            invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
            if invalid:
                raise ValueError(f"Invalid material(s): {invalid}. Allowed options: {sorted(list(ALLOWED_MATERIALS))}")
        return value

    @field_validator("status")
    def validate_status(cls, value):
        if value is not None and value.lower() not in VALID_PHASE_STATUSES:
            raise ValueError(f"Invalid status: '{value}'. Allowed options: {sorted(list(VALID_PHASE_STATUSES))}")
        return value.lower() if value else value


class PhaseResponse(BaseModel):
    id: int
    project_id: int
    phase_name: str
    materials: List[str]
    expected_start_month: int
    status: str
    sequence_order: int
    created_at: str
    updated_at: str


def _format_phase_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "phase_name": row["phase_name"],
        "materials": _parse_materials(row["materials"]),
        "expected_start_month": row["expected_start_month"],
        "status": row["status"],
        "sequence_order": row["sequence_order"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


@router.post("/{project_id}/phases", response_model=PhaseResponse, status_code=status.HTTP_201_CREATED, summary="Create a Construction Phase")
def create_phase(
    project_id: int,
    payload: PhaseCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Creates a new construction phase attached to a project owned by the user.
    """
    conn = _get_db_connection()
    try:
        _get_project_and_verify_ownership(conn, project_id, current_user["id"])

        now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        materials_json = json.dumps(payload.materials)

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO project_phases (project_id, phase_name, materials, expected_start_month, status, sequence_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'upcoming', ?, ?, ?);
            """,
            (project_id, payload.phase_name, materials_json, payload.expected_start_month, payload.sequence_order, now_iso, now_iso)
        )
        phase_id = cursor.lastrowid
        conn.commit()

        row = cursor.execute("SELECT * FROM project_phases WHERE id = ?;", (phase_id,)).fetchone()
        return _format_phase_row(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create phase: {str(e)}")
    finally:
        conn.close()


@router.get("/{project_id}/phases", response_model=List[PhaseResponse], summary="List Phases for a Project")
def list_phases(
    project_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lists all construction phases for a given project owned by the user.
    """
    conn = _get_db_connection()
    try:
        _get_project_and_verify_ownership(conn, project_id, current_user["id"])
        rows = conn.execute("SELECT * FROM project_phases WHERE project_id = ? ORDER BY sequence_order ASC, expected_start_month ASC;", (project_id,)).fetchall()
        return [_format_phase_row(r) for r in rows]
    finally:
        conn.close()


@router.patch("/{project_id}/phases/{phase_id}", response_model=PhaseResponse, summary="Update a Construction Phase")
def update_phase(
    project_id: int,
    phase_id: int,
    payload: PhaseUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates mutable attributes of a phase on a project owned by the user.
    """
    conn = _get_db_connection()
    try:
        _get_project_and_verify_ownership(conn, project_id, current_user["id"])

        row = conn.execute("SELECT * FROM project_phases WHERE id = ? AND project_id = ?;", (phase_id, project_id)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Phase #{phase_id} not found for project #{project_id}.")

        current = _format_phase_row(row)
        new_name = payload.phase_name if payload.phase_name is not None else current["phase_name"]
        new_mats = payload.materials if payload.materials is not None else current["materials"]
        new_start = payload.expected_start_month if payload.expected_start_month is not None else current["expected_start_month"]
        new_status = payload.status if payload.status is not None else current["status"]
        new_seq = payload.sequence_order if payload.sequence_order is not None else current["sequence_order"]

        now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        mats_json = json.dumps(new_mats)

        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE project_phases
            SET phase_name = ?, materials = ?, expected_start_month = ?, status = ?, sequence_order = ?, updated_at = ?
            WHERE id = ?;
            """,
            (new_name, mats_json, new_start, new_status, new_seq, now_iso, phase_id)
        )
        conn.commit()

        updated_row = conn.execute("SELECT * FROM project_phases WHERE id = ?;", (phase_id,)).fetchone()
        return _format_phase_row(updated_row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update phase: {str(e)}")
    finally:
        conn.close()


@router.delete("/{project_id}/phases/{phase_id}", status_code=status.HTTP_200_OK, summary="Delete a Construction Phase")
def delete_phase(
    project_id: int,
    phase_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Hard deletes a phase from project_phases on a project owned by the user.
    """
    conn = _get_db_connection()
    try:
        _get_project_and_verify_ownership(conn, project_id, current_user["id"])

        row = conn.execute("SELECT * FROM project_phases WHERE id = ? AND project_id = ?;", (phase_id, project_id)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Phase #{phase_id} not found for project #{project_id}.")

        conn.execute("UPDATE vendor_quotes SET phase_id = NULL WHERE phase_id = ?;", (phase_id,))
        conn.execute("DELETE FROM project_phases WHERE id = ?;", (phase_id,))
        conn.commit()
        return {"message": "Phase deleted successfully", "id": phase_id, "project_id": project_id}
    finally:
        conn.close()


@router.get("/{project_id}/phases/{phase_id}/forecast", summary="Get Forecast for a Construction Phase")
def get_phase_forecast(
    project_id: int,
    phase_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Evaluates 12-month procurement forecast trajectories for a specific phase of a project owned by the user.
    """
    conn = _get_db_connection()
    try:
        proj_row = _get_project_and_verify_ownership(conn, project_id, current_user["id"])

        phase_row = conn.execute("SELECT * FROM project_phases WHERE id = ? AND project_id = ?;", (phase_id, project_id)).fetchone()
        if not phase_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Phase #{phase_id} not found for project #{project_id}.")

        proj = _format_project_row(proj_row)
        phase = _format_phase_row(phase_row)
    finally:
        conn.close()

    try:
        raw_res = optimize_procurement(
            sqft=int(proj["sqft"]),
            target_materials=phase["materials"],
            region=proj["region"],
            project_id=proj["id"],
            start_month_offset=phase["expected_start_month"],
            db_path=DEFAULT_DB_PATH
        )

        metadata = {
            "forecast_method": "naive_plus_drift",
            "project_id": proj["id"],
            "project_name": proj["name"],
            "phase_id": phase["id"],
            "phase_name": phase["phase_name"],
            "expected_start_month": phase["expected_start_month"]
        }

        return {
            "phase": phase,
            "anchor_conversion": raw_res['anchor_conversion'],
            "forecast": raw_res['forecast_table'],
            "bom_cost_by_month": raw_res['bom_cost_table'],
            "recommendation": raw_res['recommendation'],
            "metadata": metadata
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Phase forecast error: {str(e)}")


@router.get("/{project_id}/phases/summary", summary="Get All Phase Recommendations Summary")
def get_phases_summary(
    project_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Returns all phases for a project owned by the user along with their individual forecast recommendations.
    """
    conn = _get_db_connection()
    try:
        proj_row = _get_project_and_verify_ownership(conn, project_id, current_user["id"])

        proj = _format_project_row(proj_row)
        phase_rows = conn.execute("SELECT * FROM project_phases WHERE project_id = ? ORDER BY sequence_order ASC, expected_start_month ASC;", (project_id,)).fetchall()
        phases = [_format_phase_row(r) for r in phase_rows]
    finally:
        conn.close()

    phases_summary = []
    for ph in phases:
        try:
            raw_res = optimize_procurement(
                sqft=int(proj["sqft"]),
                target_materials=ph["materials"],
                region=proj["region"],
                project_id=proj["id"],
                start_month_offset=ph["expected_start_month"],
                db_path=DEFAULT_DB_PATH
            )
            phases_summary.append({
                "phase": ph,
                "recommendation": raw_res["recommendation"],
                "anchor_conversion": raw_res["anchor_conversion"],
                "forecast": raw_res["forecast_table"],
                "bom_cost_by_month": raw_res["bom_cost_table"]
            })
        except Exception as e:
            phases_summary.append({
                "phase": ph,
                "error": str(e)
            })

    return {
        "project_id": proj["id"],
        "project_name": proj["name"],
        "phase_count": len(phases_summary),
        "phases": phases_summary
    }


@router.get("/{project_id}/procurement-strategy", summary="Get Storage-Feasibility Procurement Strategy Advisory")
def get_project_procurement_strategy(
    project_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Evaluates storage-feasibility-aware procurement strategy advisories for materials shared across project phases.
    Returns bulk vs per-phase purchase recommendations with day-count gaps, shelf-life limits, and cost comparisons.
    """
    conn = _get_db_connection()
    try:
        _get_project_and_verify_ownership(conn, project_id, current_user["id"])
    finally:
        conn.close()

    try:
        res = evaluate_storage_procurement_strategy(project_id, db_path=DEFAULT_DB_PATH)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Storage strategy evaluation failed: {str(e)}")

