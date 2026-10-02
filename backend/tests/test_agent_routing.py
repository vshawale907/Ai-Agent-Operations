"""
Tests for Multi-Agent routing logic and Orchestrator state transitions.
"""

import pytest
from app.agents.graph import route_by_orchestrator_intent
from app.agents.state import AgentState


class TestAgentRouting:
    """Test intent-based workflow routing."""

    def test_route_document_knowledge(self):
        state: AgentState = {
            "intent": "DOCUMENT_KNOWLEDGE",
            "user_question": "What is our enterprise refund policy?",
        }
        dest = route_by_orchestrator_intent(state)
        assert dest == "rag_agent"

    def test_route_hybrid_question(self):
        state: AgentState = {
            "intent": "HYBRID",
            "user_question": "Why did revenue decline according to our sales strategy document?",
        }
        dest = route_by_orchestrator_intent(state)
        assert dest == "hybrid_sql_agent"

    def test_route_general_question(self):
        state: AgentState = {
            "intent": "GENERAL",
            "user_question": "Hello, how does this platform work?",
        }
        dest = route_by_orchestrator_intent(state)
        assert dest == "response_synthesizer"

    def test_route_analytics_anomaly_question(self):
        state: AgentState = {
            "intent": "BUSINESS_DATA",
            "user_question": "Detect any recent anomalies or unusual revenue drops",
        }
        dest = route_by_orchestrator_intent(state)
        assert dest == "analytics_agent"

    def test_route_standard_sql_question(self):
        state: AgentState = {
            "intent": "BUSINESS_DATA",
            "user_question": "What was our revenue last month?",
        }
        dest = route_by_orchestrator_intent(state)
        assert dest == "sql_agent"
