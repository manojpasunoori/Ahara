from pydantic import ValidationError
import pytest
from app.schemas.profile import OnboardingRequest

BASE = {"display_name":"Test", "email":"test@example.com", "diet_type":"omnivore", "spice_tolerance":3, "adventurousness":3, "usual_budget_min":10, "usual_budget_max":20, "usual_travel_radius_miles":5, "dining_preferences":["delivery"], "cuisine_preferences":[{"name":"Thai","preference_level":4}], "comfort_foods":["Ramen"], "allergies":[]}

def test_valid_onboarding_payload() -> None:
    assert OnboardingRequest(**BASE).spice_tolerance == 3

@pytest.mark.parametrize("field,value", [("spice_tolerance", 6), ("adventurousness", 0), ("usual_travel_radius_miles", -1), ("email", "invalid")])
def test_invalid_profile_fields(field: str, value: object) -> None:
    payload = BASE | {field: value}
    with pytest.raises(ValidationError): OnboardingRequest(**payload)

def test_invalid_budget_range() -> None:
    with pytest.raises(ValidationError): OnboardingRequest(**(BASE | {"usual_budget_min": 30, "usual_budget_max": 20}))

def test_duplicate_cuisine_is_rejected() -> None:
    with pytest.raises(ValidationError): OnboardingRequest(**(BASE | {"cuisine_preferences": [{"name":"Thai","preference_level":4},{"name":"thai","preference_level":3}]}))

def test_duplicate_comfort_food_is_rejected() -> None:
    with pytest.raises(ValidationError): OnboardingRequest(**(BASE | {"comfort_foods": ["Ramen", "ramen"]}))