# Frontend (React / TypeScript / Tailwind)

Also follow the root `AGENTS.md`. This file adds frontend-specific guidance.

The frontend lets users upload a sample photo, shows processing status, and presents reports and history clearly and honestly. Users are often on phones and may have slow connections.

## Contract with the backend

- The backend API contract (OpenAPI / Pydantic models in `contracts/backend-api/`) is the source of truth for types. **Generate or centrally derive TypeScript types from it.** Never hand-copy the same shape in several places.
- All network calls go through **one API layer** (`src/api/`). Components never call `fetch` directly.
- Validate API responses at that boundary, because data can drift from the contract. An unexpected shape is an error state, not something to paper over.
- Never invent endpoints or fields. If something is missing, flag it to the backend owner.
- While the backend is not ready, mock from the contract (`src/mocks/`). Mocks must match the contract and be clearly marked as mocks. Never present mock data as a real result.

## Honest UI

- Present results as **preliminary AI predictions**. Label confidence as model confidence, show what each count measures, include the limitations notice, and flag low-confidence results for manual review. **Never show a definitive grade** (the model only detects 3 defect classes).
- Never display missing data as `0` or as an empty success. "No defects detected" and "analysis failed" must look different.
- Never show stale results, or results from another sample, as if they belong to the current image.

## State and structure

- Model the user flow as explicit states (idle, file selected, uploading, processing, success, validation error, inference failure, network failure, empty history). Use discriminated unions so impossible combinations cannot exist.
- Keep server state (fetched data, caching) separate from local UI state. Use the project's chosen data-fetching approach consistently.
- Small, focused components in `src/components/`. Put logic in hooks and services. **Group code by feature** in `src/features/` (home, upload, assessment, history, auth). Keep shared constants, types, and strings in one place (`src/strings/` for all user-facing text, EN/AM later).
- Strict TypeScript: no `any`, and no unchecked assertions or `!` just to silence the compiler. Narrow `unknown` data at the boundary.

## UX and quality

- Handle every error code defined in the contract with an actionable message. No silent catches. Every async view has loading, error, and empty states.
- Client-side checks (file type, size) are a convenience only. The backend is the authority.
- Mobile-first and responsive. Accessible: labels, keyboard use, focus, contrast, alt text. Keep user-facing text centralized so translation (Amharic) can be added later.
- Do not resize or compress images on the client unless the vision and backend owners confirm it will not hurt detection quality (small defects are easy to lose).
- Release preview resources (for example revoke object URLs).
- Tailwind: reuse through components and shared tokens rather than copy-pasting long class strings.

## Testing

- Test user-visible behavior and every UI state. Test the API layer against contract-shaped fixtures.
- Run the project's type-check, lint, test, and build commands before declaring done.
