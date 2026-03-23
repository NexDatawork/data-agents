from __future__ import annotations

import json
import math
import os
import sys
import time
import uuid
import traceback
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from openai import OpenAI

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


print("\n========== FINAL_APP v9.1 BOOT ==========")
print("RUNNING_FILE =", __file__)
print("CWD =", os.getcwd())
print("PYTHON =", sys.executable)
print("OPENAI_MODEL =", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
print("OPENAI_API_KEY_SET =", "YES" if bool(os.getenv("OPENAI_API_KEY", "")) else "NO")
print("========================================\n")


APP_TITLE = "Final Demo"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

AGENT_ID = os.getenv("AGENT_ID", "nexdatawork_demo_agent")
MODEL_ID = os.getenv("MODEL_ID", "llm_select_python_dispatch")
VERSION_ID = os.getenv("VERSION_ID", "9.1.0")

POLICY_ID = os.getenv("POLICY_ID", "no_toolcalling_python_dispatch_policy")
POLICY_VERSION = os.getenv("POLICY_VERSION", "9.1")

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
RUN_LOG_PATH = DATA_DIR / os.getenv("RUN_LOG_PATH", "run_logs.jsonl")

DEFAULT_SYNTHETIC_SEED = 42
HIGH_IMPACT_AMOUNT = float(os.getenv("HIGH_IMPACT_AMOUNT", "1000000"))
DEFAULT_PRICE_GRID = [x for x in range(42, 121, 1)]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def new_id(prefix: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{ts}_{uuid.uuid4().hex[:8]}"

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)

def run_metadata(task_type: str, thread_id: str) -> Dict[str, Any]:
    return {
        "run_id": new_id("run"),
        "agent_id": AGENT_ID,
        "model_id": MODEL_ID,
        "version_id": VERSION_ID,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "llm_model": OPENAI_MODEL,
        "task_type": task_type,
        "thread_id": thread_id,
        "timestamps": {"created_at": utc_now()},
    }


class JSONLLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload: Dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def tail(self, n: int = 50) -> List[Dict[str, Any]]:
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

LOGGER = JSONLLogger(RUN_LOG_PATH)


@dataclass
class StepTrace:
    step_id: str
    step_no: int
    title: str
    tool_used: str
    started_at: str
    ended_at: str
    duration_ms: int
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

def run_step(step_no: int, title: str, tool_used: str, inputs: Dict[str, Any], fn) -> Tuple[StepTrace, Any]:
    step_id = new_id("step")
    started = utc_now()
    t0 = time.time()
    err = None
    out = None
    out_obj: Dict[str, Any] = {}
    try:
        out = fn()
        if isinstance(out, dict):
            out_obj = out
        else:
            out_obj = {"value": out}
    except Exception:
        err = traceback.format_exc()
    ended = utc_now()
    dur = int((time.time() - t0) * 1000)
    return StepTrace(
        step_id=step_id,
        step_no=step_no,
        title=title,
        tool_used=tool_used,
        started_at=started,
        ended_at=ended,
        duration_ms=dur,
        inputs=inputs,
        outputs=out_obj if err is None else {},
        error=err,
    ), out


# -------------------------
# LLM (NO tool-calling): pick tool + write explanation
# -------------------------

def require_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY", ""):
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in the terminal or Space Secrets and rerun.")

def llm_choose_tool(client: OpenAI, mode: str, about: str, inputs: Dict[str, Any], allowed: List[str]) -> Dict[str, Any]:
    require_api_key()
    prompt = {
        "mode": mode,
        "about": about,
        "inputs": inputs,
        "allowed_tools": allowed,
        "instruction": (
            "Pick exactly one tool from allowed_tools. "
            "Return STRICT JSON with keys: selected_tool, short_reason. "
            "No markdown, no backticks."
        )
    }
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": "Output STRICT JSON only."},
            {"role": "user", "content": json.dumps(prompt)},
        ],
    )
    raw = (resp.choices[0].message.content or "").strip()
    obj = json.loads(raw)
    tool = str(obj.get("selected_tool", "")).strip()
    if tool not in allowed:
        tool = allowed[0]
    return {"selected_tool": tool, "short_reason": str(obj.get("short_reason", "")).strip()[:400], "raw": raw[:1200]}

def llm_explain(client: OpenAI, title: str, about: str, inputs: Dict[str, Any], results: Dict[str, Any]) -> str:
    require_api_key()
    payload = {
        "title": title,
        "about": about,
        "inputs": inputs,
        "results": results,
        "instruction": "Write 5-8 short bullets in English. No tool names. No code."
    }
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": "You are a business analyst."},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )
    return (resp.choices[0].message.content or "").strip()[:1500]


# =========================
# FinTech Python tools
# =========================

def fintech_build_row(inp: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([{
        "Income": inp["income"],
        "Debt": inp["debt"],
        "Credit_Score": inp["credit_score"],
        "Employment_Status": inp["employment_status"],
        "Missed_Payments_12m": inp["missed_payments_12m"],
        "Months_On_Book": inp["months_on_book"],
        "Credit_Lines": inp["credit_lines"],
        "Requested_Amount": inp["requested_amount"],
    }])

def fintech_preprocess(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    out = df.copy()
    missing_before = out.isna().sum().astype(int).to_dict()

    # simple deterministic missing handling
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            if out[col].isna().any():
                med = pd.to_numeric(out[col], errors="coerce").median()
                out[col] = pd.to_numeric(out[col], errors="coerce").fillna(med)
        else:
            if out[col].isna().any():
                out[col] = out[col].fillna("Unknown")

    missing_after = out.isna().sum().astype(int).to_dict()
    return out, {"missing_before": missing_before, "missing_after": missing_after}

def fintech_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["DTI"] = (out["Debt"] / out["Income"]).clip(lower=0, upper=5)
    out["Score_Gap"] = ((850 - out["Credit_Score"]) / 550).clip(lower=0, upper=1)
    out["Missed_Norm"] = (out["Missed_Payments_12m"].clip(lower=0, upper=12) / 12.0)
    out["Tenure_Norm"] = (out["Months_On_Book"].clip(lower=0, upper=120) / 120.0)
    out["Lines_Norm"] = (out["Credit_Lines"].clip(lower=0, upper=20) / 20.0)

    emp = out["Employment_Status"].astype(str).str.lower().str.strip()
    emp_w = emp.map({
        "employed": 0.00, "self-employed": 0.05, "student": 0.08,
        "unemployed": 0.18, "retired": 0.04, "contract": 0.06, "other": 0.07
    }).fillna(0.07)
    out["Employment_Risk_Weight"] = emp_w
    return out

def fintech_tool_heuristic(df_feat: pd.DataFrame) -> Dict[str, Any]:
    dti = float(df_feat.loc[0, "DTI"])
    gap = float(df_feat.loc[0, "Score_Gap"])
    missed = float(df_feat.loc[0, "Missed_Norm"])
    tenure = float(df_feat.loc[0, "Tenure_Norm"])
    lines = float(df_feat.loc[0, "Lines_Norm"])
    emp_w = float(df_feat.loc[0, "Employment_Risk_Weight"])

    x = -1.20 + 1.60*dti + 1.40*gap + 1.10*missed + 0.90*emp_w - 0.40*tenure - 0.25*lines
    pd_risk = sigmoid(x)
    conf = float(clamp(abs(pd_risk - 0.5) * 200.0, 0.0, 100.0))
    urg = float(clamp((100.0 - conf) * 0.75, 0.0, 100.0))
    return {"tool": "heuristic", "pd_risk": pd_risk, "confidence_0_100": conf, "hitl_urgency_0_100": urg}

def fintech_tool_logreg(df_case_feat: pd.DataFrame, seed: int = 42) -> Dict[str, Any]:
    # synthetic training
    rng = np.random.default_rng(seed)
    n = 1200
    income = rng.lognormal(mean=np.log(65000), sigma=0.55, size=n).clip(12000, 250000)
    debt = rng.lognormal(mean=np.log(18000), sigma=0.75, size=n).clip(0, 200000)
    score = rng.integers(300, 851, size=n)
    missed = rng.integers(0, 7, size=n)
    mob = rng.integers(0, 121, size=n)
    lines = rng.integers(0, 21, size=n)
    emp = rng.choice(["Employed","Self-employed","Student","Unemployed","Retired","Contract","Other"], size=n)

    df = pd.DataFrame({
        "Income": income, "Debt": debt, "Credit_Score": score,
        "Employment_Status": emp, "Missed_Payments_12m": missed,
        "Months_On_Book": mob, "Credit_Lines": lines,
    })
    df_feat = fintech_features(df)

    x = (-1.20 + 1.60*df_feat["DTI"] + 1.40*df_feat["Score_Gap"] + 1.10*df_feat["Missed_Norm"]
         + 0.90*df_feat["Employment_Risk_Weight"] - 0.40*df_feat["Tenure_Norm"] - 0.25*df_feat["Lines_Norm"])
    p = 1 / (1 + np.exp(-x))
    y = rng.binomial(1, p).astype(int)

    cols = ["DTI","Score_Gap","Missed_Norm","Tenure_Norm","Lines_Norm","Employment_Risk_Weight"]
    X = df_feat[cols].astype(float)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)

    model = LogisticRegression(max_iter=1000, solver="lbfgs")
    model.fit(X_tr, y_tr)

    auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))
    pd_risk = float(model.predict_proba(df_case_feat[cols].astype(float))[:, 1][0])
    conf = float(clamp(abs(pd_risk - 0.5) * 200.0, 0.0, 100.0))
    urg = float(clamp((100.0 - conf) * 0.75, 0.0, 100.0))
    return {"tool": "logreg_synth", "auc_test_synth": auc, "pd_risk": pd_risk, "confidence_0_100": conf, "hitl_urgency_0_100": urg}

FINTECH_TOOLS = {
    "heuristic": fintech_tool_heuristic,
    "logreg_synth": fintech_tool_logreg,
}

def fintech_recommend(score: Dict[str, Any], requested_amount: float) -> Dict[str, Any]:
    conf = float(score["confidence_0_100"])
    urg = float(score["hitl_urgency_0_100"])
    bump = 0.0
    if HIGH_IMPACT_AMOUNT > 0 and requested_amount > 0:
        ratio = requested_amount / HIGH_IMPACT_AMOUNT
        bump = 20.0 * clamp(math.log10(ratio + 1.0) / math.log10(11.0), 0.0, 1.0)
    urg2 = float(clamp(urg + bump, 0.0, 100.0))
    decision = "Needs Human Review" if (urg2 >= 60.0 or conf <= 25.0) else "Decision Draft"
    return {"decision": decision, "hitl_urgency_0_100": urg2}


# =========================
# TE Tools
# =========================
def te_tool_grid_demand(inp: Dict[str, Any]) -> Dict[str, Any]:
    cogs = float(inp["cogs"])
    landed = float(inp["landed"])
    mult = float(inp["presale_mult"])
    discount = float(inp["discount"])
    alpha = float(inp["alpha"])
    beta = float(inp["beta"])

    floor = mult * cogs
    grid = [p for p in DEFAULT_PRICE_GRID if p >= floor]
    best = None
    for p in grid:
        demand = float(alpha * math.exp(-beta * p))
        profit = (p - landed) * demand
        if best is None or profit > best["objective_profit"]:
            best = {"presale": float(p), "demand": float(demand), "objective_profit": float(profit)}

    presale = float(best["presale"]) if best else float(floor)
    retail = presale / (1.0 - discount)

    def as_99(x: float) -> float:
        v = round(x)
        return float(f"{max(v, 1) - 0.01:.2f}")

    presale = as_99(presale)
    retail = as_99(retail)

    return {
        "tool": "grid_demand",
        "presale_price": presale,
        "retail_price": retail,
        "checks": {"presale_ge_7xcogs": presale >= 7.0*cogs, "retail_gt_presale": retail > presale},
    }

def te_tool_rule_based(inp: Dict[str, Any]) -> Dict[str, Any]:
    cogs = float(inp["cogs"])
    landed = float(inp["landed"])
    mult = float(inp["presale_mult"])
    discount = float(inp["discount"])

    presale_floor = max(mult * cogs, 7.0 * cogs)
    presale = presale_floor
    retail = presale / (1.0 - discount)

    def as_99(x: float) -> float:
        v = round(x)
        return float(f"{max(v, 1) - 0.01:.2f}")

    presale = as_99(presale)
    retail = as_99(retail)

    return {
        "tool": "rule_based",
        "presale_price": presale,
        "retail_price": retail,
        "checks": {"presale_ge_7xcogs": presale >= 7.0*cogs, "retail_gt_presale": retail > presale},
    }

TE_TOOLS = {"grid_demand": te_tool_grid_demand, "rule_based": te_tool_rule_based}


# =========================
# Workflows
# =========================
FIVE_STEP_TITLES = [
    "Interpreting Context & Metrics",
    "Pre-Processing Data",
    "Processing Data",
    "Analyzing Data",
    "Trend Analysis & Predictions",
]

def run_fintech(client: OpenAI, thread_id: str, about: str, inp: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    meta = run_metadata("fintech", thread_id)
    steps: List[StepTrace] = []

    s1, _ = run_step(1, FIVE_STEP_TITLES[0], "context_capture", {"about": about[:300]}, lambda: {"about_len": len(about)})
    steps.append(s1)

    df_raw = fintech_build_row(inp)
    s2, prep = run_step(2, FIVE_STEP_TITLES[1], "fintech_preprocess", {}, lambda: fintech_preprocess(df_raw)[1])
    steps.append(s2)

    df_clean, _ = fintech_preprocess(df_raw)
    s3, feat_prev = run_step(3, FIVE_STEP_TITLES[2], "fintech_features", {}, lambda: {"features": fintech_features(df_clean)[["DTI","Score_Gap","Missed_Norm","Tenure_Norm","Employment_Risk_Weight"]].iloc[0].to_dict()})
    steps.append(s3)

    df_feat = fintech_features(df_clean)

    choice = llm_choose_tool(client, "fintech", about, inp, allowed=list(FINTECH_TOOLS.keys()))
    chosen = choice["selected_tool"]

    def _score():
        fn = FINTECH_TOOLS[chosen]
        if chosen == "heuristic":
            return fn(df_feat)  # type: ignore
        return fn(df_feat, seed=DEFAULT_SYNTHETIC_SEED)  # type: ignore

    s4, score = run_step(4, FIVE_STEP_TITLES[3], f"python_dispatch::{chosen}", {"llm_reason": choice["short_reason"]}, _score)
    steps.append(s4)

    score = score if isinstance(score, dict) else fintech_tool_heuristic(df_feat)
    s5, rec = run_step(5, FIVE_STEP_TITLES[4], "fintech_recommend", {}, lambda: fintech_recommend(score, float(inp["requested_amount"])))
    steps.append(s5)
    rec = rec if isinstance(rec, dict) else {"decision": "Needs Human Review", "hitl_urgency_0_100": 100.0}

    final = {
        "decision": rec["decision"],
        "pd_risk": float(score["pd_risk"]),
        "confidence_0_100": float(score["confidence_0_100"]),
        "hitl_urgency_0_100": float(rec["hitl_urgency_0_100"]),
        "selected_tool": chosen,
        "llm_reason": choice["short_reason"],
    }

    explanation = llm_explain(client, "FinTech Credit Risk", about, inp, final)
    report = (
        "## Summary\n"
        f"- Decision: **{final['decision']}**\n"
        f"- PD risk: **{final['pd_risk']:.3f}**\n"
        f"- Confidence: **{final['confidence_0_100']:.1f}/100**\n"
        f"- HITL urgency: **{final['hitl_urgency_0_100']:.1f}/100**\n\n"
        "## Explanation\n"
        f"{explanation}"
    )

    payload = {**meta, "about": about, "inputs": inp, "steps": [asdict(x) for x in steps], "outputs": {"final": final, "llm_choice": choice, "prep": prep, "feat": feat_prev}}
    LOGGER.append(payload)
    return report, payload

def run_te(client: OpenAI, thread_id: str, about: str, inp: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    meta = run_metadata("te_pricing", thread_id)
    steps: List[StepTrace] = []

    s1, _ = run_step(1, FIVE_STEP_TITLES[0], "context_capture", {"about": about[:300]}, lambda: {"about_len": len(about)})
    steps.append(s1)

    s2, checks = run_step(2, FIVE_STEP_TITLES[1], "te_input_checks", {}, lambda: {"checks": {"discount_ok": 0.0 < float(inp["discount"]) < 0.9}})
    steps.append(s2)

    s3, derived = run_step(3, FIVE_STEP_TITLES[2], "te_derive", {}, lambda: {"presale_floor": max(float(inp["presale_mult"])*float(inp["cogs"]), 7.0*float(inp["cogs"]))})
    steps.append(s3)

    choice = llm_choose_tool(client, "te_pricing", about, inp, allowed=list(TE_TOOLS.keys()))
    chosen = choice["selected_tool"]

    s4, pricing = run_step(4, FIVE_STEP_TITLES[3], f"python_dispatch::{chosen}", {"llm_reason": choice["short_reason"]}, lambda: TE_TOOLS[chosen](inp))
    steps.append(s4)
    pricing = pricing if isinstance(pricing, dict) else TE_TOOLS["rule_based"](inp)

    s5, _ = run_step(5, FIVE_STEP_TITLES[4], "te_summary", {}, lambda: {"presale_price": pricing["presale_price"], "retail_price": pricing["retail_price"], "checks": pricing["checks"]})
    steps.append(s5)

    final = {"presale_price": pricing["presale_price"], "retail_price": pricing["retail_price"], "checks": pricing["checks"], "selected_tool": chosen, "llm_reason": choice["short_reason"]}
    explanation = llm_explain(client, "TE Pricing", about, inp, final)

    report = (
        "## Summary\n"
        f"- Presale price: **{final['presale_price']}**\n"
        f"- Retail price: **{final['retail_price']}**\n"
        f"- Checks: `{final['checks']}`\n\n"
        "## Explanation\n"
        f"{explanation}"
    )

    payload = {**meta, "about": about, "inputs": inp, "steps": [asdict(x) for x in steps], "outputs": {"final": final, "llm_choice": choice, "checks": checks, "derived": derived}}
    LOGGER.append(payload)
    return report, payload


# =========================
# Gradio UI
# =========================
def build_gradio_app():
    import gradio as gr

    # IMPORTANT: require key so you can confirm API is actually used
    require_api_key()
    client = OpenAI()

    STATE: Dict[str, Any] = {"last_payload": None}
    emp_choices = ["Employed", "Self-employed", "Student", "Unemployed", "Retired", "Contract", "Other"]

    def safe_call(fn):
        try:
            return fn()
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            return "ERROR:\n\n```text\n" + tb + "\n```", ""

    def ui_fintech(about, income, debt, credit_score, employment_status, missed_12m, months_on_book, credit_lines, requested_amount, thread_id):
        def _do():
            inp = {
                "income": float(income),
                "debt": float(debt),
                "credit_score": int(credit_score),
                "employment_status": str(employment_status),
                "missed_payments_12m": int(missed_12m),
                "months_on_book": int(months_on_book),
                "credit_lines": int(credit_lines),
                "requested_amount": float(requested_amount),
            }
            report, payload = run_fintech(client, str(thread_id), str(about or ""), inp)
            STATE["last_payload"] = payload
            return report, payload["run_id"]
        return safe_call(_do)

    def ui_te(about2, cogs, landed, mult, discount, alpha, beta, thread_id):
        def _do():
            inp = {
                "cogs": float(cogs),
                "landed": float(landed),
                "presale_mult": float(mult),
                "discount": float(discount),
                "alpha": float(alpha),
                "beta": float(beta),
            }
            report, payload = run_te(client, str(thread_id), str(about2 or ""), inp)
            STATE["last_payload"] = payload
            return report, payload["run_id"]
        return safe_call(_do)

    def ui_current_trace():
        p = STATE.get("last_payload")
        if not p:
            return "No run yet."
        return json.dumps(p, indent=2)

    def ui_logs(n):
        return json.dumps(LOGGER.tail(int(n)), indent=2)

    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown("## Final Demo (API ON, LLM selects tool, Python executes)")

        with gr.Row():
            thread_id = gr.Textbox(value="demo_thread", label="thread_id")

        with gr.Tabs():
            with gr.Tab("FinTech"):
                with gr.Row():
                    with gr.Column(scale=5, min_width=460):
                        gr.Markdown("### Inputs")
                        about = gr.Textbox(label="About this account", lines=6, placeholder="Type customer context here.")

                        employment_status = gr.Dropdown(choices=emp_choices, value="Employed", label="Employment status")

                        with gr.Row():
                            income = gr.Number(value=75000, label="Income (annual)")
                            debt = gr.Number(value=30000, label="Debt (total)")
                        with gr.Row():
                            credit_score = gr.Number(value=680, label="Credit score (300-850)")
                            requested_amount = gr.Number(value=250000, label="Requested amount")
                        with gr.Row():
                            missed_12m = gr.Number(value=1, label="Missed payments (12m)")
                            months_on_book = gr.Number(value=18, label="Months on book")
                        credit_lines = gr.Number(value=4, label="Credit lines")
                        btn = gr.Button("Run", variant="primary")

                    with gr.Column(scale=7, min_width=640):
                        gr.Markdown("### Output")
                        out = gr.Markdown(value="_(Run to see result.)_")
                        run_id_out = gr.Textbox(label="run_id")

                btn.click(
                    fn=ui_fintech,
                    inputs=[about, income, debt, credit_score, employment_status, missed_12m, months_on_book, credit_lines, requested_amount, thread_id],
                    outputs=[out, run_id_out],
                )

            with gr.Tab("TE"):
                with gr.Row():
                    with gr.Column(scale=5, min_width=460):
                        gr.Markdown("### Inputs")
                        about2 = gr.Textbox(label="About this product", lines=6, placeholder="Type product/customer context here.")

                        with gr.Row():
                            cogs = gr.Number(value=6, label="COGS per unit")
                            landed = gr.Number(value=10, label="Landed cost per unit")
                        with gr.Row():
                            mult = gr.Number(value=7, label="Presale floor multiplier")
                            discount = gr.Number(value=0.20, label="Discount (0-0.9)")
                        with gr.Row():
                            alpha = gr.Number(value=120, label="Demand alpha (placeholder)")
                            beta = gr.Number(value=0.08, label="Demand beta (placeholder)")
                        btn2 = gr.Button("Run", variant="primary")

                    with gr.Column(scale=7, min_width=640):
                        gr.Markdown("### Output")
                        out2 = gr.Markdown(value="_(Run to see result.)_")
                        run_id_out2 = gr.Textbox(label="run_id")

                btn2.click(
                    fn=ui_te,
                    inputs=[about2, cogs, landed, mult, discount, alpha, beta, thread_id],
                    outputs=[out2, run_id_out2],
                )

            with gr.Tab("Trace"):
                gr.Markdown("### Current run (full trace JSON)")
                btn3 = gr.Button("Show current run")
                cur = gr.Code(language="json")
                btn3.click(fn=ui_current_trace, inputs=[], outputs=[cur])

                gr.Markdown("### Log tail (JSONL)")
                n = gr.Slider(10, 200, value=30, step=10, label="show last N runs")
                btn4 = gr.Button("Refresh logs")
                logs = gr.Code(language="json")
                btn4.click(fn=ui_logs, inputs=[n], outputs=[logs])

    return demo


def main():
    app = build_gradio_app()
    app.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")), debug=True)


if __name__ == "__main__":
    main()
# http://localhost:7860 