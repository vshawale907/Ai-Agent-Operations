"""
Chat API route with conversation memory and multi-agent orchestration.

POST /api/chat — Send a message to the AI agent and receive a response.
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_agent_graph
from app.agents.state import AgentState
from app.core.logging import get_logger
from app.core.rate_limiter import rate_limit
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.chat import ChartData, ChatMetadata, ChatRequest, ChatResponse
from app.services.auth_service import get_current_user
from app.services.memory_service import memory_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("", response_model=ChatResponse, dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))])
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a business question through the Multi-Agent Orchestrator with memory."""
    start_time = time.time()

    # Retrieve or initialize conversation thread
    conv = await memory_service.get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        title=request.message[:40] + ("..." if len(request.message) > 40 else ""),
    )
    conversation_id = conv.id

    # Retrieve recent history for multi-turn conversational context
    history = await memory_service.get_recent_history(db, conversation_id, limit=6)

    logger.info(f"Chat request [user {current_user.id}, conv {conversation_id}]: '{request.message[:70]}'")

    try:
        # Build initial multi-agent state
        initial_state: AgentState = {
            "user_question": request.message,
            "user_id": current_user.id,
            "conversation_id": conversation_id,
            "conversation_history": history,
            "errors": [],
            "warnings": [],
            "citations": [],
            "retry_count": 0,
            "max_retries": 2,
        }

        # Run the multi-agent graph
        graph = get_agent_graph()
        result = await graph.ainvoke(initial_state)

        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        logger.info(f"Multi-Agent execution completed in {elapsed_ms}ms")

        final_msg = result.get("final_response", "I have completed processing your request.")
        citations = result.get("citations", [])
        intent = result.get("intent", "BUSINESS_DATA")
        data_sources = result.get("data_sources", ["PostgreSQL Warehouse"])

        # Format ChartData if provided
        chart_data = None
        if result.get("chart_data"):
            cd = result["chart_data"]
            chart_data = ChartData(
                chart_type=cd.get("chart_type", "bar"),
                title=cd.get("title", "Analytics Visualization"),
                data=cd.get("data", []),
                x_key=cd.get("x_key"),
                y_key=cd.get("y_key"),
                keys=cd.get("keys"),
            )

        metadata = ChatMetadata(
            sql_query=result.get("generated_sql"),
            execution_time_ms=result.get("execution_time_ms", elapsed_ms),
            data_sources=data_sources,
            intent=intent,
            row_count=result.get("row_count"),
        )

        table_data = result.get("table_data") or result.get("query_result")

        # Persist conversation turn
        await memory_service.save_turn(
            db=db,
            conversation_id=conversation_id,
            user_content=request.message,
            assistant_content=final_msg,
            intent=intent,
            chart_data=chart_data.model_dump() if chart_data else None,
            table_data=table_data,
            citations=citations,
            metadata_json=metadata.model_dump(),
        )

        return ChatResponse(
            message=final_msg,
            chart_data=chart_data,
            table_data=table_data,
            citations=citations,
            metadata=metadata,
            conversation_id=conversation_id,
        )

    except ValueError as ve:
        # Raised deliberately (e.g. analytics data missing, SQL plan error)
        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        logger.warning(f"Validation/data error after {elapsed_ms}ms: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except TimeoutError as te:
        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        logger.error(f"LLM timeout after {elapsed_ms}ms: {te}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI model took too long to respond. Please try a simpler question or try again shortly.",
        )
    except Exception as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        err_str = str(e).lower()
        logger.error(f"Chat error after {elapsed_ms}ms: {e}")

        # Categorize error for a more helpful frontend message
        if "connection" in err_str or "could not connect" in err_str:
            detail = "Database connection failed. Please ensure the PostgreSQL service is running."
        elif "429" in err_str or "rate limit" in err_str:
            detail = "The AI model is rate-limited. Please wait a moment and try again."
        elif "sql" in err_str or "syntax error" in err_str:
            detail = "Could not build a valid database query for your question. Try rephrasing."
        else:
            detail = f"An unexpected error occurred while processing your request: {str(e)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
