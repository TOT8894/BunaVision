# ☕ BunaVision — AI-Powered Green Coffee Quality Pre-Assessment

> **BunaVision** helps Ethiopian coffee producers, washing stations, cooperatives, and exporters get a **preliminary** AI screening of green coffee bean photos. A user uploads a sample image; a computer-vision model detects the visible defects it supports; the system returns a report (defects, counts, confidence, annotated image) that is stored and can be revisited.
>
> It is a **decision-support tool, not official grading**, and never presents itself as one.

---

## Monorepo: three services

BunaVision is a **monorepo of three separately deployable services**. No service imports another's code — they meet only at the two HTTP contracts in `contracts/`.

```
Browser ──▶ frontend ──▶ backend ──▶ vision
                            │
                            ├──▶ Gemini   (narrative analysis only)
                            ├──▶ S3        (image storage)
                            └──▶ database  (assessment records)
```

| Service | Folder | Owners | Role |
|---|---|---|---|
| **Frontend** | [`frontend/`](frontend/) | 2 members | React + TypeScript + Tailwind web app. Knows only the backend API. |
| **Backend** | [`backend/`](backend/) + [`infra/`](infra/) | 2 members | Public API, upload validation, workflow, Gemini, grading, S3, DB, AWS. |
| **Vision** | [`vision/`](vision/) | 1 member | Defect detection. Image bytes in → structured detections out. Knows nothing about users, S3, DB, or Gemini. |

**Team: 5 members** (2 frontend, 2 backend, 1 vision).

## Repository layout

```text
bunavision/
├── AGENTS.md                 shared rules for all subsystems
├── README.md                 this file
├── docker-compose.yml        run all three services locally
├── .github/CODEOWNERS        folder → owner, routes reviews automatically
├── contracts/
│   ├── backend-api/          OpenAPI + examples (backend owns, frontend consumes)
│   └── vision-api/           OpenAPI + examples (vision owns, backend consumes)
├── frontend/                 React/TS/Tailwind app  (+ frontend/AGENTS.md)
├── backend/                  FastAPI public API      (+ backend/AGENTS.md)
│   └── app/{api,core,schemas,services,domain,adapters}
├── vision/                   defect-detection service (+ vision/AGENTS.md)
│   └── {core,service,model,training,evaluation,tests}
├── infra/                    AWS as code
└── docs/                     architecture, migration notes, decisions
```

## Contracts-first, parallel work

So the five of us can build in parallel without blocking each other:

- **Frontend ⇄ Backend:** `contracts/backend-api/` — the backend owns it; the frontend generates TypeScript types from it.
- **Backend ⇄ Vision:** `contracts/vision-api/` — the vision owner owns it; the backend generates its vision-client models from it.
- On day one, each contract owner commits stub endpoints + example JSON. Nobody hand-copies shapes. Contract changes need review from both sides.

## Running locally

```bash
# All three services (entry points are filled in by their owners):
docker compose up --build
```

Per-service dev instructions live in each service's folder. See each `*/AGENTS.md` for the rules that apply to that area.

## Product invariants (every service upholds)

- Output is a **preliminary AI prediction**, never a verified finding or an official grade.
- **Never** fabricate, default, or simulate results and present them as real — fail loudly instead.
- "Zero detections" ≠ "processing failed" — keep them distinct everywhere.
- Report only the defect classes the model actually supports (currently **3**: Full Black, Partial Black, Coffee Husk / Parchment).
- Every result records the model version that produced it. Any metric quoted must have been measured.

## Status

This repo was recently restructured from a single `app/` monolith into the three-service layout above. **Existing code was moved, not rewritten.** Migrated files carry a header comment noting imports that still need rewiring, and each service's remaining work is tracked in **[`docs/MIGRATION.md`](docs/MIGRATION.md)**. Architecture details are in **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)**.

## Documentation

- [`AGENTS.md`](AGENTS.md) — shared engineering rules.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — target architecture & open decisions.
- [`docs/MIGRATION.md`](docs/MIGRATION.md) — the monolith→3-service move + what each member still implements.
- [`docs/BunaVision.md`](docs/BunaVision.md) — full product specification.
