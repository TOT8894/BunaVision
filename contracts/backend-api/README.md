# Backend API Contract (Frontend ⇄ Backend)

**Owner:** Backend members (`@worku404`, `@danieltuemay350-web`).  
**Consumer:** Frontend members (`@TOT8894`, `@mikimek23`).

This directory contains the **single source of truth** for the public HTTP API between the frontend browser application and the backend service. The frontend generates its TypeScript types from the `openapi.json` committed here.

---

## 1. What Goes Here

* **`openapi.json`**: The complete OpenAPI specification for the public API (`POST /api/v1/assessments`, `GET /health`, etc.).
* **`examples/`**: Realistic JSON payloads for assessment reports and error responses so the frontend can develop components before the backend is deployed.

---

## 2. How to Generate `openapi.json`

Whenever backend schemas in `backend/app/schemas/` or endpoints in `backend/app/api/` are modified, update `openapi.json` using one of two methods:

### Option 1 (Via Browser)
1. Start the backend service:
   ```bash
   uvicorn app.api.main:app --port 8000
   ```
2. Open [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) in your browser.
3. Save the response into `contracts/backend-api/openapi.json`.

### Option 2 (One-Line CLI Command)
From the repository root:

* **Windows PowerShell:**
  ```powershell
  python -c "import json; from backend.app.api.main import app; print(json.dumps(app.openapi(), indent=2))" | Out-File -Encoding utf8 contracts/backend-api/openapi.json
  ```

* **Linux / macOS (Bash):**
  ```bash
  python3 -c "import json; from backend.app.api.main import app; print(json.dumps(app.openapi(), indent=2))" > contracts/backend-api/openapi.json
  ```

---

## 3. Rules & Governance

- **Frontend Type Generation:** The frontend team generates TypeScript interfaces from this file using tools such as `npx openapi-typescript contracts/backend-api/openapi.json -o src/api/types.d.ts`.
- **Review Requirement:** Changes to this contract require review from both backend and frontend owners per [`.github/CODEOWNERS`](../../.github/CODEOWNERS).
