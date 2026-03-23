from __future__ import annotations

"""
FINAL DEMO (v10.2): Stable, runs locally + HF Spaces.

Design goals (per your 5-step analyst workflow)
- Output must always be non-empty and human-readable.
- Trace tab must record: run_id / model_id / version_id / policy_id + 5 steps + tool_used per step.
- NO LangGraph. NO LLM tool-calling.
- FinTech:
  - Python computes PD + confidence + HITL urgency (and optional model choice via LLM selector).
  - Output includes explicit prediction + decision bullet.
- TE Pricing:
  - Primary: Python "pricing_heuristic" (value/segment/channel aware) so it won't stick to 42/52.
  - Optional: LLM proposes a price range and adjustments (no browsing). If LLM fails, we still output a valid result.
  - Hard constraints enforced in Python: presale >= max(7*COGS, mult*COGS), retail > presale.

HF Spaces:
- Rename to app.py
- Set OPENAI_API_KEY in Space Secrets (optional for TE/FinTech explanation add-on, NOT required for base output)
"""

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

# OpenAI is OPTIONAL (we never allow "no content" if API fails)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


print("\n========== FINAL_APP BOOT (v10.6) ==========")
print("RUNNING_FILE =", __file__)
print("CWD =", os.getcwd())
print("PYTHON =", sys.executable)
print("OPENAI_MODEL =", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
print("OPENAI_API_KEY_SET =", "YES" if bool(os.getenv("OPENAI_API_KEY", "")) else "NO")
print("===========================================\n")


# =========================
# Config
# =========================
APP_TITLE = "Demo C"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

AGENT_ID = os.getenv("AGENT_ID", "nexdatawork_demo_agent")
MODEL_ID = os.getenv("MODEL_ID", "python_5step_traceable")
VERSION_ID = os.getenv("VERSION_ID", "10.6.0")

POLICY_ID = os.getenv("POLICY_ID", "5step_traceable_policy")
POLICY_VERSION = os.getenv("POLICY_VERSION", "10.6")

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
RUN_LOG_PATH = DATA_DIR / os.getenv("RUN_LOG_PATH", "run_logs.jsonl")

DEFAULT_SYNTHETIC_SEED = 42
HIGH_IMPACT_AMOUNT = float(os.getenv("HIGH_IMPACT_AMOUNT", "1000000"))


# =========================
# Helpers
# =========================
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

def as_99(x: float) -> float:
    v = round(float(x))
    return float(f"{max(v, 1) - 0.01:.2f}")

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


# =========================
# JSONL Logger
# =========================
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


# =========================
# Trace structures
# =========================
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


# =========================
# Optional LLM helpers (never required)
# =========================
def _client_or_none():
    if OpenAI is None:
        return None
    if not os.getenv("OPENAI_API_KEY", ""):
        return None
    try:
        return OpenAI()
    except Exception:
        return None

def llm_te_adjustment(client: Any, about: str, inputs: Dict[str, Any], base: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional: ask LLM for adjustment factor and competitor range.
    Must not break if it fails.
    """
    prompt = {
        "about": about,
        "inputs": inputs,
        "base": base,
        "instruction": (
            "No browsing. Return STRICT JSON: "
            "{"
            "\"adj_presale_delta\": number, "
            "\"adj_retail_delta\": number, "
            "\"competitor_range\": {\"low\": number, \"high\": number}, "
            "\"confidence_0_100\": number, "
            "\"rationale_bullets\": [..]"
            "}. Keep bullets 4-7."
        ),
    }
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Return STRICT JSON only. No markdown."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
        obj = json.loads(raw)
        return {
            "adj_presale_delta": float(obj.get("adj_presale_delta", 0.0)),
            "adj_retail_delta": float(obj.get("adj_retail_delta", 0.0)),
            "competitor_range": obj.get("competitor_range", {}) or {"low": 0.0, "high": 0.0},
            "confidence_0_100": float(clamp(float(obj.get("confidence_0_100", 50.0)), 0.0, 100.0)),
            "rationale_bullets": [str(x)[:200] for x in (obj.get("rationale_bullets", []) or [])][:10],
            "raw": raw[:1400],
        }
    except Exception as e:
        return {
            "error": str(e)[:400],
            "adj_presale_delta": 0.0,
            "adj_retail_delta": 0.0,
            "competitor_range": {"low": 0.0, "high": 0.0},
            "confidence_0_100": 0.0,
            "rationale_bullets": ["LLM adjustment unavailable (API missing or invalid JSON)."],
        }


# =========================
# FinTech tools
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
        "Savings": inp["savings"],
        "Collateral_Value": inp["collateral_value"],
        "Fraud_Flag": inp["fraud_flag"],
        "Existing_Customer": inp["existing_customer"],
    }])

def fintech_preprocess(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    out = df.copy()
    missing_before = out.isna().sum().astype(int).to_dict()
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
    income = out["Income"].clip(lower=1.0)
    debt = out["Debt"].clip(lower=0.0)
    savings = out["Savings"].clip(lower=0.0)
    collateral = out["Collateral_Value"].clip(lower=0.0)
    amount = out["Requested_Amount"].clip(lower=1.0)

    out["DTI"] = (debt / income).clip(lower=0, upper=5)
    out["Savings_to_Income"] = (savings / income).clip(lower=0, upper=5)
    out["Collateral_to_Amount"] = (collateral / amount).clip(lower=0, upper=10)

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

    out["Fraud_Risk"] = out["Fraud_Flag"].astype(int).clip(0, 1)
    out["Loyalty_Boost"] = out["Existing_Customer"].astype(int).clip(0, 1)
    return out

def fintech_tool_heuristic(df_feat: pd.DataFrame) -> Dict[str, Any]:
    f = df_feat.iloc[0].to_dict()
    x = (
        -1.10
        + 1.50 * f["DTI"]
        + 1.20 * f["Score_Gap"]
        + 0.95 * f["Missed_Norm"]
        + 0.70 * f["Employment_Risk_Weight"]
        - 0.35 * f["Tenure_Norm"]
        - 0.25 * f["Lines_Norm"]
        - 0.45 * f["Savings_to_Income"]
        - 0.35 * f["Collateral_to_Amount"]
        + 2.00 * f["Fraud_Risk"]
        - 0.20 * f["Loyalty_Boost"]
    )
    pd_risk = sigmoid(float(x))
    conf = float(clamp(abs(pd_risk - 0.5) * 200.0, 0.0, 100.0))
    urg = float(clamp((100.0 - conf) * 0.75, 0.0, 100.0))
    return {"tool": "heuristic", "pd_risk": pd_risk, "confidence_0_100": conf, "hitl_urgency_0_100": urg, "linear_x": float(x)}

def _fintech_make_synth_training(seed: int = 42, n: int = 1500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    income = rng.lognormal(mean=np.log(65000), sigma=0.55, size=n).clip(12000, 250000)
    debt = rng.lognormal(mean=np.log(18000), sigma=0.75, size=n).clip(0, 200000)
    score = rng.integers(300, 851, size=n)
    missed = rng.integers(0, 7, size=n)
    mob = rng.integers(0, 121, size=n)
    lines = rng.integers(0, 21, size=n)
    savings = rng.lognormal(mean=np.log(8000), sigma=0.9, size=n).clip(0, 200000)
    collateral = rng.lognormal(mean=np.log(15000), sigma=0.9, size=n).clip(0, 300000)
    fraud = rng.binomial(1, 0.03, size=n)
    existing = rng.binomial(1, 0.55, size=n)
    emp = rng.choice(["Employed","Self-employed","Student","Unemployed","Retired","Contract","Other"], size=n)
    req_amount = rng.lognormal(mean=np.log(25000), sigma=0.8, size=n).clip(500, 250000)

    df = pd.DataFrame({
        "Income": income, "Debt": debt, "Credit_Score": score,
        "Employment_Status": emp, "Missed_Payments_12m": missed,
        "Months_On_Book": mob, "Credit_Lines": lines,
        "Requested_Amount": req_amount,
        "Savings": savings,
        "Collateral_Value": collateral,
        "Fraud_Flag": fraud,
        "Existing_Customer": existing,
    })
    df_clean, _ = fintech_preprocess(df)
    df_feat = fintech_features(df_clean)

    x = (
        -1.10
        + 1.50 * df_feat["DTI"]
        + 1.20 * df_feat["Score_Gap"]
        + 0.95 * df_feat["Missed_Norm"]
        + 0.70 * df_feat["Employment_Risk_Weight"]
        - 0.35 * df_feat["Tenure_Norm"]
        - 0.25 * df_feat["Lines_Norm"]
        - 0.45 * df_feat["Savings_to_Income"]
        - 0.35 * df_feat["Collateral_to_Amount"]
        + 2.00 * df_feat["Fraud_Risk"]
        - 0.20 * df_feat["Loyalty_Boost"]
    )
    p = 1 / (1 + np.exp(-x))
    y = rng.binomial(1, p).astype(int)

    df_feat = df_feat.copy()
    df_feat["y"] = y
    return df_feat

def fintech_tool_logreg_synth(df_case_feat: pd.DataFrame, seed: int = 42) -> Dict[str, Any]:
    train_df = _fintech_make_synth_training(seed=seed, n=1500)
    cols = [
        "DTI","Score_Gap","Missed_Norm","Tenure_Norm","Lines_Norm",
        "Employment_Risk_Weight","Savings_to_Income","Collateral_to_Amount","Fraud_Risk","Loyalty_Boost"
    ]
    X = train_df[cols].astype(float)
    y = train_df["y"].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    model = LogisticRegression(max_iter=1000, solver="lbfgs")
    model.fit(X_tr, y_tr)

    auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))
    case_x = df_case_feat[cols].astype(float)

    pd_risk = float(model.predict_proba(case_x)[:, 1][0])
    conf = float(clamp(abs(pd_risk - 0.5) * 200.0, 0.0, 100.0))
    urg = float(clamp((100.0 - conf) * 0.75, 0.0, 100.0))
    return {"tool": "logreg_synth", "auc_test_synth": auc, "pd_risk": pd_risk, "confidence_0_100": conf, "hitl_urgency_0_100": urg}

def fintech_tool_tree_synth(df_case_feat: pd.DataFrame, seed: int = 42) -> Dict[str, Any]:
    train_df = _fintech_make_synth_training(seed=seed, n=1500)
    cols = [
        "DTI","Score_Gap","Missed_Norm","Tenure_Norm","Lines_Norm",
        "Employment_Risk_Weight","Savings_to_Income","Collateral_to_Amount","Fraud_Risk","Loyalty_Boost"
    ]
    X = train_df[cols].astype(float)
    y = train_df["y"].astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
    model = DecisionTreeClassifier(max_depth=4, random_state=seed)
    model.fit(X_tr, y_tr)

    auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))
    case_x = df_case_feat[cols].astype(float)

    pd_risk = float(model.predict_proba(case_x)[:, 1][0])
    conf = float(clamp(abs(pd_risk - 0.5) * 200.0, 0.0, 100.0))
    urg = float(clamp((100.0 - conf) * 0.75, 0.0, 100.0))
    return {"tool": "tree_synth", "auc_test_synth": auc, "pd_risk": pd_risk, "confidence_0_100": conf, "hitl_urgency_0_100": urg}

FINTECH_TOOL_REGISTRY = {
    "heuristic": fintech_tool_heuristic,
    "logreg_synth": fintech_tool_logreg_synth,
    "tree_synth": fintech_tool_tree_synth,
}

def fintech_recommend(score: Dict[str, Any], requested_amount: float) -> Dict[str, Any]:
    conf = float(score.get("confidence_0_100", 0.0))
    urg = float(score.get("hitl_urgency_0_100", 100.0))
    bump = 0.0
    if HIGH_IMPACT_AMOUNT > 0 and requested_amount > 0:
        ratio = requested_amount / HIGH_IMPACT_AMOUNT
        bump = 20.0 * clamp(math.log10(ratio + 1.0) / math.log10(11.0), 0.0, 1.0)
    urg2 = float(clamp(urg + bump, 0.0, 100.0))
    decision = "Needs Human Review" if (urg2 >= 60.0 or conf <= 25.0) else "Decision Draft"
    return {"decision": decision, "hitl_urgency_0_100": urg2, "prediction_pd": float(score.get("pd_risk", 0.5))}


# =========================
# TE pricing heuristic (PRIMARY)
# =========================
def te_pricing_heuristic(inp: Dict[str, Any]) -> Dict[str, Any]:
    cogs = float(inp["cogs"])
    landed = float(inp["landed"])
    mult = float(inp["presale_mult"])
    discount = float(inp["discount"])
    channel = str(inp.get("channel", "DTC"))
    segment = str(inp.get("target_segment", "Mid-market"))
    units = int(inp.get("expected_presale_units", 0))

    # User-friendly demand controls (0-100)
    demand_index = float(inp.get("demand_index", 60.0))
    price_sensitivity = float(inp.get("price_sensitivity", 60.0))
    price_step = float(inp.get("price_step", 10.0))
    demand_index = clamp(demand_index, 0.0, 100.0)
    price_sensitivity = clamp(price_sensitivity, 0.0, 100.0)
    price_step = max(1.0, float(price_step))

    floor = max(7.0 * cogs, mult * cogs)

    # segment anchor retail
    # (pure heuristic so the AI demo doesn't get stuck at 42/52)
    if segment.lower().startswith("budget"):
        retail_anchor = 79.99
    elif segment.lower().startswith("premium"):
        retail_anchor = 149.99
    else:
        retail_anchor = 109.99

    # channel adjustments
    if channel.lower() == "amazon":
        retail_anchor -= 10.0
    elif channel.lower() == "retail":
        retail_anchor += 10.0
    elif channel.lower() == "wholesale":
        retail_anchor -= 15.0

    # volume signal: more units -> can accept slightly lower retail
    if units >= 5000:
        retail_anchor -= 8.0
    elif units >= 2000:
        retail_anchor -= 4.0
    elif units > 0 and units < 300:
        retail_anchor += 6.0

    # Demand controls: higher demand_index supports higher willingness-to-pay; higher sensitivity pushes price down.
    retail_anchor += (demand_index - 50.0) * 0.3  # up to about +/-15
    retail_anchor -= (price_sensitivity - 50.0) * 0.2  # up to about +/-10

    retail_floor_from_discount = floor / max(1e-6, (1.0 - discount))
    retail = max(retail_anchor, retail_floor_from_discount)

    presale = retail * (1.0 - discount)
    presale = max(presale, floor)

    presale = as_99(presale)
    retail = as_99(retail)

    # ensure retail>presale strictly
    if retail <= presale:
        retail = as_99(presale / max(1e-6, (1.0 - discount)))

    checks = {
        "presale_ge_7xcogs": presale >= 7.0 * cogs,
        "presale_ge_floor": presale >= floor,
        "retail_gt_presale": retail > presale,
        "presale_gt_landed": presale > landed,
        "retail_gt_landed": retail > landed,
    }

    return {
        "tool": "pricing_heuristic",
        "floor": floor,
        "presale_price": presale,
        "retail_price": retail,
        "unit_margin_presale": float(presale - landed),
        "unit_margin_retail": float(retail - landed),
        "checks": checks,
        "anchors": {"segment": segment, "channel": channel, "retail_anchor": retail_anchor, "units": units, "demand_index": demand_index, "price_sensitivity": price_sensitivity, "price_step": price_step},
    }


# =========================
# 5-step explanation builder (Python, always non-empty)
# =========================
def build_5step_explanation_md(title: str, step_bullets: Dict[int, List[str]], evidence_md: str, prediction_bullet: str, decision_bullet: str) -> str:
    md: List[str] = []
    md.append("## Explanation")
    # Use professional workflow section titles instead of "Step 1..5"
    for i in range(1, 6):
        section_title = FIVE_STEP_TITLES[i - 1]
        md.append(f"### {section_title}")
        blt = step_bullets.get(i, [])
        if not blt:
            blt = ["(no content)"]
        for b in blt[:8]:
            md.append(f"- {b}")
    md.append("")
    md.append("## Evidence")
    md.append(evidence_md.strip() if evidence_md.strip() else "- (no evidence)")
    md.append("")
    md.append("## Prediction")
    md.append(f"- {prediction_bullet}")
    md.append("")
    md.append("## Decision")
    md.append(f"- {decision_bullet}")
    return "\n".join(md).strip()



# =========================
# Simple visualizations (matplotlib)
# =========================
def plot_fintech_pd_bar(pd_risk: float):
    """
    Gauge-style horizontal bar (0-100%).
    Robust for a single probability value.
    """
    import matplotlib.pyplot as plt

    pd_risk = float(clamp(pd_risk, 0.0, 1.0))
    pct = pd_risk * 100.0

    fig = plt.figure(figsize=(6.0, 1.6))
    ax = fig.add_subplot(111)

    # Background track (100%)
    ax.barh([0], [100], height=0.5, color="#e6e6e6")

    # Foreground value
    ax.barh([0], [pct], height=0.5, color="#1f77b4")

    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xlabel("PD (%)")
    ax.set_title(f"Delinquency probability (PD): {pct:.1f}%")

    # Label at the end of the filled bar
    ax.text(min(pct + 2, 98), 0, f"{pct:.1f}%", va="center", ha="left", fontsize=11)

    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig

def plot_te_price_stacked(presale: float, retail: float):
    """
    Overlay bars: Retail is the taller bar; Presale is the shorter bar on top (same x).
    Also annotate values on bars. Keep it minimal and robust.
    """
    import matplotlib.pyplot as plt

    presale = float(max(presale, 0.0))
    retail = float(max(retail, presale))

    fig = plt.figure(figsize=(6.0, 2.2))
    ax = fig.add_subplot(111)

    x = [0]
    # Draw retail first (background), then presale (foreground)
    bars_retail = ax.bar(x, [retail], width=0.6, color="#9f1bdd", label="Retail")
    bars_presale = ax.bar(x, [presale], width=0.6, color="#4d74f3", label="Presale")

    ax.set_xticks(x)
    ax.set_xticklabels(["Price"])
    ax.set_ylabel("$")
    ax.set_title("Presale vs Retail")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ymax = max(retail, presale)
    ax.set_ylim(0, ymax * 1.25)

    # Put legend outside the plot area on the right
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    # Annotate values
    def annotate(bar, value: float):
        rect = bar[0]
        ax.text(
            rect.get_x() + rect.get_width() / 2.0,
            rect.get_height() + max(1.0, 0.02 * retail),
            f"${value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    annotate(bars_retail, retail)
    annotate(bars_presale, presale)

    fig.tight_layout()
    return fig

# =========================
# Workflows
# =========================
FIVE_STEP_TITLES = [
    "Interpreting Context & Metrics (Questions + EDA)",
    "Pre-Processing Data (Cleaning + Missing Values)",
    "Processing Data (Transform + Feature Build)",
    "Analyzing Data (Modeling + Scoring)",
    "Trend Analysis & Predictions (Decision + Share)",
]
def run_fintech_workflow(thread_id: str, about: str, inp: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    meta = run_metadata("fintech", thread_id)
    steps: List[StepTrace] = []

    s1, _ = run_step(1, FIVE_STEP_TITLES[0], "context_capture", {"about_preview": about[:200]}, lambda: {"about_len": len(about)})
    steps.append(s1)

    df_raw = fintech_build_row(inp)
    df_clean, prep = fintech_preprocess(df_raw)
    s2, _ = run_step(2, FIVE_STEP_TITLES[1], "fintech_preprocess", {}, lambda: prep)
    steps.append(s2)

    df_feat = fintech_features(df_clean)
    feat_preview = df_feat[[
        "DTI","Score_Gap","Missed_Norm","Tenure_Norm","Lines_Norm",
        "Savings_to_Income","Collateral_to_Amount","Fraud_Risk","Loyalty_Boost"
    ]].iloc[0].to_dict()
    s3, _ = run_step(3, FIVE_STEP_TITLES[2], "fintech_features", {}, lambda: {"feature_preview": feat_preview})
    steps.append(s3)

    # Model tool selection: default heuristic; if you later want LLM selector here, it can be added safely.
    chosen_tool = "logreg_synth" if inp.get("use_ml_model", True) else "heuristic"
    if chosen_tool not in FINTECH_TOOL_REGISTRY:
        chosen_tool = "heuristic"

    def _score():
        fn = FINTECH_TOOL_REGISTRY[chosen_tool]
        if chosen_tool == "heuristic":
            return fn(df_feat)  # type: ignore
        return fn(df_feat, seed=DEFAULT_SYNTHETIC_SEED)  # type: ignore

    s4, score = run_step(4, FIVE_STEP_TITLES[3], f"python_dispatch::{chosen_tool}", {}, _score)
    steps.append(s4)
    score = score if isinstance(score, dict) else fintech_tool_heuristic(df_feat)

    requested_amount = float(inp["requested_amount"])
    s5, rec = run_step(5, FIVE_STEP_TITLES[4], "fintech_recommend + viz_pd_bar", {"requested_amount": requested_amount}, lambda: fintech_recommend(score, requested_amount))
    steps.append(s5)
    rec = rec if isinstance(rec, dict) else {"decision": "Needs Human Review", "hitl_urgency_0_100": 100.0, "prediction_pd": float(score.get("pd_risk", 0.5))}

    final = {
        "decision": rec["decision"],
        "pd_risk": float(score.get("pd_risk", 0.5)),
        "confidence_0_100": float(score.get("confidence_0_100", 0.0)),
        "hitl_urgency_0_100": float(rec.get("hitl_urgency_0_100", score.get("hitl_urgency_0_100", 100.0))),
        "selected_tool": chosen_tool,
        "auc_test_synth": float(score.get("auc_test_synth", -1.0)),
    }

    # build step bullets (Python, always non-empty)
    step_bullets = {
        1: [
            "Captured account context and key request parameters.",
            f"Requested amount = {requested_amount:.0f}, employment = {inp['employment_status']}, fraud_flag = {inp['fraud_flag']}.",
        ],
        2: [
            "Checked and filled missing values using simple deterministic rules.",
            f"Missing values: before {prep.get('missing_before', {})} → after {prep.get('missing_after', {})}.",
        ],
        3: [
            "Engineered core risk features (DTI, credit score gap, missed payments, tenure, liquidity, collateral, fraud).",
            "These features act as inputs to the scoring model.",
        ],
        4: [
            f"Ran scoring tool: {chosen_tool}.",
            f"Produced PD={final['pd_risk']*100:.1f}% and confidence={final['confidence_0_100']:.1f}/100.",
        ],
        5: [
            "Converted score to an operational decision using HITL urgency and confidence.",
            f"Decision={final['decision']} with HITL_urgency={final['hitl_urgency_0_100']:.1f}/100.",
        ],
    }

    evidence_md = (
        f"- Tool used: `{chosen_tool}`\n"
        f"- Key engineered features (preview):\n\n```json\n{json.dumps(feat_preview, indent=2)}\n```\n"
    )
    if final.get("auc_test_synth", -1.0) >= 0:
        evidence_md += f"- Synthetic AUC (internal): `{final['auc_test_synth']:.3f}`\n"

    prediction_bullet = f"Predicted delinquency probability (PD) = {final['pd_risk']*100:.1f}%"
    decision_bullet = f"{final['decision']} (confidence={final['confidence_0_100']:.1f}/100, HITL_urgency={final['hitl_urgency_0_100']:.1f}/100)"

    explanation_md = build_5step_explanation_md("FinTech Credit Risk", step_bullets, evidence_md, prediction_bullet, decision_bullet)

    report = (
        "## Result\n"
        f"- Decision: **{final['decision']}**\n"
        f"- Delinquency probability (PD): **{final['pd_risk']*100:.1f}%**\n"
        f"- Confidence score: **{final['confidence_0_100']:.1f}/100**\n"
        f"- HITL urgency: **{final['hitl_urgency_0_100']:.1f}/100**\n"
        f"- Tool used: `{final['selected_tool']}`\n\n"
        f"{explanation_md}"
    )

    payload = {
        **meta,
        "about": about,
        "inputs": inp,
        "steps": [asdict(x) for x in steps],
        "outputs": {"final": final, "preprocess": prep, "feature_preview": feat_preview},
    }
    LOGGER.append(payload)
    return report, payload

def run_te_workflow(thread_id: str, about: str, inp: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    meta = run_metadata("te_pricing", thread_id)
    steps: List[StepTrace] = []

    s1, _ = run_step(1, FIVE_STEP_TITLES[0], "context_capture", {"about_preview": about[:200]}, lambda: {"about_len": len(about)})
    steps.append(s1)

    s2, checks = run_step(2, FIVE_STEP_TITLES[1], "te_input_checks", {}, lambda: {
        "checks": {
            "discount_range": 0.0 < float(inp["discount"]) < 0.9,
            "cogs_gt_0": float(inp["cogs"]) > 0,
            "landed_gt_0": float(inp["landed"]) > 0,
        }
    })
    steps.append(s2)

    # Step 3: derive
    floor = max(7.0 * float(inp["cogs"]), float(inp["presale_mult"]) * float(inp["cogs"]))
    s3, derived = run_step(3, FIVE_STEP_TITLES[2], "te_derive", {}, lambda: {
        "presale_floor": floor,
        "implied_retail_floor": floor / max(1e-6, (1.0 - float(inp["discount"]))),
        "channel": str(inp.get("channel", "")),
        "segment": str(inp.get("target_segment", "")),
        "expected_units": int(inp.get("expected_presale_units", 0)),
        "demand_index": float(inp.get("demand_index", 60.0)),
        "price_sensitivity": float(inp.get("price_sensitivity", 60.0)),
        "price_step": float(inp.get("price_step", 10.0)),
    })
    steps.append(s3)

    # Step 4: Python pricing heuristic always runs (so not stuck at 42/52)
    s4, base_price = run_step(4, FIVE_STEP_TITLES[3], "pricing_heuristic", {}, lambda: te_pricing_heuristic(inp))
    steps.append(s4)
    base_price = base_price if isinstance(base_price, dict) else te_pricing_heuristic(inp)

    # Optional LLM adjustment (if key exists)
    client = _client_or_none()
    adj = None
    if client is not None:
        s4b, adj = run_step(4, "LLM Adjustment (optional)", "llm_adjustment", {}, lambda: llm_te_adjustment(client, about, inp, base_price))
        # keep as step 4.5 in trace by using step_no=4 but different title; still 5-step in main trace? We keep it in steps list.
        steps.append(s4b)
    else:
        adj = {"confidence_0_100": 0.0, "rationale_bullets": ["LLM adjustment skipped (no API key)."], "competitor_range": {"low": 0.0, "high": 0.0}}

    # Apply adjustment deltas safely
    presale = float(base_price["presale_price"]) + float(adj.get("adj_presale_delta", 0.0))
    retail = float(base_price["retail_price"]) + float(adj.get("adj_retail_delta", 0.0))

    # Re-enforce constraints
    presale = max(presale, floor)
    retail_floor = presale / max(1e-6, (1.0 - float(inp["discount"])))
    retail = max(retail, retail_floor)

    presale = as_99(presale)
    retail = as_99(retail)
    if retail <= presale:
        retail = as_99(retail_floor)

    final = {
        "presale_price": presale,
        "retail_price": retail,
        "unit_margin_presale": float(presale - float(inp["landed"])),
        "unit_margin_retail": float(retail - float(inp["landed"])),
        "checks": {
            "presale_ge_7xcogs": presale >= 7.0 * float(inp["cogs"]),
            "presale_ge_floor": presale >= floor,
            "retail_gt_presale": retail > presale,
            "presale_gt_landed": presale > float(inp["landed"]),
            "retail_gt_landed": retail > float(inp["landed"]),
        },
        "llm_confidence_0_100": float(adj.get("confidence_0_100", 0.0)),
        "competitor_range": adj.get("competitor_range", {"low": 0.0, "high": 0.0}),
        "tool_used": "pricing_heuristic (+optional_llm_adjustment)",
    }

    s5, _ = run_step(5, FIVE_STEP_TITLES[4], "te_finalize + viz_price_stacked", {}, lambda: final)
    steps.append(s5)

    # Explanation bullets (Python, always non-empty)
    step_bullets = {
        1: [
            "Captured product/channel/segment context and pricing constraints.",
            f"Channel={inp.get('channel')}, segment={inp.get('target_segment')}, expected_units={int(inp.get('expected_presale_units', 0))}.",
        ],
        2: [
            "Validated inputs and constraints (COGS, landed, discount range).",
            f"Key constraint: presale floor = max(7×COGS, multiplier×COGS) = {floor:.2f}.",
        ],
        3: [
            "Derived operational floor prices and retail floor implied by discount.",
            f"Implied retail floor ≈ {floor / max(1e-6, (1.0 - float(inp['discount']))):.2f}.",
        ],
        4: [
            "Computed a value-based retail anchor using segment + channel + volume signals (Python heuristic).",
            f"Optional LLM adjustment used only if API key exists (LLM_conf={final['llm_confidence_0_100']:.0f}/100).",
        ],
        5: [
            "Output final recommended presale/retail prices and margins, plus constraint checks.",
            f"Presale={final['presale_price']:.2f}, Retail={final['retail_price']:.2f}.",
        ],
    }

    evidence_md = (
        f"- Tool used: `{final['tool_used']}`\n"
        f"- Base anchors: `{base_price.get('anchors', {})}`\n"
        f"- Competitor range (optional, no browsing): `{final['competitor_range']}`\n"
        f"- Checks: `{final['checks']}`\n"
    )
    if adj and adj.get("rationale_bullets"):
        evidence_md += "- LLM rationale (optional):\n"
        for b in adj["rationale_bullets"][:7]:
            evidence_md += f"  - {b}\n"

    prediction_bullet = f"Recommended presale={final['presale_price']:.2f}, retail={final['retail_price']:.2f}"
    decision_bullet = "Decision Draft (pricing recommendation ready). Human review recommended if brand/legal constraints are strict."

    explanation_md = build_5step_explanation_md("TE Pricing", step_bullets, evidence_md, prediction_bullet, decision_bullet)

    report = (
        "## Result\n"
        f"- Presale price: **{final['presale_price']:.2f}**\n"
        f"- Retail price: **{final['retail_price']:.2f}**\n"
        f"- Margin (presale/retail): **{final['unit_margin_presale']:.2f} / {final['unit_margin_retail']:.2f}**\n"
        f"- Checks: `{final['checks']}`\n"
        f"- Tool used: `{final['tool_used']}`\n\n"
        f"{explanation_md}"
    )

    payload = {
        **meta,
        "about": about,
        "inputs": inp,
        "steps": [asdict(x) for x in steps],
        "outputs": {"final": final, "derived": derived, "base_price": base_price, "llm_adjustment": adj},
    }
    LOGGER.append(payload)
    return report, payload


# =========================
# Gradio UI
# =========================
def build_gradio_app():
    import gradio as gr

    STATE: Dict[str, Any] = {"last_payload": None}
    emp_choices = ["Employed", "Self-employed", "Student", "Unemployed", "Retired", "Contract", "Other"]

    def safe_call(fn):
        try:
            return fn()
        except Exception:
            tb = traceback.format_exc()
            print(tb)
            return "ERROR:\n\n```text\n" + tb + "\n```", None, ""

    def ui_fintech(
        about_account,
        income, debt, credit_score,
        employment_status,
        missed_12m, months_on_book, credit_lines,
        requested_amount,
        savings, collateral_value,
        fraud_flag, existing_customer,
        use_ml_model,
        thread_id
    ):
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
                "savings": float(savings),
                "collateral_value": float(collateral_value),
                "fraud_flag": int(fraud_flag),
                "existing_customer": int(existing_customer),
                "use_ml_model": bool(use_ml_model),
            }
            report, payload = run_fintech_workflow(str(thread_id), str(about_account or ""), inp)
            STATE["last_payload"] = payload
            pd_val = float((payload.get("outputs") or {}).get("final", {}).get("pd_risk", 0.0))
            fig = plot_fintech_pd_bar(pd_val)
            return report, fig, payload["run_id"]
        return safe_call(_do)

    def ui_te(about_product, cogs, landed, presale_mult, discount, demand_index, price_sensitivity, price_step, channel, target_segment, expected_presale_units, thread_id):
        def _do():
            inp = {
                "cogs": float(cogs),
                "landed": float(landed),
                "presale_mult": float(presale_mult),
                "discount": float(discount),
                "demand_index": float(demand_index),
                "price_sensitivity": float(price_sensitivity),
                "price_step": float(price_step),
                "channel": str(channel),
                "target_segment": str(target_segment),
                "expected_presale_units": int(expected_presale_units),
            }
            about_text = str(about_product or "").strip()
            if not about_text:
                about_text = f"channel={inp['channel']}; segment={inp['target_segment']}; expected_presale_units={inp['expected_presale_units']}"
            report, payload = run_te_workflow(str(thread_id), about_text, inp)
            STATE["last_payload"] = payload
            final = (payload.get("outputs") or {}).get("final", {}) or {}
            presale = float(final.get("presale_price", 0.0))
            retail = float(final.get("retail_price", 0.0))
            fig = plot_te_price_stacked(presale, retail)
            return report, fig, payload["run_id"]
        return safe_call(_do)

    def ui_current_trace():
        p = STATE.get("last_payload")
        if not p:
            return "No run yet."
        return json.dumps(p, indent=2)

    def ui_logs(n):
        return json.dumps(LOGGER.tail(int(n)), indent=2)

    with gr.Blocks(title=APP_TITLE) as demo:
        gr.Markdown("## Demo C")

        with gr.Row():
            thread_id = gr.Textbox(value="demo_thread", label="thread_id")

        with gr.Tabs():
            with gr.Tab("FinTech"):
                with gr.Row():
                    with gr.Column(scale=5, min_width=480):
                        gr.Markdown("### Inputs")
                        about_account = gr.Textbox(
                            label="About this account (customer context)",
                            lines=6,
                            placeholder="Type customer/account details: repayment history, special situations, collateral notes, verification notes, etc."
                        )

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

                        with gr.Row():
                            savings = gr.Number(value=8000, label="Savings / liquid assets")
                            collateral_value = gr.Number(value=0, label="Collateral value")

                        with gr.Row():
                            fraud_flag = gr.Dropdown(choices=[0, 1], value=0, label="Fraud flag (0/1)")
                            existing_customer = gr.Dropdown(choices=[0, 1], value=1, label="Existing customer (0/1)")

                        use_ml_model = gr.Checkbox(value=True, label="Use synthetic data")

                        btn = gr.Button("Run", variant="primary")

                    with gr.Column(scale=7, min_width=640):
                        gr.Markdown("### Output")
                        out = gr.Markdown(value="_(Run to see result.)_")
                        fintech_plot = gr.Plot(label="PD visualization")
                        run_id_out = gr.Textbox(label="run_id")

                btn.click(
                    fn=ui_fintech,
                    inputs=[
                        about_account,
                        income, debt, credit_score,
                        employment_status,
                        missed_12m, months_on_book, credit_lines,
                        requested_amount,
                        savings, collateral_value,
                        fraud_flag, existing_customer,
                        use_ml_model,
                        thread_id
                    ],
                    outputs=[out, fintech_plot, run_id_out],
                )

            with gr.Tab("TE"):
                with gr.Row():
                    with gr.Column(scale=5, min_width=480):
                        gr.Markdown("### Inputs")
                        about_product = gr.Textbox(
                            label="About this product/account (context)",
                            lines=6,
                            placeholder="Type product + customer context: segment, channel, positioning, constraints, demand signals."
                        )

                        with gr.Row():
                            cogs = gr.Number(value=6, label="COGS per unit")
                            landed = gr.Number(value=10, label="Landed cost per unit")
                        with gr.Row():
                            presale_mult = gr.Number(value=7, label="Presale floor multiplier")
                            discount = gr.Number(value=0.20, label="Discount (0-0.9)")
                        with gr.Row():
                            demand_index = gr.Slider(0, 100, value=60, step=1, label="Demand level (0-100)")
                            price_sensitivity = gr.Slider(0, 100, value=60, step=1, label="Price sensitivity (0-100)")
                        price_step = gr.Dropdown(choices=[10, 20, 50], value=10, label="Price step ($)")
                        channel = gr.Dropdown(choices=["DTC (Direct-to-Consumer)", "Amazon", "Retail", "Wholesale"], value="DTC", label="Channel")
                        target_segment = gr.Dropdown(choices=["Budget", "Mid-market", "Premium"], value="Mid-market", label="Target segment")
                        expected_presale_units = gr.Number(value=1000, label="Expected presale units (rough)")

                        btn2 = gr.Button("Run", variant="primary")

                    with gr.Column(scale=7, min_width=640):
                        gr.Markdown("### Output")
                        out2 = gr.Markdown(value="_(Run to see result.)_")
                        te_plot = gr.Plot(label="Price visualization")
                        run_id_out2 = gr.Textbox(label="run_id")

                btn2.click(
                    fn=ui_te,
                    inputs=[about_product, cogs, landed, presale_mult, discount, demand_index, price_sensitivity, price_step, channel, target_segment, expected_presale_units, thread_id],
                    outputs=[out2, te_plot, run_id_out2],
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
    demo = build_gradio_app()
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")), debug=True)


if __name__ == "__main__":
    main()
