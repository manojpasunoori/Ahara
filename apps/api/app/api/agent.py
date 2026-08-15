from fastapi import APIRouter
from app.agents.schemas import AgentRunRequest, AgentRunResponse
from app.agents.service import AharaAgentService
from app.api.ai import _service
router=APIRouter(prefix='/api/v1/agent',tags=['agent'])
@router.post('/run',response_model=AgentRunResponse)
def run(request:AgentRunRequest)->AgentRunResponse:return AharaAgentService(_service()).run(request.message,str(request.user_id) if request.user_id else None)