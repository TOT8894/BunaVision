import asyncio
import json
import unittest
from types import SimpleNamespace

from google.genai import errors as genai_errors

from app.adapters.gemini.advisor import GeminiAdvisoryGenerator
from app.adapters.gemini.prompts import render_facts
from app.domain.analysis import build_coverage, summarize
from app.domain.errors import AdvisoryInvalidError, AdvisoryUnavailableError
from app.domain.models import BoundingBox, Detection
from app.domain.taxonomy import ECX_TAXONOMY
from app.services.ports import AdvisoryFacts

FACTS = AdvisoryFacts(
    model_version="v1",
    summary=summarize(
        [Detection(ECX_TAXONOMY.from_vision_label("Full Black"), 0.9, BoundingBox(0, 0, 1, 1))]
    ),
    coverage=build_coverage(ECX_TAXONOMY),
)


def reply(**overrides: object) -> str:
    payload = {
        "summary": {"en": "One primary defect was detected.", "am": "አንድ ዋና ጉድለት ተገኝቷል።"},
        "recommendations": [{"en": "Verify manually.", "am": "በእጅ ያረጋግጡ።"}],
    }
    payload.update(overrides)
    return json.dumps(payload, ensure_ascii=False)


class FakeClient:
    """Stands in for genai.Client: only `aio.models.generate_content` is used."""

    def __init__(self, *, text: str | None = None, error: Exception | None = None, delay: float = 0) -> None:
        self.calls: list[dict] = []

        async def generate_content(**kwargs: object) -> SimpleNamespace:
            self.calls.append(kwargs)
            if delay:
                await asyncio.sleep(delay)
            if error is not None:
                raise error
            return SimpleNamespace(text=text)

        self.aio = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))


def generator(client: FakeClient, timeout_s: float = 5) -> GeminiAdvisoryGenerator:
    return GeminiAdvisoryGenerator(
        client=client, model="m-1", temperature=0.2, timeout_s=timeout_s, max_output_tokens=1024  # type: ignore[arg-type]
    )


class AdvisorTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_reply_becomes_an_advisory_that_names_its_model(self) -> None:
        client = FakeClient(text=reply())
        advisory = await generator(client).generate(FACTS)
        self.assertEqual(advisory.generator_model, "m-1")
        self.assertEqual(len(advisory.recommendations), 1)
        sent = client.calls[0]
        self.assertEqual(sent["model"], "m-1")
        self.assertEqual(sent["contents"], render_facts(FACTS))
        self.assertEqual(sent["config"].response_mime_type, "application/json")

    async def test_unusable_replies_are_rejected(self) -> None:
        bad = {
            "no text": None,
            "not json": "sorry",
            "wrong shape": json.dumps({"summary": "x"}),
            "no recommendations": reply(recommendations=[]),
            "too many": reply(recommendations=[{"en": "a", "am": "አ"}] * 5),
            "amharic in latin letters": reply(summary={"en": "Fine.", "am": "Meche new"}),
            "empty english": reply(summary={"en": " ", "am": "አ"}),
        }
        for name, text in bad.items():
            with self.subTest(name), self.assertRaises(AdvisoryInvalidError):
                await generator(FakeClient(text=text)).generate(FACTS)

    async def test_api_error_and_timeout_are_unavailable_not_invalid(self) -> None:
        api_error = genai_errors.APIError(429, {"error": {"message": "quota"}})
        with self.assertRaises(AdvisoryUnavailableError):
            await generator(FakeClient(error=api_error)).generate(FACTS)
        with self.assertRaises(AdvisoryUnavailableError):
            await generator(FakeClient(text=reply(), delay=1), timeout_s=0.05).generate(FACTS)


class PromptFactsTests(unittest.TestCase):
    def test_facts_contain_only_derived_data(self) -> None:
        text = render_facts(FACTS)
        self.assertIn('"defect_detections_total": 1', text)
        self.assertIn("Full Black", text)
        self.assertIn("Floater / Chalky", text)  # listed as not scanned


if __name__ == "__main__":
    unittest.main()
