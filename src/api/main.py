"""
FastAPI Service for BuildCost AI - Phase 4 API Deployment.

Exposes live endpoints for procurement optimization and health monitoring.
"""

import os
import sqlite3
import sys
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.optimization.bom_optimizer import optimize_procurement, DEFAULT_DB_PATH

ALLOWED_MATERIALS = {"steel", "cement", "sand", "brick", "bricks", "gravel"}

app = FastAPI(
    title="BuildCost AI - Procurement Optimization API",
    description=(
        "Live deployment endpoint for BOM cost calculation and procurement window optimization. "
        "Integrates PWD Schedule of Rates anchors with 12-month WPI drift trajectory forecasts."
    ),
    version="1.0.0"
)


class OptimizationRequest(BaseModel):
    sqft: int = Field(
        ...,
        gt=0,
        description="Project size in square feet. Must be a positive integer greater than 0.",
        example=1000
    )
    target_materials: Optional[List[str]] = Field(
        default=["steel", "cement", "sand", "brick", "gravel"],
        description="List of materials to include in the BOM total cost. Options: steel, cement, sand, brick, gravel.",
        example=["steel", "cement", "sand", "brick", "gravel"]
    )

    @field_validator("target_materials")

    def validate_materials(cls, value):
        if value is not None:
            invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
            if invalid:
                raise ValueError(
                    f"Invalid target material(s): {invalid}. Allowed options are: ['steel', 'cement', 'sand', 'brick', 'gravel']."
                )
        return value


class OptimizationResponse(BaseModel):
    anchor_conversion: Dict[str, Any] = Field(
        ...,
        description="PWD FY 2025-26 reference rates, average WPI index points, conversion factors (₹/index point), and sanity check results."
    )
    forecast: List[Dict[str, Any]] = Field(
        ...,
        description="12-month forward WPI index values and ₹/MT price trajectories for dynamic materials (cement and steel)."
    )
    bom_cost_by_month: List[Dict[str, Any]] = Field(
        ...,
        description="Monthly BOM cost breakdown per material and total BOM cost over the 12-month forecast horizon."
    )
    recommendation: Dict[str, Any] = Field(
        ...,
        description="Procurement recommendation including recommended month, immediate purchase cost, optimal cost, savings (₹ and %), and summary recommendation text."
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="API pipeline execution metadata including forecast methodology and model limitation disclosure."
    )


class HealthResponse(BaseModel):
    status: str = Field(..., description="API operational status", example="ok")
    database_connected: bool = Field(..., description="Database connectivity verification status", example=True)
    db_path: str = Field(..., description="Path to buildcost.db SQLite database")


@app.get("/health", response_model=HealthResponse, summary="API & Database Health Check")
def health_check():
    """
    Health check endpoint confirming that the API service is active and `buildcost.db` is reachable.
    """
    db_reachable = False
    if os.path.exists(DEFAULT_DB_PATH):
        try:
            conn = sqlite3.connect(DEFAULT_DB_PATH)
            conn.execute("SELECT 1;")
            conn.close()
            db_reachable = True
        except Exception:
            db_reachable = False

    if not db_reachable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unreachable or invalid at path: {DEFAULT_DB_PATH}"
        )

    return HealthResponse(
        status="ok",
        database_connected=db_reachable,
        db_path=DEFAULT_DB_PATH
    )


@app.post(
    "/predict-optimal-build-window",
    response_model=OptimizationResponse,
    summary="Predict Optimal Construction Procurement Window",
    status_code=status.HTTP_200_OK
)
def predict_optimal_build_window(payload: OptimizationRequest):
    """
    Evaluates 12-month BOM cost trajectories and identifies the optimal procurement window.

    - **sqft**: Must be a positive integer > 0.
    - **target_materials**: Subset of materials to include in BOM total.
    """
    try:
        raw_res = optimize_procurement(
            sqft=payload.sqft,
            target_materials=payload.target_materials,
            db_path=DEFAULT_DB_PATH
        )

        metadata = {
            "forecast_method": "naive_plus_drift",
            "model_limitation_note": (
                "Phase 3 evaluation revealed that complex ML models provided only a marginal, "
                "unreliable edge over naive baseline forecasts. Therefore, this procurement engine uses "
                "a simple, transparent naive + recent drift extrapolation to estimate near-term cost trajectories "
                "rather than presenting a fragile model as more capable than it is."
            )
        }

        return OptimizationResponse(
            anchor_conversion=raw_res['anchor_conversion'],
            forecast=raw_res['forecast_table'],
            bom_cost_by_month=raw_res['bom_cost_table'],
            recommendation=raw_res['recommendation'],
            metadata=metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Procurement engine error: {str(e)}")
