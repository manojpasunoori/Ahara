from app.schemas.intent import DiningMode, MealOverride, SpicePreference
from app.services.explicit_facts import ExplicitFactExtractor
from app.services.intent import IntentExtractionService


class FakeProvider:
    name = "fake"

    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls = 0

    def generate_structured(self, system_prompt: str, user_message: str, schema: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        return self.response


def test_explicit_budget_and_pickup() -> None:
    facts = ExplicitFactExtractor().extract("I want biryani pickup under $18.")
    assert facts.dining_mode is DiningMode.pickup
    assert facts.budget_max == 18


def test_explicit_budget_meal_and_distance() -> None:
    facts = ExplicitFactExtractor().extract("Between $15 and $30 for dinner. Within 5 miles, pickup.")
    assert (facts.budget_min, facts.budget_max) == (15, 30)
    assert facts.meal_override is MealOverride.dinner
    assert facts.max_distance_miles == 5
    assert facts.dining_mode is DiningMode.pickup


def test_explicit_terms_do_not_infer_from_home_or_hunger() -> None:
    facts = ExplicitFactExtractor().extract("I'm sitting at home. I'm hungry.")
    assert facts.dining_mode is None
    assert facts.budget_max is None
    assert facts.meal_override is None
    assert facts.dietary_constraints == []


def test_explicit_diet_and_spice() -> None:
    facts = ExplicitFactExtractor().extract("Vegan and very spicy, please.")
    assert facts.dietary_constraints == ["vegan"]
    assert facts.spice_preference is SpicePreference.very_spicy


def test_hybrid_merge_preserves_llm_semantics_and_explicit_constraints() -> None:
    provider = FakeProvider({"food_terms": ["biryani"], "budget_max": None, "dining_mode": "unspecified"})
    intent = IntentExtractionService(provider).extract("I want biryani pickup under $18.")
    assert intent.food_terms == ["biryani"]
    assert intent.dining_mode is DiningMode.pickup
    assert intent.budget_max == 18
    assert provider.calls == 1


def test_explicit_values_override_conflicting_llm_hard_constraints() -> None:
    provider = FakeProvider({"budget_max": 40, "dining_mode": "delivery"})
    intent = IntentExtractionService(provider).extract("Pickup under $18.")
    assert intent.dining_mode is DiningMode.pickup
    assert intent.budget_max == 18