"""GeminiService — thin wrapper over the unified google-genai SDK on Vertex AI.

Per Phase 0 spec:
  - Gemini 2.5 Pro for reasoning + multimodal PDF parsing.
  - Gemini 2.5 Flash for cheap routing.
  - All structured outputs go through response_mime_type="application/json" +
    response_schema (a Pydantic model class — the SDK converts it).
  - safety_settings BLOCK_NONE for HARASSMENT and HATE_SPEECH (bid docs carry
    legal/contractual language Gemini sometimes over-blocks).
  - temperature 0.1 default (consistency > creativity for evaluators).
  - Vertex occasionally returns 503/429 — retry with exponential backoff + jitter.

`parts` is a flat list mixing strings and PIL.Image.Image objects, e.g. the
interleaved [Image, "PAGE 1", Image, "PAGE 2", ...] pattern. The SDK accepts
PIL images and strings directly in `contents`.
"""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Any, Sequence

from google import genai
from google.genai import types

logger = logging.getLogger("tenderiq.gemini")

# HTTP status codes worth retrying on Vertex.
_RETRYABLE = {429, 500, 502, 503, 504}


class GeminiService:
    def __init__(
        self,
        project: str | None = None,
        location: str | None = None,
        pro_location: str | None = None,
        pro_model: str | None = None,
        flash_model: str | None = None,
    ) -> None:
        self.project = project or os.environ["GCP_PROJECT_ID"]
        # Flash is served in asia-south1 (Mumbai); 2.5 Pro is NOT — it lives on
        # us-central1 / global. So Pro uses its own location (default "global").
        self.location = location or os.environ.get("GCP_LOCATION", "asia-south1")
        self.pro_location = pro_location or os.environ.get("GEMINI_PRO_LOCATION", "global")
        self.pro_model = pro_model or os.environ.get("GEMINI_PRO_MODEL", "gemini-2.5-pro")
        self.flash_model = flash_model or os.environ.get("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
        # vertexai=True -> Application Default Credentials (GOOGLE_APPLICATION_CREDENTIALS).
        self.flash_client = genai.Client(
            vertexai=True, project=self.project, location=self.location
        )
        self.pro_client = (
            self.flash_client
            if self.pro_location == self.location
            else genai.Client(vertexai=True, project=self.project, location=self.pro_location)
        )

    @staticmethod
    def _safety_settings() -> list[types.SafetySetting]:
        return [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

    def _generate(
        self,
        client: "genai.Client",
        model: str,
        parts: Sequence[Any],
        schema: Any,
        temperature: float,
        max_retries: int = 4,
    ):
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
            safety_settings=self._safety_settings(),
        )

        attempt = 0
        while True:
            try:
                return client.models.generate_content(
                    model=model, contents=list(parts), config=config
                )
            except genai.errors.APIError as e:
                code = getattr(e, "code", None)
                if code in _RETRYABLE and attempt < max_retries:
                    delay = min(2**attempt + random.random(), 30.0)
                    logger.warning(
                        "Vertex %s on %s (attempt %d/%d); retrying in %.1fs",
                        code, model, attempt + 1, max_retries, delay,
                    )
                    time.sleep(delay)
                    attempt += 1
                    continue
                raise

    def generate_pro(self, parts: Sequence[Any], schema: Any, temperature: float = 0.1):
        """Reasoning + multimodal PDF parsing. Returns the raw SDK response.

        Use `response.parsed` for the Pydantic instance, `response.text` for raw JSON.
        """
        return self._generate(self.pro_client, self.pro_model, parts, schema, temperature)

    def generate_flash(self, parts: Sequence[Any], schema: Any, temperature: float = 0.1):
        """Cheap routing / classification. Returns the raw SDK response."""
        return self._generate(self.flash_client, self.flash_model, parts, schema, temperature)
