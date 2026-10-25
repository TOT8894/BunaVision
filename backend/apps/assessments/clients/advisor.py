"""Gemini advisory writer (sync). Structured output, validated again on our side.

Any failure is an explicit `AdvisoryFailed`: there is no offline or canned advisory, because a
made-up advisory would look like a real one. The SDK's own HTTP timeout is the only per-call
bound here (gunicorn's worker timeout is the backstop). SDK names and units (timeout in
milliseconds) were checked against google-genai 2.32.0 by an earlier session, not re-checked.
"""

import re
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

import httpx
from django.conf import settings
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from apps.assessments.clients.prompts import (
    MAX_RECOMMENDATIONS,
    SYSTEM_INSTRUCTION,
    AdvisoryPayload,
    BilingualPayload,
    render_facts,
)
from apps.assessments.taxonomy import DefectClass
from apps.common.errors import AdvisoryFailed

_ETHIOPIC = re.compile(r"[\u1200-\u137f]")
_LATIN = re.compile(r"[A-Za-z]")
_MAX_TEXT_CHARS = 1200


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """One shared client. Tests patch this function."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate(
    summary: dict[str, Any], scanned: Sequence[DefectClass], not_scanned: Sequence[DefectClass]
) -> dict[str, Any]:
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=AdvisoryPayload,
        temperature=settings.GEMINI_TEMPERATURE,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
        http_options=types.HttpOptions(timeout=int(settings.GEMINI_TIMEOUT_S * 1000)),
    )
    try:
        response = get_client().models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=render_facts(summary, scanned, not_scanned),
            config=config,
        )
    except genai_errors.APIError as exc:
        raise AdvisoryFailed(f"Gemini API error {exc.code}: {exc}") from exc
    except httpx.HTTPError as exc:
        raise AdvisoryFailed(f"Gemini transport error: {exc!r}") from exc
    return _checked(response.text)


def _checked(text: str | None) -> dict[str, Any]:
    if not text:
        raise AdvisoryFailed("Gemini returned no text (blocked, empty or truncated)")
    try:
        payload = AdvisoryPayload.model_validate_json(text)
    except ValidationError as exc:
        raise AdvisoryFailed(f"Gemini reply did not match the schema: {exc}") from exc
    if not 1 <= len(payload.recommendations) <= MAX_RECOMMENDATIONS:
        raise AdvisoryFailed(f"expected 1-{MAX_RECOMMENDATIONS} recommendations, got {len(payload.recommendations)}")
    return {
        "generator_model": settings.GEMINI_MODEL,
        "summary": _bilingual(payload.summary),
        "recommendations": [_bilingual(item) for item in payload.recommendations],
    }


def _bilingual(text: BilingualPayload) -> dict[str, str]:
    """Reject empty, over-long, or wrong-script text (e.g. Amharic written in Latin letters)."""
    en, am = text.en.strip(), text.am.strip()
    if not en or not am:
        raise AdvisoryFailed("advisory text was empty in one language")
    if len(en) > _MAX_TEXT_CHARS or len(am) > _MAX_TEXT_CHARS:
        raise AdvisoryFailed("advisory text exceeded the length limit")
    if not _LATIN.search(en):
        raise AdvisoryFailed("English text contained no Latin letters")
    if not _ETHIOPIC.search(am):
        raise AdvisoryFailed("Amharic text contained no Ethiopic characters")
    return {"en": en, "am": am}
