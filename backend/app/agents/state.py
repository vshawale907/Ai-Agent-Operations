"""
Agent state definition for Multi-Agent Orchestration.

Maintains typed state across Orchestrator, SQL Agent, RAG Agent,
Analytics Agent, Insight Agent, and Report Agent.
"""

from typing import Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Typed state for the multi-agent LangGraph workflow."""

    # --- User Input & Context ---
    user_question: str
    resolved_question: Optional[str]
    user_id: int
    conversation_id: Optional[str]
    conversation_history: List[Dict[str, str]]  # [{"role": "user"|"assistant", "content": "..."}]

    # --- Orchestration & Classification ---
    intent: Literal["BUSINESS_DATA", "DOCUMENT_KNOWLEDGE", "HYBRID", "GENERAL", "GREETING", "OFF_TOPIC"]
    sub_intent: Optional[str]
    requires_chart: bool

    # --- SQL Agent State ---
    schema_context: str
    period_label: Optional[str]  # e.g. "September 2026" resolved from relative date
    glossary_context: str
    generated_sql: Optional[str]
    sql_explanation: Optional[str]
    is_sql_valid: bool
    validation_error: Optional[str]
    query_result: Optional[List[Dict[str, Any]]]
    row_count: int
    execution_time_ms: float

    # --- RAG Agent State ---
    retrieved_documents: Optional[List[Dict[str, Any]]]
    document_summary: Optional[str]
    has_document_evidence: bool

    # --- Analytics & Anomaly State ---
    analytics_data: Optional[Dict[str, Any]]
    anomalies: Optional[List[Dict[str, Any]]]

    # --- Insight & Report Synthesis ---
    database_facts: Optional[str]
    document_facts: Optional[str]
    derived_insights: Optional[str]
    citations: List[Dict[str, Any]]
    chart_data: Optional[Dict[str, Any]]
    table_data: Optional[List[Dict[str, Any]]]

    # --- Final Response ---
    final_response: str
    confidence: float
    data_sources: List[str]

    # --- Execution & Resilience ---
    warnings: List[str]
    errors: List[str]
    retry_count: int
    max_retries: int
