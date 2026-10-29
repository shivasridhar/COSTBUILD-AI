"""
Vendor-Quote-Corrected Baseline Engine for BuildCost AI.

Blends PWD-anchored WPI baselines with real recent vendor quotes logged in buildcost.db
to bridge the ~2.5 month WPI publication delay. Uses a transparent, weighted formula
(70% WPI Anchor + 30% Vendor Quotes Median) when at least 3 quotes are logged in trailing 45 days.
"""

import os
import sys
import sqlite3
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "buildcost.db")

# Configurable constants for transparent blending logic
MIN_QUOTES_THRESHOLD = 3      # Minimum recent quotes required to nudge baseline
TRAILING_DAYS_WINDOW = 45     # Trailing days window for vendor quotes lookup
WPI_BASELINE_WEIGHT = 0.70    # 70% weight assigned to PWD-anchored WPI baseline
VENDOR_QUOTE_WEIGHT = 0.30    # 30% weight assigned to median of observed vendor quotes


def normalize_material_key(material_str: str) -> str:
    """Normalizes material names for matching."""
    if not material_str:
        return ""
    m = material_str.strip().lower()
    if m in ("brick", "bricks"):
        return "brick"
    return m


def normalize_unit(unit_str: str) -> str:
    """Normalizes unit strings for comparison."""
    if not unit_str:
        return ""
    u = unit_str.strip().lower()
    if u in {"mt", "metric ton", "tonne", "ton", "rs/mt", "₹/mt"}:
        return "mt"
    if u in {"rmt", "m", "meter", "metre", "running meter", "running metre", "rs/rmt", "₹/rmt"}:
        return "rmt"
    if u in {"cum", "cu.m", "cubic meter", "cubic metre", "m3", "rs/cum", "₹/cum"}:
        return "cum"
    if u in {"1000 nos.", "1000 nos", "1000nos", "thousand nos", "1000", "nos"}:
        return "1000 nos."
    if u in {"bag", "bags", "bag/mt"}:
        return "bag"
    return u


def get_corrected_baseline_rate(
    material: str,
    raw_wpi_baseline_rate: float,
    expected_unit: str = "MT",
    region: str = None,
    project_id: int = None,
    db_path: str = DEFAULT_DB_PATH
) -> dict:
    """
    Queries trailing vendor quotes from buildcost.db vendor_quotes table.
    If >= MIN_QUOTES_THRESHOLD quotes exist, computes a 70/30 weighted blend
    between the WPI-anchored rate and the median of recent vendor quotes.

    Returns dict containing:
      - corrected_rate (float)
      - raw_wpi_baseline (float)
      - vendor_median_rate (float or None)
      - quote_count (int)
      - baseline_source ("wpi_anchor_corrected_by_quotes" vs "wpi_anchor_only")
      - wpi_weight (float)
      - vendor_weight (float)
      - correction_applied (bool)
      - explanation_note (str)
    """
    mat_key = normalize_material_key(material)
    expected_norm_unit = normalize_unit(expected_unit)

    if not os.path.exists(db_path):
        return {
            "corrected_rate": round(raw_wpi_baseline_rate, 2),
            "raw_wpi_baseline": round(raw_wpi_baseline_rate, 2),
            "vendor_median_rate": None,
            "quote_count": 0,
            "baseline_source": "wpi_anchor_only",
            "wpi_weight": 1.0,
            "vendor_weight": 0.0,
            "correction_applied": False,
            "explanation_note": f"Baseline rate ₹{raw_wpi_baseline_rate:,.2f} relies purely on PWD SOR anchor + WPI drift (0 recent vendor quotes found)."
        }

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Query vendor quotes from last 45 days
        query = f"""
            SELECT quoted_rate, quoted_unit, region, project_id, created_at
            FROM vendor_quotes
            WHERE lower(material) IN (?, ?)
              AND created_at >= datetime('now', '-{TRAILING_DAYS_WINDOW} days')
            ORDER BY created_at DESC;
        """
        rows = conn.execute(query, (mat_key, material.lower().strip())).fetchall()

        # Filtering hierarchy: 1. Project ID match -> 2. Region match -> 3. All trailing quotes
        matched_rows = rows
        if project_id is not None:
            proj_rows = [r for r in rows if r['project_id'] is not None and int(r['project_id']) == int(project_id)]
            if len(proj_rows) >= MIN_QUOTES_THRESHOLD:
                matched_rows = proj_rows
            elif region:
                reg_lower = region.strip().lower()
                reg_rows = [r for r in rows if r['region'] and reg_lower in r['region'].strip().lower()]
                if len(reg_rows) >= MIN_QUOTES_THRESHOLD:
                    matched_rows = reg_rows
        elif region:
            reg_lower = region.strip().lower()
            reg_rows = [r for r in rows if r['region'] and reg_lower in r['region'].strip().lower()]
            if len(reg_rows) >= MIN_QUOTES_THRESHOLD:
                matched_rows = reg_rows

        valid_rates = []
        for r in matched_rows:
            q_unit_norm = normalize_unit(r['quoted_unit'])
            if q_unit_norm == expected_norm_unit:
                rate_val = float(r['quoted_rate'])
                if rate_val > 0:
                    valid_rates.append(rate_val)

        quote_count = len(valid_rates)

        if quote_count >= MIN_QUOTES_THRESHOLD:
            median_vendor_rate = float(np.median(valid_rates))
            blended_rate = (WPI_BASELINE_WEIGHT * raw_wpi_baseline_rate) + (VENDOR_QUOTE_WEIGHT * median_vendor_rate)

            note = (
                f"Baseline rate ₹{blended_rate:,.2f}/{expected_unit} is corrected by real market data "
                f"({WPI_BASELINE_WEIGHT*100:.0f}% PWD anchor ₹{raw_wpi_baseline_rate:,.2f} + "
                f"{VENDOR_QUOTE_WEIGHT*100:.0f}% median of {quote_count} recent vendor quotes ₹{median_vendor_rate:,.2f})."
            )

            return {
                "corrected_rate": round(blended_rate, 2),
                "raw_wpi_baseline": round(raw_wpi_baseline_rate, 2),
                "vendor_median_rate": round(median_vendor_rate, 2),
                "quote_count": quote_count,
                "baseline_source": "wpi_anchor_corrected_by_quotes",
                "wpi_weight": WPI_BASELINE_WEIGHT,
                "vendor_weight": VENDOR_QUOTE_WEIGHT,
                "correction_applied": True,
                "explanation_note": note
            }

        else:
            note = (
                f"Baseline rate ₹{raw_wpi_baseline_rate:,.2f}/{expected_unit} relies purely on PWD SOR anchor + WPI drift extrapolation "
                f"({quote_count} recent vendor quotes found in trailing {TRAILING_DAYS_WINDOW} days; minimum {MIN_QUOTES_THRESHOLD} required to trigger quote-nudged correction)."
            )

            return {
                "corrected_rate": round(raw_wpi_baseline_rate, 2),
                "raw_wpi_baseline": round(raw_wpi_baseline_rate, 2),
                "vendor_median_rate": None,
                "quote_count": quote_count,
                "baseline_source": "wpi_anchor_only",
                "wpi_weight": 1.0,
                "vendor_weight": 0.0,
                "correction_applied": False,
                "explanation_note": note
            }

    finally:
        conn.close()
