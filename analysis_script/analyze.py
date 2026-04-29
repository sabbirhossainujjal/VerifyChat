"""
analyze.py
Study analysis for VerifyChat HCI experiment.

Condition-1 (Standard Chat): measures hallucination detection from free-text guesses.
Condition-2 (VerifyChat):    measures claim prediction accuracy (precision/recall/F1).

Usage:
    python analysis_script/analyze.py
"""

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# Normalised participant IDs to include (all map to the same person)
PARTICIPANT_IDS = {"001", "p001", "P001"}


# ---------------------------------------------------------------------------
# Load + filter
# ---------------------------------------------------------------------------

def load():
    tables = {}
    for csv in DATA_DIR.glob("*.csv"):
        tables[csv.stem] = pd.read_csv(csv)
    missing = [t for t in [
        "sessions", "session_mode_events", "hallucinated_facts",
        "hallucination_guesses", "prediction_scores", "predictions", "claims"
    ] if t not in tables]
    if missing:
        raise FileNotFoundError(
            f"Missing CSVs: {missing}. Run fetch_data.py first."
        )

    # Keep only sessions whose participant_id matches any of the target IDs
    sessions = tables["sessions"]
    sessions = sessions[sessions["participant_id"].isin(PARTICIPANT_IDS)].copy()
    tables["sessions"] = sessions

    # Filter every other table by the surviving session_ids
    valid_session_ids = set(sessions["id"])
    for name, df in tables.items():
        if name == "sessions":
            continue
        if "session_id" in df.columns:
            tables[name] = df[df["session_id"].isin(valid_session_ids)].copy()

    return tables


# ---------------------------------------------------------------------------
# Condition-1: hallucination detection (Standard Chat)
# ---------------------------------------------------------------------------

def analyze_condition1(tables):
    print("\n" + "=" * 60)
    print("CONDITION-1  —  Standard Chat (hallucination detection)")
    print("=" * 60)

    facts   = tables["hallucinated_facts"]
    guesses = tables["hallucination_guesses"]

    if guesses.empty:
        print("  No guess data yet.")
        return

    # Parse eval_result JSON stored in the guesses table
    def parse_eval(val):
        try:
            if pd.isna(val):
                return None
        except (TypeError, ValueError):
            pass
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

    guesses = guesses.copy()
    guesses["eval_parsed"] = guesses["eval_result"].apply(parse_eval)

    # Per-message: how many of the 2 injected facts did the student detect?
    rows = []
    for _, g in guesses.iterrows():
        ev = g["eval_parsed"]
        if not isinstance(ev, dict):
            continue
        facts_list = ev.get("facts", [])
        detected   = sum(1 for f in facts_list if f.get("detected", False))
        total      = len(facts_list)
        rows.append({
            "session_id":     g["session_id"],
            "message_id":     g["message_id"],
            "total_injected": total,
            "detected":       detected,
            "detection_rate": detected / total if total else 0,
        })

    if not rows:
        print("  Eval results not yet computed.")
        return

    df = pd.DataFrame(rows)

    print(f"\n  Participants with guesses : {df['session_id'].nunique()}")
    print(f"  Messages evaluated        : {len(df)}")
    print(f"\n  Per-message detection rate")
    print(f"    Mean  : {df['detection_rate'].mean():.2%}")
    print(f"    Median: {df['detection_rate'].median():.2%}")
    print(f"    Std   : {df['detection_rate'].std():.2%}")

    buckets = df["detection_rate"].value_counts().sort_index()
    print("\n  Detection breakdown (per message)")
    labels = {0.0: "Detected 0/2", 0.5: "Detected 1/2", 1.0: "Detected 2/2"}
    for rate, count in buckets.items():
        label = labels.get(round(rate, 1), f"{rate:.0%}")
        print(f"    {label}: {count} message(s)")

    print("\n  Per-participant summary")
    per_part = df.groupby("session_id")["detection_rate"].mean().reset_index()
    per_part.columns = ["session_id", "avg_detection_rate"]
    print(per_part.to_string(index=False))


# ---------------------------------------------------------------------------
# Condition-2: VerifyChat prediction accuracy (precision / recall / F1)
# ---------------------------------------------------------------------------

def analyze_condition2(tables):
    print("\n" + "=" * 60)
    print("CONDITION-2  —  VerifyChat (claim prediction accuracy)")
    print("=" * 60)

    scores = tables["prediction_scores"]

    if scores.empty:
        print("  No prediction score data yet.")
        return

    print(f"\n  Participants with reveals  : {scores['session_id'].nunique()}")
    print(f"  Reveal events             : {len(scores)}")

    metrics = scores[["precision", "recall", "f1"]].dropna()
    if metrics.empty:
        print("  No metric data yet.")
        return

    print("\n  Aggregate metrics (mean ± std)")
    for col in ["precision", "recall", "f1"]:
        print(f"    {col.capitalize():<10}: {metrics[col].mean():.3f}  ±  {metrics[col].std():.3f}")

    print("\n  Per-participant averages")
    per_part = scores.groupby("session_id")[["precision", "recall", "f1"]].mean().reset_index()
    print(per_part.to_string(index=False))


# ---------------------------------------------------------------------------
# Session overview
# ---------------------------------------------------------------------------

def analyze_sessions(tables):
    print("\n" + "=" * 60)
    print("SESSION OVERVIEW")
    print("=" * 60)

    sessions    = tables["sessions"]
    mode_events = tables["session_mode_events"]

    print(f"\n  Total sessions: {len(sessions)}")

    if "mode" in sessions.columns:
        print("\n  Current mode distribution")
        print(sessions["mode"].value_counts().to_string())

    if not mode_events.empty:
        print(f"\n  Mode switches logged: {len(mode_events)}")
        print(mode_events[["session_id", "mode", "switched_at"]].to_string(index=False))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tables = load()
    analyze_sessions(tables)
    analyze_condition1(tables)
    analyze_condition2(tables)
    print("\n")
