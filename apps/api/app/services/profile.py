from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.profile import Allergy, ComfortFood, Cuisine, FoodProfile, User, UserAllergy, UserComfortFood, UserCuisinePreference
from app.schemas.profile import FoodProfileResponse, FoodProfileUpdate, OnboardingRequest, OnboardingResponse, UserResponse

class ProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def onboard(self, payload: OnboardingRequest) -> OnboardingResponse:
        if self.session.scalar(select(User).where(User.email == str(payload.email))):
            raise ValueError("A user with this email already exists")
        user = User(display_name=payload.display_name, email=str(payload.email), country=payload.country, city=payload.city, state_or_region=payload.state_or_region)
        self.session.add(user)
        self.session.flush()
        self._replace_profile(user, payload)
        self.session.commit()
        return OnboardingResponse(user=self.user_response(user), food_profile=self.profile_response(self._load_user(user.id).food_profile))

    def get_user(self, user_id: object) -> User | None:
        return self._load_user(user_id)

    def get_profile(self, user_id: object) -> FoodProfile | None:
        user = self._load_user(user_id)
        return user.food_profile if user else None

    def update_profile(self, user_id: object, payload: FoodProfileUpdate) -> FoodProfile | None:
        user = self._load_user(user_id)
        if user is None:
            return None
        self._replace_profile(user, payload)
        self.session.commit()
        return self._load_user(user.id).food_profile

    def list_cuisines(self) -> list[Cuisine]:
        return list(self.session.scalars(select(Cuisine).order_by(Cuisine.name)))

    def _load_user(self, user_id: object) -> User | None:
        statement = select(User).options(
            selectinload(User.food_profile), selectinload(User.cuisine_preferences).selectinload(UserCuisinePreference.cuisine),
            selectinload(User.comfort_foods).selectinload(UserComfortFood.comfort_food), selectinload(User.allergies).selectinload(UserAllergy.allergy),
        ).where(User.id == user_id)
        return self.session.scalar(statement)

    def _replace_profile(self, user: User, payload: OnboardingRequest | FoodProfileUpdate) -> None:
        profile = user.food_profile or FoodProfile(user_id=user.id)
        profile.diet_type = payload.diet_type
        profile.spice_tolerance = payload.spice_tolerance
        profile.adventurousness = payload.adventurousness
        profile.usual_budget_min = payload.usual_budget_min
        profile.usual_budget_max = payload.usual_budget_max
        profile.usual_travel_radius_miles = payload.usual_travel_radius_miles
        profile.prefers_delivery = "delivery" in payload.dining_preferences
        profile.prefers_pickup = "pickup" in payload.dining_preferences
        profile.prefers_dine_in = "dine_in" in payload.dining_preferences
        if profile not in self.session:
            self.session.add(profile)
        if isinstance(payload, OnboardingRequest):
            user.cuisine_preferences.clear(); user.comfort_foods.clear(); user.allergies.clear()
            for item in payload.cuisine_preferences:
                cuisine = self._find_or_create(Cuisine, item.name)
                user.cuisine_preferences.append(UserCuisinePreference(cuisine=cuisine, preference_level=item.preference_level))
            for name in payload.comfort_foods:
                comfort_food = self._find_or_create(ComfortFood, name)
                user.comfort_foods.append(UserComfortFood(comfort_food=comfort_food))
            for item in payload.allergies:
                allergy = self._find_or_create(Allergy, item.name)
                user.allergies.append(UserAllergy(allergy=allergy, notes=item.notes))

    def _find_or_create(self, model: type[Cuisine] | type[ComfortFood] | type[Allergy], name: str):
        normalized = name.strip()
        entity = self.session.scalar(select(model).where(model.name.ilike(normalized)))
        if entity is None:
            entity = model(name=normalized)
            self.session.add(entity)
            self.session.flush()
        return entity

    @staticmethod
    def user_response(user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    @staticmethod
    def profile_response(profile: FoodProfile) -> FoodProfileResponse:
        dining = []
        if profile.prefers_delivery: dining.append("delivery")
        if profile.prefers_pickup: dining.append("pickup")
        if profile.prefers_dine_in: dining.append("dine_in")
        return FoodProfileResponse(id=profile.id, user_id=profile.user_id, diet_type=profile.diet_type, spice_tolerance=profile.spice_tolerance, adventurousness=profile.adventurousness, usual_budget_min=profile.usual_budget_min, usual_budget_max=profile.usual_budget_max, usual_travel_radius_miles=profile.usual_travel_radius_miles, dining_preferences=dining, cuisine_preferences=[{"name": p.cuisine.name, "preference_level": p.preference_level} for p in user_cuisines(profile)], comfort_foods=[item.comfort_food.name for item in profile.user.comfort_foods], allergies=[{"name": item.allergy.name, "notes": item.notes} for item in profile.user.allergies], created_at=profile.created_at, updated_at=profile.updated_at)

def user_cuisines(profile: FoodProfile) -> list[UserCuisinePreference]:
    return sorted(profile.user.cuisine_preferences, key=lambda item: (-item.preference_level, item.cuisine.name))