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

## Push to GitHub

```bash
git init
git add .
git commit -m "Prepare FairLens for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Deploy Both Frontend + Backend on Render

This repository is already prepared for a **two-service Render deployment**.

### Backend service
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Required env vars:
  - `GEMINI_API_KEY` = your Google Gemini API key (optional, but needed for AI narrative in reports)
  - `FAIRLENS_CORS_ORIGINS` = your frontend domain after deploy, for example `https://fairlens-frontend.onrender.com`

### Frontend service
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
- Required env vars:
  - `FAIRLENS_BACKEND_URL` = your deployed backend URL, for example `https://fairlens-backend.onrender.com`

### Render deployment steps
1. Push this repo to GitHub.
2. Log in to Render and choose **New + → Blueprint**.
3. Select this GitHub repository. Render will detect `render.yaml`.
4. Create both services.
5. Open the backend service and set: 
   - `GEMINI_API_KEY`
   - `FAIRLENS_CORS_ORIGINS` to your frontend URL
6. Open the frontend service and set:
   - `FAIRLENS_BACKEND_URL` to your backend URL
7. Redeploy both services after updating env vars.
8. Test:
   - Backend health: `https://YOUR-BACKEND/api/v1/health`
   - Frontend app: `https://YOUR-FRONTEND`

## Manual Deployment Without Blueprint

If you do not want to use `render.yaml`, create two separate Render web services from the same repo using the same commands above.

## Notes

- Uploaded files and generated PDF reports are stored on ephemeral disk in hosted environments, which is fine for demo usage but not for long-term storage.
- For production persistence, connect object storage (for example AWS S3, Cloudinary, or Supabase Storage) for uploads and reports.
- `FAIRLENS_CORS_ORIGINS` supports a comma-separated list of allowed frontend domains.

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
