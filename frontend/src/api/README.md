# API boundary

All frontend network access belongs in this directory. Components must not call `fetch` directly.

The backend OpenAPI document at `../../contracts/backend-api/openapi.json` is the contract source of truth. Generate types into this directory before adding API calls:

```powershell
npx openapi-typescript ../contracts/backend-api/openapi.json -o src/api/types.d.ts
```

Validate successful responses at this boundary before they reach UI components. The current contract supports synchronous creation, cursor-paginated history, and completed or failed assessments.
