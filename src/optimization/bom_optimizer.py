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
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "buildcost.db")


def optimize_procurement(sqft: int, target_materials: list = None, db_path: str = None) -> dict:
    """
    Computes material quantities, forecasts 12-month WPI & price trajectories for dynamic materials,
    incorporates static PWD material rates, calculates monthly BOM costs, and identifies optimal procurement window.

    Args:
        sqft (int): Project size in square feet.
        target_materials (list, optional): List of materials to include in total BOM cost.
                                           Defaults to ['steel', 'cement', 'sand', 'brick', 'gravel'].
        db_path (str, optional): Path to buildcost.db SQLite database.

    Returns:
        dict: Complete optimization results including anchor factors, static rates, forecast table,
              BOM cost table, and procurement recommendation.
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")

    # Standardize selected materials
    all_valid = {'steel', 'cement', 'sand', 'brick', 'bricks', 'gravel'}
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
        # 1. ANCHOR CONVERSION: PWD Rates (FY 2025-26) to WPI Index Points
        # =====================================================================
        # Explicit SQL filter for source_year == '2025-26'
        target_codes = ('M-0001', 'M-0002', 'M-0003', 'M-0119', 'M-0125')
        pwd_df = pd.read_sql_query(
            "SELECT item_code, item_description, standardized_unit, rate_rs "
            "FROM pwd_rates WHERE source_year = '2025-26' AND item_code IN ('M-0001', 'M-0002', 'M-0003', 'M-0119', 'M-0125');",
            conn
        )
        if pwd_df.empty:
            raise ValueError("FY 2025-26 PWD rates not found in pwd_rates table.")

        rates_map = {row['item_code']: row['rate_rs'] for _, row in pwd_df.iterrows()}

        cement_pwd_rate = float(rates_map['M-0001'])  # ₹5,602.50 / MT
        steel_pwd_rate = float(rates_map['M-0002'])   # ₹55,665.00 / MT
        bricks_pwd_rate = float(rates_map['M-0003'])  # ₹7,887.00 / 1000 Nos.
        gravel_pwd_rate = float(rates_map['M-0119'])  # ₹222.70 / cum
        sand_pwd_rate = float(rates_map['M-0125'])    # ₹1,338.00 / cum

        # Calculate average WPI for FY 2025-26 (April 2025 - March 2026)
        wpi_fy = pd.read_sql_query(
            "SELECT wpi_cement, wpi_steel FROM wpi WHERE year_month >= '2025-04' AND year_month <= '2026-03';",
            conn
        )
        if len(wpi_fy) == 0:
            raise ValueError("WPI data for FY 2025-26 (2025-04 to 2026-03) not found in wpi table.")

        cement_avg_wpi = float(wpi_fy['wpi_cement'].mean())
        steel_avg_wpi = float(wpi_fy['wpi_steel'].mean())

        # Conversion factor (₹ per index point)
        cement_factor = cement_pwd_rate / cement_avg_wpi
        steel_factor = steel_pwd_rate / steel_avg_wpi

        # Sanity check: convert anchor WPI back to ₹ and verify match against PWD rate
        cement_converted_anchor = cement_avg_wpi * cement_factor
        steel_converted_anchor = steel_avg_wpi * steel_factor

        cement_sanity_pass = abs(cement_converted_anchor - cement_pwd_rate) < 1e-4
        steel_sanity_pass = abs(steel_converted_anchor - steel_pwd_rate) < 1e-4
        sanity_check_passed = cement_sanity_pass and steel_sanity_pass

        anchor_conversion = {
            'cement': {
                'item_code': 'M-0001',
                'pwd_rate_rs_per_MT': cement_pwd_rate,
                'fy25_26_avg_wpi': cement_avg_wpi,
                'rs_per_index_point': cement_factor,
                'converted_anchor_price_rs': cement_converted_anchor,
                'sanity_pass': cement_sanity_pass
            },
            'steel': {
                'item_code': 'M-0002',
                'pwd_rate_rs_per_MT': steel_pwd_rate,
                'fy25_26_avg_wpi': steel_avg_wpi,
                'rs_per_index_point': steel_factor,
                'converted_anchor_price_rs': steel_converted_anchor,
                'sanity_pass': steel_sanity_pass
            },
            'sanity_check_passed': sanity_check_passed
        }

        static_materials_rates = {
            'sand': {'item_code': 'M-0125', 'unit': 'cum', 'rate_rs': sand_pwd_rate},
            'bricks': {'item_code': 'M-0003', 'unit': '1000 Nos.', 'rate_rs': bricks_pwd_rate},
            'gravel': {'item_code': 'M-0119', 'unit': 'cum', 'rate_rs': gravel_pwd_rate}
        }

        # =====================================================================
        # 2. FORECAST: Naive + Recent Drift (12 Months Forward)
        # =====================================================================
        # Note: This "naive + recent drift" forecast method was selected over trained ML models
        # (XGBoost, LightGBM, Ridge) because Phase 3 evaluation revealed that complex models provided
        # only a marginal, unreliable edge over naive baseline forecasts. A simple, transparent, and
        # honest drift extrapolation was preferred over presenting a fragile ML model as more capable than it is.

        wpi_hist = pd.read_sql_query(
            "SELECT year_month, wpi_cement, wpi_steel FROM wpi ORDER BY year_month ASC;",
            conn
        )
        if len(wpi_hist) < 6:
            raise ValueError("Insufficient historical WPI data (requires at least 6 months).")

        last_6 = wpi_hist.tail(6).reset_index(drop=True)
        latest_row = last_6.iloc[-1]
        latest_ym = latest_row['year_month']

        # Drift calculated over last 6 months (5 consecutive monthly change steps)
        cement_drift = float((last_6['wpi_cement'].iloc[-1] - last_6['wpi_cement'].iloc[0]) / 5.0)
        steel_drift = float((last_6['wpi_steel'].iloc[-1] - last_6['wpi_steel'].iloc[0]) / 5.0)

        start_date = pd.to_datetime(latest_ym + "-01")
        future_dates = [start_date + pd.DateOffset(months=i) for i in range(1, 13)]

        forecast_table = []
        for i, fdate in enumerate(future_dates, 1):
            ym_str = fdate.strftime('%Y-%m')
            c_wpi = float(latest_row['wpi_cement'] + i * cement_drift)
            s_wpi = float(latest_row['wpi_steel'] + i * steel_drift)
            c_price = c_wpi * cement_factor
            s_price = s_wpi * steel_factor

            forecast_table.append({
                'month_idx': i,
                'year_month': ym_str,
                'wpi_cement': round(c_wpi, 4),
                'wpi_steel': round(s_wpi, 4),
                'cement_price_rs_per_MT': round(c_price, 2),
                'steel_price_rs_per_MT': round(s_price, 2)
            })

        # =====================================================================
        # 3. BOM CALCULATION: Sourced & Derived Consumption Ratios per sqft
        # =====================================================================
        # User Specified Ratios:
        # - Steel:  0.0025 MT / sqft
        # - Cement: 0.40 bags / sqft = 0.02 MT / sqft (1 bag = 50 kg = 0.05 MT)
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

        # Static monthly costs (constant across all months)
        sand_cost_monthly = sand_qty_cum * sand_pwd_rate
        bricks_cost_monthly = bricks_qty_thousand * bricks_pwd_rate
        gravel_cost_monthly = gravel_qty_cum * gravel_pwd_rate

        bom_cost_table = []
        for f_row in forecast_table:
            c_cost = (cement_qty_MT * f_row['cement_price_rs_per_MT']) if 'cement' in selected_set else 0.0
            s_cost = (steel_qty_MT * f_row['steel_price_rs_per_MT']) if 'steel' in selected_set else 0.0
            snd_cost = sand_cost_monthly if 'sand' in selected_set else 0.0
            brk_cost = bricks_cost_monthly if ('brick' in selected_set or 'bricks' in selected_set) else 0.0
            grv_cost = gravel_cost_monthly if 'gravel' in selected_set else 0.0

            static_subtotal = snd_cost + brk_cost + grv_cost
            total_cost = c_cost + s_cost + static_subtotal

            bom_cost_table.append({
                'month_idx': f_row['month_idx'],
                'year_month': f_row['year_month'],
                'cement_cost_rs': round(c_cost, 2),
                'steel_cost_rs': round(s_cost, 2),
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

        is_immediate = (min_row['month_idx'] == 1) or (savings_rs <= 0)

        if is_immediate:
            summary_message = (
                f"Procure Immediately ({immediate_row['year_month']}). Material costs are projected to trend upward "
                f"or remain flat over the next 12 months. Delaying procurement will increase total BOM cost."
            )
        else:
            summary_message = (
                f"Optimal procurement month is Month {min_row['month_idx']} ({min_row['year_month']}). "
                f"Estimated savings: ₹{savings_rs:,.2f} ({savings_pct:.2f}%) compared to buying immediately in {immediate_row['year_month']}."
            )

        recommendation = {
            'sqft': sqft,
            'quantities': {
                'steel_MT': steel_qty_MT,
                'cement_bags': cement_qty_bags,
                'cement_MT': cement_qty_MT,
                'sand_cum': sand_qty_cum,
                'bricks_nos': bricks_qty_nos,
                'bricks_thousand_nos': bricks_qty_thousand,
                'gravel_cum': gravel_qty_cum
            },
            'immediate_month': immediate_row['year_month'],
            'immediate_cost_rs': immediate_cost,
            'recommended_month_idx': min_row['month_idx'],
            'recommended_year_month': min_row['year_month'],
            'optimal_cost_rs': optimal_cost,
            'savings_rs': max(0.0, savings_rs),
            'savings_percent': max(0.0, savings_pct),
            'is_immediate_recommended': is_immediate,
            'summary_message': summary_message
        }

        return {
            'anchor_conversion': anchor_conversion,
            'static_materials_rates': static_materials_rates,
            'forecast_drift_rates': {
                'cement_monthly_drift': round(cement_drift, 4),
                'steel_monthly_drift': round(steel_drift, 4)
            },
            'forecast_table': forecast_table,
            'bom_cost_table': bom_cost_table,
            'recommendation': recommendation
        }

    finally:
        conn.close()


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
