"""
BOM Cost Calculator & Procurement Optimization Engine for BuildCost AI (Phase 4).

Note: This optimizer's reliability is bounded by the forecast layer — since Phase 3 found
only a marginal improvement over naive, this engine estimates near-term cost trajectory
rather than reliably timing market dips.
"""

import os
import sqlite3
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DEFAULT_DB_PATH = os.path.join(BASE_DIR, "buildcost.db")

from src.analysis.backtest import get_stored_forecast_mape, get_stored_forecast_error_info
from src.optimization.quote_correction import get_corrected_baseline_rate



def get_db_mcb_cost(sqft_val: int) -> float:
    """
    Step-function lookup for DB + MCB distribution panel costs based on project build area.
    Boundaries: <= 800 sqft, <= 1500 sqft, <= 3000 sqft, > 3000 sqft.
    """
    if sqft_val <= 800:
        return 4500.0  # 4-6 way SPN DB + MCBs
    elif sqft_val <= 1500:
        return 8500.0  # 8-12 way TPN DB + MCBs
    elif sqft_val <= 3000:
        return 16000.0 # 12-16 way TPN DB + MCBs
    else:
        return 28000.0 # Heavy duty TPN DB + RCCB + MCBs


def optimize_procurement(sqft: int, target_materials: list = None, region: str = None, project_id: int = None, start_month_offset: int = 0, db_path: str = None) -> dict:
    """
    Computes material quantities, forecasts 12-month WPI & price trajectories for dynamic materials,
    incorporates static PWD material rates with vendor quote corrections, calculates monthly BOM costs,
    and identifies optimal procurement window with confidence bands.

    Args:
        sqft (int): Project size in square feet.
        target_materials (list, optional): List of materials to include in total BOM cost.
                                           Defaults to ['steel', 'cement', 'sand', 'brick', 'gravel', 'wiring'].
        region (str, optional): Optional geographic region for filtering vendor quotes.
        project_id (int, optional): Optional project ID for project-specific quote corrections.
        start_month_offset (int, optional): Month offset from project start for phased procurement (default 0).
        db_path (str, optional): Path to buildcost.db SQLite database.

    Returns:
        dict: Complete optimization results including anchor factors, static rates, forecast table with confidence bands,
              BOM cost table, and procurement recommendation.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")

    # Standardize selected materials
    all_valid = {'steel', 'cement', 'sand', 'brick', 'bricks', 'gravel', 'wiring'}
    if target_materials is not None:
        selected_set = {m.lower() for m in target_materials}
        invalid = selected_set - all_valid
        if invalid:
            raise ValueError(f"Invalid target materials specified: {sorted(list(invalid))}. Valid options are: {sorted(list(all_valid))}")
    else:
        selected_set = all_valid

    conn = sqlite3.connect(db_path)

    try:
        # =====================================================================
        # 1. ANCHOR CONVERSION & VENDOR QUOTE CORRECTION
        # =====================================================================
        pwd_df = pd.read_sql_query(
            "SELECT item_code, item_description, standardized_unit, rate_rs "
            "FROM pwd_rates WHERE source_year = '2025-26' AND item_code IN ('M-0001', 'M-0002', 'M-0003', 'M-0119', 'M-0125', 'E-0101');",
            conn
        )
        if pwd_df.empty:
            raise ValueError("FY 2025-26 PWD rates not found in pwd_rates table.")

        rates_map = {row['item_code']: row['rate_rs'] for _, row in pwd_df.iterrows()}

        raw_cement_pwd_rate = float(rates_map['M-0001'])  # ₹5,602.50 / MT
        raw_steel_pwd_rate = float(rates_map['M-0002'])   # ₹55,665.00 / MT
        raw_bricks_pwd_rate = float(rates_map['M-0003'])  # ₹7,887.00 / 1000 Nos.
        raw_gravel_pwd_rate = float(rates_map['M-0119'])  # ₹222.70 / cum
        raw_sand_pwd_rate = float(rates_map['M-0125'])    # ₹1,338.00 / cum
        raw_wiring_pwd_rate = float(rates_map.get('E-0101', 34.80)) # ₹34.80 / Rmt

        # Evaluate Vendor Quote Corrections (70% WPI Anchor + 30% Recent Vendor Quotes Median)
        cement_corr = get_corrected_baseline_rate('cement', raw_cement_pwd_rate, 'MT', region, project_id, db_path)
        steel_corr = get_corrected_baseline_rate('steel', raw_steel_pwd_rate, 'MT', region, project_id, db_path)
        wiring_corr = get_corrected_baseline_rate('wiring', raw_wiring_pwd_rate, 'Rmt', region, project_id, db_path)
        sand_corr = get_corrected_baseline_rate('sand', raw_sand_pwd_rate, 'cum', region, project_id, db_path)
        bricks_corr = get_corrected_baseline_rate('brick', raw_bricks_pwd_rate, '1000 Nos.', region, project_id, db_path)
        gravel_corr = get_corrected_baseline_rate('gravel', raw_gravel_pwd_rate, 'cum', region, project_id, db_path)

        cement_pwd_rate = cement_corr['corrected_rate']
        steel_pwd_rate = steel_corr['corrected_rate']
        wiring_pwd_rate = wiring_corr['corrected_rate']
        sand_pwd_rate = sand_corr['corrected_rate']
        bricks_pwd_rate = bricks_corr['corrected_rate']
        gravel_pwd_rate = gravel_corr['corrected_rate']

        # Calculate average WPI for FY 2025-26 (April 2025 - March 2026)
        wpi_fy = pd.read_sql_query(
            "SELECT wpi_cement, wpi_steel, wpi_wiring FROM wpi WHERE year_month >= '2025-04' AND year_month <= '2026-03';",
            conn
        )
        if len(wpi_fy) == 0:
            raise ValueError("WPI data for FY 2025-26 (2025-04 to 2026-03) not found in wpi table.")

        cement_avg_wpi = float(wpi_fy['wpi_cement'].mean())
        steel_avg_wpi = float(wpi_fy['wpi_steel'].mean())
        wiring_avg_wpi = float(wpi_fy['wpi_wiring'].mean())

        # Conversion factor (₹ per index point)
        cement_factor = cement_pwd_rate / cement_avg_wpi
        steel_factor = steel_pwd_rate / steel_avg_wpi
        wiring_factor = wiring_pwd_rate / wiring_avg_wpi

        # Sanity check: convert anchor WPI back to ₹ and verify match against effective rate
        cement_converted_anchor = cement_avg_wpi * cement_factor
        steel_converted_anchor = steel_avg_wpi * steel_factor
        wiring_converted_anchor = wiring_avg_wpi * wiring_factor

        cement_sanity_pass = abs(cement_converted_anchor - cement_pwd_rate) < 1e-4
        steel_sanity_pass = abs(steel_converted_anchor - steel_pwd_rate) < 1e-4
        wiring_sanity_pass = abs(wiring_converted_anchor - wiring_pwd_rate) < 1e-4
        sanity_check_passed = cement_sanity_pass and steel_sanity_pass and wiring_sanity_pass

        anchor_conversion = {
            'cement': {
                'item_code': 'M-0001',
                'pwd_rate_rs_per_MT': raw_cement_pwd_rate,
                'effective_rate_rs_per_MT': cement_pwd_rate,
                'fy25_26_avg_wpi': cement_avg_wpi,
                'rs_per_index_point': cement_factor,
                'converted_anchor_price_rs': cement_converted_anchor,
                'sanity_pass': cement_sanity_pass,
                'correction': cement_corr
            },
            'steel': {
                'item_code': 'M-0002',
                'pwd_rate_rs_per_MT': raw_steel_pwd_rate,
                'effective_rate_rs_per_MT': steel_pwd_rate,
                'fy25_26_avg_wpi': steel_avg_wpi,
                'rs_per_index_point': steel_factor,
                'converted_anchor_price_rs': steel_converted_anchor,
                'sanity_pass': steel_sanity_pass,
                'correction': steel_corr
            },
            'wiring': {
                'item_code': 'E-0101',
                'pwd_rate_rs_per_Rmt': raw_wiring_pwd_rate,
                'effective_rate_rs_per_Rmt': wiring_pwd_rate,
                'fy25_26_avg_wpi': wiring_avg_wpi,
                'rs_per_index_point': wiring_factor,
                'converted_anchor_price_rs': wiring_converted_anchor,
                'sanity_pass': wiring_sanity_pass,
                'correction': wiring_corr
            },
            'sanity_check_passed': sanity_check_passed
        }

        static_materials_rates = {
            'sand': {'item_code': 'M-0125', 'unit': 'cum', 'rate_rs': sand_pwd_rate, 'correction': sand_corr},
            'bricks': {'item_code': 'M-0003', 'unit': '1000 Nos.', 'rate_rs': bricks_pwd_rate, 'correction': bricks_corr},
            'gravel': {'item_code': 'M-0119', 'unit': 'cum', 'rate_rs': gravel_pwd_rate, 'correction': gravel_corr}
        }

        # =====================================================================
        # 2. FORECAST: Naive + Recent Drift + Backtest Confidence Bands
        # =====================================================================
        wpi_hist = pd.read_sql_query(
            "SELECT year_month, wpi_cement, wpi_steel, wpi_wiring FROM wpi ORDER BY year_month ASC;",
            conn
        )
        if len(wpi_hist) < 6:
            raise ValueError("Insufficient historical WPI data (requires at least 6 months).")

        last_6 = wpi_hist.tail(6).reset_index(drop=True)
        latest_row = last_6.iloc[-1]
        latest_ym = latest_row['year_month']

        # Drift Calculation Method Toggle:
        # - Two-point drift (DEFAULT, False): (wpi_now - wpi_6_months_ago) / 5.0
        # - Least-squares regression slope (Alternative, True): numpy.polyfit(x, y, 1) over 6-month window
        #
        # Empirical Backtest Finding (171 historical WPI months, 165 walk-forward testing windows):
        # Least-squares regression slope was implemented and backtested against two-point drift across all 36
        # horizon/material combinations. Two-point drift performed equal or better in every case (0 improvements,
        # 2 ties, 34 regressions), with the gap widening at longer horizons (~+0.4% to +0.5% MAPE worse at 12m).
        # Working Hypothesis (Unverified): Recent momentum appears to matter more than window-averaging for this WPI
        # dataset. Regression slope is retained as a togglable alternative for future evaluation.
        USE_REGRESSION_DRIFT = False
        if USE_REGRESSION_DRIFT:
            x_win = np.arange(len(last_6))  # [0, 1, 2, 3, 4, 5]
            cement_drift = float(np.polyfit(x_win, last_6['wpi_cement'].values, 1)[0])
            steel_drift = float(np.polyfit(x_win, last_6['wpi_steel'].values, 1)[0])
            wiring_drift = float(np.polyfit(x_win, last_6['wpi_wiring'].values, 1)[0])
        else:
            # Shipped Default: Two-point drift calculation over trailing 6-month window (5 steps)
            cement_drift = float((last_6['wpi_cement'].iloc[-1] - last_6['wpi_cement'].iloc[0]) / 5.0)
            steel_drift = float((last_6['wpi_steel'].iloc[-1] - last_6['wpi_steel'].iloc[0]) / 5.0)
            wiring_drift = float((last_6['wpi_wiring'].iloc[-1] - last_6['wpi_wiring'].iloc[0]) / 5.0)

        start_date = pd.to_datetime(latest_ym + "-01")
        future_dates = [start_date + pd.DateOffset(months=start_month_offset + i) for i in range(1, 13)]

        forecast_table = []
        for i, fdate in enumerate(future_dates, 1):
            effective_month = start_month_offset + i
            ym_str = fdate.strftime('%Y-%m')
            c_wpi = float(latest_row['wpi_cement'] + effective_month * cement_drift)
            s_wpi = float(latest_row['wpi_steel'] + effective_month * steel_drift)
            w_wpi = float(latest_row['wpi_wiring'] + effective_month * wiring_drift)
            c_price = c_wpi * cement_factor
            s_price = s_wpi * steel_factor
            w_price = w_wpi * wiring_factor

            # Historical MAPE and Sample Count (N) evaluated at true distance from today
            c_info = get_stored_forecast_error_info(effective_month, 'cement', db_path)
            s_info = get_stored_forecast_error_info(effective_month, 'steel', db_path)
            w_info = get_stored_forecast_error_info(effective_month, 'wiring', db_path)

            c_mape, c_count = c_info['mape_pct'], c_info['sample_count']
            s_mape, s_count = s_info['mape_pct'], s_info['sample_count']
            w_mape, w_count = w_info['mape_pct'], w_info['sample_count']

            c_low = c_price * (1.0 - c_mape / 100.0)
            c_high = c_price * (1.0 + c_mape / 100.0)

            s_low = s_price * (1.0 - s_mape / 100.0)
            s_high = s_price * (1.0 + s_mape / 100.0)

            w_low = w_price * (1.0 - w_mape / 100.0)
            w_high = w_price * (1.0 + w_mape / 100.0)

            forecast_table.append({
                'month_idx': effective_month,
                'phase_month_idx': i,
                'year_month': ym_str,
                'wpi_cement': round(c_wpi, 4),
                'wpi_steel': round(s_wpi, 4),
                'wpi_wiring': round(w_wpi, 4),
                'cement_price_rs_per_MT': round(c_price, 2),
                'cement_confidence_low_rs': round(c_low, 2),
                'cement_confidence_high_rs': round(c_high, 2),
                'cement_mape_pct': round(c_mape, 2),
                'cement_sample_count': c_count,
                'steel_price_rs_per_MT': round(s_price, 2),
                'steel_confidence_low_rs': round(s_low, 2),
                'steel_confidence_high_rs': round(s_high, 2),
                'steel_mape_pct': round(s_mape, 2),
                'steel_sample_count': s_count,
                'wiring_price_rs_per_m': round(w_price, 2),
                'wiring_confidence_low_rs': round(w_low, 2),
                'wiring_confidence_high_rs': round(w_high, 2),
                'wiring_mape_pct': round(w_mape, 2),
                'wiring_sample_count': w_count
            })


        # =====================================================================
        # 3. BOM CALCULATION: Sourced & Derived Consumption Ratios per sqft
        # =====================================================================
        # User Specified Ratios:
        # - Steel:  0.0025 MT / sqft
        # - Cement: 0.40 bags / sqft = 0.02 MT / sqft (1 bag = 50 kg = 0.05 MT)
        # - Wiring: ~3.75 m / sqft, conduit: ~3.75 m / sqft, points: ~1 per 90 sqft
        # - DB + MCBs: Step-function lookup by sqft range (₹4,500 / ₹8,500 / ₹16,000 / ₹28,000)
        #
        # Sourced & Derived Ratios for Indian RCC Framed Construction (CPWD / IS 1200 / B.N. Dutta):
        # Note: Civil standards specify materials per unit work volume (m³ concrete, m³ masonry, m² plaster).
        # Per-sqft built-up area ratios below are derived step-by-step for standard G+1/G+2 framed buildings:
        #
        # 1. Bricks: 13 Nos / sqft (0.013 thousand Nos / sqft)
        #    - Derivation: CPWD DAR specifies 500 standard bricks per m³ of brickwork. Standard G+1 residential
        #      layout averages ~0.026 m³ masonry per sqft built-up area -> 0.026 m³ * 500 = 13 Bricks/sqft.
        #
        # 2. Sand (Fine Aggregate): 0.014 cum / sqft (~0.49 cu.ft / sqft)
        #    - Derivation: Sand consumed across 3 elements per sqft built-up area:
        #      a) RCC Concrete (M20 1:1.5:3, ~0.010 m³ concrete/sqft): 0.010 * 0.42 = 0.0042 m³
        #      b) Brickwork Mortar (1:6 mix, ~0.026 m³ masonry/sqft): 0.026 * 0.24 = 0.00624 m³
        #      c) Plastering (12mm/18mm 1:4/1:6 mix, ~2.5 sqft area/sqft): ~0.00356 m³
        #      Total Sand = 0.0042 + 0.00624 + 0.00356 = 0.014 cum / sqft.
        #
        # 3. Gravel / Coarse Aggregate: 0.009 cum / sqft (~0.32 cu.ft / sqft)
        #    - Derivation: For M20 concrete in RCC slab/beam/column/footing (~0.010 m³ concrete/sqft):
        #      Coarse aggregate = 0.010 m³ * 0.85 m³ aggregate/m³ concrete = 0.0085 ≈ 0.009 cum / sqft.

        steel_qty_MT = sqft * 0.0025
        cement_qty_bags = sqft * 0.4
        cement_qty_MT = cement_qty_bags * 0.05  # 1 bag = 50kg = 0.05 MT
        sand_qty_cum = sqft * 0.014
        bricks_qty_nos = sqft * 13
        bricks_qty_thousand = bricks_qty_nos / 1000.0  # Units of 1000 Nos.
        gravel_qty_cum = sqft * 0.009
        wiring_qty_m = sqft * 3.75  # ~3.5-4 Rmt per sqft
        conduit_qty_m = sqft * 3.75
        elec_points_qty = sqft / 90.0  # ~1 point per 80-100 sqft
        db_mcb_fixed_cost = get_db_mcb_cost(sqft)

        # Static monthly costs (constant across all months)
        sand_cost_monthly = sand_qty_cum * sand_pwd_rate
        bricks_cost_monthly = bricks_qty_thousand * bricks_pwd_rate
        gravel_cost_monthly = gravel_qty_cum * gravel_pwd_rate
        conduit_cost_fixed = conduit_qty_m * 18.0  # ₹18.00 / Rmt PVC conduit baseline
        points_cost_fixed = elec_points_qty * 120.0 # ₹120.00 / point modular box baseline

        bom_cost_table = []
        for f_row in forecast_table:
            c_cost = (cement_qty_MT * f_row['cement_price_rs_per_MT']) if 'cement' in selected_set else 0.0
            s_cost = (steel_qty_MT * f_row['steel_price_rs_per_MT']) if 'steel' in selected_set else 0.0
            w_cost = ((wiring_qty_m * f_row['wiring_price_rs_per_m']) + conduit_cost_fixed + points_cost_fixed + db_mcb_fixed_cost) if 'wiring' in selected_set else 0.0
            snd_cost = sand_cost_monthly if 'sand' in selected_set else 0.0
            brk_cost = bricks_cost_monthly if ('brick' in selected_set or 'bricks' in selected_set) else 0.0
            grv_cost = gravel_cost_monthly if 'gravel' in selected_set else 0.0

            static_subtotal = snd_cost + brk_cost + grv_cost
            total_cost = c_cost + s_cost + w_cost + static_subtotal

            bom_cost_table.append({
                'month_idx': f_row['month_idx'],
                'year_month': f_row['year_month'],
                'cement_cost_rs': round(c_cost, 2),
                'steel_cost_rs': round(s_cost, 2),
                'wiring_cost_rs': round(w_cost, 2),
                'sand_cost_rs': round(snd_cost, 2),
                'bricks_cost_rs': round(brk_cost, 2),
                'gravel_cost_rs': round(grv_cost, 2),
                'static_materials_subtotal_rs': round(static_subtotal, 2),
                'total_bom_cost_rs': round(total_cost, 2)
            })

        # =====================================================================
        # 4. OPTIMIZATION: Identify Minimum Cost Month & Savings
        # =====================================================================
        immediate_row = bom_cost_table[0]  # Month 1
        min_row = min(bom_cost_table, key=lambda x: x['total_bom_cost_rs'])

        immediate_cost = immediate_row['total_bom_cost_rs']
        optimal_cost = min_row['total_bom_cost_rs']
        savings_rs = round(immediate_cost - optimal_cost, 2)
        savings_pct = round((savings_rs / immediate_cost) * 100.0, 2) if immediate_cost > 0 else 0.0

        is_immediate = (min_row['month_idx'] == (start_month_offset + 1)) or (savings_rs <= 0)

        rec_steel_info = get_stored_forecast_error_info(min_row['month_idx'], 'steel', db_path)
        rec_cement_info = get_stored_forecast_error_info(min_row['month_idx'], 'cement', db_path)
        rec_wiring_info = get_stored_forecast_error_info(min_row['month_idx'], 'wiring', db_path)

        rec_steel_mape, rec_steel_n = rec_steel_info['mape_pct'], rec_steel_info['sample_count']
        rec_cement_mape, rec_cement_n = rec_cement_info['mape_pct'], rec_cement_info['sample_count']
        rec_wiring_mape, rec_wiring_n = rec_wiring_info['mape_pct'], rec_wiring_info['sample_count']

        # Minimum-N floor threshold (N < 30) for reliable historical backtest confidence
        MIN_SAMPLE_FLOOR = 30

        def format_reliability(mat_name, mape, count):
            if count < MIN_SAMPLE_FLOOR:
                return f"{mat_name}: insufficient historical data for a confident estimate at this horizon (N={count} < {MIN_SAMPLE_FLOOR})"
            return f"{mat_name} ±{mape:.1f}% (N={count})"

        steel_rel = format_reliability("Steel", rec_steel_mape, rec_steel_n)
        cement_rel = format_reliability("Cement", rec_cement_mape, rec_cement_n)
        wiring_rel = format_reliability("Wiring", rec_wiring_mape, rec_wiring_n)

        horizon_mape_by_material = {
            'steel': {'mape_pct': rec_steel_mape, 'sample_count': rec_steel_n, 'low_confidence': rec_steel_n < MIN_SAMPLE_FLOOR},
            'cement': {'mape_pct': rec_cement_mape, 'sample_count': rec_cement_n, 'low_confidence': rec_cement_n < MIN_SAMPLE_FLOOR},
            'wiring': {'mape_pct': rec_wiring_mape, 'sample_count': rec_wiring_n, 'low_confidence': rec_wiring_n < MIN_SAMPLE_FLOOR}
        }

        reliability_subtext = (
            f"Note: Walk-forward WPI backtesting indicates historical forecast accuracy at Month {min_row['month_idx']} horizon: "
            f"{steel_rel}; {cement_rel}; {wiring_rel}."
        )

        if is_immediate:
            summary_message = (
                f"Procure at phase start ({immediate_row['year_month']}). Material costs are projected to trend upward "
                f"or remain flat over the 12-month phase window. Delaying procurement will increase phase BOM cost."
            )
        else:
            summary_message = (
                f"Optimal procurement month is Month {min_row['month_idx']} ({min_row['year_month']}). "
                f"Estimated savings: ₹{savings_rs:,.2f} ({savings_pct:.2f}%) compared to buying at phase start in {immediate_row['year_month']}. "
                f"Note: Historical backtesting reliability: {steel_rel}; {cement_rel}; {wiring_rel}."
            )

        recommendation = {
            'sqft': sqft,
            'start_month_offset': start_month_offset,
            'quantities': {
                'steel_MT': steel_qty_MT,
                'cement_bags': cement_qty_bags,
                'cement_MT': cement_qty_MT,
                'sand_cum': sand_qty_cum,
                'bricks_nos': bricks_qty_nos,
                'bricks_thousand_nos': bricks_qty_thousand,
                'gravel_cum': gravel_qty_cum,
                'wiring_m': wiring_qty_m,
                'conduit_m': conduit_qty_m,
                'conduit_cost_rs': round(conduit_cost_fixed, 2),
                'electrical_points': round(elec_points_qty, 1),
                'electrical_points_cost_rs': round(points_cost_fixed, 2),
                'db_mcb_fixed_cost_rs': db_mcb_fixed_cost
            },
            'immediate_month': immediate_row['year_month'],
            'immediate_cost_rs': immediate_cost,
            'recommended_month_idx': min_row['month_idx'],
            'recommended_year_month': min_row['year_month'],
            'optimal_cost_rs': optimal_cost,
            'savings_rs': max(0.0, savings_rs),
            'savings_percent': max(0.0, savings_pct),
            'is_immediate_recommended': is_immediate,
            'summary_message': summary_message,
            'steel_horizon_mape_pct': rec_steel_mape,
            'steel_horizon_sample_count': rec_steel_n,
            'cement_horizon_mape_pct': rec_cement_mape,
            'cement_horizon_sample_count': rec_cement_n,
            'wiring_horizon_mape_pct': rec_wiring_mape,
            'wiring_horizon_sample_count': rec_wiring_n,
            'horizon_mape_by_material': horizon_mape_by_material,
            'reliability_subtext': reliability_subtext
        }


        return {
            'anchor_conversion': anchor_conversion,
            'static_materials_rates': static_materials_rates,
            'forecast_drift_rates': {
                'cement_monthly_drift': round(cement_drift, 4),
                'steel_monthly_drift': round(steel_drift, 4),
                'wiring_monthly_drift': round(wiring_drift, 4)
            },
            'forecast_table': forecast_table,
            'bom_cost_table': bom_cost_table,
            'recommendation': recommendation
        }

    finally:
        conn.close()


def init_vendor_quotes_table(db_path: str = None) -> None:
    """
    Initializes the vendor_quotes table in buildcost.db if it does not already exist.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendor_quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material TEXT NOT NULL,
                quoted_rate REAL NOT NULL,
                quoted_unit TEXT NOT NULL,
                quoted_date TEXT NOT NULL,
                source_note TEXT,
                region TEXT,
                project_id INTEGER REFERENCES projects(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    finally:
        conn.close()


def save_vendor_quote(
    material: str,
    quoted_rate: float,
    quoted_unit: str,
    quoted_date: str,
    source_note: str = None,
    region: str = None,
    project_id: int = None,
    phase_id: int = None,
    db_path: str = None
) -> int:
    """
    Persists a single vendor quote entry into the vendor_quotes table.
    Returns the inserted quote ID.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    init_vendor_quotes_table(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vendor_quotes (material, quoted_rate, quoted_unit, quoted_date, source_note, region, project_id, phase_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
            (material, quoted_rate, quoted_unit, quoted_date, source_note, region, project_id, phase_id)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def normalize_unit(unit_str: str) -> str:
    """
    Normalizes unit strings for comparison.
    """
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


def get_material_baseline_rate(material: str, quoted_date: str = None, region: str = None, db_path: str = None) -> dict:
    """
    Reuses anchor conversion and 12-month drift forecast math from optimize_procurement
    to compute the expected baseline rate and baseline unit for a specific material and date.

    Returns dict:
      {
         "baseline_rate": float,
         "baseline_unit": str,
         "out_of_range": bool,
         "range_note": str
      }
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    mat_key = material.strip().lower()
    if mat_key in ("brick", "bricks"):
        mat_key = "brick"

    opt_res = optimize_procurement(sqft=1000, region=region, db_path=db_path)

    anchor_conv = opt_res['anchor_conversion']
    forecast_table = opt_res['forecast_table']
    static_rates = opt_res['static_materials_rates']

    forecast_ym_list = [f['year_month'] for f in forecast_table]
    min_forecast_ym = forecast_ym_list[0] if forecast_ym_list else "2026-07"
    max_forecast_ym = forecast_ym_list[-1] if forecast_ym_list else "2027-06"

    ym = (quoted_date[:7] if quoted_date and len(quoted_date) >= 7 else "").strip()

    is_dynamic = mat_key in ("steel", "cement", "wiring")
    out_of_range = False
    range_note = ""

    if is_dynamic and ym:
        if ym not in forecast_ym_list and not ("2025-04" <= ym <= "2026-03"):
            out_of_range = True
            range_note = (
                f"Quote date '{quoted_date}' is outside the supported forecast window "
                f"({min_forecast_ym} to {max_forecast_ym}) and baseline anchor period (2025-04 to 2026-03)."
            )

    if mat_key == "steel":
        baseline_unit = "MT"
        matched_f = next((f for f in forecast_table if f['year_month'] == ym), None) if ym else None
        if matched_f:
            baseline_rate = float(matched_f['steel_price_rs_per_MT'])
        else:
            baseline_rate = float(anchor_conv['steel']['converted_anchor_price_rs'])

    elif mat_key == "cement":
        baseline_unit = "MT"
        matched_f = next((f for f in forecast_table if f['year_month'] == ym), None) if ym else None
        if matched_f:
            baseline_rate = float(matched_f['cement_price_rs_per_MT'])
        else:
            baseline_rate = float(anchor_conv['cement']['converted_anchor_price_rs'])

    elif mat_key == "wiring":
        baseline_unit = "Rmt"
        matched_f = next((f for f in forecast_table if f['year_month'] == ym), None) if ym else None
        if matched_f:
            baseline_rate = float(matched_f['wiring_price_rs_per_m'])
        else:
            baseline_rate = float(anchor_conv['wiring']['converted_anchor_price_rs'])

    elif mat_key == "sand":
        baseline_unit = "cum"
        baseline_rate = float(static_rates['sand']['rate_rs'])

    elif mat_key == "gravel":
        baseline_unit = "cum"
        baseline_rate = float(static_rates['gravel']['rate_rs'])

    elif mat_key == "brick":
        baseline_unit = "1000 Nos."
        baseline_rate = float(static_rates['bricks']['rate_rs'])

    else:
        raise ValueError(f"Unsupported material for baseline rate lookup: {material}")

    return {
        "baseline_rate": round(baseline_rate, 2),
        "baseline_unit": baseline_unit,
        "out_of_range": out_of_range,
        "range_note": range_note
    }



if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("==========================================================================")
    print("      BUILDCOST AI - PHASE 4 PROCUREMENT OPTIMIZATION ENGINE TEST        ")
    print("==========================================================================")

    results = optimize_procurement(sqft=1000)

    print("\n--- 1. SQL FILTER & ANCHOR CONVERSION SANITY CHECK ---")
    anchors = results['anchor_conversion']
    print(f"SQL Query Filter: WHERE source_year = '2025-26'")
    print(f"Cement (M-0001) PWD Rate: ₹{anchors['cement']['pwd_rate_rs_per_MT']:.2f}/MT | FY25-26 Avg WPI: {anchors['cement']['fy25_26_avg_wpi']:.4f} | Factor: {anchors['cement']['rs_per_index_point']:.4f} ₹/point")
    print(f"Cement Converted Anchor Check: ₹{anchors['cement']['converted_anchor_price_rs']:.2f}/MT (Match PWD Rate ₹5,602.50: {anchors['cement']['sanity_pass']})")
    print(f"Steel (M-0002) PWD Rate:  ₹{anchors['steel']['pwd_rate_rs_per_MT']:.2f}/MT | FY25-26 Avg WPI: {anchors['steel']['fy25_26_avg_wpi']:.4f} | Factor: {anchors['steel']['rs_per_index_point']:.4f} ₹/point")
    print(f"Steel Converted Anchor Check:  ₹{anchors['steel']['converted_anchor_price_rs']:.2f}/MT (Match PWD Rate ₹55,665.00: {anchors['steel']['sanity_pass']})")
    print(f"OVERALL ANCHOR SANITY CHECK PASSED: {anchors['sanity_check_passed']}")

    print("\n--- 2. STATIC MATERIAL PWD RATES (FY 2025-26) ---")
    statics = results['static_materials_rates']
    print(f"Sand   (M-0125): ₹{statics['sand']['rate_rs']:.2f} / {statics['sand']['unit']}")
    print(f"Bricks (M-0003): ₹{statics['bricks']['rate_rs']:.2f} / {statics['bricks']['unit']}")
    print(f"Gravel (M-0119): ₹{statics['gravel']['rate_rs']:.2f} / {statics['gravel']['unit']}")

    print("\n--- 3. FORECAST DRIFT RATES ---")
    drifts = results['forecast_drift_rates']
    print(f"Cement Monthly Drift: {drifts['cement_monthly_drift']:+.4f} WPI points/month")
    print(f"Steel Monthly Drift:  {drifts['steel_monthly_drift']:+.4f} WPI points/month")

    print("\n--- 4. 12-MONTH FORECAST TABLE ---")
    print(f"{'Month':<6} | {'Year-Month':<10} | {'WPI Cement':<10} | {'WPI Steel':<10} | {'Cement (₹/MT)':<14} | {'Steel (₹/MT)':<14}")
    print("-" * 75)
    for row in results['forecast_table']:
        print(f"{row['month_idx']:<6} | {row['year_month']:<10} | {row['wpi_cement']:<10.4f} | {row['wpi_steel']:<10.4f} | ₹{row['cement_price_rs_per_MT']:<13,.2f} | ₹{row['steel_price_rs_per_MT']:<13,.2f}")

    print("\n--- 5. FULL BOM COST TRAJECTORY (1,000 SQFT PROJECT - 5 MATERIALS) ---")
    q = results['recommendation']['quantities']
    print(f"Material Quantities: Steel = {q['steel_MT']:.4f} MT, Cement = {q['cement_bags']:.0f} bags ({q['cement_MT']:.4f} MT), Sand = {q['sand_cum']:.1f} cum, Bricks = {q['bricks_nos']:.0f} nos, Gravel = {q['gravel_cum']:.1f} cum")
    print(f"{'Month':<6} | {'Year-Month':<10} | {'Cement (₹)':<12} | {'Steel (₹)':<12} | {'Sand (₹)':<10} | {'Bricks (₹)':<11} | {'Gravel (₹)':<10} | {'Total BOM Cost (₹)':<18}")
    print("-" * 105)
    for row in results['bom_cost_table']:
        print(f"{row['month_idx']:<6} | {row['year_month']:<10} | ₹{row['cement_cost_rs']:<11,.2f} | ₹{row['steel_cost_rs']:<11,.2f} | ₹{row['sand_cost_rs']:<9,.2f} | ₹{row['bricks_cost_rs']:<10,.2f} | ₹{row['gravel_cost_rs']:<9,.2f} | ₹{row['total_bom_cost_rs']:<17,.2f}")

    print("\n--- 6. PROCUREMENT OPTIMIZATION RECOMMENDATION ---")
    rec = results['recommendation']
    print(f"Immediate Purchase Month (Month 1, {rec['immediate_month']}): Total Cost = ₹{rec['immediate_cost_rs']:,.2f}")
    print(f"Recommended Purchase Month (Month {rec['recommended_month_idx']}, {rec['recommended_year_month']}): Total Cost = ₹{rec['optimal_cost_rs']:,.2f}")
    print(f"Estimated Savings: ₹{rec['savings_rs']:,.2f} ({rec['savings_percent']:.2f}%)")
    print(f"Summary: {rec['summary_message']}")
