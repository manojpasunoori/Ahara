from app.agents.schemas import AgentError, RequiredContext
from app.agents.state import AharaAgentState
from app.providers.llm import LLMProviderError
from app.services.intent import IntentExtractionService

def extract_intent(service: IntentExtractionService):
    def node(state: AharaAgentState) -> dict:
        trace = [*state.get('trace', []), 'extract_intent']
        try:
            return {'intent': service.extract(state['message']), 'trace': trace}
        except LLMProviderError:
            return {'errors': [AgentError(stage='extract_intent', code='intent_extraction_failed', message='Ahara could not understand the food request.')], 'trace': trace}
    return node

def plan_context(state: AharaAgentState) -> dict:
    return {'required_context': RequiredContext(), 'trace': [*state.get('trace', []), 'plan_context']}

def evaluate_readiness(state: AharaAgentState) -> dict:
    required = state['required_context']
    values = {'profile': state.get('profile_context'), 'location': state.get('location_context'), 'weather': state.get('weather_context'), 'restaurants': state.get('restaurant_candidates')}
    missing = [name for name, needed in [('profile', required.needs_profile), ('location', required.needs_location), ('weather', required.needs_weather), ('restaurants', required.needs_restaurants)] if needed and not values[name]]
    return {'missing_context': missing, 'ready_for_recommendation': not missing and not state.get('errors'), 'trace': [*state.get('trace', []), 'evaluate_readiness']}

def finalize(state: AharaAgentState) -> dict:
    return {'ready_for_recommendation': False if state.get('errors') else state.get('ready_for_recommendation', False), 'trace': [*state.get('trace', []), 'finalize']}