"""
Upgraded Multi-Agent LangGraph Workflow.

Orchestrates multi-agent routing across:
1. BUSINESS_DATA: Text-to-SQL & Analytics Engine
2. DOCUMENT_KNOWLEDGE: RAG Vector Search & Policy Retrieval
3. HYBRID: Dual-Agent Execution (SQL + RAG) with Insight Synthesis
4. GENERAL: Conversational Assistant
"""

from langgraph.graph import END, StateGraph

from app.agents.nodes.multi_agent_nodes import (
    analytics_agent_node,
    hybrid_sql_agent_node,
    insight_agent_node,
    orchestrator_node,
    rag_agent_node,
    response_synthesizer_node,
    sql_agent_node,
)
from app.agents.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def route_by_orchestrator_intent(state: AgentState) -> str:
    """Route question based on orchestrator classification."""
    intent = state.get("intent", "BUSINESS_DATA")
    question = (state.get("resolved_question") or state.get("user_question", "")).lower()

    if intent in ("GENERAL", "GREETING", "OFF_TOPIC"):
        return "response_synthesizer"

    if intent == "DOCUMENT_KNOWLEDGE":
        return "rag_agent"

    if intent == "HYBRID":
        return "hybrid_sql_agent"

    # Only route to analytics_agent for explicit anomaly scan requests
    if "anomal" in question or any(w in question for w in ("unusual drop", "unusual spike", "outlier")):
        return "analytics_agent"

    # All standard data queries (revenue, products, regions, margins, customers, expenses, comparisons) route to sql_agent
    return "sql_agent"


def build_multi_agent_graph() -> StateGraph:
    """Build and compile the multi-agent orchestration graph."""
    graph = StateGraph(AgentState)

    # Add agent nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("sql_agent", sql_agent_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("hybrid_sql_agent", hybrid_sql_agent_node)  # dedicated hybrid node
    graph.add_node("hybrid_rag_agent", rag_agent_node)
    graph.add_node("insight_agent", insight_agent_node)
    graph.add_node("analytics_agent", analytics_agent_node)
    graph.add_node("response_synthesizer", response_synthesizer_node)

    # Set entry point
    graph.set_entry_point("orchestrator")

    # Conditional branching from orchestrator
    graph.add_conditional_edges(
        "orchestrator",
        route_by_orchestrator_intent,
        {
            "sql_agent": "sql_agent",
            "rag_agent": "rag_agent",
            "hybrid_sql_agent": "hybrid_sql_agent",
            "analytics_agent": "analytics_agent",
            "response_synthesizer": "response_synthesizer",
        },
    )

    # SQL path
    graph.add_edge("sql_agent", "response_synthesizer")

    # Document RAG path
    graph.add_edge("rag_agent", "response_synthesizer")

    # Hybrid path: SQL -> RAG -> Insight Agent -> END
    graph.add_edge("hybrid_sql_agent", "hybrid_rag_agent")
    graph.add_edge("hybrid_rag_agent", "insight_agent")
    graph.add_edge("insight_agent", END)

    # Analytics path -> END
    graph.add_edge("analytics_agent", END)

    # Terminal node
    graph.add_edge("response_synthesizer", END)

    logger.info("Multi-Agent LangGraph compiled successfully.")
    return graph.compile()


# Singleton compiled graph
_agent_graph = None


def get_agent_graph():
    """Get or compile the multi-agent graph singleton."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = build_multi_agent_graph()
    return _agent_graph
