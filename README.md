# Fuzzy Lookup Platform

FastAPI + React application for fuzzy matching across uploaded datasets with subscription controls and API configurability.

## Stack
- Backend: FastAPI, SQLAlchemy (Postgres), Firestore for subscriptions, pandas/string_grouper for matching.
- Frontend: React (Vite + TypeScript).
- Auth: JWT.

## Running locally
1) Install Docker + Docker Compose.  
2) Create `backend/.env` with at least:
```
DATABASE_URL=postgresql+psycopg://fuzzy_user:fuzzy_password@postgres:5432/fuzzy_lookup
JWT_SECRET_KEY=change-me
JWT_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
GOOGLE_APPLICATION_CREDENTIALS=/app/creds/serviceAccountKey.json
SUBSCRIPTION_COLLECTION=payments
SUBSCRIPTION_DOC_IDS=Fuzzycloud
```
3) Add your Firestore service account to `backend/serviceAccountKey.json`.  
4) `docker-compose up --build` from the repo root. Backend will listen on `:8000`, frontend on `:3000`.

Data storage: uploads/downloads live under `backend/data/` (mounted in the backend container).

## Key flows
- **Auth**: `/auth/register`, `/auth/login` return JWT; frontend stores token and attaches to API calls.
- **Subscriptions**: `/license/types` exposes plan names + PayPal links; `/license/info` returns the user’s active plan/limits.
- **File upload + columns**: `POST /api/column_names` with a file (and optional `sheet_name`) saves the file for the user and returns `file_id`, `filename`, `sheet_names`, `sheet_name`, and `column_names`.
- **Sheet-aware columns**: `GET /files/{file_id}/columns?sheet_name=...` returns columns for a specific sheet (Excel). CSVs ignore `sheet_name`.
- **Fuzzy matching (multi-file)**: `POST /api/lookup_multi_file` with stored `file_name_1`, `file_name_2`, their column names, `threshold`, optional `delimiter`/`output_type`, and optional `file_1_sheet_name`/`file_2_sheet_name`. Returns a CSV/XLSX download.
- **Duplicates (single file)**: `POST /api/find_duplicates` with file upload, `column_name`, `threshold`, `output_type`, optional `sheet_name`; returns download of ranked duplicates.
- **Query DataFrame**: `POST /api/query_dataframe` with file upload, `query_column`, `search_term`, optional `sheet_name`.
- **Job history/downloads**: `GET /api/jobs` and `GET /api/download/{job_id}`.
- **API configurations**: `POST /api/configurations/` to save a dataset+column for programmatic querying, then `POST /api/configurations/{id}/query`. Docs helper at `/api/configurations/{id}/docs` returns example payloads (JWT required).

## Multi-sheet usage
- Column listing endpoints now return available `sheet_names` for Excel files.
- When selecting a different sheet, call `/files/{file_id}/columns?sheet_name=...` to refresh columns without re-uploading.
- Pass `sheet_name` (or `file_1_sheet_name`/`file_2_sheet_name`) to fuzzy lookup and duplicate endpoints to process the intended sheet; CSV uploads ignore this value.

## Notes for handover
- Subscription plan links are served from `/license/types`; values come from `backend/app/core/subscriptions.py`.
- License checks enforce file-size and conversion limits on upload/processing endpoints.
- Backend startup creates upload/download directories automatically; ensure container user has write access.
- Update env vars and PayPal plan IDs per environment before deploy.
