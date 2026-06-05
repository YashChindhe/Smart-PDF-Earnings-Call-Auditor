import os
import asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, AuditRun, AuditCard
from agent import build_agent_graph, run_audit_stream

# Mock LLM response class to verify LangGraph execution
class MockChunk:
    def __init__(self, content):
        self.content = content

class MockLLM:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    async def astream(self, messages):
        # Return mocked JSON response corresponding to the call count
        response_text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        
        # Stream it in two chunks
        half = len(response_text) // 2
        yield MockChunk(response_text[:half])
        yield MockChunk(response_text[half:])

async def test_state_machine():
    print("Initializing test database...")
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create dummy audit run
    run = AuditRun(file_id=1, status="in_progress")
    db.add(run)
    db.commit()

    # Define mock LLM responses
    # First call: Guidance Extractor (returns guidance metrics JSON)
    guidance_response = """
    ```json
    [
      {
        "metric": "Q3 Revenue Guidance",
        "value": "$10.5B",
        "source_context": "We expect Q3 revenue to reach $10.5B."
      }
    ]
    ```
    """
    # Second call: Forensic Auditor (finds contradiction and claims soundness is sound)
    auditor_response = """
    ```json
    {
      "contradictions": [
        {
          "metric": "Q3 Revenue Guidance",
          "guidance_value": "$10.5B",
          "contradictory_value": "$9.0B in historical tables",
          "explanation": "Guidance states Q3 revenue of $10.5B, but Q2 actual revenue table lists $9.0B representing an unrealistic QoQ jump.",
          "severity": "High"
        }
      ],
      "soundness": "sound",
      "correction_message": ""
    }
    ```
    """

    mock_llm = MockLLM([guidance_response, auditor_response])

    # Callback list to store SSE events
    events = []
    async def sse_callback(event_type, data):
        events.append((event_type, data))

    print("Running state machine with mock LLM...")
    # Patch the get_llm function in agent.py to return our mock LLM
    with patch("agent.get_llm", return_value=mock_llm):
        await run_audit_stream(
            pdf_text="Dummy earnings transcript. Q2 Revenue was $9.0B. We expect Q3 revenue to reach $10.5B.",
            db=db,
            audit_run_id=run.id,
            stream_callback=sse_callback
        )

    # Verify results
    print("\n--- Test Verification Results ---")
    
    # 1. Check database updates
    db.refresh(run)
    print(f"Audit Status in DB: {run.status} (Expected: completed)")
    assert run.status == "completed"

    cards = db.query(AuditCard).filter(AuditCard.audit_id == run.id).all()
    print(f"Cards saved in DB: {len(cards)} (Expected: 1)")
    assert len(cards) == 1
    print(f"Card Title: {cards[0].title}")
    print(f"Card Severity: {cards[0].severity}")
    assert cards[0].severity == "High"

    # 2. Check SSE Event logs
    log_events = [data for event, data in events if event == "log"]
    card_events = [data for event, data in events if event == "card"]
    
    print(f"Log events streamed: {len(log_events)}")
    assert len(log_events) > 0
    print(f"Card events streamed: {len(card_events)}")
    assert len(card_events) == 1

    print("\nState machine verification: SUCCESS!")
    db.close()

if __name__ == "__main__":
    asyncio.run(test_state_machine())
