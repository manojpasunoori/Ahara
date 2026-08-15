from typing import TypedDict
from app.schemas.intent import FoodIntent
from app.agents.schemas import RequiredContext, AgentError
class AharaAgentState(TypedDict, total=False):
    user_id: str | None; message: str; intent: FoodIntent | None; required_context: RequiredContext | None
    profile_context: object | None; location_context: object | None; weather_context: object | None; restaurant_candidates: list[object]
    ready_for_recommendation: bool; missing_context: list[str]; errors: list[AgentError]; trace: list[str]