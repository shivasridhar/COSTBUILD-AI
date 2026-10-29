"""
FastAPI Service for BuildCost AI - Phase 4 API Deployment.

Exposes live endpoints for procurement optimization and health monitoring.
"""

import os
import sqlite3
import sys
import datetime
import json
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.optimization.bom_optimizer import (
    optimize_procurement,
    get_material_baseline_rate,
    save_vendor_quote,
    normalize_unit,
    DEFAULT_DB_PATH
)
from src.reports.generator import generate_pdf_report
from src.api.projects import router as projects_router
from src.api.auth import router as auth_router

ALLOWED_MATERIALS = {"steel", "cement", "sand", "brick", "bricks", "gravel", "wiring"}


app = FastAPI(
    title="BuildCost AI - Procurement Optimization API",
    description=(
        "Live deployment endpoint for BOM cost calculation and procurement window optimization. "
        "Integrates PWD Schedule of Rates anchors with 12-month WPI drift trajectory forecasts."
    ),
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(projects_router)

# Enable CORS for frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizationRequest(BaseModel):
    sqft: int = Field(
        ...,
        gt=0,
        description="Project size in square feet. Must be a positive integer greater than 0.",
        example=1000
    )
    target_materials: Optional[List[str]] = Field(
        default=["steel", "cement", "sand", "brick", "gravel", "wiring"],
        description="List of materials to include in the BOM total cost. Options: steel, cement, sand, brick, gravel, wiring.",
        example=["steel", "cement", "sand", "brick", "gravel", "wiring"]
    )
    region: Optional[str] = Field(
        default=None,
        description="Optional geographic region to filter vendor quote corrections (e.g. Tamil Nadu).",
        example="Tamil Nadu"
    )


    @field_validator("target_materials")
    def validate_materials(cls, value):
        if value is not None:
            invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
            if invalid:
                raise ValueError(
                    f"Invalid target material(s): {invalid}. Allowed options are: ['steel', 'cement', 'sand', 'brick', 'gravel', 'wiring']."
                )
        return value


class OptimizationResponse(BaseModel):
    anchor_conversion: Dict[str, Any] = Field(
        ...,
        description="PWD FY 2025-26 reference rates, average WPI index points, conversion factors (₹/index point), and sanity check results."
    )
    forecast: List[Dict[str, Any]] = Field(
        ...,
        description="12-month forward WPI index values and ₹/MT price trajectories for dynamic materials (cement, steel, wiring)."
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


class FairPriceCheckRequest(BaseModel):
    material: str = Field(..., description="Material name to check", example="steel")
    quoted_rate: float = Field(..., gt=0, description="Vendor quoted rate per unit in INR", example=58000.0)
    quoted_unit: str = Field(..., description="Unit of measurement used in the vendor quote", example="MT")
    quoted_date: str = Field(..., description="Quote date in YYYY-MM or YYYY-MM-DD format", example="2026-07-01")
    source_note: Optional[str] = Field(None, description="Optional vendor name or quote note")
    region: Optional[str] = Field(None, description="Optional geographic region")
    project_id: Optional[int] = Field(None, description="Optional project ID to associate quote with")
    phase_id: Optional[int] = Field(None, description="Optional construction phase ID to associate quote with")

    @field_validator("material")
    def validate_material(cls, value):
        if not value or value.lower().strip() not in ALLOWED_MATERIALS:
            raise ValueError(f"Invalid material: '{value}'. Allowed materials are: {sorted(list(ALLOWED_MATERIALS))}")
        return value


class FairPriceCheckResponse(BaseModel):
    baseline_rate: float = Field(..., description="Market baseline rate calculated from PWD anchor + WPI drift")
    baseline_unit: str = Field(..., description="Standard market unit for baseline rate comparison")
    deviation_pct: float = Field(..., description="Percentage deviation from baseline rate")
    verdict: str = Field(..., description="Fair price verdict: 'above market', 'at market', 'below market', 'unit mismatch', or 'date out of range'")
    note: str = Field(..., description="Explanatory note detailing verdict reasoning or unit/date mismatch details")
    quote_id: Optional[int] = Field(None, description="Inserted vendor quote ID")


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
            region=payload.region,
            db_path=DEFAULT_DB_PATH
        )


        metadata = {
            "forecast_method": "naive_plus_drift",
            "model_limitation_note": (
                "Phase 3 evaluation revealed that complex ML models provided only a marginal, "
                "unreliable edge over naive baseline forecasts. Therefore, this procurement engine uses "
                "a simple, transparent naive + recent drift extrapolation to estimate near-term cost trajectories "
                "rather than presenting a fragile model as more capable than it is."
            ),
            "methodology_note": (
                "Wiring cost (wiring_cost_rs) includes 4 electrical components: (1) PVC insulated copper wire (3.75 Rmt/sqft calibrated to WPI Wires & Cables index trajectory), "
                "(2) rigid PVC conduit (~3.75 Rmt/sqft @ ₹18.00/Rmt PWD baseline), (3) modular switch boxes & faceplates (1 point/90 sqft @ ₹120.00/point baseline), and "
                "(4) discrete DB/MCB distribution panel step-function lookup (₹4,500–₹28,000 based on area tier). "
                "Note: The move from FY 2025-26 PWD anchor (₹34.80/Rmt) to Month 1 (₹42.20/Rmt) reflects the verified historical surge in the official WPI Electric Wires & Cables series "
                "(WPI index rose from 120.4 FY25-26 average to 143.2 in mid-2026 due to global copper commodity price increases)."
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


@app.post(
    "/check-fair-price",
    response_model=FairPriceCheckResponse,
    summary="Check Vendor Quote Against Fair Market Baseline",
    status_code=status.HTTP_200_OK
)
def check_fair_price(payload: FairPriceCheckRequest):
    """
    Evaluates a single vendor quote for a specific material and date against the market baseline.

    - Stores quote entry in `vendor_quotes` table in `buildcost.db`.
    - Returns baseline rate, baseline unit, deviation %, verdict, and explanatory note.
    - If quoted_unit != baseline_unit, returns verdict: "unit mismatch" without silent conversion.
    """
    try:
        # Save vendor quote record into SQLite database
        quote_id = save_vendor_quote(
            material=payload.material,
            quoted_rate=payload.quoted_rate,
            quoted_unit=payload.quoted_unit,
            quoted_date=payload.quoted_date,
            source_note=payload.source_note,
            region=payload.region,
            project_id=payload.project_id,
            phase_id=payload.phase_id,
            db_path=DEFAULT_DB_PATH
        )

        # Retrieve baseline rate and expected baseline unit for material and date
        baseline_info = get_material_baseline_rate(
            material=payload.material,
            quoted_date=payload.quoted_date,
            db_path=DEFAULT_DB_PATH
        )

        baseline_rate = baseline_info['baseline_rate']
        baseline_unit = baseline_info['baseline_unit']

        # Handle out of range forecast date
        if baseline_info.get('out_of_range'):
            return FairPriceCheckResponse(
                baseline_rate=baseline_rate,
                baseline_unit=baseline_unit,
                deviation_pct=0.0,
                verdict="date out of range",
                note=baseline_info['range_note'],
                quote_id=quote_id
            )

        # Compare units without silent conversion
        quoted_norm = normalize_unit(payload.quoted_unit)
        base_norm = normalize_unit(baseline_unit)

        if quoted_norm != base_norm:
            return FairPriceCheckResponse(
                baseline_rate=baseline_rate,
                baseline_unit=baseline_unit,
                deviation_pct=0.0,
                verdict="unit mismatch",
                note=(
                    f"Unit mismatch: Vendor quote was provided in '{payload.quoted_unit}', "
                    f"but market baseline is expressed in '{baseline_unit}'. "
                    f"Please re-enter quote using '{baseline_unit}' for accurate price comparison."
                ),
                quote_id=quote_id
            )

        # Calculate deviation percentage when units match
        deviation_pct = round(((payload.quoted_rate - baseline_rate) / baseline_rate) * 100.0, 2)

        # Verdict classification (±5% at-market band)
        if deviation_pct > 5.0:
            verdict = "above market"
            note = (
                f"Quoted rate (₹{payload.quoted_rate:,.2f}/{payload.quoted_unit}) is {abs(deviation_pct):.2f}% ABOVE "
                f"the market baseline rate of ₹{baseline_rate:,.2f}/{baseline_unit}."
            )
        elif deviation_pct < -5.0:
            verdict = "below market"
            note = (
                f"Quoted rate (₹{payload.quoted_rate:,.2f}/{payload.quoted_unit}) is {abs(deviation_pct):.2f}% BELOW "
                f"the market baseline rate of ₹{baseline_rate:,.2f}/{baseline_unit}."
            )
        else:
            verdict = "at market"
            note = (
                f"Quoted rate (₹{payload.quoted_rate:,.2f}/{payload.quoted_unit}) is AT MARKET "
                f"(within normal ±5% band of baseline rate ₹{baseline_rate:,.2f}/{baseline_unit})."
            )

        return FairPriceCheckResponse(
            baseline_rate=baseline_rate,
            baseline_unit=baseline_unit,
            deviation_pct=deviation_pct,
            verdict=verdict,
            note=note,
            quote_id=quote_id
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Fair price check failed: {str(e)}")


class ReportGenerationRequest(BaseModel):
    sqft: Optional[int] = Field(
        default=None,
        gt=0,
        description="Project size in square feet. Pulled from project if project_id is provided.",
        example=1500
    )
    target_materials: Optional[List[str]] = Field(
        default=["steel", "cement", "sand", "brick", "gravel", "wiring"],
        description="List of materials to include in report. Options: steel, cement, sand, brick, gravel, wiring."
    )
    region: Optional[str] = Field(
        default=None,
        description="Optional geographic region to filter vendor quote baseline corrections (e.g. Tamil Nadu).",
        example="Tamil Nadu"
    )
    include_vendor_quotes: bool = Field(
        default=True,
        description="Whether to include vendor quotes audit log in the report."
    )
    vendor_quote_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional list of specific vendor quote IDs to include in report."
    )
    project_id: Optional[int] = Field(
        default=None,
        description="Optional project ID. When provided, sqft, target_materials, and region are pulled from project."
    )

    @field_validator("target_materials")
    def validate_materials(cls, value):
        if value is not None:
            invalid = [m for m in value if m.lower() not in ALLOWED_MATERIALS]
            if invalid:
                raise ValueError(
                    f"Invalid target material(s): {invalid}. Allowed options are: ['steel', 'cement', 'sand', 'brick', 'gravel', 'wiring']."
                )
        return value


@app.post(
    "/generate-report",
    summary="Generate PDF Procurement & Forecast Report",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Executive PDF report file stream."
        }
    }
)
def generate_report(payload: ReportGenerationRequest):
    """
    Generates and streams an executive PDF report consolidating forecast trajectories,
    BOM cost breakdowns, reference rate anchors, vendor quote checks, and model disclosures.
    """
    try:
        project_id = payload.project_id
        sqft = payload.sqft
        target_materials = payload.target_materials
        region = payload.region

        if project_id is not None:
            conn = sqlite3.connect(DEFAULT_DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
                if not row:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID {project_id} not found.")

                if sqft is None:
                    sqft = int(row["sqft"])
                if target_materials is None or len(target_materials) == 0:
                    try:
                        target_materials = json.loads(row["target_materials"])
                    except Exception:
                        target_materials = ["steel", "cement", "sand", "brick", "gravel", "wiring"]
                if region is None:
                    region = row["region"]
            finally:
                conn.close()

        if sqft is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Either 'sqft' or a valid 'project_id' must be provided.")

        pdf_bytes = generate_pdf_report(
            sqft=sqft,
            target_materials=target_materials,
            region=region,
            include_vendor_quotes=payload.include_vendor_quotes,
            vendor_quote_ids=payload.vendor_quote_ids,
            project_id=project_id,
            db_path=DEFAULT_DB_PATH
        )

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"buildcost-report-{today_str}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF report generation failed: {str(e)}")


