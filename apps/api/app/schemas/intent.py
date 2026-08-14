from __future__ import annotations
from enum import StrEnum
from pydantic import BaseModel, Field, ValidationInfo, field_validator
class Mood(StrEnum): stressed="stressed"; relaxed="relaxed"; happy="happy"; tired="tired"; social="social"; romantic="romantic"; neutral="neutral"; unknown="unknown"
class SpicePreference(StrEnum): mild="mild"; medium="medium"; spicy="spicy"; very_spicy="very_spicy"; unspecified="unspecified"
class DistancePreference(StrEnum): very_near="very_near"; nearby="nearby"; normal="normal"; willing_to_drive="willing_to_drive"; unspecified="unspecified"
class DiningMode(StrEnum): delivery="delivery"; pickup="pickup"; dine_in="dine_in"; unspecified="unspecified"
class MealOverride(StrEnum): breakfast="breakfast"; lunch="lunch"; snacks="snacks"; dinner="dinner"; late_night="late_night"; unspecified="unspecified"
class Occasion(StrEnum): comfort_meal="comfort_meal"; date="date"; group_outing="group_outing"; netflix="netflix"; quick_meal="quick_meal"; work_break="work_break"; celebration="celebration"; casual="casual"; unknown="unknown"
class FoodIntent(BaseModel):
    mood: Mood = Field(default=Mood.unknown, description="Explicit mood only; otherwise unknown.")
    cuisines: list[str] = Field(default_factory=list, description="Cuisine names only, for example Thai or South Indian.")
    food_terms: list[str] = Field(default_factory=list, description="Dish or ingredient terms only, for example biryani or ramen.")
    spice_preference: SpicePreference = Field(default=SpicePreference.unspecified)
    budget_min: float | None = Field(default=None, ge=0, description="Explicit numeric lower budget only.")
    budget_max: float | None = Field(default=None, ge=0, description="Explicit numeric upper budget. For under/below/less than $N, this MUST be N; never leave $N only in free_text_constraints.")
    distance_preference: DistancePreference = Field(default=DistancePreference.unspecified)
    max_distance_miles: float | None = Field(default=None, gt=0, description="Explicit maximum travel distance in miles only.")
    dining_mode: DiningMode = Field(default=DiningMode.unspecified)
    meal_override: MealOverride = Field(default=MealOverride.unspecified, description="Only explicitly named meal period.")
    occasion: Occasion = Field(default=Occasion.unknown)
    adventurousness_signal: int | None = Field(default=None, ge=1, le=5)
    dietary_constraints: list[str] = Field(default_factory=list, description="Only explicit dietary restrictions.")
    free_text_constraints: list[str] = Field(default_factory=list)
    @field_validator("budget_max")
    @classmethod
    def budget_range_is_valid(cls, budget_max: float | None, info: ValidationInfo) -> float | None:
        budget_min = info.data.get("budget_min")
        if budget_min is not None and budget_max is not None and budget_max < budget_min: raise ValueError("budget_max cannot be below budget_min")
        return budget_max
class IntentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, message: str) -> str:
        if not message.strip(): raise ValueError("message must not be blank")
        return message.strip()