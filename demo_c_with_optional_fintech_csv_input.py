from __future__ import annotations

"""
demo_c.py (v11): Most complete "Manager-ready" Demo C

Key upgrades (per manager feedback)
1) FinTech: optional CSV/PDF upload
   - CSV: auto-fill inputs (first row by default) with transparent mapping + evidence
   - PDF: optional context extraction (best-effort, no new deps required)
2) TE: prompt has real influence WITHOUT relying on LLM
   - Prompt influence slider (0-100)
   - Lightweight prompt parser -> adjusts demand_index / price_sensitivity / segment / channel / anchor delta
   - Still keeps all hard constraints (floors, retail > presale)
3) Preserves: two-panel layout, Markdown output, 5-step workflow, evidence, matplotlib visuals, trace + JSONL logs
4) No requirement changes: uses existing libs; PDF extraction is optional if PyPDF2 exists
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

# OpenAI is OPTIONAL (never required)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


print("\n========== DEMO_C BOOT (v11) ==========")
print("RUNNING_FILE =", __file__)
print("CWD =", os.getcwd())
print("PYTHON =", sys.executable)
print("OPENAI_MODEL =", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
print("OPENAI_API_KEY_SET =", "YES" if bool(os.getenv("OPENAI_API_KEY", "")) else "NO")
print("======================================\n")


# =========================
# Config
# =========================
APP_TITLE = "Demo C"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

AGENT_ID = os.getenv("AGENT_ID", "nexdatawork_demo_agent")
MODEL_ID = os.getenv("MODEL_ID", "python_5step_traceable")
VERSION_ID = os.getenv("VERSION_ID", "11.0.0")

POLICY_ID = os.getenv("POLICY_ID", "5step_traceable_policy")
POLICY_VERSION = os.getenv("POLICY_VERSION", "11.0")

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
# FinTech CSV/PDF ingest (new)
# =========================
FINTECH_COLUMN_ALIASES: Dict[str, List[str]] = {
    "income": ["income", "annual_income", "Income", "Income_Annual"],
    "debt": ["debt", "total_debt", "Debt"],
    "credit_score": ["credit_score", "creditscore", "fico", "Credit_Score", "CreditScore"],
    "employment_status": ["employment_status", "employment", "Employment_Status", "EmploymentStatus"],
    "missed_payments_12m": ["missed_payments_12m", "missed_12m", "Missed_Payments_12m"],
    "months_on_book": ["months_on_book", "Months_On_Book", "mob", "tenure_months"],
    "credit_lines": ["credit_lines", "Credit_Lines", "lines"],
    "requested_amount": ["requested_amount", "amount", "Requested_Amount", "loan_amount"],
    "savings": ["savings", "Savings", "liquid_assets"],
    "collateral_value": ["collateral_value", "collateral", "Collateral_Value", "Collateral_Value"],
    "fraud_flag": ["fraud_flag", "Fraud_Flag", "fraud"],
    "existing_customer": ["existing_customer", "Existing_Customer", "loyal_customer"],
}

def _normalize_cols(cols: List[str]) -> Dict[str, str]:
    # map lower->original
    out = {}
    for c in cols:
        out[str(c).strip().lower()] = c
    return out

def fintech_parse_csv_first_row(file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    df = pd.read_csv(file_path)
    if df.shape[0] < 1:
        return {}, {"error": "CSV has no rows."}
    row = df.iloc[0].to_dict()
    norm = _normalize_cols(list(df.columns))

    used = {}
    missing = []
    parsed: Dict[str, Any] = {}

    for k, aliases in FINTECH_COLUMN_ALIASES.items():
        found_col = None
        for a in aliases:
            a_norm = str(a).strip().lower()
            if a_norm in norm:
                found_col = norm[a_norm]
                break
        if found_col is None:
            missing.append(k)
            continue
        used[k] = found_col
        parsed[k] = row.get(found_col)

    # Simple cleaning
    def to_float(x, default=0.0):
        try:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return float(default)
            s = str(x).replace("$", "").replace(",", "").strip()
            return float(s)
        except Exception:
            return float(default)

    def to_int(x, default=0):
        try:
            if x is None or (isinstance(x, float) and np.isnan(x)):
                return int(default)
            s = str(x).replace(",", "").strip()
            return int(float(s))
        except Exception:
            return int(default)

    cleaned = {
        "income": to_float(parsed.get("income", 75000), 75000),
        "debt": to_float(parsed.get("debt", 30000), 30000),
        "credit_score": to_int(parsed.get("credit_score", 680), 680),
        "employment_status": str(parsed.get("employment_status", "Employed") or "Employed"),
        "missed_payments_12m": to_int(parsed.get("missed_payments_12m", 1), 1),
        "months_on_book": to_int(parsed.get("months_on_book", 18), 18),
        "credit_lines": to_int(parsed.get("credit_lines", 4), 4),
        "requested_amount": to_float(parsed.get("requested_amount", 250000), 250000),
        "savings": to_float(parsed.get("savings", 8000), 8000),
        "collateral_value": to_float(parsed.get("collateral_value", 0), 0),
        "fraud_flag": to_int(parsed.get("fraud_flag", 0), 0),
        "existing_customer": to_int(parsed.get("existing_customer", 1), 1),
    }

    meta = {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "used_columns": used,
        "missing_fields": missing,
    }
    return cleaned, meta

def fintech_extract_pdf_text_best_effort(file_path: str, max_chars: int = 2000) -> Tuple[str, str]:
    """
    No new requirements. If PyPDF2 exists, use it. Otherwise return a safe message.
    """
    try:
        import PyPDF2  # type: ignore
    except Exception:
        return "", "PyPDF2 not installed; PDF text extraction skipped."
    try:
        txts: List[str] = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for p in reader.pages[:10]:
                t = p.extract_text() or ""
                if t.strip():
                    txts.append(t.strip())
        joined = "\n".join(txts).strip()
        return joined[:max_chars], "PDF text extracted (best-effort)."
    except Exception as e:
        return "", f"PDF parse failed: {str(e)[:200]}"


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
# TE prompt influence (new, no LLM required)
# =========================
def te_prompt_parse(about: str) -> Dict[str, Any]:
    """
    Lightweight parsing. Keeps it stable and transparent.
    Output is "signals" we can mix into the heuristic.
    """
    t = (about or "").lower()

    # demand signals
    demand_boost = 0.0
    if any(k in t for k in ["high demand", "strong demand", "sold out", "waitlist", "viral", "hype"]):
        demand_boost += 20.0
    if any(k in t for k in ["low demand", "weak demand", "slow", "hard to sell"]):
        demand_boost -= 20.0

    # sensitivity signals
    sens_boost = 0.0
    if any(k in t for k in ["price sensitive", "tight budget", "discount", "coupon", "cheap"]):
        sens_boost += 20.0
    if any(k in t for k in ["not price sensitive", "premium buyers", "quality first", "luxury"]):
        sens_boost -= 15.0

    # segment override hints
    seg = None
    if any(k in t for k in ["premium", "high-end", "luxury"]):
        seg = "Premium"
    elif any(k in t for k in ["budget", "low-cost", "cheap"]):
        seg = "Budget"
    elif any(k in t for k in ["mid", "mid-market", "mainstream"]):
        seg = "Mid-market"

    # channel hints
    ch = None
    if "amazon" in t:
        ch = "Amazon"
    elif "retail" in t:
        ch = "Retail"
    elif "wholesale" in t or "b2b" in t:
        ch = "Wholesale"
    elif any(k in t for k in ["dtc", "direct", "website", "shopify"]):
        ch = "DTC"

    # direct anchor delta hints
    anchor_delta = 0.0
    if any(k in t for k in ["raise price", "increase price", "higher price", "maximize margin"]):
        anchor_delta += 10.0
    if any(k in t for k in ["lower price", "decrease price", "aggressive discount", "penetration"]):
        anchor_delta -= 10.0

    return {
        "demand_delta": float(clamp(demand_boost, -30.0, 30.0)),
        "sensitivity_delta": float(clamp(sens_boost, -30.0, 30.0)),
        "segment_hint": seg,
        "channel_hint": ch,
        "anchor_delta": float(clamp(anchor_delta, -20.0, 20.0)),
    }

def te_apply_prompt_influence(inp: Dict[str, Any], about: str, influence_0_100: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Mix prompt signals into numeric controls with a single influence slider.
    Keeps deterministic behavior and full transparency.
    """
    influence = clamp(float(influence_0_100), 0.0, 100.0) / 100.0
    sig = te_prompt_parse(about)

    out = dict(inp)

    # apply segment/channel hints (soft)
    if sig["segment_hint"] and influence >= 0.15:
        out["target_segment"] = sig["segment_hint"]
    if sig["channel_hint"] and influence >= 0.15:
        out["channel"] = sig["channel_hint"]

    # numeric controls
    base_d = float(out.get("demand_index", 60.0))
    base_s = float(out.get("price_sensitivity", 60.0))

    out["demand_index"] = clamp(base_d + influence * sig["demand_delta"], 0.0, 100.0)
    out["price_sensitivity"] = clamp(base_s + influence * sig["sensitivity_delta"], 0.0, 100.0)

    # anchor delta saved for heuristic
    out["_prompt_anchor_delta"] = float(influence * sig["anchor_delta"])

    meta = {
        "prompt_influence_0_100": float(influence_0_100),
        "prompt_signals": sig,
        "applied": {
            "demand_index": out["demand_index"],
            "price_sensitivity": out["price_sensitivity"],
            "target_segment": out.get("target_segment"),
            "channel": out.get("channel"),
            "anchor_delta": out["_prompt_anchor_delta"],
        },
    }
    return out, meta


# =========================
# TE pricing heuristic (PRIMARY) — updated to accept _prompt_anchor_delta
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

    prompt_anchor_delta = float(inp.get("_prompt_anchor_delta", 0.0))

    floor = max(7.0 * cogs, mult * cogs)

    # segment anchor retail
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

    # volume signal
    if units >= 5000:
        retail_anchor -= 8.0
    elif units >= 2000:
        retail_anchor -= 4.0
    elif units > 0 and units < 300:
        retail_anchor += 6.0

    # Demand controls
    retail_anchor += (demand_index - 50.0) * 0.3
    retail_anchor -= (price_sensitivity - 50.0) * 0.2

    # Prompt anchor delta (new)
    retail_anchor += prompt_anchor_delta

    retail_floor_from_discount = floor / max(1e-6, (1.0 - discount))
    retail = max(retail_anchor, retail_floor_from_discount)

    presale = retail * (1.0 - discount)
    presale = max(presale, floor)

    presale = as_99(presale)
    retail = as_99(retail)

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
        "anchors": {
            "segment": segment,
            "channel": channel,
            "retail_anchor": retail_anchor,
            "units": units,
            "demand_index": demand_index,
            "price_sensitivity": price_sensitivity,
            "price_step": price_step,
            "prompt_anchor_delta": prompt_anchor_delta,
        },
    }


# =========================
# 5-step explanation builder (Python, always non-empty)
# =========================
def build_5step_explanation_md(step_bullets: Dict[int, List[str]], evidence_md: str, prediction_bullet: str, decision_bullet: str) -> str:
    md: List[str] = []
    md.append("## Explanation")
    for i in range(1, 6):
        section_title = FIVE_STEP_TITLES[i - 1]
        md.append(f"### {section_title}")
        blt = step_bullets.get(i, [])
        if not blt:
            blt = ["(no content)"]
        for b in blt[:10]:
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
    import matplotlib.pyplot as plt
    pd_risk = float(clamp(pd_risk, 0.0, 1.0))
    pct = pd_risk * 100.0

    fig = plt.figure(figsize=(6.0, 1.6))
    ax = fig.add_subplot(111)

    ax.barh([0], [100], height=0.5, color="#e6e6e6")
    ax.barh([0], [pct], height=0.5, color="#1f77b4")

    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xlabel("PD (%)")
    ax.set_title(f"Delinquency probability (PD): {pct:.1f}%")
    ax.text(min(pct + 2, 98), 0, f"{pct:.1f}%", va="center", ha="left", fontsize=11)

    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig

def plot_te_price_stacked(presale: float, retail: float):
    import matplotlib.pyplot as plt

    presale = float(max(presale, 0.0))
    retail = float(max(retail, presale))

    fig = plt.figure(figsize=(6.0, 2.2))
    ax = fig.add_subplot(111)

    x = [0]
    bars_retail = ax.bar(x, [retail], width=0.6, color="#9f1bdd", label="Retail")
    bars_presale = ax.bar(x, [presale], width=0.6, color="#4d74f3", label="Presale")

    ax.set_xticks(x)
    ax.set_xticklabels(["Price"])
    ax.set_ylabel("$")
    ax.set_title("Presale vs Retail")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ymax = max(retail, presale)
    ax.set_ylim(0, ymax * 1.25)

    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

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

def run_fintech_workflow(thread_id: str, about: str, inp: Dict[str, Any], ingest_meta: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    meta = run_metadata("fintech", thread_id)
    steps: List[StepTrace] = []

    ingest_meta = ingest_meta or {}
    s1, _ = run_step(
        1,
        FIVE_STEP_TITLES[0],
        "context_capture",
        {"about_preview": about[:200], "ingest": ingest_meta},
        lambda: {"about_len": len(about), "ingest": ingest_meta},
    )
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

    step_bullets = {
        1: [
            "Captured account context and key request parameters (manual inputs and/or uploaded file).",
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
        f"- Ingest (optional): `{ingest_meta}`\n"
        f"- Key engineered features (preview):\n\n```json\n{json.dumps(feat_preview, indent=2)}\n```\n"
    )
    if final.get("auc_test_synth", -1.0) >= 0:
        evidence_md += f"- Synthetic AUC (internal): `{final['auc_test_synth']:.3f}`\n"

    prediction_bullet = f"Predicted delinquency probability (PD) = {final['pd_risk']*100:.1f}%"
    decision_bullet = f"{final['decision']} (confidence={final['confidence_0_100']:.1f}/100, HITL_urgency={final['hitl_urgency_0_100']:.1f}/100)"
    explanation_md = build_5step_explanation_md(step_bullets, evidence_md, prediction_bullet, decision_bullet)

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
        "ingest_meta": ingest_meta,
        "inputs": inp,
        "steps": [asdict(x) for x in steps],
        "outputs": {"final": final, "preprocess": prep, "feature_preview": feat_preview},
    }
    LOGGER.append(payload)
    return report, payload

def run_te_workflow(thread_id: str, about: str, inp: Dict[str, Any], prompt_meta: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    meta = run_metadata("te_pricing", thread_id)
    steps: List[StepTrace] = []
    prompt_meta = prompt_meta or {}

    s1, _ = run_step(
        1,
        FIVE_STEP_TITLES[0],
        "context_capture",
        {"about_preview": about[:200], "prompt_meta": prompt_meta},
        lambda: {"about_len": len(about), "prompt_meta": prompt_meta},
    )
    steps.append(s1)

    s2, checks = run_step(2, FIVE_STEP_TITLES[1], "te_input_checks", {}, lambda: {
        "checks": {
            "discount_range": 0.0 < float(inp["discount"]) < 0.9,
            "cogs_gt_0": float(inp["cogs"]) > 0,
            "landed_gt_0": float(inp["landed"]) > 0,
        }
    })
    steps.append(s2)

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

    s4, base_price = run_step(4, FIVE_STEP_TITLES[3], "pricing_heuristic (+prompt_influence)", {}, lambda: te_pricing_heuristic(inp))
    steps.append(s4)
    base_price = base_price if isinstance(base_price, dict) else te_pricing_heuristic(inp)

    # Optional LLM adjustment (still optional, but prompt already has strong influence now)
    client = _client_or_none()
    adj = None
    if client is not None:
        s4b, adj = run_step(4, "LLM Adjustment (optional)", "llm_adjustment", {}, lambda: llm_te_adjustment(client, about, inp, base_price))
        steps.append(s4b)
    else:
        adj = {
            "confidence_0_100": 0.0,
            "rationale_bullets": ["LLM adjustment skipped (no API key). Prompt influence still applied in Python."],
            "competitor_range": {"low": 0.0, "high": 0.0},
        }

    presale = float(base_price["presale_price"]) + float(adj.get("adj_presale_delta", 0.0))
    retail = float(base_price["retail_price"]) + float(adj.get("adj_retail_delta", 0.0))

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
        "tool_used": "pricing_heuristic (+prompt_influence +optional_llm_adjustment)",
        "prompt_meta": prompt_meta,
    }

    s5, _ = run_step(5, FIVE_STEP_TITLES[4], "te_finalize + viz_price_stacked", {}, lambda: final)
    steps.append(s5)

    step_bullets = {
        1: [
            "Captured product/channel/segment context, including prompt-based instructions.",
            f"Prompt influence = {prompt_meta.get('prompt_influence_0_100', 0):.0f}/100 (applied in Python).",
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
            "Computed value-based retail anchor using segment + channel + volume signals.",
            "Applied prompt influence to adjust demand/sensitivity/segment/channel/anchor (still constrained by floors).",
        ],
        5: [
            "Output final recommended presale/retail prices and margins, plus constraint checks.",
            f"Presale={final['presale_price']:.2f}, Retail={final['retail_price']:.2f}.",
        ],
    }

    evidence_md = (
        f"- Tool used: `{final['tool_used']}`\n"
        f"- Prompt influence meta: `{prompt_meta}`\n"
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
    explanation_md = build_5step_explanation_md(step_bullets, evidence_md, prediction_bullet, decision_bullet)

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

    def ui_fintech_autofill(file_obj):
        """
        Returns values for all FinTech input components + about_account appended context.
        """
        if file_obj is None:
            return [gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()]

        path = getattr(file_obj, "name", None) or str(file_obj)
        ingest_meta = {}
        about_extra = ""
        vals = {}

        if path.lower().endswith(".csv"):
            cleaned, meta_csv = fintech_parse_csv_first_row(path)
            ingest_meta = {"type": "csv", **meta_csv}
            vals = cleaned
            about_extra = f"[CSV uploaded] rows={meta_csv.get('rows')} cols={meta_csv.get('cols')} used={meta_csv.get('used_columns')}"
        elif path.lower().endswith(".pdf"):
            txt, note = fintech_extract_pdf_text_best_effort(path)
            ingest_meta = {"type": "pdf", "note": note, "chars": len(txt)}
            about_extra = f"[PDF uploaded] {note}\n\n{txt}"
        else:
            ingest_meta = {"type": "unknown", "path": path}

        # Return update objects (only fill if we have values)
        # Order must match: about_account, income, debt, credit_score, employment_status,
        # missed_12m, months_on_book, credit_lines, requested_amount, savings, collateral_value,
        # fraud_flag, existing_customer
        out = [
            gr.update(value=about_extra),
            gr.update(value=vals.get("income", 75000)),
            gr.update(value=vals.get("debt", 30000)),
            gr.update(value=vals.get("credit_score", 680)),
            gr.update(value=vals.get("employment_status", "Employed")),
            gr.update(value=vals.get("missed_payments_12m", 1)),
            gr.update(value=vals.get("months_on_book", 18)),
            gr.update(value=vals.get("credit_lines", 4)),
            gr.update(value=vals.get("requested_amount", 250000)),
            gr.update(value=vals.get("savings", 8000)),
            gr.update(value=vals.get("collateral_value", 0)),
            gr.update(value=vals.get("fraud_flag", 0)),
            gr.update(value=vals.get("existing_customer", 1)),
        ]
        return out

    def ui_fintech(
        uploaded_file,
        about_account,
        income, debt, credit_score,
        employment_status,
        missed_12m, months_on_book, credit_lines,
        requested_amount,
        savings, collateral_value,
        fraud_flag, existing_customer,
        use_ml_model,
        thread_id,
    ):
        def _do():
            ingest_meta = {}
            about_text = str(about_account or "").strip()

            if uploaded_file is not None:
                path = getattr(uploaded_file, "name", None) or str(uploaded_file)
                if path.lower().endswith(".csv"):
                    cleaned, meta_csv = fintech_parse_csv_first_row(path)
                    ingest_meta = {"type": "csv", **meta_csv}
                    # override structured inputs from CSV
                    income_v = cleaned["income"]
                    debt_v = cleaned["debt"]
                    credit_v = cleaned["credit_score"]
                    emp_v = cleaned["employment_status"]
                    missed_v = cleaned["missed_payments_12m"]
                    mob_v = cleaned["months_on_book"]
                    lines_v = cleaned["credit_lines"]
                    amt_v = cleaned["requested_amount"]
                    sav_v = cleaned["savings"]
                    col_v = cleaned["collateral_value"]
                    fraud_v = cleaned["fraud_flag"]
                    exist_v = cleaned["existing_customer"]
                else:
                    income_v, debt_v, credit_v = float(income), float(debt), int(credit_score)
                    emp_v = str(employment_status)
                    missed_v, mob_v, lines_v = int(missed_12m), int(months_on_book), int(credit_lines)
                    amt_v, sav_v, col_v = float(requested_amount), float(savings), float(collateral_value)
                    fraud_v, exist_v = int(fraud_flag), int(existing_customer)

                if path.lower().endswith(".pdf"):
                    txt, note = fintech_extract_pdf_text_best_effort(path)
                    ingest_meta = {"type": "pdf", "note": note, "chars": len(txt)}
                    if txt.strip():
                        about_text = (about_text + "\n\n" + txt.strip()).strip()

            else:
                income_v, debt_v, credit_v = float(income), float(debt), int(credit_score)
                emp_v = str(employment_status)
                missed_v, mob_v, lines_v = int(missed_12m), int(months_on_book), int(credit_lines)
                amt_v, sav_v, col_v = float(requested_amount), float(savings), float(collateral_value)
                fraud_v, exist_v = int(fraud_flag), int(existing_customer)

            inp = {
                "income": float(income_v),
                "debt": float(debt_v),
                "credit_score": int(credit_v),
                "employment_status": str(emp_v),
                "missed_payments_12m": int(missed_v),
                "months_on_book": int(mob_v),
                "credit_lines": int(lines_v),
                "requested_amount": float(amt_v),
                "savings": float(sav_v),
                "collateral_value": float(col_v),
                "fraud_flag": int(fraud_v),
                "existing_customer": int(exist_v),
                "use_ml_model": bool(use_ml_model),
            }
            report, payload = run_fintech_workflow(str(thread_id), about_text, inp, ingest_meta=ingest_meta)
            STATE["last_payload"] = payload
            pd_val = float((payload.get("outputs") or {}).get("final", {}).get("pd_risk", 0.0))
            fig = plot_fintech_pd_bar(pd_val)
            return report, fig, payload["run_id"]
        return safe_call(_do)

    def ui_te(
        about_product,
        prompt_influence,
        cogs, landed, presale_mult, discount,
        demand_index, price_sensitivity, price_step,
        channel, target_segment, expected_presale_units,
        thread_id,
    ):
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

            # apply prompt influence in Python (no LLM needed)
            inp2, prompt_meta = te_apply_prompt_influence(inp, about_text, float(prompt_influence))

            report, payload = run_te_workflow(str(thread_id), about_text, inp2, prompt_meta=prompt_meta)
            STATE["last_payload"] = payload
            final = (payload.get("outputs") or {}).get("final", {}) or {}
            presale_v = float(final.get("presale_price", 0.0))
            retail_v = float(final.get("retail_price", 0.0))
            fig = plot_te_price_stacked(presale_v, retail_v)
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

                        uploaded_file = gr.File(
                            label="Upload CSV/PDF (optional)",
                            file_types=[".csv", ".pdf"],
                        )
                        fill_btn = gr.Button("Auto-fill from file", variant="secondary")

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

                fill_btn.click(
                    fn=ui_fintech_autofill,
                    inputs=[uploaded_file],
                    outputs=[about_account, income, debt, credit_score, employment_status, missed_12m, months_on_book,
                             credit_lines, requested_amount, savings, collateral_value, fraud_flag, existing_customer],
                )

                btn.click(
                    fn=ui_fintech,
                    inputs=[
                        uploaded_file,
                        about_account,
                        income, debt, credit_score,
                        employment_status,
                        missed_12m, months_on_book, credit_lines,
                        requested_amount,
                        savings, collateral_value,
                        fraud_flag, existing_customer,
                        use_ml_model,
                        thread_id,
                    ],
                    outputs=[out, fintech_plot, run_id_out],
                )

            with gr.Tab("TE"):
                with gr.Row():
                    with gr.Column(scale=5, min_width=480):
                        gr.Markdown("### Inputs")

                        about_product = gr.Textbox(
                            label="Chat instructions (high influence)",
                            lines=6,
                            placeholder="Example: premium positioning, strong demand, not price sensitive, retail channel, maximize margin."
                        )
                        prompt_influence = gr.Slider(0, 100, value=70, step=1, label="Prompt influence (0-100)")

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
                        channel = gr.Dropdown(choices=["DTC", "Amazon", "Retail", "Wholesale"], value="DTC", label="Channel")
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
                    inputs=[
                        about_product,
                        prompt_influence,
                        cogs, landed, presale_mult, discount,
                        demand_index, price_sensitivity, price_step,
                        channel, target_segment, expected_presale_units,
                        thread_id,
                    ],
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