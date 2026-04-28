# 🔍 FairLens — AI Bias Detection Platform

Premium Streamlit frontend + FastAPI backend for detecting workplace bias.

## Project Structure

- `main.py` — FastAPI backend entrypoint
- `streamlit_app.py` — Streamlit frontend entrypoint
- `app/` — analysis modules, API router, PDF utilities
- `assets/fairlens_logo.png` — brand logo used by the frontend
- `sample_data/` — demo CSV files for local testing
- `render.yaml` — one-repo/two-service deployment blueprint for Render

## Local Development

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create a local env file (optional but recommended)
```bash
cp .env.example .env
```

Set these values as needed:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FAIRLENS_BACKEND_URL=http://localhost:8000
FAIRLENS_CORS_ORIGINS=*
```

### 3. Start the FastAPI backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the Streamlit frontend
```bash
streamlit run streamlit_app.py
```

Open: `http://localhost:8501`

Backend docs: `http://localhost:8000/docs`



## Uploading Data

| Card | File | Required |
|------|------|----------|
| Hiring Data | hiring.csv | ✅ Yes |
| ML Predictions | ml_predictions.csv | Optional |
| Manager Data | manager.csv | Optional |
| Leave Data | leave.csv | Optional |
| Task Data | task.csv | Optional |

Sample data is available in `sample_data/`.

## Fairness Score Scale
- **75–100**: LOW BIAS ✅
- **50–74**: MODERATE BIAS ⚠️
- **0–49**: HIGH BIAS ❌
