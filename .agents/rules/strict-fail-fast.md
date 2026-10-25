---
trigger: always_on
---

# Strict Zero-Fallback Policy

1. **NEVER write fallback defaults anywhere in code or configuration**:
   - In Docker / Compose / Shell: NEVER use `${VAR:-default}`. Use strict `${VAR}` or `${VAR:?VAR must be set}`.
   - In Python / Pydantic: NEVER supply default values for credentials, hostnames, ports, keys, or database URLs. Do NOT use `os.getenv("KEY", "default")` or `.get("key", default)`. Use `os.environ["KEY"]` or Pydantic fields with no default so missing variables raise immediate exceptions.
   - In Application Logic: Never silently fall back to mock data, stub behavior, or default parameters when external services or configurations are missing.

2. **Fail Fast and Explicitly**:
   - If a setting, service, or dependency is missing, the application or command MUST crash immediately and loudly.
   - In your explanations, state clearly: "This will fail unless you provide X in your .env or environment." Do NOT write code that cushions the failure.
