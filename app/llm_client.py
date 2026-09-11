"""
llm_client.py
-------------
This file is the ONLY place in the project that knows how to actually
talk to an LLM provider (e.g. Anthropic Claude, OpenAI GPT, etc.).

Why isolate this?
    If your team ever switches LLM providers, or if you (the P3 owner)
    get an API key later, you only need to change this one file. The
    rest of the project (extractor.py, prompts.py, validator.py, ...)
    never needs to know which provider is being used.

Two implementations are provided:

1. MockLLMClient
   - Does NOT call any real API.
   - Used for development and for `pytest` so you (and the judges, if
     they ask to see tests run) don't need a paid API key.
   - It does simple, honest, rule-based extraction so tests are
     deterministic and repeatable.

2. RealLLMClient
   - Calls a real LLM API over HTTPS.
   - Configured entirely through environment variables:
       LLM_PROVIDER   e.g. "anthropic" (default) or "openai"
       LLM_API_KEY    your secret key (never hard-coded!)
       LLM_MODEL      e.g. "claude-sonnet-4-6" or "gpt-4o-mini"
   - We default to Anthropic's Claude because this project already
     talks to Claude (Claude built this module!), and Claude has
     strong instruction-following behaviour which matters a lot for
     "never invent missing information" style rules. Swapping to
     another provider only requires editing the `_call_openai` /
     `_call_anthropic` methods below, or adding a new `_call_x`
     method -- the rest of the codebase is unaffected.

Beginner note:
    "Client" here just means "the piece of code responsible for
    sending a request over the internet and getting a reply back."
    It has nothing to do with a customer/client in the business sense.
"""

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Optional

from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.schemas import empty_record


class LLMClient(ABC):
    """Abstract base class. Both the mock and the real client must
    implement `extract_raw`, so extractor.py can use either one
    interchangeably (this is the "configurable LLM provider"
    requirement)."""

    @abstractmethod
    def extract_raw(self, ocr_text: str) -> dict:
        """Return a dict following the fixed schema (see schemas.py).
        Implementations must NEVER raise on malformed model output --
        they should catch parsing errors internally and fall back to
        `empty_record()` so the rest of the pipeline stays robust.
        """
        raise NotImplementedError


class MockLLMClient(LLMClient):
    """A deterministic, fake "LLM" used for local development and
    automated tests.

    It does NOT use any AI model. It uses simple label-matching
    (regular expressions) to pull values out of the text, similar to
    what a real LLM would do for these fairly explicit "Label: Value"
    style OCR lines. Because it's deterministic, our tests always
    produce the same result, which is exactly what we want for
    `pytest`.

    IMPORTANT: This is a stand-in for development only. It is
    intentionally simple. The real intelligence (handling messy
    phrasing, creative Hindi/English mixes, heavy OCR noise) is meant
    to come from RealLLMClient in production.
    """

    # label -> field name, plus the regex fragment used to spot the label.
    _LABELS = {
        "owner_name": [
            r"owner\s*name", r"0wner\s*na[mn]e", r"owner", r"name",
            r"खातेदार", r"नाम",
        ],
        "khasra_number": [
            r"khasra\s*no\.?", r"khasra\s*number", r"khasra\s*n[0o]",
            r"खसरा\s*नंबर", r"खसरा\s*नं",
        ],
        "area": [
            r"area", r"arca", r"क्षेत्रफल", r"रकबा",
        ],
        "village": [
            r"village", r"vilage", r"ग्राम", r"गांव",
        ],
        "tehsil": [
            r"tehsil", r"तहसील",
        ],
        "district": [
            r"district", r"जिला",
        ],
        "land_use": [
            r"land\s*use", r"भू[- ]?उपयोग",
        ],
    }

    _UNIT_WORDS = [
        "hectares", "hectare", "hectar", "ha", "acres", "acre",
        "बीघा", "हेक्टेयर", "एकड़",
    ]

    def extract_raw(self, ocr_text: str) -> dict:
        result = empty_record()
        lines = ocr_text.splitlines()

        for line in lines:
            field = self._match_field(line)
            if field is None:
                continue
            value = self._value_after_label(line, field)
            if not value:
                continue

            if field == "area":
                number, unit = self._split_area(value)
                if number is not None:
                    result["area"] = number
                if unit is not None:
                    result["area_unit"] = unit
            else:
                result[field] = value.strip()

        return result

    def _match_field(self, line: str) -> Optional[str]:
        for field, patterns in self._LABELS.items():
            for pat in patterns:
                if re.search(pat, line, flags=re.IGNORECASE):
                    return field
        return None

    def _value_after_label(self, line: str, field: str) -> Optional[str]:
        # Split on the first ":" — labels in our sample OCR are
        # formatted as "Label: value".
        if ":" not in line:
            return None
        _, _, rest = line.partition(":")
        return rest.strip() or None

    def _split_area(self, value: str):
        # Pull out the first number in the string, and separately
        # look for a known unit word.
        number = None
        match = re.search(r"-?\d+(\.\d+)?", value)
        if match:
            try:
                candidate = float(match.group())
                if candidate >= 0:
                    number = candidate
            except ValueError:
                number = None

        unit = None
        lowered = value.lower()
        for word in self._UNIT_WORDS:
            if word.lower() in lowered or word in value:
                unit = self._normalise_unit(word)
                break
        return number, unit

    @staticmethod
    def _normalise_unit(word: str) -> str:
        from app.schemas import KNOWN_AREA_UNITS
        return KNOWN_AREA_UNITS.get(word.lower(), KNOWN_AREA_UNITS.get(word, word))


class RealLLMClient(LLMClient):
    """Calls a real LLM over HTTPS. Configured via environment
    variables so no secrets are ever hard-coded in source code:

        LLM_PROVIDER = "anthropic" (default) | "openai"
        LLM_API_KEY  = your secret API key
        LLM_MODEL    = model name, e.g. "claude-sonnet-4-6"

    If LLM_API_KEY is not set, this class raises a clear error when
    you try to use it -- it will never silently pretend to call a
    real model.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = provider or os.environ.get("LLM_PROVIDER", "anthropic")
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL", "claude-sonnet-4-6")

        if not self.api_key:
            raise RuntimeError(
                "RealLLMClient requires LLM_API_KEY to be set as an "
                "environment variable (see .env.example). Use "
                "MockLLMClient for local development/testing without "
                "an API key."
            )

    def extract_raw(self, ocr_text: str) -> dict:
        if self.provider == "anthropic":
            raw_text = self._call_anthropic(ocr_text)
        elif self.provider == "openai":
            raw_text = self._call_openai(ocr_text)
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")

        return self._safe_parse_json(raw_text)

    def _call_anthropic(self, ocr_text: str) -> str:
        import requests  # imported lazily so MockLLMClient users
        # don't need `requests` installed just to run tests.

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 1000,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": build_user_prompt(ocr_text)}
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        return "".join(parts)

    def _call_openai(self, ocr_text: str) -> str:
        import requests

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(ocr_text)},
                ],
                "temperature": 0,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _safe_parse_json(raw_text: str) -> dict:
        """LLMs sometimes wrap JSON in ```json fences or add stray
        whitespace. Clean that up, and if parsing still fails, fall
        back to an all-null record rather than crashing the pipeline.
        """
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return empty_record()


def get_llm_client() -> LLMClient:
    """Factory function: decides which LLM client to hand back based
    on environment configuration.

    - If LLM_API_KEY is set -> use the real client.
    - Otherwise -> fall back to the mock client, so the module never
      crashes just because no API key is configured yet.
    """
    if os.environ.get("LLM_API_KEY"):
        return RealLLMClient()
    return MockLLMClient()
