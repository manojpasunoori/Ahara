from __future__ import annotations

import logging
import time

from pydantic import ValidationError

from app.providers.llm import LLMProvider, LLMProviderResponseError
from app.schemas.intent import FoodIntent
from app.services.explicit_facts import ExplicitFactExtractor, ExplicitFacts
from app.services.intent_prompt import INTENT_EXTRACTION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class IntentExtractionService:
    def __init__(self, provider: LLMProvider, explicit_fact_extractor: ExplicitFactExtractor | None = None) -> None:
        self._provider = provider
        self._explicit_fact_extractor = explicit_fact_extractor or ExplicitFactExtractor()

    def extract(self, message: str) -> FoodIntent:
        started = time.perf_counter()
        facts = self._explicit_fact_extractor.extract(message)
        schema = FoodIntent.model_json_schema()
        for attempt in range(2):
            try:
                llm_intent = FoodIntent.model_validate(
                    self._provider.generate_structured(INTENT_EXTRACTION_SYSTEM_PROMPT, message, schema)
                )
                break
            except ValidationError as error:
                if attempt:
                    raise LLMProviderResponseError("The model returned an invalid intent object.") from error
        else:
            raise LLMProviderResponseError("The model returned an invalid intent object.")
        intent = self._merge(llm_intent, facts)
        logger.info(
            "intent extraction succeeded provider=%s elapsed_ms=%d",
            self._provider.name,
            (time.perf_counter() - started) * 1000,
        )
        return intent

    def _merge(self, llm_intent: FoodIntent, facts: ExplicitFacts) -> FoodIntent:
        merged = llm_intent.model_dump()
        if facts.budget_min is None and facts.budget_max is None:
            merged["budget_min"] = None
            merged["budget_max"] = None
        for field in ("budget_min", "budget_max", "dining_mode", "meal_override", "max_distance_miles", "spice_preference"):
            value = getattr(facts, field)
            if value is not None:
                if merged[field] not in (None, "unspecified") and merged[field] != value:
                    logger.warning("explicit intent fact overrides model field=%s", field)
                merged[field] = value
        if facts.dietary_constraints:
            merged["dietary_constraints"] = list(dict.fromkeys([*llm_intent.dietary_constraints, *facts.dietary_constraints]))
        return FoodIntent.model_validate(merged)