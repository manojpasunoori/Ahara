from langgraph.graph import END, START, StateGraph
from app.agents.nodes import evaluate_readiness, extract_intent, finalize, plan_context
from app.agents.state import AharaAgentState
from app.services.intent import IntentExtractionService
def build_graph(service:IntentExtractionService):
 graph=StateGraph(AharaAgentState); graph.add_node('extract_intent',extract_intent(service)); graph.add_node('plan_context',plan_context); graph.add_node('evaluate_readiness',evaluate_readiness); graph.add_node('finalize',finalize); graph.add_edge(START,'extract_intent'); graph.add_conditional_edges('extract_intent',lambda s:'plan_context' if s.get('intent') else 'finalize',{'plan_context':'plan_context','finalize':'finalize'}); graph.add_edge('plan_context','evaluate_readiness'); graph.add_edge('evaluate_readiness','finalize'); graph.add_edge('finalize',END); return graph.compile()