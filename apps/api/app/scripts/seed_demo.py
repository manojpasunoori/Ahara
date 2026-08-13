from app.core.database import SessionLocal
from app.schemas.profile import OnboardingRequest
from app.services.profile import ProfileService

DEMO_EMAIL = "manoj.demo@ahara.local"

def main() -> None:
    session = SessionLocal()
    try:
        service = ProfileService(session)
        existing = session.execute(__import__("sqlalchemy").select(__import__("app.models.profile", fromlist=["User"]).User).where(__import__("app.models.profile", fromlist=["User"]).User.email == DEMO_EMAIL)).scalar_one_or_none()
        if existing:
            print(f"Demo user already exists: {existing.id}")
            return
        result = service.onboard(OnboardingRequest(display_name="Manoj", email=DEMO_EMAIL, country="United States", city="Arlington", state_or_region="Texas", diet_type="omnivore", spice_tolerance=5, adventurousness=3, usual_budget_min=10, usual_budget_max=30, usual_travel_radius_miles=20, dining_preferences=["delivery", "pickup", "dine_in"], cuisine_preferences=[{"name":"South Indian","preference_level":5},{"name":"North Indian","preference_level":4},{"name":"Mexican","preference_level":3},{"name":"Thai","preference_level":3},{"name":"Mediterranean","preference_level":3}], comfort_foods=["Biryani","Chai","Samosa","Dosa"], allergies=[]))
        print(f"Seeded demo user: {result.user.id}")
    finally:
        session.close()

if __name__ == "__main__":
    main()