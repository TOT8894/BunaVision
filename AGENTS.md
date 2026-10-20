# AGENTS.md — BunaVision (shared rules for all subsystems)

BunaVision is a web app for **preliminary AI screening of green coffee bean photos**. A user uploads a sample image, a computer-vision model finds the visible defects it supports, and the system returns a report (defects, counts, confidence, annotated image) that is stored and can be revisited. Primary users are Ethiopian coffee producers, washing stations, cooperatives, and exporters. It runs on AWS.

It is a decision-support tool. It is **not** official grading and must never present itself as one.

## Team & ownership (5 members)

- **Frontend (2):** `frontend/` — the React/TypeScript/Tailwind web app.
- **Backend (2):** `backend/` + `infra/` — the public API, workflow, Gemini, S3, database, AWS/deployment.
- **Vision (1):** `vision/` — the defect-detection model and its service.

Each subsystem is a **separately deployable service**. The repo is a monorepo, not a monolith: no service imports another service's code. They meet only at the two HTTP contracts in `contracts/`.

Each subsystem has its own file that adds rules for its area: `backend/AGENTS.md`, `frontend/AGENTS.md`, `vision/AGENTS.md`. Follow this file plus the one for the area you are working in. The more specific file wins on conflict. Instructions from the user in chat override both, unless they would compromise security or data safety (then say so and ask).

**Priority when rules conflict:** security and data safety → correctness → the user's explicit instruction → simplicity → performance → brevity.

---

## Where the truth lives

- Specifics change often: endpoints, schemas, class names, thresholds, database and compute choices, which AWS services. They live in `docs/`, `contracts/`, and in the code, **not here**. Read them before acting. Do not rely on memory or on this file for specifics.
- Docs are living documents. If docs and code disagree, or a task contradicts the docs, say so and propose which one to update. Do not silently pick one, and do not silently diverge.
- Some decisions are still open (see `docs/`). If a task depends on one, lay out the trade-offs and ask. Do not decide quietly.
- Explore before asking. You can read the whole repo, so look for existing patterns and answers first.

## Stack (fixed)

- Frontend: React, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, AWS
- Vision: Python (the vision owner chooses the model framework)

Do not introduce another language or framework without asking.

## Boundaries between subsystems

The three services are separate programs that talk **only** through explicit HTTP contracts. Nothing imports code from another service's folder.

```
Browser ──▶ backend ──▶ vision
              │
              ├──▶ Gemini
              ├──▶ S3
              └──▶ database
```

- **Frontend** knows only the backend API.
- **Backend** knows the vision API and Gemini. It never knows *how* a bean is detected.
- **Vision** knows nothing about users, S3, the database, or Gemini. Image bytes go in, structured detections come out. Vision never needs AWS credentials; the backend sends image bytes, not S3 keys.

Contracts:
- **Frontend ⇄ Backend:** an HTTP API. The backend owns it; its Pydantic models and generated OpenAPI (`contracts/backend-api/`) are the contract.
- **Backend ⇄ Vision:** an HTTP inference API. The vision owner owns it; `contracts/vision-api/` is the contract. The backend treats vision as an external dependency (validate and normalize its output, handle its errors and timeouts).

Rules:
- On day one, each contract owner commits stub endpoints + example JSON so everyone can build in parallel. The frontend generates TypeScript types from `contracts/backend-api/`; the backend generates its vision-client models from `contracts/vision-api/`.
- Never invent endpoints, fields, class names, or output formats. If the contract lacks something you need, flag it and propose a change. Do not code around it.
- A contract change affects other people. Propose it first, update the single contract definition in the same change as the code, and name which subsystems are affected. Contract changes need review from both sides (see `.github/CODEOWNERS`).
- You may read anything. Edit outside your own area only when the task requires it, and say so.

## Product invariants (every subsystem must uphold these)

- Output is a **preliminary AI prediction**, never a verified finding or an official grade. Do not produce or show a grade unless a documented, validated method exists.
- Never fabricate, default, or simulate results and present them as real. Missing or invalid model output is an error state, not a zero. **A service must never silently fall back to mock/demo output** — fail loudly instead.
- "Zero detections" is a valid result. "Processing failed" is not. Keep them distinct everywhere.
- Be exact about what is counted (beans, defect regions, or classes). Never mix them. Confidence means model confidence, not correctness.
- Every result records the model version that produced it.
- Report only the defect classes the model actually supports (currently 3: Full Black, Partial Black, Coffee Husk / Parchment).
- Any metric you quote must have been measured.

---

## How to work

**Match effort to the task.** Typo or obvious small fix: just do it. Medium task: give a short plan and your assumptions, then proceed. Large, ambiguous, or irreversible work (new feature, contract change, schema or infrastructure change, data migration): first restate the goal, list assumptions, open questions, acceptance criteria, and risks, then **wait for confirmation**.

> Note: This repo was recently restructured from a single `app/` monolith into the three-service layout. Migrated files carry a header comment noting imports that still need rewiring. See `docs/MIGRATION.md`.
