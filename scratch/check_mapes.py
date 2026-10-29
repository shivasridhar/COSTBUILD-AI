import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.analysis.backtest import run_walk_forward_backtest

res = run_walk_forward_backtest()

print("\n=== FULL HORIZON MAPE & SAMPLE COUNT MATRIX ===")
print(f"{'Horizon':<10} | {'Steel MAPE (N)':<22} | {'Cement MAPE (N)':<22} | {'Wiring MAPE (N)':<22}")
print("-" * 80)
for h in range(1, 13):
    s = res.get((h, 'steel'), {})
    c = res.get((h, 'cement'), {})
    w = res.get((h, 'wiring'), {})
    s_str = f"{s.get('mape_pct', 0.0):.2f}% (N={s.get('sample_count', 0)})"
    c_str = f"{c.get('mape_pct', 0.0):.2f}% (N={c.get('sample_count', 0)})"
    w_str = f"{w.get('mape_pct', 0.0):.2f}% (N={w.get('sample_count', 0)})"
    print(f"{h:2d} month(s) | {s_str:<22} | {c_str:<22} | {w_str:<22}")
