import os
import json
import asyncio
from typing import List, Dict, Any, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from database import AuditRun, AuditCard

# Define the state dictionary
class AgentState(TypedDict):
    pdf_text: str
    guidance_metrics: List[Dict[str, Any]]
    historical_tables: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    correction_message: str
    attempts: int
    logs: List[str]
    streaming_callback: Any  # Async function to send events to SSE client

# Helper to get the ChatOpenAI client configured for LiteLLM Proxy or OpenRouter
def get_llm():
    model_name = os.getenv("LLM_MODEL", "openrouter/free")
    api_base = os.getenv("LLM_API_BASE", "https://openrouter.ai/api/v1")
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or "dummy-key"
    
    if os.getenv("USE_LITELLM_PROXY") == "true":
        api_base = "http://127.0.0.1:8001/v1"
        api_key = "local-litellm-key"
        model_name = os.getenv("LITELLM_MODEL", "groq/llama3-70b-8192")

    return ChatOpenAI(
        model=model_name,
        openai_api_base=api_base,
        openai_api_key=api_key,
        temperature=0.0,
        streaming=True
    )

# Node A: Guidance Extractor
async def guidance_extractor_node(state: AgentState) -> AgentState:
    state["attempts"] += 1
    msg = f"--- [Node A] Guidance Extractor (Attempt {state['attempts']}) ---"
    state["logs"].append(msg)
    await state["streaming_callback"]("log", msg)

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert financial analyst. Your task is to extract forward-looking financial metrics (guidance, forecasts, outlook targets) from the provided earnings call transcript.\n"
                   "Only extract actual future expectations (e.g. Q3 revenue targets, FY margin outlooks). Do NOT extract historical metrics.\n"
                   "You must output a JSON list of objects. Each object must contain:\n"
                   "- 'metric': Name of the metric (e.g., 'Q3 Revenue Guidance', 'FY26 Gross Margin Outlook')\n"
                   "- 'value': The stated target value or range (e.g., '$10.2B - $10.5B', '54%')\n"
                   "- 'source_context': The exact sentence/context where this metric was stated.\n\n"
                   "Format your response strictly as valid JSON, wrapping it inside a JSON block: ```json ... ```\n"
                   "If correction feedback is provided, adjust your extraction accordingly."),
        ("user", "Correction Feedback: {correction}\n\nTranscript Context:\n{context}")
    ])

    formatted_prompt = prompt.format_messages(
        correction=state.get("correction_message", "None"),
        context=state["pdf_text"]
    )

    full_response = ""
    async for chunk in llm.astream(formatted_prompt):
        if chunk.content:
            full_response += chunk.content
            await state["streaming_callback"]("token", chunk.content)

    # Parse JSON list
    extracted_metrics = []
    try:
        cleaned = full_response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        extracted_metrics = json.loads(cleaned)
        if not isinstance(extracted_metrics, list):
            extracted_metrics = [extracted_metrics]
    except Exception as e:
        state["logs"].append(f"Error parsing Guidance Extractor JSON: {e}")
        extracted_metrics = []

    state["guidance_metrics"] = extracted_metrics
    msg = f"Extracted {len(extracted_metrics)} guidance metrics."
    state["logs"].append(msg)
    await state["streaming_callback"]("log", msg)
    return state

# Node B: Forensic Auditor
async def forensic_auditor_node(state: AgentState) -> AgentState:
    msg = "--- [Node B] Forensic Auditor ---"
    state["logs"].append(msg)
    await state["streaming_callback"]("log", msg)

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Forensic Financial Auditor. Your job is to compare the forward-looking guidance metrics extracted from the call against any historical results, tables, segment targets, or other disclosures in the transcript.\n"
                   "Analyze the document carefully. Look for direct mathematical, segment, or cost-based contradictions (e.g., segment targets that do not sum to the guided total, margin calculations that do not equal Net Income/Revenue targets, or growth claims that are inconsistent with historical tables).\n\n"
                   "Verification Protocol:\n"
                   "1. If all figures, segments, and margins align perfectly, do not create false contradictions. Output an empty list of contradictions and soundness: 'sound'.\n"
                   "2. Only list actual contradictions. For each contradiction, write a clear proof explanation.\n\n"
                   "You must output a JSON object containing:\n"
                   "- 'contradictions': A list of contradiction objects, each with:\n"
                   "  * 'metric': The guidance metric name.\n"
                   "  * 'guidance_value': Stated guidance value.\n"
                   "  * 'contradictory_value': The conflicting segment sum, table value, or operational cost.\n"
                   "  * 'explanation': The mathematical or logical proof of the contradiction.\n"
                   "  * 'severity': 'High' or 'Med'.\n"
                   "- 'soundness': 'sound' (if the data is clear and consistent) or 'ambiguous' (if details mismatch, numbers don't add up, or guidance metrics lack sufficient context/tables to verify).\n"
                   "- 'correction_message': If 'ambiguous', provide a detailed note explaining what guidance metrics need refinement or what tables Node A should re-examine. If 'sound', write an empty string.\n\n"
                   "Format your response strictly as valid JSON, wrapping it inside a JSON block: ```json ... ```"),
        ("user", "Extracted Guidance Metrics:\n{metrics}\n\nFull Transcript Data Context:\n{historical}")
    ])

    formatted_prompt = prompt.format_messages(
        metrics=json.dumps(state["guidance_metrics"], indent=2),
        historical=state["pdf_text"]
    )

    full_response = ""
    async for chunk in llm.astream(formatted_prompt):
        if chunk.content:
            full_response += chunk.content
            await state["streaming_callback"]("token", chunk.content)

    # Parse JSON response
    auditor_result = {"contradictions": [], "soundness": "sound", "correction_message": ""}
    try:
        cleaned = full_response.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        auditor_result = json.loads(cleaned)
    except Exception as e:
        state["logs"].append(f"Error parsing Forensic Auditor JSON: {e}")

    state["contradictions"] = auditor_result.get("contradictions", [])
    state["correction_message"] = auditor_result.get("correction_message", "")
    
    soundness = auditor_result.get("soundness", "sound")
    state["logs"].append(f"Auditor Soundness rating: {soundness}")
    await state["streaming_callback"]("log", f"Forensic audit finished. Soundness: {soundness}")
    
    return state

# Node C: Synthesizer
async def synthesizer_node(state: AgentState) -> AgentState:
    msg = "--- [Node C] Synthesizer ---"
    state["logs"].append(msg)
    await state["streaming_callback"]("log", msg)

    final_cards = []
    if not state["contradictions"]:
        final_cards.append({
            "severity": "Low",
            "title": "Clean Audit: No Financial Contradictions Detected",
            "description": "The Guidance Extractor and Forensic Auditor matched all forward-looking guidance figures against historical figures and found no material anomalies.",
            "contradiction_details": "No contradictions found."
        })
    else:
        for idx, item in enumerate(state["contradictions"]):
            final_cards.append({
                "severity": item.get("severity", "High"),
                "title": f"Financial Contradiction: {item.get('metric', 'Metric discrepancy')}",
                "description": f"Stated Guidance: {item.get('guidance_value')}. Conflicting Value: {item.get('contradictory_value')}.",
                "contradiction_details": item.get("explanation", "Discrepancy detected between guidance and tables.")
            })

    state["logs"].append(f"Synthesized {len(final_cards)} Audit Cards.")
    await state["streaming_callback"]("card", final_cards)
    await state["streaming_callback"]("log", "Audit execution complete.")
    return state

# Conditional routing edge
def audit_routing_edge(state: AgentState):
    if state["correction_message"] and state["attempts"] < 3:
        return "GuidanceExtractor"
    return "Synthesizer"

# Build state graph
def build_agent_graph():
    builder = StateGraph(AgentState)
    
    builder.add_node("GuidanceExtractor", guidance_extractor_node)
    builder.add_node("ForensicAuditor", forensic_auditor_node)
    builder.add_node("Synthesizer", synthesizer_node)
    
    builder.set_entry_point("GuidanceExtractor")
    builder.add_edge("GuidanceExtractor", "ForensicAuditor")
    
    builder.add_conditional_edges(
        "ForensicAuditor",
        audit_routing_edge,
        {
            "GuidanceExtractor": "GuidanceExtractor",
            "Synthesizer": "Synthesizer"
        }
    )
    
    return builder.compile()

# Streaming execution entrypoint
async def run_audit_stream(pdf_text: str, db: Session, audit_run_id: int, stream_callback):
    state: AgentState = {
        "pdf_text": pdf_text,
        "guidance_metrics": [],
        "historical_tables": [],
        "contradictions": [],
        "correction_message": "",
        "attempts": 0,
        "logs": [],
        "streaming_callback": stream_callback
    }
    
    graph = build_agent_graph()
    
    try:
        final_state = await graph.ainvoke(state)
        
        # Save synthesized cards to DB
        run = db.query(AuditRun).filter(AuditRun.id == audit_run_id).first()
        if run:
            run.status = "completed"
            db.commit()
            
            # Save the final cards generated
            if "contradictions" in final_state:
                cards_to_save = []
                if not final_state["contradictions"]:
                    cards_to_save.append(AuditCard(
                        audit_id=audit_run_id,
                        severity="Low",
                        title="Clean Audit: No Financial Contradictions Detected",
                        description="The Guidance Extractor and Forensic Auditor matched all forward-looking guidance figures against historical figures and found no material anomalies.",
                        contradiction_details="No contradictions found."
                    ))
                else:
                    for item in final_state["contradictions"]:
                        cards_to_save.append(AuditCard(
                            audit_id=audit_run_id,
                            severity=item.get("severity", "High"),
                            title=f"Financial Contradiction: {item.get('metric', 'Metric discrepancy')}",
                            description=f"Stated Guidance: {item.get('guidance_value')}. Conflicting Value: {item.get('contradictory_value')}.",
                            contradiction_details=item.get("explanation", "")
                        ))
                
                db.add_all(cards_to_save)
                db.commit()
    except Exception as e:
        error_msg = f"Error during LangGraph audit execution: {str(e)}"
        await stream_callback("log", error_msg)
        run = db.query(AuditRun).filter(AuditRun.id == audit_run_id).first()
        if run:
            run.status = "failed"
            db.commit()
        await stream_callback("card", [{
            "severity": "High",
            "title": "Audit Pipeline Failure",
            "description": error_msg,
            "contradiction_details": "Execution error inside LangGraph."
        }])
