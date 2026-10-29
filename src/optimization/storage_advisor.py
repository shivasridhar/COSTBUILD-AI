"""
Storage-Feasibility-Aware Procurement Strategy Advisor for BuildCost AI.

Evaluates whether materials shared across multiple project construction phases can be safely
bulk-purchased upfront or must be purchased separately per phase due to real-world material
shelf-life, price trend trajectories, and degradation constraints.
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional

from src.optimization.bom_optimizer import (
    optimize_procurement,
    DEFAULT_DB_PATH
)


def get_material_storage_properties(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Retrieves reference storage properties for all registered materials from database.
    """
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM material_storage_properties;").fetchall()
        result = {}
        for r in rows:
            result[r["material"].lower()] = {
                "material": r["material"],
                "max_safe_storage_days": r["max_safe_storage_days"],
                "degrades": bool(r["degrades"]),
                "storage_notes": r["storage_notes"]
            }
        return result
    finally:
        conn.close()


def _parse_materials_list(val: Any) -> List[str]:
    if not val:
        return []
    if isinstance(val, list):
        return [str(m).strip(' "[]\'').lower() for m in val if str(m).strip(' "[]\'')]
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(m).strip(' "[]\'').lower() for m in parsed if str(m).strip(' "[]\'')]
        except Exception:
            pass
        return [m.strip(' "[]\'').lower() for m in val.split(",") if m.strip(' "[]\'')]
    return []


def evaluate_storage_procurement_strategy(
    project_id: int,
    db_path: str = None
) -> Dict[str, Any]:
    """
    Evaluates storage feasibility and cost trade-offs for materials shared across project phases.

    Reuses existing `optimize_procurement()` engine to calculate bulk vs per-phase costs.

    Decision Matrix:
    - If storage life covers phase gap AND bulk cost < per-phase cost -> Strategy: "bulk"
    - If storage life covers phase gap BUT per-phase cost <= bulk cost -> Strategy: "per_phase" (for cost optimization)
    - If storage life does NOT cover phase gap -> Strategy: "per_phase" (for material safety)
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at path: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # 1. Fetch Project Details
        proj_row = conn.execute("SELECT * FROM projects WHERE id = ?;", (project_id,)).fetchone()
        if not proj_row:
            raise ValueError(f"Project #{project_id} not found.")

        project_name = proj_row["name"]
        project_sqft = float(proj_row["sqft"])
        project_region = proj_row["region"]

        # 2. Fetch Project Phases
        phase_rows = conn.execute(
            "SELECT * FROM project_phases WHERE project_id = ? ORDER BY sequence_order ASC, expected_start_month ASC;",
            (project_id,)
        ).fetchall()

        phases = []
        for pr in phase_rows:
            phases.append({
                "id": pr["id"],
                "phase_name": pr["phase_name"],
                "materials": _parse_materials_list(pr["materials"]),
                "expected_start_month": int(pr["expected_start_month"]),
                "sequence_order": int(pr["sequence_order"])
            })

    finally:
        conn.close()

    storage_props = get_material_storage_properties(db_path)

    if len(phases) < 2:
        return {
            "project_id": project_id,
            "project_name": project_name,
            "phase_count": len(phases),
            "advisories": [],
            "message": "Project has fewer than 2 phases. Storage-feasibility strategy advisory applies to materials shared across multiple construction phases."
        }

    # Group phases by material
    material_phases_map: Dict[str, List[Dict[str, Any]]] = {}
    for ph in phases:
        for mat in ph["materials"]:
            if mat not in material_phases_map:
                material_phases_map[mat] = []
            material_phases_map[mat].append(ph)

    advisories = []

    for mat, inv_phases in material_phases_map.items():
        # Only evaluate materials spanning 2+ phases
        if len(inv_phases) < 2:
            continue

        # Sort involved phases by start month
        inv_phases.sort(key=lambda x: (x["expected_start_month"], x["sequence_order"]))

        min_month = inv_phases[0]["expected_start_month"]
        max_month = inv_phases[-1]["expected_start_month"]
        gap_months = max_month - min_month
        gap_days = gap_months * 30

        prop = storage_props.get(mat, {
            "max_safe_storage_days": None,
            "degrades": False,
            "storage_notes": "Standard construction material storage practices apply."
        })

        max_safe_days = prop["max_safe_storage_days"]
        degrades = prop["degrades"]
        storage_notes = prop["storage_notes"]

        storage_safe = (max_safe_days is None) or (gap_days <= max_safe_days)

        # -----------------------------------------------------------------
        # Calculate Bulk Cost vs Per-Phase Cost using existing engine
        # -----------------------------------------------------------------
        # A) Bulk Purchase Cost (buying full project material quantity across combined window)
        try:
            bulk_opt = optimize_procurement(
                sqft=int(project_sqft),
                target_materials=[mat],
                region=project_region,
                project_id=project_id,
                start_month_offset=min_month,
                db_path=db_path
            )
            bulk_cost = float(bulk_opt['recommendation']['optimal_cost_rs'])
            bulk_rec_month = bulk_opt['recommendation']['recommended_year_month']
        except Exception as e:
            bulk_cost = 0.0
            bulk_rec_month = "N/A"

        # B) Per-Phase Purchase Cost (sum of per-phase forecast costs)
        per_phase_total = 0.0
        phase_breakdown = []

        for ph in inv_phases:
            try:
                ph_opt = optimize_procurement(
                    sqft=int(project_sqft),
                    target_materials=[mat],
                    region=project_region,
                    project_id=project_id,
                    start_month_offset=ph["expected_start_month"],
                    db_path=db_path
                )
                ph_cost = float(ph_opt['recommendation']['optimal_cost_rs'])
                ph_rec_month = ph_opt['recommendation']['recommended_year_month']
            except Exception:
                ph_cost = 0.0
                ph_rec_month = "N/A"

            per_phase_total += ph_cost
            phase_breakdown.append({
                "phase_id": ph["id"],
                "phase_name": ph["phase_name"],
                "start_month_offset": ph["expected_start_month"],
                "recommended_month": ph_rec_month,
                "cost_rs": ph_cost
            })

        # -----------------------------------------------------------------
        # 3-Way Strategy Recommendation Logic
        # -----------------------------------------------------------------
        if storage_safe:
            if bulk_cost < per_phase_total and bulk_cost > 0:
                strategy = "bulk"
                savings_rs = round(per_phase_total - bulk_cost, 2)
                savings_pct = round((savings_rs / per_phase_total) * 100.0, 2) if per_phase_total > 0 else 0.0
                reasoning = (
                    f"Bulk purchase recommended across {len(inv_phases)} phases. "
                    f"The {gap_months}-month gap ({gap_days} days) between '{inv_phases[0]['phase_name']}' and '{inv_phases[-1]['phase_name']}' "
                    f"is within the safe storage limit ({max_safe_days or 'unlimited'} days). "
                    f"Procuring bulk in {bulk_rec_month} saves ₹{savings_rs:,.2f} ({savings_pct}%) compared to separate per-phase purchases."
                )
            else:
                strategy = "per_phase"
                cost_diff = round(bulk_cost - per_phase_total, 2)
                savings_rs = 0.0
                savings_pct = 0.0
                reasoning = (
                    f"Per-phase purchase recommended for cost optimization. "
                    f"Although storage life permits bulk buying ({gap_days} days gap vs {max_safe_days or 'unlimited'} days safe limit), "
                    f"purchasing separately per phase is ₹{cost_diff:,.2f} lower in total cost due to projected WPI price trend dips."
                )
        else:
            strategy = "per_phase"
            savings_rs = 0.0
            savings_pct = 0.0
            reasoning = (
                f"Per-phase purchase required for material safety. "
                f"The {gap_months}-month gap ({gap_days} days) between '{inv_phases[0]['phase_name']}' and '{inv_phases[-1]['phase_name']}' "
                f"exceeds {mat.capitalize()}'s safe storage limit (~{max_safe_days} days) before moisture/structural degradation risks occur."
            )

        advisories.append({
            "material": mat,
            "phases_involved": [ph["phase_name"] for ph in inv_phases],
            "phase_count": len(inv_phases),
            "gap_months": gap_months,
            "gap_days": gap_days,
            "max_safe_storage_days": max_safe_days,
            "degrades": degrades,
            "storage_safe": storage_safe,
            "strategy": strategy,
            "reasoning": reasoning,
            "bulk_cost_estimate_rs": round(bulk_cost, 2),
            "bulk_recommended_month": bulk_rec_month,
            "per_phase_cost_estimate_rs": round(per_phase_total, 2),
            "savings_rs": savings_rs,
            "savings_pct": savings_pct,
            "phase_breakdown": phase_breakdown,
            "storage_notes": storage_notes
        })

    return {
        "project_id": project_id,
        "project_name": project_name,
        "phase_count": len(phases),
        "shared_materials_count": len(advisories),
        "advisories": advisories,
        "metadata": {
            "evaluation_engine": "storage_feasibility_advisor_v1",
            "notes": "Bulk strategy recommendations require BOTH safe storage duration AND a lower total cost than per-phase purchasing."
        }
    }
