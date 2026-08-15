from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.schemas.intent import FoodIntent
class RequiredContext(BaseModel):
    needs_profile: bool = True; needs_location: bool = True; needs_weather: bool = True; needs_restaurants: bool = True
class AgentError(BaseModel): stage:str; code:str; message:str
class AgentRunRequest(BaseModel):
    message:str=Field(min_length=1,max_length=2000); user_id:UUID|None=None
    @field_validator('message')
    @classmethod
    def nonblank(cls,v:str)->str:
        if not v.strip(): raise ValueError('message must not be blank')
        return v.strip()
class AgentRunResponse(BaseModel):
    intent:FoodIntent|None; required_context:RequiredContext|None; ready_for_recommendation:bool; missing_context:list[str]; errors:list[AgentError]; trace:list[str]