# week4_threshold_loop.py
# ------------------------------------------------------------
# Goal: make threshold selection and routing reproducible.
#
# Stage A (offline, has y_true):
#   1) Train a model on historical data.
#   2) Get y_score = P(delinquent=1) for test set.
#   3) Sweep thresholds and pick an operating threshold t
#      based on minimizing FNR (missed delinquencies) with optional constraints.
#
# Stage B (online, no y_true yet):
#   4) For new cases, compute y_score and apply thresholds.
#   5) Use two thresholds t1 and t2 to create an uncertainty band:
#      low-risk zone (<t1), review zone (t1..t2), high-risk zone (>=t2).
#      The band exists because probabilities near the boundary are less reliable.
#
# Stage C (feedback):
#   6) When outcomes arrive later (y_true), recompute metrics and update threshold if needed.
# ------------------------------------------------------------

import os
import json
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


# ----------------------------
# 1) Data + feature setup
# ----------------------------

TARGET_COL = "Delinquent_Account"
ID_COL = "Customer_ID"

NUM_COLS = [
    "Age", "Income", "Credit_Score", "Credit_Utilization", "Missed_Payments",
    "Loan_Balance", "Debt_to_Income_Ratio", "Account_Tenure",
]

CAT_COLS = [
    "Employment_Status", "Credit_Card_Type", "Location",
    "Month_1", "Month_2", "Month_3", "Month_4", "Month_5", "Month_6",
]


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Basic guardrails
    assert TARGET_COL in df.columns, f"Missing target: {TARGET_COL}"
    assert ID_COL in df.columns, f"Missing id: {ID_COL}"
    return df


# ----------------------------
# 2) Models (simple + stable)
# ----------------------------

def make_preprocessor() -> ColumnTransformer:
    num_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    cat_pipe = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, NUM_COLS),
            ("cat", cat_pipe, CAT_COLS),
        ]
    )


def make_logreg() -> Pipeline:
    # Interpretable baseline, good for explainability/audit
    return Pipeline(steps=[
        ("prep", make_preprocessor()),
        ("clf", LogisticRegression(max_iter=500)),
    ])


def make_tree() -> Pipeline:
    # Non-linear challenger, still fairly explainable
    return Pipeline(steps=[
        ("prep", make_preprocessor()),
        ("clf", DecisionTreeClassifier(
            max_depth=4,
            min_samples_leaf=10,
            random_state=42
        )),
    ])


# ----------------------------
# 3) Core metrics at a threshold
# ----------------------------

def metrics_at_threshold(y_true, y_score, t: float) -> dict:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    y_pred = (y_score >= t).astype(int)

    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0  # TPR
    fnr = fn / (tp + fn) if (tp + fn) else 0.0     # 1 - recall
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "t": float(t),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": float(precision),
        "recall": float(recall),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "f1": float(f1),
    }


def threshold_sweep(y_true, y_score, step=0.05) -> pd.DataFrame:
    thresholds = np.round(np.arange(step, 1.0, step), 2)
    rows = [metrics_at_threshold(y_true, y_score, t) for t in thresholds]
    return pd.DataFrame(rows)


def pick_threshold(
    sweep_df: pd.DataFrame,
    precision_floor: float | None = 0.30,
) -> float:
    # Main objective: minimize FNR (missed delinquencies).
    # Optional constraint: keep precision above a floor to limit unnecessary actions.
    df = sweep_df.copy()

    if precision_floor is not None:
        df = df[df["precision"] >= precision_floor]
        if df.empty:
            # If the constraint is too strict, fall back to global minimum FNR.
            df = sweep_df.copy()

    best = df.sort_values(["fnr", "t"]).iloc[0]
    return float(best["t"])


def make_t1_t2(t: float, band: float = 0.05) -> tuple[float, float]:
    # Two-threshold routing:
    #   t1 < t2 creates an uncertainty band around the operating point.
    #   Scores near the boundary are more error-prone, so route them to review.
    t1 = max(0.0, t - band)
    t2 = min(1.0, t + band)
    return float(t1), float(t2)


# ----------------------------
# 4) Agent-style routing output
# ----------------------------

def route_with_t1_t2(y_score, t1: float, t2: float) -> np.ndarray:
    y_score = np.asarray(y_score).astype(float)
    route = np.empty(len(y_score), dtype=object)
    route[y_score < t1] = "low_risk"
    route[(y_score >= t1) & (y_score < t2)] = "review"
    route[y_score >= t2] = "high_risk"
    return route


def action_from_route(route: str) -> str:
    # Keep actions simple for MVP
    if route == "low_risk":
        return "auto_approve"
    if route == "high_risk":
        return "intervene_or_block"
    return "manual_review"


def build_decision_packet(df_cases: pd.DataFrame, y_score, t1: float, t2: float,
                          model_name: str, threshold_version: str) -> pd.DataFrame:
    route = route_with_t1_t2(y_score, t1, t2)
    actions = [action_from_route(r) for r in route]

    out = pd.DataFrame({
        ID_COL: df_cases[ID_COL].values,
        "score": np.asarray(y_score).astype(float),
        "t1": t1,
        "t2": t2,
        "route": route,
        "action": actions,
        "model_name": model_name,
        "threshold_version": threshold_version,
    })
    return out


# ----------------------------
# 5) End-to-end runner
# ----------------------------

def train_and_validate(df: pd.DataFrame, model_kind: str = "logreg", seed: int = 42):
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=seed, stratify=y
    )

    model = make_logreg() if model_kind == "logreg" else make_tree()
    model.fit(X_train, y_train)

    # y_score is the model output probability for class 1 (delinquent)
    y_score = model.predict_proba(X_test)[:, 1]

    return model, X_test, y_test, y_score


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def main():
    csv_path = "dpd_sample.csv"   # change if needed
    out_dir = "reports_out"
    ensure_dir(out_dir)

    df = load_data(csv_path)

    # Train two models
    results = {}
    for model_kind in ["logreg", "tree"]:
        model, X_test, y_test, y_score = train_and_validate(df, model_kind=model_kind)

        sweep = threshold_sweep(y_test, y_score, step=0.05)
        t = pick_threshold(sweep, precision_floor=0.30)
        t1, t2 = make_t1_t2(t, band=0.05)

        # Save sweep evidence
        sweep.to_csv(os.path.join(out_dir, f"{model_kind}_threshold_sweep.csv"), index=False)

        # Save chosen threshold metrics
        chosen = metrics_at_threshold(y_test, y_score, t)
        results[model_kind] = {"chosen_threshold": t, "t1": t1, "t2": t2, "metrics": chosen}

        # Build decision packets for the test set (as a proxy for online cases)
        packet = build_decision_packet(
            df_cases=X_test.assign(**{ID_COL: df.loc[X_test.index, ID_COL].values}),
            y_score=y_score,
            t1=t1, t2=t2,
            model_name=model_kind,
            threshold_version=f"{model_kind}_v1_t{t}"
        )
        packet.to_csv(os.path.join(out_dir, f"{model_kind}_decision_packet_test.csv"), index=False)

    # Save summary json for slides
    with open(os.path.join(out_dir, "week4_summary.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Done. Outputs saved to:", out_dir)


if __name__ == "__main__":
    main()
