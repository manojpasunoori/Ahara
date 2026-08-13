import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.profile import DietType

PreferenceScore = Annotated[int, Field(ge=1, le=5)]
PositiveMoney = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
PositiveDistance = Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]
DiningPreference = Literal["delivery", "pickup", "dine_in"]

class CuisinePreferenceInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    preference_level: PreferenceScore

class AllergyInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)

class ProfileInput(BaseModel):
    diet_type: DietType = DietType.OMNIVORE
    spice_tolerance: PreferenceScore
    adventurousness: PreferenceScore
    usual_budget_min: PositiveMoney
    usual_budget_max: PositiveMoney
    usual_travel_radius_miles: PositiveDistance
    dining_preferences: list[DiningPreference] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_budget_range(self) -> "ProfileInput":
        if self.usual_budget_max < self.usual_budget_min:
            raise ValueError("usual_budget_max cannot be below usual_budget_min")
        if len(set(self.dining_preferences)) != len(self.dining_preferences):
            raise ValueError("dining_preferences must not contain duplicates")
        return self

class OnboardingRequest(ProfileInput):
    display_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state_or_region: str | None = Field(default=None, max_length=100)
    cuisine_preferences: list[CuisinePreferenceInput] = Field(default_factory=list)
    comfort_foods: list[str] = Field(default_factory=list)
    allergies: list[AllergyInput] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if value.count("@") != 1 or value.startswith("@") or value.endswith("@") or "." not in value.rsplit("@", 1)[1]:
            raise ValueError("email must be valid")
        return value.lower()

    @model_validator(mode="after")
    def reject_duplicates(self) -> "OnboardingRequest":
        cuisine_names = [item.name.casefold().strip() for item in self.cuisine_preferences]
        comfort_names = [item.casefold().strip() for item in self.comfort_foods]
        allergy_names = [item.name.casefold().strip() for item in self.allergies]
        if len(cuisine_names) != len(set(cuisine_names)):
            raise ValueError("cuisine_preferences must not contain duplicate names")
        if len(comfort_names) != len(set(comfort_names)):
            raise ValueError("comfort_foods must not contain duplicates")
        if len(allergy_names) != len(set(allergy_names)):
            raise ValueError("allergies must not contain duplicate names")
        return self

class FoodProfileUpdate(ProfileInput):
    pass

class CuisineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str

class CuisinePreferenceResponse(BaseModel):
    name: str
    preference_level: int

class AllergyResponse(BaseModel):
    name: str
    notes: str | None

class FoodProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    diet_type: DietType
    spice_tolerance: int
    adventurousness: int
    usual_budget_min: Decimal
    usual_budget_max: Decimal
    usual_travel_radius_miles: Decimal
    dining_preferences: list[DiningPreference]
    cuisine_preferences: list[CuisinePreferenceResponse]
    comfort_foods: list[str]
    allergies: list[AllergyResponse]
    created_at: datetime
    updated_at: datetime

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    display_name: str
    email: str | None
    country: str | None
    city: str | None
    state_or_region: str | None
    created_at: datetime
    updated_at: datetime

class OnboardingResponse(BaseModel):
    user: UserResponse
    food_profile: FoodProfileResponse