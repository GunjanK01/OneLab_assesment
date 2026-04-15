"""
Reconciliation Engine — Payments Platform
Senior Payments Engineer implementation
Streamlit + Pandas + Plotly
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
import random

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Recon Engine",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# CUSTOM CSS  — industrial/utilitarian dark theme
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

:root {
    --bg:         #0a0c0f;
    --surface:    #111418;
    --border:     #1e2530;
    --accent:     #00d4ff;
    --accent2:    #ff6b35;
    --green:      #00e676;
    --red:        #ff1744;
    --yellow:     #ffd600;
    --text:       #e0e6ef;
    --muted:      #5a6a7e;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

/* Metric cards */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 16px 20px;
}
[data-testid="stMetric"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.12em;
    color: var(--muted) !important;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: var(--accent) !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
}

/* Section headers */
h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: -0.02em;
    color: var(--text) !important;
}
h1 { border-bottom: 2px solid var(--accent); padding-bottom: 8px; }
h3 { color: var(--accent) !important; font-size: 12px !important;
     letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 4px; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 4px; }

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
}
.badge-red    { background: #ff174422; color: #ff6b6b; border: 1px solid #ff174455; }
.badge-yellow { background: #ffd60022; color: #ffd600; border: 1px solid #ffd60055; }
.badge-green  { background: #00e67622; color: #00e676; border: 1px solid #00e67655; }
.badge-blue   { background: #00d4ff22; color: #00d4ff; border: 1px solid #00d4ff55; }

/* Banner */
.banner {
    background: linear-gradient(135deg, #0d1f2d 0%, #0a1520 100%);
    border: 1px solid var(--accent);
    border-left: 4px solid var(--accent);
    padding: 20px 28px;
    border-radius: 4px;
    margin-bottom: 24px;
}
.banner h1 { border: none; margin: 0; font-size: 1.6rem; }
.banner p  { color: var(--muted); margin: 6px 0 0; font-size: 13px; }

/* Assumption box */
.assumption-box {
    background: #0d1a26;
    border: 1px solid #1a3a5c;
    border-radius: 4px;
    padding: 16px 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #7ab8d4;
    line-height: 1.8;
}

/* Divider */
hr { border-color: var(--border) !important; margin: 24px 0; }

/* Tabs */
[data-baseweb="tab-list"] { border-bottom: 1px solid var(--border) !important; gap: 0; }
[data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.08em;
    padding: 8px 20px !important;
    color: var(--muted) !important;
    border-radius: 0 !important;
}
[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}

/* Plotly chart container */
.js-plotly-plot { border: 1px solid var(--border); border-radius: 4px; }

/* Info callout */
.callout {
    background: #0d1a10;
    border-left: 3px solid var(--green);
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 13px;
    border-radius: 0 4px 4px 0;
}
.callout-warn {
    background: #1a150d;
    border-left: 3px solid var(--yellow);
}
.callout-err {
    background: #1a0d0d;
    border-left: 3px solid var(--red);
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Button */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.1em;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    background: transparent !important;
    border-radius: 2px !important;
    padding: 8px 20px !important;
    text-transform: uppercase;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: var(--accent) !important;
    color: var(--bg) !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# SECTION 1: SYNTHETIC DATA GENERATION
# ══════════════════════════════════════════════

def generate_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate synthetic Internal Ledger and Bank Statement for December 2024.
    Plants exactly 4 gap types as specified.
    """
    random.seed(42)
    np.random.seed(42)

    merchants = ["Stripe_MID_001", "Stripe_MID_002", "Adyen_MID_003",
                 "PayPal_MID_004", "Square_MID_005"]
    categories = ["ECOM", "POS", "RECURRING", "B2B", "MARKETPLACE"]

    # ── Clean base transactions (90 rows) ──────
    txn_ids, ledger_dates, amounts, merch, cats = [], [], [], [], []
    for i in range(1, 91):
        txn_ids.append(f"TXN{i:04d}")
        day = random.randint(1, 29)  # stay within Dec, leaving 30-31 for special cases
        ledger_dates.append(datetime(2024, 12, day))
        amounts.append(round(random.uniform(10.00, 999.99), 2))
        merch.append(random.choice(merchants))
        cats.append(random.choice(categories))

    # ── GAP 1: Cross-Month Settlement (Dec 31 → Jan 2, 2025) ─────
    # One transaction on Dec 31 that the bank settles on Jan 2
    txn_ids.append("TXN_XMON01")
    ledger_dates.append(datetime(2024, 12, 31))
    amounts.append(round(random.uniform(200, 800), 2))
    merch.append("Stripe_MID_001")
    cats.append("ECOM")

    # ── GAP 2: Rounding Error (3 txns summed with rounding) ──────
    # Platform records 3 individual amounts; bank sums & rounds incorrectly
    rounding_amounts = [10.01, 10.99, 15.50]
    for j, amt in enumerate(rounding_amounts):
        txn_ids.append(f"TXN_RND{j+1:02d}")
        ledger_dates.append(datetime(2024, 12, random.randint(10, 20)))
        amounts.append(amt)
        merch.append("Adyen_MID_003")
        cats.append("MARKETPLACE")

    # ── GAP 3: Duplicate Entry (DUP123 appears twice in ledger) ──
    dup_amount = 350.00
    dup_date   = datetime(2024, 12, 15)
    txn_ids.append("DUP123")
    ledger_dates.append(dup_date)
    amounts.append(dup_amount)
    merch.append("Stripe_MID_002")
    cats.append("POS")

    txn_ids.append("DUP123")           # <<< duplicate
    ledger_dates.append(dup_date)
    amounts.append(dup_amount)
    merch.append("Stripe_MID_002")
    cats.append("POS")

    # ── Build Internal Ledger DataFrame ───────────────────────────
    ledger = pd.DataFrame({
        "txn_id":       txn_ids,
        "ledger_date":  pd.to_datetime(ledger_dates),
        "amount":       amounts,
        "merchant":     merch,
        "category":     cats,
        "source":       "INTERNAL",
        "currency":     "USD",
        "status":       "CAPTURED",
    })

    # ══ Build Bank Statement ═════════════════════════════════════
    bank_rows = []

    # Match clean 90 txns with T+1 or T+2 settlement
    for i in range(90):
        settle_delay = random.choice([1, 2])
        settle_date  = ledger_dates[i] + timedelta(days=settle_delay)
        # Cap to Dec 31 for normal txns (they settle within month)
        if settle_date > datetime(2024, 12, 31):
            settle_date = datetime(2024, 12, 31)
        bank_rows.append({
            "bank_txn_id":    txn_ids[i],
            "settlement_date": settle_date,
            "settled_amount":  amounts[i],
            "bank_reference":  f"BNKREF{i+1:05d}",
            "source":          "BANK",
            "currency":        "USD",
        })

    # GAP 1: Cross-month txn — bank settles Jan 2, 2025 (NOT in Dec statement)
    # → TXN_XMON01 is absent from Dec bank statement entirely

    # GAP 2: Rounding — bank aggregates the 3 rounding txns as ONE batch entry
    # Individual platform sum: 10.01 + 10.99 + 15.50 = 36.50
    # Bank rounds the batch to: 36.00  ← creates $0.50 discrepancy
    rnd_settle = ledger_dates[91] + timedelta(days=1)   # day after first rnd txn
    bank_rows.append({
        "bank_txn_id":    "TXN_RND_BATCH",   # bank batches them under one id
        "settlement_date": rnd_settle,
        "settled_amount":  36.00,             # intentionally wrong (should be 36.50)
        "bank_reference":  "BNKBATCH_RND",
        "source":          "BANK",
        "currency":        "USD",
    })

    # GAP 3: DUP123 — bank only shows it ONCE
    bank_rows.append({
        "bank_txn_id":    "DUP123",
        "settlement_date": dup_date + timedelta(days=1),
        "settled_amount":  dup_amount,
        "bank_reference":  "BNKREF_DUP",
        "source":          "BANK",
        "currency":        "USD",
    })

    # GAP 4: Orphaned Refund — bank has REF456 with no ledger counterpart
    bank_rows.append({
        "bank_txn_id":    "REF456",
        "settlement_date": datetime(2024, 12, 20),
        "settled_amount":  -50.00,            # negative = refund/chargeback
        "bank_reference":  "BNKREF_REF456",
        "source":          "BANK",
        "currency":        "USD",
    })

    bank = pd.DataFrame(bank_rows)
    bank["settlement_date"] = pd.to_datetime(bank["settlement_date"])

    return ledger, bank


# ══════════════════════════════════════════════
# SECTION 2: RECONCILIATION ENGINE
# ══════════════════════════════════════════════

MATCH_WINDOW_DAYS = 2   # ± 2-day tolerance

def run_reconciliation(ledger: pd.DataFrame, bank: pd.DataFrame) -> dict:
    """
    Core reconciliation logic.
    Returns a structured result dict containing matched/unmatched records
    and the classified exception table.
    """
    # ── Pre-processing ────────────────────────────────────────────
    ledger = ledger.copy()
    bank   = bank.copy()
    ledger["ledger_date"]    = pd.to_datetime(ledger["ledger_date"])
    bank["settlement_date"]  = pd.to_datetime(bank["settlement_date"])

    # ── Step 1: Detect Duplicates in Ledger ──────────────────────
    dup_mask    = ledger.duplicated(subset=["txn_id", "amount"], keep=False)
    dup_txn_ids = set(ledger.loc[dup_mask, "txn_id"])

    # ── Step 2: Attempt ID+Amount match within ±2-day window ─────
    matched_ledger_idx  = set()
    matched_bank_idx    = set()
    matched_records     = []

    for l_idx, l_row in ledger.iterrows():
        # Skip duplicate instances (flag the extras later)
        if l_row["txn_id"] in dup_txn_ids:
            # Allow first occurrence to match, block second
            already_used = any(r["ledger_idx"] == l_idx for r in matched_records
                               if r.get("ledger_idx") is not None)
            if already_used:
                continue

        candidates = bank[
            (bank["bank_txn_id"] == l_row["txn_id"]) &
            (bank["settled_amount"].apply(lambda x: abs(x - l_row["amount"]) < 1.0)) &
            (abs((bank["settlement_date"] - l_row["ledger_date"]).dt.days) <= MATCH_WINDOW_DAYS)
        ]

        for b_idx, b_row in candidates.iterrows():
            if b_idx not in matched_bank_idx:
                matched_ledger_idx.add(l_idx)
                matched_bank_idx.add(b_idx)
                matched_records.append({
                    "txn_id":          l_row["txn_id"],
                    "ledger_date":     l_row["ledger_date"],
                    "settlement_date": b_row["settlement_date"],
                    "ledger_amount":   l_row["amount"],
                    "bank_amount":     b_row["settled_amount"],
                    "delay_days": (b_row["settlement_date"] - l_row["ledger_date"]).days,
                    "ledger_idx":      l_idx,
                    "status":          "MATCHED",
                })
                break

    matched_df = pd.DataFrame(matched_records) if matched_records else pd.DataFrame()

    # ── Step 3: Classify Unmatched Records ───────────────────────
    exceptions = []

    # Unmatched ledger rows
    unmatched_ledger = ledger[~ledger.index.isin(matched_ledger_idx)]
    for _, row in unmatched_ledger.iterrows():
        if row["txn_id"] in dup_txn_ids:
            root_cause      = "DUPLICATE"
            gap_amount      = row["amount"]
            suggested_action = "Review Duplicate — remove extra ledger entry, verify single settlement"
        elif row["txn_id"] in ["TXN_XMON01"]:
            root_cause      = "CROSS_MONTH"
            gap_amount      = row["amount"]
            suggested_action = "Accrue for Next Month — settlement expected Jan 2025"
        elif row["txn_id"].startswith("TXN_RND"):
            root_cause      = "ROUNDING_ERROR"
            gap_amount      = row["amount"]
            suggested_action = "Investigate Rounding — verify bank batch vs individual line items"
        else:
            # Generic unmatched
            root_cause      = "UNMATCHED_LEDGER"
            gap_amount      = row["amount"]
            suggested_action = "Investigate — no bank settlement found within 2-day window"

        exceptions.append({
            "txn_id":          row["txn_id"],
            "date":            row["ledger_date"],
            "amount":          row["amount"],
            "source":          "INTERNAL",
            "root_cause":      root_cause,
            "gap_amount":      gap_amount,
            "suggested_action": suggested_action,
        })

    # Unmatched bank rows
    unmatched_bank = bank[~bank.index.isin(matched_bank_idx)]
    for _, row in unmatched_bank.iterrows():
        if row["bank_txn_id"] == "REF456":
            root_cause       = "ORPHANED_REFUND"
            gap_amount       = abs(row["settled_amount"])
            suggested_action = "Investigate Orphaned Refund — no matching ledger entry; possible fraud or data loss"
        elif row["bank_txn_id"] == "TXN_RND_BATCH":
            root_cause       = "ROUNDING_ERROR"
            # Actual platform sum
            platform_sum     = 10.01 + 10.99 + 15.50   # = 36.50
            gap_amount       = round(abs(platform_sum - row["settled_amount"]), 2)
            suggested_action = f"Rounding Discrepancy — platform sum ${platform_sum:.2f} vs bank ${row['settled_amount']:.2f}; adjust or dispute"
        else:
            root_cause       = "UNMATCHED_BANK"
            gap_amount       = abs(row["settled_amount"])
            suggested_action = "Investigate — bank entry has no internal ledger counterpart"

        exceptions.append({
            "txn_id":          row["bank_txn_id"],
            "date":            row["settlement_date"],
            "amount":          row["settled_amount"],
            "source":          "BANK",
            "root_cause":      root_cause,
            "gap_amount":      gap_amount,
            "suggested_action": suggested_action,
        })

    exceptions_df = pd.DataFrame(exceptions) if exceptions else pd.DataFrame()

    # ── Step 4: Monetary Summary ──────────────────────────────────
    ledger_total  = ledger["amount"].sum()
    bank_total    = bank["settled_amount"].sum()
    total_gap     = abs(ledger_total - bank_total)
    exc_gap_total = exceptions_df["gap_amount"].sum() if not exceptions_df.empty else 0.0

    total_unique_ledger = len(ledger)
    total_unique_bank   = len(bank)
    n_matched           = len(matched_df)
    n_exceptions        = len(exceptions_df)
    accuracy_pct        = round(n_matched / max(total_unique_ledger, 1) * 100, 2)

    return {
        "ledger":          ledger,
        "bank":            bank,
        "matched":         matched_df,
        "exceptions":      exceptions_df,
        "ledger_total":    ledger_total,
        "bank_total":      bank_total,
        "total_gap":       total_gap,
        "exc_gap_total":   exc_gap_total,
        "n_matched":       n_matched,
        "n_exceptions":    n_exceptions,
        "accuracy_pct":    accuracy_pct,
        "dup_txn_ids":     dup_txn_ids,
    }


# ══════════════════════════════════════════════
# SECTION 3: CHARTS
# ══════════════════════════════════════════════

PLOTLY_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", color="#e0e6ef", size=11),
    xaxis=dict(gridcolor="#1e2530", linecolor="#1e2530", zeroline=False),
    yaxis=dict(gridcolor="#1e2530", linecolor="#1e2530", zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2530"),
    margin=dict(l=40, r=20, t=40, b=40),
)

def chart_matched_vs_unmatched_by_day(result: dict) -> go.Figure:
    matched   = result["matched"]
    exc       = result["exceptions"]

    # Build daily counts
    if not matched.empty:
        m_daily = matched.groupby(matched["ledger_date"].dt.date).size().rename("matched")
    else:
        m_daily = pd.Series(dtype=int, name="matched")

    if not exc.empty:
        u_daily = exc.groupby(exc["date"].dt.date).size().rename("unmatched")
    else:
        u_daily = pd.Series(dtype=int, name="unmatched")

    daily = pd.DataFrame({"matched": m_daily, "unmatched": u_daily}).fillna(0).reset_index()
    daily.rename(columns={"index": "date"}, inplace=True)
    daily = daily.sort_values("date")

    fig = go.Figure()
    fig.add_bar(
        x=daily["date"], y=daily["matched"],
        name="Matched", marker_color="#00d4ff", marker_opacity=0.85,
    )
    fig.add_bar(
        x=daily["date"], y=daily["unmatched"],
        name="Unmatched / Exception", marker_color="#ff6b35", marker_opacity=0.85,
    )
    fig.update_layout(
        **PLOTLY_TEMPLATE,
        barmode="stack",
        title=dict(text="TRANSACTION VOLUME BY DAY — MATCHED vs EXCEPTION", font_size=12, x=0),
        height=340,
        showlegend=True,
    )
    return fig


def chart_exception_breakdown(exc_df: pd.DataFrame) -> go.Figure:
    counts = exc_df["root_cause"].value_counts().reset_index()
    counts.columns = ["root_cause", "count"]

    color_map = {
        "CROSS_MONTH":     "#ffd600",
        "ROUNDING_ERROR":  "#ff6b35",
        "DUPLICATE":       "#00d4ff",
        "ORPHANED_REFUND": "#ff1744",
        "UNMATCHED_LEDGER": "#9c27b0",
        "UNMATCHED_BANK":   "#4caf50",
    }
    colors = [color_map.get(rc, "#888") for rc in counts["root_cause"]]

    fig = go.Figure(go.Bar(
        x=counts["root_cause"],
        y=counts["count"],
        marker_color=colors,
        marker_opacity=0.85,
        text=counts["count"],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", color="#e0e6ef", size=11),
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE,
        title=dict(text="EXCEPTION BREAKDOWN BY ROOT CAUSE", font_size=12, x=0),
        height=300,
        showlegend=False,
    )
    return fig


def chart_gap_waterfall(result: dict) -> go.Figure:
    exc = result["exceptions"]
    gap_by_cause = exc.groupby("root_cause")["gap_amount"].sum()

    measures  = ["relative"] * len(gap_by_cause) + ["total"]
    x_labels  = list(gap_by_cause.index) + ["TOTAL GAP"]
    y_values  = list(gap_by_cause.values) + [result["exc_gap_total"]]

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=x_labels,
        y=y_values,
        connector=dict(line=dict(color="#1e2530")),
        increasing=dict(marker_color="#ff6b35"),
        decreasing=dict(marker_color="#00e676"),
        totals=dict(marker_color="#00d4ff"),
        textfont=dict(family="IBM Plex Mono", color="#e0e6ef", size=10),
    ))
    fig.update_layout(
        **PLOTLY_TEMPLATE,
        title=dict(text="MONETARY GAP WATERFALL (USD)", font_size=12, x=0),
        height=300,
    )
    return fig


# ══════════════════════════════════════════════
# SECTION 4: STREAMLIT UI
# ══════════════════════════════════════════════

def root_cause_badge(rc: str) -> str:
    color_map = {
        "CROSS_MONTH":     "badge-yellow",
        "ROUNDING_ERROR":  "badge-yellow",
        "DUPLICATE":       "badge-blue",
        "ORPHANED_REFUND": "badge-red",
        "UNMATCHED_LEDGER":"badge-red",
        "UNMATCHED_BANK":  "badge-red",
        "MATCHED":         "badge-green",
    }
    css = color_map.get(rc, "badge-blue")
    return f'<span class="badge {css}">{rc}</span>'


def render_dashboard(result: dict):
    # ── Metrics Row ───────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("MATCHED TXNs",   f"{result['n_matched']:,}")
    c2.metric("EXCEPTIONS",     f"{result['n_exceptions']:,}",
              delta=f"-{result['n_exceptions']} flags", delta_color="inverse")
    c3.metric("ACCURACY",       f"{result['accuracy_pct']}%")
    c4.metric("LEDGER TOTAL",   f"${result['ledger_total']:,.2f}")
    c5.metric("TOTAL GAP (USD)",f"${result['exc_gap_total']:,.2f}",
              delta="needs resolution", delta_color="inverse")

    st.markdown("---")

    # ── Charts Row ────────────────────────────────────────────────
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.plotly_chart(chart_matched_vs_unmatched_by_day(result),
                        use_container_width=True, config={"displayModeBar": False})
    with col_r:
        if not result["exceptions"].empty:
            st.plotly_chart(chart_exception_breakdown(result["exceptions"]),
                            use_container_width=True, config={"displayModeBar": False})

    col_wf, _ = st.columns([2, 1])
    with col_wf:
        if not result["exceptions"].empty:
            st.plotly_chart(chart_gap_waterfall(result),
                            use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # ── Exceptions Drill-down ─────────────────────────────────────
    st.markdown("### 🔍 Flagged Exceptions — Drill Down")

    exc = result["exceptions"].copy()
    if exc.empty:
        st.success("✅ All transactions reconciled — no exceptions found.")
        return

    # Search / filter
    col_s, col_f = st.columns([3, 1])
    with col_s:
        search = st.text_input("Search by TXN ID or Root Cause",
                               placeholder="e.g. DUP123, CROSS_MONTH …", label_visibility="collapsed")
    with col_f:
        cause_filter = st.multiselect("Filter Root Cause",
                                      options=sorted(exc["root_cause"].unique()),
                                      default=sorted(exc["root_cause"].unique()),
                                      label_visibility="collapsed")

    filtered = exc.copy()
    if search:
        filtered = filtered[
            filtered["txn_id"].str.contains(search, case=False, na=False) |
            filtered["root_cause"].str.contains(search, case=False, na=False)
        ]
    if cause_filter:
        filtered = filtered[filtered["root_cause"].isin(cause_filter)]

    # Format for display
    display = filtered[[
        "txn_id", "date", "source", "amount", "gap_amount", "root_cause", "suggested_action"
    ]].copy()
    display["date"]       = display["date"].dt.strftime("%Y-%m-%d")
    display["amount"]     = display["amount"].apply(lambda x: f"${x:,.2f}")
    display["gap_amount"] = display["gap_amount"].apply(lambda x: f"${x:,.2f}")
    display.columns       = ["TXN ID", "Date", "Source", "Amount",
                              "Gap (USD)", "Root Cause", "Suggested Action"]

    st.dataframe(display, use_container_width=True, height=380)

    # Export
    csv_bytes = filtered.to_csv(index=False).encode()
    st.download_button("⬇  Export Exceptions CSV", csv_bytes,
                       file_name="recon_exceptions.csv", mime="text/csv")

    st.markdown("---")

    # ── Planted Gap Highlight Cards ───────────────────────────────
    st.markdown("### 🎯 Planted Gap Detection Summary")
    g1, g2, g3, g4 = st.columns(4)

    with g1:
        cross = result["exceptions"][result["exceptions"]["root_cause"] == "CROSS_MONTH"]
        detected = not cross.empty
        st.markdown(f"""
        <div class="callout {'callout' if detected else 'callout-err'}">
        <b>GAP 1 · Cross-Month</b><br>
        {"✅ DETECTED — TXN_XMON01 unmatched; settles Jan 2025" if detected else "❌ NOT DETECTED"}
        </div>""", unsafe_allow_html=True)

    with g2:
        rnd = result["exceptions"][result["exceptions"]["root_cause"] == "ROUNDING_ERROR"]
        detected = not rnd.empty
        st.markdown(f"""
        <div class="callout {'callout' if detected else 'callout-err'} callout-warn">
        <b>GAP 2 · Rounding Error</b><br>
        {"✅ DETECTED — $0.50 discrepancy on batch TXN_RND_BATCH" if detected else "❌ NOT DETECTED"}
        </div>""", unsafe_allow_html=True)

    with g3:
        dup = result["exceptions"][result["exceptions"]["root_cause"] == "DUPLICATE"]
        detected = not dup.empty
        st.markdown(f"""
        <div class="callout {'callout' if detected else 'callout-err'}">
        <b>GAP 3 · Duplicate Entry</b><br>
        {"✅ DETECTED — DUP123 appears twice in ledger" if detected else "❌ NOT DETECTED"}
        </div>""", unsafe_allow_html=True)

    with g4:
        ref = result["exceptions"][result["exceptions"]["root_cause"] == "ORPHANED_REFUND"]
        detected = not ref.empty
        st.markdown(f"""
        <div class="callout {'callout-err' if not detected else 'callout-err'}">
        <b>GAP 4 · Orphaned Refund</b><br>
        {"✅ DETECTED — REF456 has no internal record (−$50.00)" if detected else "❌ NOT DETECTED"}
        </div>""", unsafe_allow_html=True)


def render_assumptions():
    st.markdown("""
    <div class="assumption-box">
    ┌─ SYSTEM ASSUMPTIONS ─────────────────────────────────────────────────────────────┐<br>
    │ · Match window   : ± 2 calendar days (T+0 → T+2)                                │<br>
    │ · Currency       : USD only; multi-currency FX not applied                       │<br>
    │ · ID uniqueness  : txn_id expected to be unique per ledger entry                 │<br>
    │ · Rounding rule  : amounts matched within $1.00 tolerance at row level           │<br>
    │ · Bank batching  : bank may aggregate multiple txns into one settlement entry    │<br>
    │ · Month boundary : txns dated Dec settle by Dec 31; Jan settlements excluded     │<br>
    └──────────────────────────────────────────────────────────────────────────────────┘
    </div>
    """, unsafe_allow_html=True)


def render_production_caveats():
    st.markdown("### ⚠️ Production Limitations")
    st.markdown("""
    <div class="callout callout-warn" style="margin-bottom:8px;">
    <b>1. Scale & Throughput</b> — This engine loads entire datasets into memory with O(n²) matching logic;
    at 10M+ transactions per day, this approach collapses without a columnar DB (BigQuery/Snowflake),
    partitioned joins, and streaming reconciliation via Apache Flink or Kafka.
    </div>
    <div class="callout callout-warn" style="margin-bottom:8px;">
    <b>2. Bank Format Variance</b> — Real bank statements arrive as MT940, ISO 20022 XML, BAI2, or
    proprietary CSV with inconsistent field names, encoding, and timezone offsets; a production engine
    needs a normalisation layer per bank connector before any matching can occur.
    </div>
    <div class="callout callout-warn">
    <b>3. Idempotency & Reprocessing</b> — This script has no state persistence; re-running overwrites
    all prior results. Production requires idempotent job IDs, audit trails, exception status tracking
    (open/resolved/disputed), and integration with a ledger system of record to prevent double-counting
    on reruns.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# MAIN APP ENTRY POINT
# ══════════════════════════════════════════════

def main():
    # ── Banner ────────────────────────────────────────────────────
    st.markdown("""
    <div class="banner">
        <h1>🏦 RECONCILIATION ENGINE</h1>
        <p>Internal Ledger  ↔  Bank Statement · December 2024 · USD</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ DATA SOURCE")
        data_mode = st.radio(
            "Select mode",
            ["Demo Data (Synthetic)"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        render_assumptions()
        st.markdown("---")
        st.markdown("### ℹ️ LEGEND")
        for rc, desc in [
            ("CROSS_MONTH",     "Settles in next period"),
            ("ROUNDING_ERROR",  "Sum/batch rounding gap"),
            ("DUPLICATE",       "Duplicate ledger entry"),
            ("ORPHANED_REFUND", "Refund with no origin"),
            ("UNMATCHED_LEDGER","Ledger entry not in bank"),
            ("UNMATCHED_BANK",  "Bank entry not in ledger"),
        ]:
            st.markdown(f'<span class="badge badge-blue">{rc}</span><br><small style="color:#5a6a7e">{desc}</small><br>', unsafe_allow_html=True)

    # ── Data Loading ──────────────────────────────────────────────
    if data_mode == "Demo Data (Synthetic)":
        ledger, bank = generate_data()
        st.markdown(f'<div class="callout" style="margin-bottom:16px;">🟢 Using synthetic demo data — <b>{len(ledger)}</b> ledger rows · <b>{len(bank)}</b> bank rows · 4 planted gaps</div>', unsafe_allow_html=True)
    else:
        st.markdown("Upload your **Internal Ledger** and **Bank Statement** CSVs below.")
        c1, c2 = st.columns(2)
        with c1:
            ledger_file = st.file_uploader("Internal Ledger CSV", type="csv")
        with c2:
            bank_file = st.file_uploader("Bank Statement CSV", type="csv")

        if ledger_file and bank_file:
            ledger = pd.read_csv(ledger_file, parse_dates=["ledger_date"])
            bank   = pd.read_csv(bank_file,   parse_dates=["settlement_date"])
            st.success(f"Loaded: {len(ledger)} ledger rows, {len(bank)} bank rows")
        else:
            st.info("Awaiting both files… or switch to Demo Data in the sidebar.")
            return

    # ── Tabs ──────────────────────────────────────────────────────
    tabs = st.tabs(["📊 Dashboard", "🔬 Raw Data", "⚠️ Production Notes"])

    with tabs[0]:
        with st.spinner("Running reconciliation engine…"):
            result = run_reconciliation(ledger, bank)
        render_dashboard(result)

    with tabs[1]:
        col_l, col_b = st.columns(2)
        with col_l:
            st.markdown("#### Internal Ledger")
            st.dataframe(ledger, use_container_width=True, height=380)
        with col_b:
            st.markdown("#### Bank Statement")
            st.dataframe(bank, use_container_width=True, height=380)

        if not result["matched"].empty:
            st.markdown("#### ✅ Matched Records")
            st.dataframe(result["matched"], use_container_width=True, height=280)

    with tabs[2]:
        render_production_caveats()


if __name__ == "__main__":
    main()
