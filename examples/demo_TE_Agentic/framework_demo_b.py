"""
LangGraph + LangChain Framework Demo (Stateful + Traceable) with OpenAI

This version is closer to LangChain/LangGraph "agent + memory" patterns:
- LangGraph ReAct agent (tool-calling) with short-term memory via checkpointer (thread_id)
- Traceable run logs: run_id, model_id, version_id, policy_id, step traces, evidence
- Two business workflows:
  1) FinTech credit risk demo (single case) + HITL policy routing
  2) TE consumer product pricing (presale + retail) + constraint checks + benchmark draft (LLM, no web)

Gradio:
- Tab 1: FinTech (form -> agent decides tools -> structured output + explanation)
- Tab 2: TE Pricing (form -> agent decides tools -> structured output + explanation)
- Tab 3: Logs (tail)

Hugging Face:
- Rename this file to app.py
- Use requirements_langgraph.txt as requirements.txt
- Add OPENAI_API_KEY in Space secrets

Security:
- This file redacts API keys from logs and UI outputs.

Note:
- "Benchmark research" here is AI-generated only. No browsing. Treat as draft until verified.

"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =========================
# IDs + versions (traceable)
# =========================

AGENT_ID = os.getenv("AGENT_ID", "nexdatawork_demo_agent")
MODEL_ID = os.getenv("MODEL_ID", "framework_langgraph_agent")
VERSION_ID = os.getenv("VERSION_ID", "1.0.0")

POLICY_ID = os.getenv("POLICY_ID", "hitl_and_pricing_policy")
POLICY_VERSION = os.getenv("POLICY_VERSION", "1.0")

LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Artifacts for HF Spaces
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
RUN_LOG_PATH = DATA_DIR / os.getenv("RUN_LOG_PATH", "run_logs.jsonl")
CHECKPOINT_PATH = DATA_DIR / os.getenv("CHECKPOINT_PATH", "checkpoints.sqlite")

# FinTech policy knobs
RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "0.50"))
BORDER_BAND = float(os.getenv("BORDER_BAND", "0.05"))
HIGH_IMPACT_AMOUNT = float(os.getenv("HIGH_IMPACT_AMOUNT", "1000000"))

# TE pricing defaults
DEFAULT_COGS = float(os.getenv("DEFAULT_COGS", "6"))
DEFAULT_LANDED = float(os.getenv("DEFAULT_LANDED", "10"))
DEFAULT_PRESALE_MULT = float(os.getenv("DEFAULT_PRESALE_MULT", "7"))
DEFAULT_PRESALE_DISCOUNT = float(os.getenv("DEFAULT_PRESALE_DISCOUNT", "0.20"))
DEFAULT_PRICE_GRID = [x for x in range(42, 121, 1)]  # 42..120 (demo grid)


# =========================
# Helpers
# =========================

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def new_id(prefix: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{ts}_{uuid.uuid4().hex[:8]}"

def run_metadata(task_type: str) -> Dict[str, Any]:
    return {
        "run_id": new_id("run"),
        "agent_id": AGENT_ID,
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "llm_model": LLM_MODEL,
        "task_type": task_type,
        "timestamps": {"created_at": utc_now()},
    }


# =========================
# Redaction (API key safety)
# =========================

_API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-]{20,}")

def redact_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    return _API_KEY_PATTERN.sub("sk-REDACTED", s)

def redact(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    if isinstance(obj, dict):
        return {k: redact(v) for k, v in obj.items()}
    return obj


# =========================
# Traceable logs
# =========================

@dataclass
class StepTrace:
    step_id: str
    name: str
    started_at: str
    ended_at: str
    duration_ms: int
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

class TraceLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, payload: Dict[str, Any]) -> None:
        payload = redact(payload)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def tail(self, n: int = 30) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        out: List[Dict[str, Any]] = []
        for ln in lines[-n:]:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out

LOGGER = TraceLogger(RUN_LOG_PATH)


# =========================
# Deterministic "model tools" (evidence-friendly)
# =========================

def fintech_score_tool(income: float, debt: float, credit_score: int) -> Dict[str, Any]:
    """
    Baseline, interpretable risk score:
    risk = 0.6*(debt/income) + 0.4*((850-credit_score)/850)
    """
    if income <= 0:
        raise ValueError("income must be > 0")
    if debt < 0:
        raise ValueError("debt must be >= 0")
    if not (300 <= credit_score <= 850):
        raise ValueError("credit_score must be between 300 and 850")

    dti = debt / income
    gap = (850 - credit_score) / 850
    risk = (0.6 * dti) + (0.4 * gap)

    return {
        "risk_score_pd": float(risk),
        "intermediates": {"debt_to_income": float(dti), "score_gap": float(gap)},
        "formula": "risk = 0.6*(debt/income) + 0.4*((850-credit_score)/850)",
    }

def hitl_policy(risk_score_pd: float, requested_amount: float) -> Dict[str, Any]:
    """
    HITL gating:
    - High impact -> review
    - High risk -> review
    - Borderline -> review
    - Else -> draft
    """
    thr = RISK_THRESHOLD
    band = BORDER_BAND
    hi = requested_amount >= HIGH_IMPACT_AMOUNT

    if hi:
        return {"decision": "Needs Human Review", "reason": "HIGH_IMPACT_CASE", "threshold": thr, "band": band}
    if risk_score_pd >= (thr + band):
        return {"decision": "Needs Human Review", "reason": "HIGH_RISK", "threshold": thr, "band": band}
    if (thr - band) <= risk_score_pd < (thr + band):
        return {"decision": "Needs Human Review", "reason": "BORDERLINE_SCORE", "threshold": thr, "band": band}
    return {"decision": "Decision Draft", "reason": "LOW_RISK", "threshold": thr, "band": band}

def te_pricing_tool(
    cogs: float,
    landed: float,
    presale_mult: float,
    discount: float,
    alpha: float = 120.0,
    beta: float = 0.08,
) -> Dict[str, Any]:
    """
    Consumer product pricing demo (predictive modeling placeholder):
    - Demand curve placeholder: demand = alpha * exp(-beta * price)
    - Objective: maximize (price - landed) * demand across a grid
    - Constraint: presale >= presale_mult * cogs, and presale >= 7*cogs (company rule)
    - Retail: retail = presale / (1 - discount), retail > presale
    """
    if cogs <= 0:
        raise ValueError("cogs must be > 0")
    if landed <= 0:
        raise ValueError("landed must be > 0")
    if presale_mult < 1:
        raise ValueError("presale_mult must be >= 1")
    if not (0.0 < discount < 0.9):
        raise ValueError("discount must be in (0, 0.9)")

    floor = presale_mult * cogs
    grid = [p for p in DEFAULT_PRICE_GRID if p >= floor]

    # exp without extra deps
    def exp(x: float) -> float:
        return float((2.718281828459045) ** x)

    best = None
    for p in grid:
        demand = float(alpha * exp(-beta * p))
        profit = (p - landed) * demand
        if best is None or profit > best["objective_profit"]:
            best = {"presale": float(p), "demand": float(demand), "objective_profit": float(profit)}

    presale = float(best["presale"]) if best else float(floor)
    retail = presale / (1.0 - discount)

    # round to .99
    def as_99(x: float) -> float:
        v = round(x)
        return float(f"{max(v, 1) - 0.01:.2f}")

    presale = as_99(presale)
    retail = as_99(retail)

    checks = {
        "presale_ge_floor": bool(presale >= floor),
        "presale_ge_7xcogs": bool(presale >= 7.0 * cogs),
        "retail_gt_presale": bool(retail > presale),
    }

    return {
        "inputs": {"cogs": cogs, "landed": landed, "presale_mult": presale_mult, "discount": discount, "alpha": alpha, "beta": beta},
        "presale_price": presale,
        "retail_price": retail,
        "unit_margin_presale": presale - landed,
        "unit_margin_retail": retail - landed,
        "optimization": best,
        "policy_checks": checks,
        "demand_model": "alpha * exp(-beta * price) (placeholder)",
        "notes": "Replace alpha/beta with real presale conversion or fitted demand model.",
    }

def te_benchmark_placeholder() -> Dict[str, Any]:
    """
    No browsing in this demo. Provide a safe placeholder list.
    The OpenAI agent can draft an unverified benchmark list (marked as draft).
    """
    return {
        "benchmark_items": [
            {"category": "smart_plug", "brand": "TP-Link Kasa"},
            {"category": "smart_plug", "brand": "Amazon Smart Plug"},
            {"category": "in_wall_outlet", "brand": "Leviton Decora Smart"},
            {"category": "premium", "brand": "Eve (Matter/Thread)"},
        ],
        "limitations": "Placeholder only. Verify with real market data.",
    }


# =========================
# LangChain tools (for ReAct agent)
# =========================

def build_tools():
    from langchain_core.tools import tool

    @tool("fintech_score")
    def fintech_score(income: float, debt: float, credit_score: int) -> str:
        """Compute a baseline risk score (PD) with intermediates. Returns JSON string."""
        out = fintech_score_tool(income, debt, credit_score)
        return json.dumps(out)

    @tool("hitl_route")
    def hitl_route(score_pd: float, requested_amount: float) -> str:
        """Apply HITL policy routing. Returns JSON string."""
        out = hitl_policy(score_pd, requested_amount)
        return json.dumps(out)

    @tool("te_pricing")
    def te_pricing(cogs: float, landed: float, presale_mult: float, discount: float) -> str:
        """Compute presale + retail pricing under constraints. Returns JSON string."""
        out = te_pricing_tool(cogs, landed, presale_mult, discount)
        return json.dumps(out)

    @tool("te_benchmark_placeholder")
    def te_benchmark() -> str:
        """Return a placeholder competitor benchmark list. Returns JSON string."""
        return json.dumps(te_benchmark_placeholder())

    return [fintech_score, hitl_route, te_pricing, te_benchmark]


# =========================
# LangGraph agent with memory (thread_id)
# =========================

def build_checkpointer():
    """
    Use SQLite checkpointer if available; otherwise memory.
    We use SqliteSaver(conn) to avoid context-manager issues.
    """
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        conn = sqlite3.connect(str(CHECKPOINT_PATH), check_same_thread=False)
        return SqliteSaver(conn), "sqlite"
    except Exception:
        from langgraph.checkpoint.memory import InMemorySaver
        return InMemorySaver(), "memory"

CHECKPOINTER, CHECKPOINTER_KIND = build_checkpointer()

def build_agent():
    """
    Create a tool-calling ReAct agent with memory.
    This follows the LangGraph "add memory" pattern using a checkpointer keyed by thread_id.
    """
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)

    tools = build_tools()

    # Compatibility: create_react_agent moved across versions.
    try:
        from langgraph.prebuilt import create_react_agent  # older path
        agent = create_react_agent(llm, tools, checkpointer=CHECKPOINTER)
        return agent
    except Exception:
        # Newer versions may not have prebuilt; fallback to langchain.agents
        from langchain.agents import create_react_agent as lc_create_react_agent
        agent = lc_create_react_agent(llm, tools)
        return agent

AGENT = None

def get_agent():
    global AGENT
    if AGENT is None:
        AGENT = build_agent()
    return AGENT


# =========================
# Agent runner (traceable wrapper)
# =========================

def invoke_agent(thread_id: str, task_type: str, user_prompt: str) -> Dict[str, Any]:
    """
    Run the agent under a thread_id, record a traceable payload, return payload.
    """
    meta = run_metadata(task_type)
    steps: List[StepTrace] = []

    # Step: memory touch (invoke a noop by reading state indirectly)
    # We rely on checkpointer in agent; we still record thread_id + checkpointer kind as evidence.
    steps.append(StepTrace(
        step_id=new_id("step"),
        name="memory_scope",
        started_at=utc_now(),
        ended_at=utc_now(),
        duration_ms=0,
        inputs={"thread_id": thread_id},
        outputs={"checkpointer_kind": CHECKPOINTER_KIND},
        evidence={"note": "Memory is keyed by thread_id via LangGraph checkpointer."},
    ))

    agent = get_agent()

    t0 = time.time()
    err = None
    raw = ""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        result = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]}, config=config)
        raw = result["messages"][-1].content if result and "messages" in result else ""
        raw = redact_text(raw)
    except Exception as e:
        err = redact_text(str(e))

    steps.append(StepTrace(
        step_id=new_id("step"),
        name="agent_invoke",
        started_at=utc_now(),
        ended_at=utc_now(),
        duration_ms=int((time.time() - t0) * 1000),
        inputs={"task_type": task_type},
        outputs={"raw_text_preview": raw[:2000]},
        error=err,
        evidence={"llm_model": LLM_MODEL},
    ))

    payload = {
        **meta,
        "decision": "Needs Human Review" if err else "Draft",
        "result": {"raw_text": raw, "error": err},
        "evidence": {"steps": [asdict(s) for s in steps]},
    }

    LOGGER.log(payload)
    return redact(payload)


# =========================
# Prompt templates (keep it simple + tool-focused)
# =========================

def fintech_prompt(income: float, debt: float, credit_score: int, requested_amount: float) -> str:
    return f"""
You are running the FinTech credit risk demo.
Use tools in this order:
1) fintech_score(income, debt, credit_score)
2) hitl_route(score_pd, requested_amount)

Then return:
- A short decision summary (Decision Draft vs Needs Human Review) and the reason.
- Include the tool JSON outputs in the response (copy them).
Inputs:
income={income}
debt={debt}
credit_score={credit_score}
requested_amount={requested_amount}
""".strip()

def te_pricing_prompt(cogs: float, landed: float, mult: float, discount: float) -> str:
    return f"""
You are running the TE pricing demo (consumer product use case).
Constraints:
- presale >= 7 * COGS
- retail > presale
Use tools:
1) te_pricing(cogs, landed, presale_mult, discount)
2) te_benchmark_placeholder()

Then return:
- Suggested presale and retail prices (from tool output)
- Policy checks status
- A short note on what data we need to make the demand model more accurate
Inputs:
cogs={cogs}
landed={landed}
presale_mult={mult}
discount={discount}
""".strip()


# =========================
# Gradio UI
# =========================

def build_gradio_app():
    import gradio as gr

    def run_fintech(income, debt, credit_score, requested_amount, thread_id):
        prompt = fintech_prompt(float(income), float(debt), int(credit_score), float(requested_amount))
        payload = invoke_agent(thread_id=str(thread_id), task_type="fintech_credit_risk", user_prompt=prompt)
        return payload["run_id"], json.dumps(payload, indent=2)

    def run_te(cogs, landed, mult, discount, thread_id):
        prompt = te_pricing_prompt(float(cogs), float(landed), float(mult), float(discount))
        payload = invoke_agent(thread_id=str(thread_id), task_type="te_pricing", user_prompt=prompt)
        return payload["run_id"], json.dumps(payload, indent=2)

    def view_logs(n):
        return json.dumps(LOGGER.tail(int(n)), indent=2)

    with gr.Blocks(title="Demo B") as demo:
        gr.Markdown(
            "## LangGraph Memory + Traceable Demo\n"
            "This demo shows a LangGraph/LangChain agent with memory (thread_id) and traceable run logs.\n"
            f"- Checkpointer: **{CHECKPOINTER_KIND}**\n"
        )

        with gr.Row():
            thread_id = gr.Textbox(value="demo_thread", label="thread_id (memory scope)")
            gr.Markdown(f"Logs: `{RUN_LOG_PATH}`  \nCheckpoints: `{CHECKPOINT_PATH}`")

        with gr.Tabs():
            with gr.Tab("FinTech: Credit Risk Demo"):
                gr.Markdown("Simple form. Agent calls tools and returns a traceable payload.")
                with gr.Row():
                    income = gr.Number(value=75000, label="Income (annual)")
                    debt = gr.Number(value=30000, label="Debt (total)")
                    credit_score = gr.Number(value=680, label="Credit score (300-850)")
                    requested_amount = gr.Number(value=250000, label="Requested amount")
                btn = gr.Button("Run FinTech agent")
                out_run = gr.Textbox(label="run_id")
                out_json = gr.Textbox(label="traceable output JSON", lines=22)
                btn.click(fn=run_fintech, inputs=[income, debt, credit_score, requested_amount, thread_id], outputs=[out_run, out_json])

            with gr.Tab("TE: Pricing Demo"):
                gr.Markdown(
                    "Consumer product use case. Agent computes presale + retail under constraints and shows benchmark placeholder.\n"
                    "For a real benchmark, replace placeholder with curated market dataset (or verified research)."
                )
                with gr.Row():
                    cogs = gr.Number(value=DEFAULT_COGS, label="COGS per unit")
                    landed = gr.Number(value=DEFAULT_LANDED, label="Landed cost per unit")
                    mult = gr.Number(value=DEFAULT_PRESALE_MULT, label="Presale floor multiplier (>=7)")
                    discount = gr.Slider(0.10, 0.40, value=DEFAULT_PRESALE_DISCOUNT, step=0.05, label="Presale discount vs retail")
                btn2 = gr.Button("Run TE pricing agent")
                out_run2 = gr.Textbox(label="run_id")
                out_json2 = gr.Textbox(label="traceable output JSON", lines=22)
                btn2.click(fn=run_te, inputs=[cogs, landed, mult, discount, thread_id], outputs=[out_run2, out_json2])

            with gr.Tab("Trace Logs"):
                n = gr.Slider(10, 200, value=30, step=10, label="show last N runs")
                btn3 = gr.Button("Refresh logs")
                logs_out = gr.Textbox(lines=24, label="logs (JSON list)")
                btn3.click(fn=view_logs, inputs=[n], outputs=[logs_out])

        gr.Markdown(
            "### Hugging Face deploy\n"
            "1) Rename this file to `app.py`\n"
            "2) Use the provided requirements file as `requirements.txt`\n"
            "3) Add `OPENAI_API_KEY` in Space Secrets\n\n"
            "Note: I can't provide a Hugging Face account for org access. Use your own HF username and ask to be added."
        )

    return demo


def main():
    demo = build_gradio_app()
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))


if __name__ == "__main__":
    main()

# http://localhost:7860 