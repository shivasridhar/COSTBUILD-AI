"""
Headless Matplotlib Forecast Chart Renderer for BuildCost AI Reports.

Renders 12-month forward price trajectories for cement, steel, and wiring
into a PNG image and encodes it as a Base64 Data URI string.
"""

import io
import base64
import matplotlib
matplotlib.use('Agg')  # Headless backend for web server environments
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def render_forecast_chart_base64(forecast_table: list) -> str:
    """
    Renders 12-month forecast trajectories from forecast_table as a static Matplotlib plot.

    Args:
        forecast_table (list of dicts): 12-month forecast table containing
            'year_month', 'cement_price_rs_per_MT', 'steel_price_rs_per_MT', 'wiring_price_rs_per_m'.

    Returns:
        str: Base64 data URI string ('data:image/png;base64,...')
    """
    months = [row['year_month'] for row in forecast_table]
    cement_prices = [row['cement_price_rs_per_MT'] for row in forecast_table]
    cement_low = [row.get('cement_confidence_low_rs', p) for row, p in zip(forecast_table, cement_prices)]
    cement_high = [row.get('cement_confidence_high_rs', p) for row, p in zip(forecast_table, cement_prices)]

    steel_prices = [row['steel_price_rs_per_MT'] for row in forecast_table]
    steel_low = [row.get('steel_confidence_low_rs', p) for row, p in zip(forecast_table, steel_prices)]
    steel_high = [row.get('steel_confidence_high_rs', p) for row, p in zip(forecast_table, steel_prices)]

    wiring_prices = [row['wiring_price_rs_per_m'] for row in forecast_table]
    wiring_low = [row.get('wiring_confidence_low_rs', p) for row, p in zip(forecast_table, wiring_prices)]
    wiring_high = [row.get('wiring_confidence_high_rs', p) for row, p in zip(forecast_table, wiring_prices)]

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8), dpi=150)
    fig.patch.set_facecolor('#ffffff')

    # Color palette matching UI tokens
    color_steel = '#2563eb'   # Royal Blue
    color_cement = '#059669'  # Emerald Green
    color_wiring = '#d97706'  # Amber / Copper

    # Left Panel: Steel & Cement (₹/MT)
    # Shaded confidence band for Steel
    ax1.fill_between(months, steel_low, steel_high, color=color_steel, alpha=0.15, label='Steel ±MAPE Band')
    ax1.plot(months, steel_prices, marker='o', color=color_steel, linewidth=2, markersize=4, label='Steel Forecast (₹/MT)')
    ax1.set_title('Steel & Cement Trajectories with Accuracy Bands', fontsize=9.5, fontweight='bold', pad=10, color='#1e293b')
    ax1.set_ylabel('Steel Price (₹/MT)', fontsize=8, color=color_steel)
    ax1.tick_params(axis='x', rotation=45, labelsize=7)
    ax1.tick_params(axis='y', labelcolor=color_steel, labelsize=8)
    ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹{x:,.0f}'))
    ax1.grid(True, linestyle='--', alpha=0.4)

    # Cement on ax1 twin
    ax1_twin = ax1.twinx()
    ax1_twin.fill_between(months, cement_low, cement_high, color=color_cement, alpha=0.15, label='Cement ±MAPE Band')
    ax1_twin.plot(months, cement_prices, marker='s', color=color_cement, linewidth=2, linestyle='--', markersize=4, label='Cement Forecast (₹/MT)')
    ax1_twin.set_ylabel('Cement Price (₹/MT)', fontsize=8, color=color_cement)
    ax1_twin.tick_params(axis='y', labelcolor=color_cement, labelsize=8)
    ax1_twin.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹{x:,.0f}'))

    # Combine legends for ax1
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=6.5, frameon=True, facecolor='#f8fafc', edgecolor='#e2e8f0')

    # Right Panel: Wiring (₹/Rmt)
    ax2.fill_between(months, wiring_low, wiring_high, color=color_wiring, alpha=0.18, label='Wiring ±MAPE Band')
    ax2.plot(months, wiring_prices, marker='^', color=color_wiring, linewidth=2, markersize=4, label='Wiring Forecast (₹/Rmt)')
    ax2.set_title('Electrical Wiring Trajectory with Accuracy Band', fontsize=9.5, fontweight='bold', pad=10, color='#1e293b')
    ax2.set_ylabel('Wiring Price (₹/Rmt)', fontsize=8, color=color_wiring)
    ax2.tick_params(axis='x', rotation=45, labelsize=7)
    ax2.tick_params(axis='y', labelcolor=color_wiring, labelsize=8)
    ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter('₹{x:,.1f}'))
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.legend(loc='upper left', fontsize=6.5, frameon=True, facecolor='#f8fafc', edgecolor='#e2e8f0')

    plt.tight_layout()

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)

    # Encode as Base64 string
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{img_b64}"
