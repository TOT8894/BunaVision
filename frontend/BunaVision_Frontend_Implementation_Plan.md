# BunaVision — Frontend Implementation Plan

**Derived from:** `BunaVision.md` v1.0
**Scope:** Frontend only (React web app). Backend, AI inference, and AWS infrastructure are referenced only where the frontend depends on them.
**Owner (per spec §17):** Member 1 — Frontend Development

---

## 1. Frontend Scope

### 1.1 What the frontend must deliver (MVP, spec §4.1 and §11)

| # | Deliverable                                                                                                   | Spec ref                  | Priority      |
| - | ------------------------------------------------------------------------------------------------------------- | ------------------------- | ------------- |
| 1 | Landing page with product explanation, 3-step workflow, and "preliminary result" disclaimer                   | FR-01, §11.1 Page 1      | Must          |
| 2 | Upload page: dropzone, capture instructions, preview, validation messages, Analyze button, loading state      | FR-02, FR-03, FR-04, §10 | Must          |
| 3 | Results page: original image, annotated image (if supported), defect classes, counts, confidence, limitations | FR-09, FR-10              | Must / Should |
| 4 | History page: list with pagination, status, summary, link to report                                           | FR-12                     | Should        |
| 5 | Assessment details page: full results, model version, timestamp, warnings                                     | FR-14                     | Should        |
| 6 | Complete UI state coverage (idle → success, all error states, empty history)                                 | §11.2, FR-13             | Must          |
| 7 | AI transparency copy on every report                                                                          | §15.3                    | Must          |
| 8 | Responsive layout                                                                                             | §7.4, §16.1             | Must          |

### 1.2 Optional / conditional (build only if time permits)

- Authentication UI and ownership-scoped history (FR-15, conditional on the open auth decision)
- Report export / download (FR-16, Could)
- Sample comparison over time (FR-17, Could)
- Charts (the spec says "only if useful")

### 1.3 Explicitly out of scope

- Any overall coffee grade or score (spec §11.1: do not show a grade unless a validated method exists)
- Mobile-native app, marketplace, payments, multi-tenant admin
- Client-side AI inference or any client-side "defect detection"

### 1.4 Non-negotiable frontend rules (from the spec)

1. **Never show fabricated or stale results** as belonging to the current image (§11.2).
2. **Never present predictions as verified findings** or as an official grade (§7.4, §15.5).
3. **Never treat defect-region counts as bean counts.** Label exactly what a count measures (§9.5).
4. **Confidence is "model confidence"**, not the probability that a sample meets a grade (§9.6).
5. **Placeholder values in the API example are not real output.** Mock data must be clearly flagged as mock in dev builds and never shipped to the demo (§12.1, §16.5).
6. Do not trust client-side validation. It is a convenience; the backend is authoritative (§15.1).

---

## 2. Technology Stack

The spec proposes React + TypeScript + Tailwind CSS (§8.2, marked "confirm with the team"). Recommended concrete choices:

| Concern            | Choice                             | Reason                                                                        |
| ------------------ | ---------------------------------- | ----------------------------------------------------------------------------- |
| Build tool         | **Vite**                     | Fast dev server, simple env var handling, static output for S3/Amplify        |
| Language           | **TypeScript (strict mode)** | Types mirror the API contract                                                 |
| UI framework       | **React 18+**                | Per spec                                                                      |
| Styling            | **Tailwind CSS**             | Per spec                                                                      |
| Routing            | **React Router**             | 5 pages, simple                                                               |
| Server state       | **TanStack Query**           | Caching, polling for async status, retry, request cancellation                |
| Forms              | Plain controlled state             | Only one tiny form (file + optional note); a form library is overkill         |
| Runtime validation | **Zod**                      | Validate API responses so malformed model output never crashes the UI (§7.2) |
| Api integration    | **Axios**                         |                                                                               |
| Icons              | **lucide-react**             | Lightweight                                                                   |
| Lint/format        | ESLint + Prettier                  | Consistency across 4 contributors                                             |

> **Decision to confirm with the team:** the framework choice (React + TS) is already assumed by the spec; the rest above is a recommendation, not a requirement.

---

## 3. Project Structure

Matches the monorepo layout in spec §18.1 (`frontend/src/{components,pages,services,hooks,types}`), with a few additions.

```text
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx                  # Router + providers
│   ├── config/
│   │   └── env.ts               # Typed access to VITE_* variables
│   ├── types/
│   │   ├── assessment.ts        # Assessment, Prediction, Summary, Status
│   │   └── api.ts               # ApiError, ErrorCode, ListResponse
│   ├── schemas/
│   │   └── assessment.schema.ts # Zod schemas mirroring types
│   ├── services/
│   │   ├── apiClient.ts         # fetch wrapper, error normalization, timeouts
│   │   └── assessmentsApi.ts    # create / get / list
│   ├── hooks/
│   │   ├── useCreateAssessment.ts
│   │   ├── useAssessment.ts     # with polling for pending/processing
│   │   ├── useAssessments.ts    # paginated history
│   │   └── useImageValidation.ts
│   ├── utils/
│   │   ├── imageValidation.ts   # type/size/dimension checks
│   │   ├── errorMessages.ts     # ErrorCode -> user-friendly message + next step
│   │   └── format.ts            # dates, percentages
│   ├── components/
│   │   ├── layout/              # AppShell, Header, Footer, PageContainer
│   │   ├── upload/              # Dropzone, CaptureInstructions, ImagePreview, ValidationMessage
│   │   ├── results/             # ImageCompare, DefectTable, SummaryCards, LimitationsPanel, ConfidenceBadge
│   │   ├── history/             # HistoryList, HistoryRow, EmptyHistory, Pagination
│   │   ├── feedback/            # ProcessingState, ErrorState, Spinner, Skeletons
│   │   └── common/              # Button, Card, Badge, Disclaimer, StatusPill
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── UploadPage.tsx
│   │   ├── AssessmentResultPage.tsx   # also serves details view (see §6.4)
│   │   ├── HistoryPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── mocks/                   # MSW handlers and fixtures (dev/test only)
│   └── test/                    # Test setup and utilities
├── .env.example
├── index.html
├── tsconfig.json
├── vite.config.ts
└── package.json
```

---

## 4. API Integration Contract (Frontend View)

Base path: `/api/v1` (spec §12). The contract is proposed and may change, so **isolate it in `services/` and `types/`** so a change touches one place.

### 4.1 Types

```ts
// types/assessment.ts
export type AssessmentStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Prediction {
  class_name: string;
  confidence: number;      // 0..1, model confidence
  count: number;           // meaning defined by the team (see §9.5 of spec)
}

export interface AssessmentSummary {
  detected_classes: number;
  detection_count: number;
}

export interface Assessment {
  assessment_id: string;
  status: AssessmentStatus;
  model_version: string;
  created_at: string;            // ISO 8601
  completed_at?: string | null;
  summary?: AssessmentSummary;
  predictions?: Prediction[];
  original_image_url?: string | null;   // presigned, short-lived (may be added by backend)
  annotated_image_url: string | null;
  limitations: string[];
  error_code?: ErrorCode | null;
}

// types/api.ts
export type ErrorCode =
  | 'INVALID_IMAGE' | 'IMAGE_TOO_LARGE' | 'UNSUPPORTED_FORMAT'
  | 'INFERENCE_FAILED' | 'ASSESSMENT_NOT_FOUND' | 'UNAUTHORIZED'
  | 'RATE_LIMITED' | 'INTERNAL_ERROR';

export interface ApiErrorBody { error: { code: ErrorCode; message: string } }
```

### 4.2 Endpoints used

| Frontend action   | Request                                                                 | Notes                                                                                                    |
| ----------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Submit image      | `POST /api/v1/assessments` (multipart: `image`, optional `notes`) | May return `200/201` with a completed result (sync MVP) or `202` with `pending/processing` (async) |
| Fetch one         | `GET /api/v1/assessments/{id}`                                        | Poll while `pending` / `processing`                                                                  |
| List history      | `GET /api/v1/assessments`                                             | Paginated                                                                                                |
| Health (optional) | `GET /health`                                                         | Optional "service unavailable" banner                                                                    |

### 4.3 Items to agree with Member 3 **before** parallel work (spec §18.3)

These are blocking for the frontend. Raise them in the first sync:

- [ ] Sync vs. async: does `POST` return a finished result or a `202` + ID? (Plan supports both.)
- [ ] How are original and annotated images delivered: presigned URL fields in the response, or a separate endpoint? Expiry time?
- [ ] Pagination shape (cursor vs. page/limit) and response envelope for the list endpoint
- [ ] Final prediction class names and what `count` measures per class
- [ ] Whether per-detection bounding boxes will be returned (enables a client-side overlay) or only a pre-rendered annotated image
- [ ] Idempotency: how a retry avoids duplicate records (e.g., an `Idempotency-Key` header). See §7.2 of spec
- [ ] Authentication: none (public demo), or tokens/cookies? Affects the API client and routing
- [ ] Max upload size and accepted dimensions (the frontend mirrors these as config)
- [ ] Rate-limit response format (`RATE_LIMITED`, `Retry-After` header?)
- [ ] CORS origin for dev and deployed frontend (with Member 4)

### 4.4 API client behavior (`services/apiClient.ts`)

- Base URL from `VITE_API_BASE_URL`.
- Wrap `fetch`; always parse the error body into a typed `ApiError` (`code`, `message`, `httpStatus`).
- Map network failure / abort / timeout to a distinct `NETWORK_ERROR` (client-side code, not from the backend).
- Request timeout via `AbortController` (default 60s for upload; configurable, since inference latency is unknown until benchmarked).
- Validate every successful response with Zod. On a schema mismatch, throw `INVALID_RESPONSE` and show a generic failure state instead of rendering partial data.
- Never log image contents; log only error codes and assessment IDs (spec §14.4).
- Attach auth header only if/when auth is enabled.

---

## 5. State Management and UI State Machine

### 5.1 Upload flow state (spec §11.2)

```text
idle ──select file──▶ imageSelected ──(invalid)──▶ validationError ──select new──▶ imageSelected
                          │
                       analyze
                          ▼
                      uploading ──(network fail)──▶ networkError ──retry──▶ uploading
                          │
                          ▼
                      processing ──(INFERENCE_FAILED etc.)──▶ inferenceFailure ──retry/new image──▶ idle
                          │
                          ▼
                       success ──▶ navigate to /assessments/:id
```

Implement as a small `useReducer` state machine in `UploadPage` (or a `useUploadFlow` hook) so impossible states cannot occur (e.g., "success" without a result).

### 5.2 Server state

- **TanStack Query** owns assessments: `['assessment', id]`, `['assessments', page]`.
- `useAssessment(id)` sets `refetchInterval` (e.g., 2s, with backoff) only while status is `pending` or `processing`, stopping on `completed` / `failed`. Add a max polling duration with a "taking longer than expected" message.
- On creating an assessment, **do not seed the cache with data from a previous assessment**. Navigate by ID and key all data by ID so stale results can never show against a new image.

### 5.3 Local-only state

- Selected `File`, preview object URL (revoke on unmount / replace), optional notes text.
- No global store needed. If auth is added, a tiny context for the session is enough.

---

## 6. Pages and Components

### 6.1 Route map

| Route                    | Page                                     | Spec ref             |
| ------------------------ | ---------------------------------------- | -------------------- |
| `/`                    | HomePage                                 | §11.1 Page 1        |
| `/assess`              | UploadPage                               | §11.1 Page 2        |
| `/assessments`         | HistoryPage                              | §11.1 Page 4        |
| `/assessments/:id`     | AssessmentResultPage (results + details) | §11.1 Pages 3 and 5 |
| `*`                    | NotFoundPage                             | n/a                  |
| `/login` (conditional) | LoginPage                                | FR-15                |

### 6.2 Home page

**Components:** `Header` (logo/name, nav: Assess, History), hero (short explanation + primary **"Assess a Sample"** button → `/assess`), `HowItWorks` (3 steps: Upload → AI analyzes → Review report), `Disclaimer`.

**Content requirements**

- Plain-language explanation of what BunaVision does.
- Visible disclaimer: *results are a preliminary AI assessment, not an official grade* (§1, §15.5).
- Keep copy short and avoid claims about commercial benefit (spec §2.5 says benefits are unproven).

### 6.3 Upload page

**Components**

- `CaptureInstructions`: checklist from §10.1 (single layer of beans, plain contrasting background, bright even light, no harsh shadows/reflections, in focus, beans separated, full sample in frame). Include a good-vs-bad example image pair if available. Note that instructions are preliminary and may be adapted to the chosen model.
- `Dropzone`: drag-and-drop + click + keyboard-accessible file input. On mobile, `accept="image/jpeg,image/png"` plus `capture="environment"` option so users can take a photo directly.
- `ImagePreview`: preview via `URL.createObjectURL`, file name, size, dimensions, "Replace" and "Remove".
- `ValidationMessage`: inline, specific, actionable.
- `AnalyzeButton`: disabled until a valid image is selected; disabled while uploading to prevent double submits.
- `ProcessingState`: spinner, upload progress (if using `XMLHttpRequest` or fetch streams; otherwise an indeterminate indicator), status text ("Uploading…", "Analyzing…"), and a Cancel action.

**Client-side validation (convenience only; backend is authoritative)**

| Check          | Rule                                                                                                                                             | Source |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| Type           | JPEG/PNG; verify by reading magic bytes (first bytes of file), not just extension/MIME                                                           | §10.2 |
| Size           | ≤ `VITE_MAX_UPLOAD_MB` (config; value TBD after testing)                                                                                      | §10.2 |
| Decodable      | Load into an `Image`/`createImageBitmap`; failure → "cannot be read"                                                                        | §10.3 |
| Min dimensions | ≥ `VITE_MIN_IMAGE_PX` (config; from model requirements)                                                                                       | §10.3 |
| Optional       | Basic blur/brightness hints. Treat as a warning, not a block, and only if time permits (spec: "optional enhancements, not assumed capabilities") | §10.3 |

**Duplicate-submit protection:** disable the button on submit; generate one idempotency key per selected file and reuse it for retries of the same file (if the backend supports it).

### 6.4 Results and details page (`/assessments/:id`)

The spec lists Results (Page 3) and Details (Page 5) separately, but they show largely the same data. Build **one page** that renders the report, and show extra "details" (model version, timestamp, full predictions, warnings) in a collapsible section or lower on the page. This reduces duplicate code. Split later only if a real need appears.

**Layout (top to bottom)**

1. Header row: Assessment ID, created timestamp, `StatusPill`.
2. If status is `pending`/`processing` → `ProcessingState` (polling). If `failed` → `ErrorState` with the mapped message (see §8). Only render results for `completed`.
3. `ImageCompare`: original vs. annotated image (side-by-side on desktop, tabs/toggle on mobile). If `annotated_image_url` is `null`, show the original only with a note: "Annotated image not available for this model" (spec FR-10: Should, only if supported).
4. `SummaryCards`: detected classes, total detections. **Label the unit of every count precisely** once the team defines it (beans vs. defect regions, §9.5).
5. `DefectTable`: class name, count, confidence (as "Model confidence"), with a `ConfidenceBadge`. Sort by count by default.
6. **Low-confidence flag:** items below a configurable threshold get a "Review manually" badge (§9.6, user story 5.2). The threshold comes from backend/AI validation, not chosen to make the demo look good.
7. `LimitationsPanel`: always visible; renders `limitations[]` from the API plus the fixed AI-transparency block (§15.3):
   - Results are generated by an AI model.
   - Confidence values describe model predictions, not guaranteed correctness.
   - Only supported visible defect classes are assessed.
   - Hidden defects cannot be reliably determined from a photograph.
   - Results are preliminary and need human verification.
8. Details section: model version, timestamp (created/completed), raw predictions, warnings.
9. Actions: "Assess another sample" → `/assess`, "Back to history" → `/assessments`. (Saving happens server-side on creation, so the **"Save"** action in §11.1 is really a confirmation: show "Saved to history" once status is `completed`. Confirm this with the backend owner.)

**Do not render:** an overall grade, pass/fail, price estimate, or cup-quality claim.

**Image handling**

- Presigned URLs expire: if an `<img>` fails to load, refetch the assessment to obtain fresh URLs, then retry once before showing "Image unavailable".
- Provide `alt` text ("Original sample image", "Annotated sample image with detected defects").
- Optional zoom/lightbox for inspecting small defects.
- If the backend later returns bounding boxes, add a canvas/SVG overlay layer with per-class colors and a legend. Not required if a pre-rendered annotated image is provided.

### 6.5 History page

**Components:** `HistoryList` (table on desktop, cards on mobile), `HistoryRow` (date, ID, `StatusPill`, summary of detected categories, "Open report" link), `Pagination` (or "Load more"), `EmptyHistory` (message + CTA to `/assess`), loading skeletons, error state with retry.

**Rules**

- Use the pagination shape agreed in §4.3.
- If auth is enabled, history is scoped by the backend; the frontend must handle `UNAUTHORIZED` by redirecting to login.
- Failed assessments appear in history with a clear "Failed" status (they must not look like successes, §7.2).

### 6.6 Shared components

| Component           | Purpose                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| `Disclaimer`      | Reusable "preliminary AI assessment" notice (Home, Results)                    |
| `StatusPill`      | pending / processing / completed / failed with text and icon (not color alone) |
| `ConfidenceBadge` | Shows percent plus label "Model confidence"; low-confidence variant            |
| `ErrorState`      | Message + suggested next step + retry/back action                              |
| `ProcessingState` | Spinner, status text, elapsed time, cancel                                     |
| `AppShell`        | Header, nav, footer with disclaimer link                                       |

---

## 7. Error Handling and Messaging

Every error must say **what happened** and **what the user can do next** (spec §7.4).

| Source / code                               | User-facing message (draft)                                                               | Next action         |
| ------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------- |
| Client: wrong type / `UNSUPPORTED_FORMAT` | "This file type isn't supported. Please upload a JPEG or PNG photo."                      | Choose another file |
| Client: too large / `IMAGE_TOO_LARGE`     | "This image is larger than {max} MB. Try a lower-resolution photo."                       | Choose another file |
| Client: cannot decode / `INVALID_IMAGE`   | "We couldn't read this image. Try taking the photo again."                                | Choose another file |
| Client: too small                           | "This image is too small for analysis. Use at least {min}px on the shorter side."         | Choose another file |
| `INFERENCE_FAILED`                        | "The analysis didn't complete. Your image was not assessed."                              | Retry / new image   |
| `ASSESSMENT_NOT_FOUND`                    | "We couldn't find that assessment."                                                       | Go to history       |
| `UNAUTHORIZED`                            | "Please sign in to view this." (only if auth enabled)                                     | Sign in             |
| `RATE_LIMITED`                            | "Too many requests. Please wait a moment and try again." (use `Retry-After` if present) | Retry later         |
| `INTERNAL_ERROR` / unknown                | "Something went wrong on our side. Please try again."                                     | Retry               |
| Network error / timeout                     | "Can't reach the server. Check your connection and try again."                            | Retry               |
| `INVALID_RESPONSE` (client-side)          | "We received an unexpected response. Please try again."                                   | Retry               |

**Rules**

- Centralize in `utils/errorMessages.ts`. Do not scatter strings across components.
- Never expose raw stack traces, internal URLs, or backend details.
- A failed or aborted upload must **never** navigate to a results page or display a success state (§7.2).
- Retry reuses the same idempotency key for the same file; selecting a new file generates a new key.
- Add a top-level React **Error Boundary** so an unexpected render error shows a recovery screen rather than a blank page.

---

## 8. Accessibility, Responsiveness, and UX Quality

- **Responsive:** design mobile-first (users likely photograph samples on phones). Test at 360px, 768px, 1280px (spec §16.1).
- **Accessibility:** keyboard-operable dropzone, visible focus states, labelled inputs, `aria-live` regions for processing and error messages, sufficient color contrast, status conveyed by text/icon and not color alone.
- **Performance:** route-level code splitting (`React.lazy`), lazy-load images, revoke object URLs, avoid heavy dependencies (skip chart libraries unless clearly useful).
- **Low-bandwidth friendliness:** consider optional client-side downscaling of very large photos before upload, **only if** it matches the model's documented input requirements (spec §7.1). Confirm with Member 2 first, since resizing can change detection results.
- **Language:** English for MVP. Keep all UI strings in one module (`copy.ts` or an i18n-ready structure) so multilingual support (spec §22 future work, e.g. Amharic) is easier later. Do not build i18n now.

---

## 9. Configuration and Environment

`frontend/.env.example` (no secrets; everything prefixed `VITE_` is public in the browser bundle):

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_MAX_UPLOAD_MB=10            # placeholder; set after backend testing
VITE_MIN_IMAGE_PX=640            # placeholder; set from model requirements
VITE_LOW_CONFIDENCE_THRESHOLD=0.5  # placeholder; must come from validation, not demo tuning
VITE_POLL_INTERVAL_MS=2000
VITE_REQUEST_TIMEOUT_MS=60000
VITE_USE_MOCKS=false             # true only in local dev/tests
```

**Security notes (spec §7.3, §14.4)**

- Never put AWS keys or secrets in the frontend or in `VITE_*` variables.
- Use HTTPS in deployed environments; CORS must match the real frontend origin (coordinate with Member 4).
- Do not store images or results in `localStorage`. If auth tokens are needed, prefer httpOnly cookies set by the backend over `localStorage`.
- Render all backend-provided text as plain text (React escapes by default; never use `dangerouslySetInnerHTML`).

---

## 10. Development Without a Backend (Mock Layer)

To avoid being blocked by the backend and AI work:

1. Add **MSW** handlers in `src/mocks/` for `POST /assessments`, `GET /assessments/:id`, `GET /assessments`.
2. Fixtures cover: completed with annotated image, completed without annotated image, processing → completed (polling), failed (`INFERENCE_FAILED`), `RATE_LIMITED`, empty history, paginated history.
3. **Label mock data clearly** (e.g., class names like `mock_defect_A`, a visible "MOCK DATA" banner when `VITE_USE_MOCKS=true`). The spec warns that illustrative values are not real model output, and the final demo must use real inference (§16.5, §21.3).
4. Remove or disable mocks in production builds.

---

## 11. Testing Plan

Maps to spec §16.1.

### 11.1 Unit and component tests (Vitest + RTL)

- `imageValidation`: accepts valid JPEG/PNG, rejects wrong type (including a renamed `.txt` as `.jpg`), oversize, undecodable, undersized.
- `errorMessages`: every `ErrorCode` maps to a message and next action.
- `ConfidenceBadge`, `StatusPill`, `DefectTable`: render correct values; low-confidence flag appears below the threshold.
- `ImageCompare`: shows the fallback note when `annotated_image_url` is `null`.
- Zod schema: rejects malformed responses (missing fields, confidence outside 0–1).

### 11.2 Flow tests (RTL + MSW)

- Upload a valid image → processing state → navigate to the result → predictions render.
- Upload an unsupported file → validation message, Analyze stays disabled.
- Backend returns `INFERENCE_FAILED` → error state with retry, no results shown.
- Network failure → network error state; retry works.
- Async path: `202` → polling → `completed`; polling stops on `failed`.
- Opening an existing assessment from history.
- Empty history and loading-history states.
- Double-click on Analyze produces a single request.
- Stale-data guard: after viewing assessment A, uploading B never shows A's data.

### 11.3 Responsive / manual checks

- Layout at 360 / 768 / 1280 widths; camera capture on a real phone; slow-network throttling in dev tools.

### 11.4 E2E (optional, Playwright)

- One happy-path test against the deployed or staging environment using a known sample image.
- Part of the final demo-readiness checklist.

---

## 12. Build, Deployment, and Hand-off (Frontend Part)

Infrastructure is owned by Member 4; the frontend must provide:

- `npm run build` → static `dist/` output.
- A **single-page-app fallback** configuration (all routes → `index.html`) so deep links like `/assessments/:id` work. In S3 + CloudFront this means a custom error response mapping 403/404 to `/index.html`; in Amplify Hosting use a rewrite rule.
- Build-time environment variables for the deployed API URL (`VITE_API_BASE_URL`).
- A short `frontend/README.md`: install, run, mock mode, env vars, test commands, build/deploy notes.
- Hosting choice (Amplify Hosting vs. S3 static hosting, optionally with CloudFront) is an open decision (spec §14.1). Either works with the output above.

---

## 13. Milestones (Frontend Tasks Mapped to Spec §19)

The spec uses milestones rather than dates (deadline unknown). Convert to a schedule once the deadline is known.

### Milestone 0 — Setup and contract alignment *(do first)*

- [ ] Scaffold Vite + React + TS + Tailwind; configure ESLint, Prettier, Vitest
- [ ] Create folder structure, `.env.example`, base layout and routing
- [ ] Walk through §4.3 contract questions with Member 3 and Member 2; record decisions in `docs/API.md`
- [ ] Define types and Zod schemas from the agreed contract

**Exit:** app runs, routes render placeholder pages, contract questions answered or tracked.

### Milestone 1 — Feasibility support

- [ ] Get sample model output from Member 2 to confirm what can be displayed (classes, counts, boxes or not)
- [ ] Decide whether the results UI uses only an annotated image or also an overlay
- [ ] Draft the exact definition of "count" shown in the UI

**Exit:** the team knows what the results page can truthfully show.

### Milestone 2 — Vertical slice *(frontend side)*

- [ ] Home page with disclaimer
- [ ] Upload page: dropzone, preview, client validation, instructions
- [ ] API client + `useCreateAssessment`
- [ ] Results page rendering real (or clearly-labeled mock) data
- [ ] Processing and basic error states

**Exit:** one end-to-end local assessment works through the UI.

### Milestone 3 — Persistence

- [ ] `useAssessment` with polling, `useAssessments` with pagination
- [ ] History page, empty/loading/error states
- [ ] Details section (model version, timestamp, warnings)
- [ ] Presigned-image refresh handling

**Exit:** a completed assessment can be reopened from history after the original request finished.

### Milestone 4 — Deployment support

- [ ] Production build; SPA fallback; deployed API URL configured
- [ ] CORS and HTTPS verified with Member 4
- [ ] Smoke test on the public URL from a phone and a desktop

**Exit:** a remote user can complete an assessment in the browser.

### Milestone 5 — Test and refine

- [ ] Full test suite passing (§11)
- [ ] Polish loading/error copy; accessibility pass; responsive pass
- [ ] Verify annotated image display with real model output
- [ ] Remove/disable mocks and any placeholder data

**Exit:** the core workflow is repeatable; known limitations are documented in the UI.

### Milestone 6 — Final demonstration

- [ ] Choose representative demo images with Member 2
- [ ] Rehearse the UI demo path (spec §21.1 steps 2–8)
- [ ] Prepare fallback: screen recording / screenshots of a real run in case network or inference fails (label them as recordings)

**Exit:** the demo can be completed reliably.

---

## 14. Frontend Risks and Mitigations

| Risk                                                | Impact | Mitigation                                                                                                |
| --------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| API contract changes late                           | High   | Isolate in `services/` + `types/` + Zod; agree contract early (§4.3)                                 |
| Backend/model not ready                             | High   | MSW mock layer with clearly labeled fixtures                                                              |
| Model returns only classification (no boxes/counts) | Medium | Results UI degrades gracefully: hide annotated panel and per-bean counts; never imply localization        |
| Misleading count labels                             | High   | Define count unit with Member 2; label it explicitly in the table (§9.5)                                 |
| Results read as an official grade                   | High   | No grade UI; persistent disclaimer and limitations panel                                                  |
| Slow inference confuses users                       | Medium | Clear processing state, elapsed time, cancel, "taking longer than expected"                               |
| Presigned image URLs expire                         | Medium | Refetch on image error; retry once                                                                        |
| Inconsistent user photos                            | High   | Prominent capture instructions; client checks for size/dimensions; rely on backend rejection for the rest |
| Duplicate records on retry                          | Medium | Disable button; idempotency key; confirm backend support                                                  |
| SPA deep links 404 on hosting                       | Medium | Configure the fallback to `index.html` at deploy time                                                   |
| Demo network failure                                | Medium | Recorded fallback; optionally a local dev setup with the backend                                          |

---

## 15. Frontend Definition of Done

Subset of spec §24 that the frontend owns:

- [ ] Home page explains the product and shows the preliminary-assessment disclaimer
- [ ] Upload accepts valid JPEG/PNG and rejects invalid inputs with clear messages
- [ ] Capture instructions are visible on the upload page
- [ ] Processing/loading states shown; double-submit prevented
- [ ] Results page shows classes, counts, and "model confidence" exactly as returned, with count units labeled
- [ ] Annotated image displayed when provided; graceful fallback when not
- [ ] Low-confidence predictions flagged for manual review
- [ ] AI-transparency/limitations text present on every report
- [ ] No overall grade or official-quality claim anywhere in the UI
- [ ] History page lists saved assessments (with empty, loading, error states) and opens reports
- [ ] Model version and timestamp visible in details
- [ ] All error codes mapped to actionable messages; failures never appear as successes
- [ ] No stale or fabricated results displayed; mock data removed from production
- [ ] Responsive at common screen sizes; keyboard and screen-reader basics covered
- [ ] Frontend tests pass (unit, flow, and the demo happy path)
- [ ] Deployed build works on AWS, including deep links
- [ ] `frontend/README.md` documents setup, env vars, and build steps
- [ ] Member 1 can explain the full system, not only the UI

---

## 16. Open Decisions Affecting the Frontend

| Item                                           | Needed from  | Impact                                                     |
| ---------------------------------------------- | ------------ | ---------------------------------------------------------- |
| Sync vs. async assessment creation             | Member 3     | Polling logic and processing UX                            |
| Authentication (yes/no, mechanism)             | Whole team   | Login page, route guards, API auth header, history scoping |
| Defect classes and meaning of `count`        | Member 2     | Labels and table design                                    |
| Bounding boxes in the response?                | Member 2 / 3 | Client overlay vs. pre-rendered annotated image            |
| Max upload size / min dimensions               | Member 3 / 2 | Client validation config                                   |
| Pagination shape                               | Member 3     | History page                                               |
| Image delivery (presigned URL fields, expiry)  | Member 3 / 4 | Image components and refresh logic                         |
| Low-confidence threshold                       | Member 2     | "Review manually" flag                                     |
| Frontend hosting (Amplify vs. S3 + CloudFront) | Member 4     | Build/deploy config only                                   |
| Report export (FR-16)                          | Team         | Optional extra scope                                       |
