import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.profile import CuisineResponse, FoodProfileResponse, FoodProfileUpdate, OnboardingRequest, OnboardingResponse, UserResponse
from app.services.profile import ProfileService

router = APIRouter(prefix="/api/v1", tags=["personalization"])

def get_profile_service(session: Session = Depends(get_db)) -> ProfileService:
    return ProfileService(session)

@router.post("/onboarding", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
def onboard(payload: OnboardingRequest, service: ProfileService = Depends(get_profile_service)) -> OnboardingResponse:
    try:
        return service.onboard(payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, service: ProfileService = Depends(get_profile_service)) -> UserResponse:
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return service.user_response(user)

@router.get("/users/{user_id}/food-profile", response_model=FoodProfileResponse)
def get_food_profile(user_id: uuid.UUID, service: ProfileService = Depends(get_profile_service)) -> FoodProfileResponse:
    profile = service.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food profile not found")
    return service.profile_response(profile)

@router.put("/users/{user_id}/food-profile", response_model=FoodProfileResponse)
def update_food_profile(user_id: uuid.UUID, payload: FoodProfileUpdate, service: ProfileService = Depends(get_profile_service)) -> FoodProfileResponse:
    profile = service.update_profile(user_id, payload)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return service.profile_response(profile)

@router.get("/cuisines", response_model=list[CuisineResponse])
def list_cuisines(service: ProfileService = Depends(get_profile_service)) -> list[CuisineResponse]:
    return [CuisineResponse.model_validate(cuisine) for cuisine in service.list_cuisines()]