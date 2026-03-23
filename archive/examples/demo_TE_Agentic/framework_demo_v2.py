"""
Simple Framework Demo (LangGraph + Traceable + Gradio)

What this demo is
- NOT a full data analysis agent
- A straightforward demo to showcase the workflow:
  1) Stateful memory via LangGraph (thread_id)
  2) Traceable outputs: run_id, model_id, version_id, policy_id, steps, evidence
  3) Two example cases:
     - FinTech credit risk (single-case scoring + HITL routing)
     - TE pricing (presale + retail), TE branding only on this tab
  4) Easy to deploy to Hugging Face: single file + requirements


Run locally
  python -m pip install -r requirements_demo.txt
  python framework_demo_2.py
Open:
  http://localhost:7860

HF Spaces
- Rename this file to app.py
- Keep requirements_demo.txt as requirements.txt
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
# Config (IDs + versions)
# =========================

AGENT_ID = os.getenv("AGENT_ID", "demo_agent")
MODEL_ID = os.getenv("MODEL_ID", "workflow_demo_model")
VERSION_ID = os.getenv("VERSION_ID", "0.1.0")

POLICY_ID = os.getenv("POLICY_ID", "hitl_and_pricing_policy")
POLICY_VERSION = os.getenv("POLICY_VERSION", "1.0")

# Keep all artifacts in ./data for HF Spaces
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

RUN_LOG_PATH = DATA_DIR / os.getenv("RUN_LOG_PATH", "run_logs.jsonl")
CHECKPOINT_PATH = DATA_DIR / os.getenv("CHECKPOINT_PATH", "checkpoints.sqlite")

# FinTech policy knobs (simple + explainable)
RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "0.50"))
BORDER_BAND = float(os.getenv("BORDER_BAND", "0.05"))
HIGH_IMPACT_AMOUNT = float(os.getenv("HIGH_IMPACT_AMOUNT", "1000000"))

# TE pricing defaults
DEFAULT_COGS = float(os.getenv("DEFAULT_COGS", "6"))
DEFAULT_LANDED = float(os.getenv("DEFAULT_LANDED", "10"))
DEFAULT_PRESALE_MULT = float(os.getenv("DEFAULT_PRESALE_MULT", "7"))
DEFAULT_PRESALE_DISCOUNT = float(os.getenv("DEFAULT_PRESALE_DISCOUNT", "0.20"))
DEFAULT_PRICE_GRID = [x for x in range(42, 121, 1)]  # 42..120


# =========================
# Helpers (time + IDs)
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
        "task_type": task_type,
        "timestamps": {"created_at": utc_now()},
    }


# =========================
# Secret redaction (safe logs)
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
# Traceable logging (JSONL)
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
# Deterministic tools (explainable)
# =========================

def fintech_risk_score(income: float, debt: float, credit_score: int) -> Dict[str, Any]:
    """
    Simple baseline score (explainable):
    - debt_to_income = debt / income
    - score_gap = (850 - credit_score) / 850
    - risk = 0.6 * debt_to_income + 0.4 * score_gap

    Output is a probability-like score in [0, ~] (not calibrated).
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

def hitl_route(risk_score_pd: float, requested_amount: float) -> Dict[str, Any]:
    """
    HITL routing policy:
    - If requested_amount >= HIGH_IMPACT_AMOUNT -> Needs Human Review
    - Else if risk_score >= threshold + band -> Needs Human Review (HIGH_RISK)
    - Else if within [threshold - band, threshold + band] -> Needs Human Review (BORDERLINE)
    - Else -> Decision Draft
    """
    thr = RISK_THRESHOLD
    band = BORDER_BAND
    high_impact = requested_amount >= HIGH_IMPACT_AMOUNT

    if high_impact:
        return {"decision": "Needs Human Review", "reason": "HIGH_IMPACT_CASE", "threshold": thr, "band": band}

    if risk_score_pd >= (thr + band):
        return {"decision": "Needs Human Review", "reason": "HIGH_RISK", "threshold": thr, "band": band}

    if (thr - band) <= risk_score_pd < (thr + band):
        return {"decision": "Needs Human Review", "reason": "BORDERLINE_SCORE", "threshold": thr, "band": band}

    return {"decision": "Decision Draft", "reason": "LOW_RISK", "threshold": thr, "band": band}


def te_optimize_pricing(
    cogs: float,
    landed: float,
    presale_mult: float,
    discount: float,
    alpha: float = 120.0,
    beta: float = 0.08,
) -> Dict[str, Any]:
    """
    Simple pricing demo:
    - Constraint: presale >= presale_mult * cogs (and presale >= 7*cogs when mult=7)
    - Demand curve placeholder: demand = alpha * exp(-beta * price)
    - Objective: maximize (price - landed) * demand over a small grid
    - Retail rule: retail = presale / (1 - discount), and retail > presale
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

    best = None
    for p in grid:
        demand = float(alpha * (2.718281828459045 ** (-beta * p)))
        profit = (p - landed) * demand
        if best is None or profit > best["objective_profit"]:
            best = {"presale": float(p), "demand": float(demand), "objective_profit": float(profit)}

    presale = float(best["presale"]) if best else float(floor)
    retail = presale / (1.0 - discount)

    # Friendly rounding to .99
    def as_99(x: float) -> float:
        v = round(x)
        return float(f"{max(v, 1) - 0.01:.2f}")

    presale = as_99(presale)
    retail = as_99(retail)

    policy_checks = {
        "presale_ge_floor": bool(presale >= floor),
        "presale_ge_7xcogs": bool(presale >= 7.0 * cogs),
        "retail_gt_presale": bool(retail > presale),
    }

    return {
        "presale_price": presale,
        "retail_price": retail,
        "unit_margin_presale": presale - landed,
        "unit_margin_retail": retail - landed,
        "assumptions": {"alpha": alpha, "beta": beta, "discount": discount},
        "optimization": best,
        "policy_checks": policy_checks,
        "benchmark_placeholder": [
            {"category": "smart_plug", "brand": "TP-Link Kasa"},
            {"category": "smart_plug", "brand": "Amazon Smart Plug"},
            {"category": "in_wall_outlet", "brand": "Leviton Decora Smart"},
            {"category": "premium", "brand": "Eve (Matter/Thread)"},
        ],
        "limitations": "Benchmark list is a placeholder. Replace with a curated dataset for evidence.",
    }


# =========================
# LangGraph (stateful memory via thread_id)
# =========================

def build_checkpointer():
    """
    SQLite saver if available; otherwise in-memory saver.
    This avoids the 'GeneratorContextManager' issue by using SqliteSaver(conn).
    """
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        conn = sqlite3.connect(str(CHECKPOINT_PATH), check_same_thread=False)
        return SqliteSaver(conn), "sqlite"
    except Exception:
        from langgraph.checkpoint.memory import InMemorySaver
        return InMemorySaver(), "memory"

CHECKPOINTER, CHECKPOINTER_KIND = build_checkpointer()

def build_graph():
    """
    Tiny LangGraph to keep short-term thread state.
    """
    from langgraph.graph import StateGraph, START, END

    class S(dict):
        pass

    def node_identity(state: S) -> S:
        # Short-term state stored per thread_id.
        # Return a NEW dict to avoid mutation edge cases.
        new_state: S = dict(state)

        ts = dict(new_state.get("thread_state", {}))
        if "created_at" not in ts:
            ts["created_at"] = utc_now()

        ts["last_seen"] = utc_now()
        ts["checkpointer_kind"] = CHECKPOINTER_KIND

        new_state["thread_state"] = ts
        return new_state

    g = StateGraph(S)
    g.add_node("identity", node_identity)
    g.add_edge(START, "identity")
    g.add_edge("identity", END)

    return g.compile(checkpointer=CHECKPOINTER)

GRAPH = build_graph()

def touch_memory(thread_id: str) -> Dict[str, Any]:
    """Touch LangGraph so the thread_id has short-term state.
    Some LangGraph versions may return None; we handle that safely.
    """
    out = GRAPH.invoke({"ping": True}, config={"configurable": {"thread_id": thread_id}})
    if not isinstance(out, dict):
        return {"note": "no_state_returned", "thread_id": thread_id}
    return out.get("thread_state", {})


# =========================
# Simple dashboard (straightforward)
# =========================

def dashboard_summary(last_n: int = 50) -> Dict[str, Any]:
    """
    Very simple dashboard:
    - total runs
    - last N breakdown by task_type
    - HITL rate for fintech scoring runs (if present)
    """
    rows = LOGGER.tail(last_n)
    total = len(rows)

    by_task: Dict[str, int] = {}
    hitl_flags: List[int] = []

    for r in rows:
        t = r.get("task_type", "unknown")
        by_task[t] = by_task.get(t, 0) + 1
        if t == "fintech_credit_risk":
            hitl_flags.append(1 if r.get("decision") == "Needs Human Review" else 0)

    hitl_rate = (sum(hitl_flags) / len(hitl_flags)) if hitl_flags else None
    return {"total_runs_in_tail": total, "by_task_type": by_task, "fintech_hitl_rate_in_tail": hitl_rate}


# =========================
# Gradio UI (HF friendly)
# =========================

def build_gradio_app():
    import gradio as gr

    def fintech_run(income, debt, credit_score, requested_amount, thread_id):
        meta = run_metadata("fintech_credit_risk")
        steps: List[StepTrace] = []
        created_at = meta["timestamps"]["created_at"]

        # Step: memory
        t0 = time.time()
        state = touch_memory(thread_id)
        steps.append(StepTrace(
            step_id=new_id("step"),
            name="memory_touch",
            started_at=utc_now(),
            ended_at=utc_now(),
            duration_ms=int((time.time() - t0) * 1000),
            inputs={"thread_id": thread_id},
            outputs={"thread_state": state},
            evidence={"checkpointer": CHECKPOINTER_KIND},
        ))

        # Step: compute score
        t1 = time.time()
        try:
            score = fintech_risk_score(float(income), float(debt), int(credit_score))
            steps.append(StepTrace(
                step_id=new_id("step"),
                name="risk_scoring",
                started_at=utc_now(),
                ended_at=utc_now(),
                duration_ms=int((time.time() - t1) * 1000),
                inputs={"income": float(income), "debt": float(debt), "credit_score": int(credit_score)},
                outputs=score,
            ))
        except Exception as e:
            payload = {
                **meta,
                "decision": "Needs Human Review",
                "result": {"error": redact_text(str(e))},
                "evidence": {"steps": [asdict(s) for s in steps]},
            }
            LOGGER.log(payload)
            safe = redact(payload)
            return safe["run_id"], json.dumps(safe, indent=2)

        # Step: HITL policy
        t2 = time.time()
        route = hitl_route(score["risk_score_pd"], float(requested_amount))
        steps.append(StepTrace(
            step_id=new_id("step"),
            name="hitl_policy",
            started_at=utc_now(),
            ended_at=utc_now(),
            duration_ms=int((time.time() - t2) * 1000),
            inputs={"risk_score_pd": score["risk_score_pd"], "requested_amount": float(requested_amount)},
            outputs=route,
            evidence={
                "policy": {"threshold": RISK_THRESHOLD, "border_band": BORDER_BAND, "high_impact_amount": HIGH_IMPACT_AMOUNT}
            },
        ))

        payload = {
            **meta,
            "decision": route["decision"],
            "result": {
                "risk_score_pd": score["risk_score_pd"],
                "requested_amount": float(requested_amount),
                "routing_reason": route["reason"],
                "explainability": {
                    "formula": score["formula"],
                    "intermediates": score["intermediates"],
                    "how_to_read": "Higher risk_score_pd means higher predicted risk (baseline, not calibrated).",
                },
            },
            "evidence": {"steps": [asdict(s) for s in steps]},
        }

        LOGGER.log(payload)
        safe = redact(payload)
        return safe["run_id"], json.dumps(safe, indent=2)

    def te_pricing_run(cogs, landed, mult, discount, thread_id):
        meta = run_metadata("te_pricing")
        steps: List[StepTrace] = []

        # Step: memory
        t0 = time.time()
        state = touch_memory(thread_id)
        steps.append(StepTrace(
            step_id=new_id("step"),
            name="memory_touch",
            started_at=utc_now(),
            ended_at=utc_now(),
            duration_ms=int((time.time() - t0) * 1000),
            inputs={"thread_id": thread_id},
            outputs={"thread_state": state},
            evidence={"checkpointer": CHECKPOINTER_KIND},
        ))

        # Step: pricing
        t1 = time.time()
        try:
            out = te_optimize_pricing(
                cogs=float(cogs),
                landed=float(landed),
                presale_mult=float(mult),
                discount=float(discount),
            )
            steps.append(StepTrace(
                step_id=new_id("step"),
                name="pricing_optimization",
                started_at=utc_now(),
                ended_at=utc_now(),
                duration_ms=int((time.time() - t1) * 1000),
                inputs={"cogs": float(cogs), "landed": float(landed), "presale_mult": float(mult), "discount": float(discount)},
                outputs={"presale_price": out["presale_price"], "retail_price": out["retail_price"], "policy_checks": out["policy_checks"]},
            ))
        except Exception as e:
            payload = {
                **meta,
                "decision": "Needs Human Review",
                "result": {"error": redact_text(str(e))},
                "evidence": {"steps": [asdict(s) for s in steps]},
            }
            LOGGER.log(payload)
            safe = redact(payload)
            return safe["run_id"], json.dumps(safe, indent=2)

        payload = {
            **meta,
            "decision": "Pricing Draft",
            "result": {
                "brand_context": "TE",
                "pricing": out,
                "explainability": {
                    "objective": "(price - landed) * demand(price)",
                    "demand_curve": "alpha * exp(-beta * price) (placeholder)",
                    "why_placeholder": "Replace alpha/beta using real presale conversion data.",
                },
            },
            "evidence": {"steps": [asdict(s) for s in steps], "brand_rule": "TE naming only on this tab."},
        }

        LOGGER.log(payload)
        safe = redact(payload)
        return safe["run_id"], json.dumps(safe, indent=2)

    def view_dashboard(n):
        return json.dumps(dashboard_summary(int(n)), indent=2)

    def view_logs(n):
        return json.dumps(LOGGER.tail(int(n)), indent=2)

    with gr.Blocks(title="Framework Demo (LangGraph + Traceable)") as demo:
        gr.Markdown(
            "## Framework Demo (LangGraph + Traceable)\n"
            "- FinTech tab: single-case credit risk + HITL routing\n"
            "- TE tab: presale + retail pricing (TE branding only here)\n"
            "- Logs tab: run_id + metadata + step traces\n"
        )

        with gr.Row():
            thread_id = gr.Textbox(value="demo_thread", label="thread_id (short-term memory)")
            gr.Markdown(f"Logs: `{RUN_LOG_PATH}`  \nCheckpoints: `{CHECKPOINT_PATH}`  \nCheckpointer: **{CHECKPOINTER_KIND}**")

        with gr.Tabs():
            with gr.Tab("FinTech: Credit Risk (Demo)"):
                gr.Markdown("Single-case demo. Inputs are simple and explainable.")
                with gr.Row():
                    income = gr.Number(value=75000, label="Income (annual)")
                    debt = gr.Number(value=30000, label="Debt (total)")
                    credit_score = gr.Number(value=680, label="Credit score (300-850)")
                    requested_amount = gr.Number(value=250000, label="Requested amount")
                btn = gr.Button("Run FinTech demo")
                out_run = gr.Textbox(label="run_id")
                out_json = gr.Textbox(label="output JSON", lines=22)
                btn.click(fn=fintech_run, inputs=[income, debt, credit_score, requested_amount, thread_id], outputs=[out_run, out_json])

                with gr.Accordion("Simple Dashboard (last N runs)", open=False):
                    n = gr.Slider(10, 200, value=50, step=10, label="N")
                    btn_d = gr.Button("Refresh dashboard")
                    dash_out = gr.Textbox(lines=8, label="dashboard JSON")
                    btn_d.click(fn=view_dashboard, inputs=[n], outputs=[dash_out])

            with gr.Tab("TE: Pricing (Demo)"):
                gr.Markdown("TE branding is used ONLY on this tab.")
                with gr.Row():
                    cogs = gr.Number(value=DEFAULT_COGS, label="COGS per unit")
                    landed = gr.Number(value=DEFAULT_LANDED, label="Landed cost per unit")
                    mult = gr.Number(value=DEFAULT_PRESALE_MULT, label="Presale floor multiplier (>=7)")
                    discount = gr.Slider(0.10, 0.40, value=DEFAULT_PRESALE_DISCOUNT, step=0.05, label="Presale discount vs retail")
                btn2 = gr.Button("Run TE pricing demo")
                out_run2 = gr.Textbox(label="run_id")
                out_json2 = gr.Textbox(label="output JSON", lines=22)
                btn2.click(fn=te_pricing_run, inputs=[cogs, landed, mult, discount, thread_id], outputs=[out_run2, out_json2])

            with gr.Tab("Trace Logs"):
                n2 = gr.Slider(10, 200, value=30, step=10, label="show last N runs")
                btn3 = gr.Button("Refresh logs")
                logs_out = gr.Textbox(lines=24, label="logs (JSON list)")
                btn3.click(fn=view_logs, inputs=[n2], outputs=[logs_out])

        gr.Markdown(
            "### Deploy to Hugging Face\n"
            "1) Rename this file to `app.py`\n"
            "2) Rename requirements_demo.txt to `requirements.txt`\n"
            "3) Push to a HF Space (Gradio)\n"
        )

    return demo


def main():
    demo = build_gradio_app()
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))


if __name__ == "__main__":
    main()
