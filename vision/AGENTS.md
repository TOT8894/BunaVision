# Vision / AI (Python)

Also follow the root `AGENTS.md`. This file adds vision-specific guidance.

This subsystem turns a green coffee bean image into structured, honest predictions. The model framework is the vision owner's choice, so read the code and docs to see what is in use. The **inference HTTP API is the product** the backend depends on.

> Naming: this folder is `vision/` (not `ai/`). "AI" also describes the Gemini work that lives in the **backend**, so we reserve "vision" for defect detection to avoid confusion.

## Structure: library vs. service (keep them separate)

- **`vision/core/`** — a pure Python library: inference, NMS, annotation, the class/label map, and the detection schemas. **No web framework here.** It must be importable and testable on a laptop with no server running.
- **`vision/service/`** — a *thin* FastAPI wrapper over `core/`. It only receives image bytes, calls `core`, and returns the structured result. **No detection logic in the service layer.**
- `vision/model/` — `classes.json`, model card, model metadata. Model **weights do not live in plain git** (use Git LFS or S3 — see `docs/`).
- `vision/training/` — notebooks and training scripts.
- `vision/evaluation/` — evaluation harness and golden images.
- `vision/tests/` — tests, including golden-image regression tests.

This core/service split resolves the old "no FastAPI in vision" concern: the library stays web-free and portable, and the service is just a deployable skin over it.

## The inference contract

- Expose **one stable, typed entry point**: image bytes in, structured result out (including the model version). Everything behind it is internal and can change freely. The backend depends only on this interface, published as `contracts/vision-api/`.
- Document and keep stable: the output schema, class names, confidence range, coordinate format and units (pixel vs normalized, box convention), and exactly what is counted. Any change affects the backend, so announce it and update `contracts/vision-api/` in the same change.
- Define the class/label map once and use it in training, evaluation, and inference. Do the same for preprocessing settings, so training and serving never drift.

## Honesty and safety (vision-specific)

- **No silent mock mode.** If model weights are missing or fail to load, the service must **fail at startup**, not serve fabricated/demo detections. The legacy `_fallback_demo` path was eliminated; fail-loud is enforced across core engines, reload, and FastAPI lifespan startup.
- "Zero detections" is a valid, real result and must be distinguishable from "inference failed".
- Report only the classes the model truly supports. Never imply coverage of defect classes the model was not trained on.
- Vision never receives or needs AWS credentials, user data, S3 keys, or Gemini keys. It gets image bytes and returns detections.

## Testing

- Unit-test `core/` directly (no server). Golden-image tests for regression. Test the `service/` layer against the published contract shape.
- Run the project's type-check, lint, and test commands before declaring done. Pin dependency versions.
