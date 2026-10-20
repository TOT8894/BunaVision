# BunaVision — Architecture

> Status: the repo was restructured from a single `app/` monolith into a **three-service monorepo**. This document describes the target architecture the team is building toward. For the move itself, see `MIGRATION.md`.

## Shape

Three **separately deployable** services, one monorepo. No service imports another's code; they meet only at the two HTTP contracts in `contracts/`.

```
Browser ──▶ frontend ──▶ backend ──▶ vision
                            │
                            ├──▶ Gemini   (narrative analysis only)
                            ├──▶ S3        (image storage)
                            └──▶ database  (assessment records)
```

## Services

| Service    | Folder      | Owner(s)        | Responsibility |
|------------|-------------|-----------------|----------------|
| Frontend   | `frontend/` | 2 members       | Upload UI, status, report & history pages. Knows only the backend API. |
| Backend    | `backend/` + `infra/` | 2 members | Public API, upload validation, workflow, Gemini, grading, S3, DB, AWS. Knows the vision API and Gemini. |
| Vision     | `vision/`   | 1 member        | Defect detection. Image bytes in → structured detections out. Knows nothing about users, S3, DB, or Gemini. |

## Contracts

- **`contracts/backend-api/`** — Frontend ⇄ Backend HTTP API. Backend owns it; frontend generates TS types from it.
- **`contracts/vision-api/`** — Backend ⇄ Vision HTTP inference API. Vision owns it; backend generates its vision-client models from it.

## Request flow (assessment)

1. Browser uploads an image to the **backend** `/assessments` endpoint.
2. Backend validates the upload by actual content, size, dimensions.
3. Backend stores the image (S3) and calls the **vision** service with the image bytes.
4. Vision returns structured detections (bounding boxes, per-class defect counts, model version).
5. Backend normalizes/validates vision output, runs the grading rules (`backend/app/domain/`), and calls **Gemini** for narrative notes (cupping, advisory, Amharic) — labelled AI-generated, not measurements.
6. Backend persists the assessment (with status + model version) and returns the report.
7. Frontend renders the report honestly (preliminary prediction, limitations, distinct empty vs failed states).

## Open decisions (see spec + ask before deciding)

- **Vision deployment** — separate AWS service (chosen) vs. in-process library. Chosen: separate service for independent ownership; weigh the second deployment cost.
- **Who draws the boxes** — vision returns an annotated image vs. coordinates the frontend draws. Coordinates are lighter.
- **Model weights** — Git LFS vs. S3 (not plain git).
- **Authentication** — still undecided.
- **Database & compute** — RDS/Postgres vs. alternatives; container vs. serverless.
- **Gemini model** — move the model name to env; the migrated `config.py` hardcodes it.
