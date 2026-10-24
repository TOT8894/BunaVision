"""Gemini implementation of the `AdvisoryGenerator` port.

Uses Gemini's structured output (`response_schema`) so the reply is shaped by the API, then
validates it again here. Any failure is an explicit `DependencyError`: there is no offline or
canned advisory, because a made-up advisory would look like a real one.

SDK behaviour relied on (checked against google-genai 2.32.0 by the previous session's
introspection, not re-checked here): `client.aio.models.generate_content` is a coroutine,
`GenerateContentConfig` accepts `system_instruction`, `response_mime_type`, `response_schema`,
`temperature`, `max_output_tokens` and `http_options`, errors derive from
`google.genai.errors.APIError`, and `response.text` is None when there is no text.
"""

import asyncio
import re

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.adapters.gemini.prompts import (
    MAX_RECOMMENDATIONS,
    SYSTEM_INSTRUCTION,
    AdvisoryPayload,
    BilingualPayload,
    render_facts,
)
from app.domain.errors import AdvisoryInvalidError, AdvisoryUnavailableError
from app.domain.models import Advisory, BilingualText
from app.services.ports import AdvisoryFacts

_ETHIOPIC = re.compile(r"[\u1200-\u137f]")
_LATIN = re.compile(r"[A-Za-z]")
_MAX_TEXT_CHARS = 1200


class GeminiAdvisoryGenerator:
    def __init__(
        self,
        *,
        client: genai.Client,
        model: str,
        temperature: float,
        timeout_s: float,
        max_output_tokens: int,
    ) -> None:
        self._client = client
        self._model = model
        self._timeout_s = timeout_s
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=AdvisoryPayload,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),  # milliseconds
        )

    async def generate(self, facts: AdvisoryFacts) -> Advisory:
        try:
            # The outer timeout is the authority; the SDK's own timeout is a second layer.
            async with asyncio.timeout(self._timeout_s):
                response = await self._client.aio.models.generate_content(
                    model=self._model, contents=render_facts(facts), config=self._config
                )
        except TimeoutError as exc:
            raise AdvisoryUnavailableError(f"Gemini timed out after {self._timeout_s}s") from exc
        except genai_errors.APIError as exc:
            raise AdvisoryUnavailableError(f"Gemini API error {exc.code}: {exc}") from exc
        except httpx.HTTPError as exc:
            raise AdvisoryUnavailableError(f"Gemini transport error: {exc!r}") from exc

        return self._to_advisory(response.text)

    def _to_advisory(self, text: str | None) -> Advisory:
        if not text:
            raise AdvisoryInvalidError("Gemini returned no text (blocked, empty or truncated)")
        try:
            payload = AdvisoryPayload.model_validate_json(text)
        except ValidationError as exc:
            raise AdvisoryInvalidError(f"Gemini reply did not match the schema: {exc}") from exc

        if not 1 <= len(payload.recommendations) <= MAX_RECOMMENDATIONS:
            raise AdvisoryInvalidError(
                f"expected 1-{MAX_RECOMMENDATIONS} recommendations, got {len(payload.recommendations)}"
            )
        return Advisory(
            generator_model=self._model,
            summary=_checked(payload.summary),
            recommendations=tuple(_checked(item) for item in payload.recommendations),
        )


def _checked(text: BilingualPayload) -> BilingualText:
    """Reject empty, over-long, or wrong-script text (e.g. Amharic written in Latin letters)."""
    en, am = text.en.strip(), text.am.strip()
    if not en or not am:
        raise AdvisoryInvalidError("advisory text was empty in one language")
    if len(en) > _MAX_TEXT_CHARS or len(am) > _MAX_TEXT_CHARS:
        raise AdvisoryInvalidError("advisory text exceeded the length limit")
    if not _LATIN.search(en):
        raise AdvisoryInvalidError("English text contained no Latin letters")
    if not _ETHIOPIC.search(am):
        raise AdvisoryInvalidError("Amharic text contained no Ethiopic characters")
    return BilingualText(en=en, am=am)
