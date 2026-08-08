# BuildCost AI - Construction Procurement Optimization Platform

BuildCost AI combines Public Works Department (PWD) reference rates with 12-month Wholesale Price Index (WPI) trend extrapolations to optimize construction Bill of Materials (BOM) purchasing decisions.

---

## System Architecture

- **Backend**: FastAPI Python REST Service (`src/api/main.py`) running on `http://localhost:8000`
- **Frontend**: Vite + React Dashboard (`frontend/`) running on `http://localhost:5173`
- **Database**: SQLite `buildcost.db` storing historical indices & reference anchors

---

## Getting Started & Run Instructions

### 1. Start the FastAPI Backend Service

Ensure Python dependencies are installed (`fastapi`, `uvicorn`, `pydantic`, `pandas`, `scikit-learn`, `xgboost`).

Run from project root directory:

```bash
# Windows / Linux / macOS
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be operational at:
- Base API: `http://localhost:8000`
- Interactive API Docs (Swagger): `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

### 2. Start the React Frontend Dashboard

Open a separate terminal window and navigate to the `frontend/` directory:

```bash
cd frontend

# Install Node modules (if not already installed)
npm install

# Start Vite development server
npm run dev
```

The frontend application will be running at:
- Web App URL: `http://localhost:5173`

---

## Environment Variables

### Frontend (`frontend/.env` or shell env)

- `VITE_API_BASE_URL`: Base URL of the FastAPI backend service (Default: `http://localhost:8000`).

Example `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## API Endpoints Overview

1. **`GET /health`**
   - Returns system connectivity status for API and SQLite database (`buildcost.db`).

2. **`POST /predict-optimal-build-window`**
   - Request Payload:
     ```json
     {
       "sqft": 1000,
       "target_materials": ["steel", "cement", "sand", "brick", "gravel"]
     }
     ```
   - Response Payload:
     - `anchor_conversion`: Baseline rates & `sanity_check_passed` indicator
     - `forecast`: 12-month forward price trajectories for cement and steel (₹/MT)
     - `bom_cost_by_month`: Monthly breakdown per material and total BOM cost in ₹
     - `recommendation`: Recommended procurement month, optimal cost, and projected savings
     - `metadata`: Forecast methodology and model limitation disclosure note
