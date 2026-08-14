from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.intent import DiningMode, MealOverride, SpicePreference


@dataclass(frozen=True)
class ExplicitFacts:
    budget_min: float | None = None
    budget_max: float | None = None
    dining_mode: DiningMode | None = None
    meal_override: MealOverride | None = None
    max_distance_miles: float | None = None
    dietary_constraints: list[str] = field(default_factory=list)
    spice_preference: SpicePreference | None = None


class ExplicitFactExtractor:
    """Extract only unambiguous, directly stated hard constraints."""

    _BETWEEN_BUDGET = re.compile(r"\bbetween\s+\$?(\d+(?:\.\d+)?)\s+(?:and|to)\s+\$?(\d+(?:\.\d+)?)", re.I)
    _MAX_BUDGET = re.compile(r"\b(?:under|below|less than)\s+\$?(\d+(?:\.\d+)?)(?:\s+dollars?)?", re.I)
    _MAX_DISTANCE = re.compile(r"\b(?:within|under|no more than)\s+(\d+(?:\.\d+)?)\s+miles?\b", re.I)

    def extract(self, message: str) -> ExplicitFacts:
        text = message.casefold()
        budget_min, budget_max = self._budget(text)
        return ExplicitFacts(
            budget_min=budget_min,
            budget_max=budget_max,
            dining_mode=self._dining_mode(text),
            meal_override=self._meal(text),
            max_distance_miles=self._distance(text),
            dietary_constraints=[term for term in ("vegetarian", "vegan", "pescatarian", "halal") if re.search(rf"\b{term}\b", text)],
            spice_preference=self._spice(text),
        )

    def _budget(self, text: str) -> tuple[float | None, float | None]:
        if match := self._BETWEEN_BUDGET.search(text):
            return float(match.group(1)), float(match.group(2))
        if match := self._MAX_BUDGET.search(text):
            return None, float(match.group(1))
        return None, None

    def _dining_mode(self, text: str) -> DiningMode | None:
        if re.search(r"\b(?:delivery|delivered|deliver it)\b", text):
            return DiningMode.delivery
        if re.search(r"\b(?:pickup|pick up|takeout)\b", text):
            return DiningMode.pickup
        if re.search(r"\b(?:dine[ -]?in|eat there)\b", text):
            return DiningMode.dine_in
        return None

    def _meal(self, text: str) -> MealOverride | None:
        for phrase, value in (("late-night", MealOverride.late_night), ("late night", MealOverride.late_night), ("breakfast", MealOverride.breakfast), ("lunch", MealOverride.lunch), ("snacks", MealOverride.snacks), ("dinner", MealOverride.dinner)):
            if re.search(rf"\b{re.escape(phrase)}\b", text):
                return value
        return None

    def _distance(self, text: str) -> float | None:
        match = self._MAX_DISTANCE.search(text)
        return float(match.group(1)) if match else None

    def _spice(self, text: str) -> SpicePreference | None:
        if "very spicy" in text:
            return SpicePreference.very_spicy
        if re.search(r"\bspicy\b", text):
            return SpicePreference.spicy
        if re.search(r"\bmedium spicy\b", text):
            return SpicePreference.medium
        if re.search(r"\bmild\b", text):
            return SpicePreference.mild
        return None