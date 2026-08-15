from app.agents.graph import build_graph
from app.agents.schemas import AgentRunResponse
from app.services.intent import IntentExtractionService
class AharaAgentService:
 def __init__(self,intent_service:IntentExtractionService): self._graph=build_graph(intent_service)
 def run(self,message:str,user_id:str|None=None)->AgentRunResponse:
  state=self._graph.invoke({'message':message,'user_id':user_id,'errors':[],'trace':[],'restaurant_candidates':[]}); return AgentRunResponse(intent=state.get('intent'),required_context=state.get('required_context'),ready_for_recommendation=state.get('ready_for_recommendation',False),missing_context=state.get('missing_context',[]),errors=state.get('errors',[]),trace=state.get('trace',[]))