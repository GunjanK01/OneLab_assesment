# 🏦 Payments Reconciliation Engine

> **Automated Internal Ledger ↔ Bank Statement reconciliation with gap classification, monetary quantification, and a production-grade Streamlit dashboard.**

---

## The Problem

In a payments platform, every transaction is recorded **instantly** in an internal ledger the moment a customer pays (T+0). The bank, however, batches and settles funds **one to two business days later** (T+1 or T+2). At month-end, every ledger entry must have a corresponding bank settlement — and the totals must agree to the cent.

In practice, they rarely do. Cross-month timing gaps, floating-point rounding on batched settlements, duplicate entries from retry logic, and orphaned refunds from chargebacks or data loss all silently erode the books. Manual investigation of these discrepancies at scale is slow, error-prone, and expensive.

This engine automates the full reconciliation lifecycle: ingesting both datasets, matching records within a configurable tolerance window, classifying every unmatched record by root cause, and surfacing actionable exceptions in an interactive dashboard.

---

## Key Features

### Gap Detection — 4 Classified Exception Types

- **Cross-Month Settlement** — Transactions posted in the current period that the bank settles in the next calendar month, requiring an accrual entry to keep the books balanced at month-end.

- **Rounding Error** — Banks frequently aggregate multiple individual transactions into a single batch settlement and apply their own rounding. This engine detects the residual discrepancy between the platform's precise per-transaction sum and the bank's rounded batch total.

- **Duplicate Ledger Entry** — Retry logic, webhook replay, or ETL bugs can cause the same transaction ID to appear more than once in the internal ledger while the bank correctly settles it only once. Every duplicate instance is flagged with a suggested remediation.

- **Orphaned Refund** — A negative settlement appearing in the bank statement with no matching original transaction in the internal ledger — a pattern that can indicate fraud, a manual bank-side reversal, or a data ingestion failure.

### Dashboard & Reporting

- Big-number KPI metrics: total matched, exceptions count, accuracy percentage, and total monetary gap in USD
- Daily stacked bar chart of matched vs. unmatched transaction volume (Plotly)
- Monetary gap waterfall chart breaking down the USD impact by exception type
- Searchable, filterable exceptions drill-down table with a **Suggested Action** column per row
- One-click CSV export of all flagged exceptions
- Planted gap detection summary cards confirming each of the 4 gap types was caught

### Data Ingestion

- Launches immediately with synthetic December 2024 demo data (4 planted gaps, ~100 rows per dataset)
- Supports CSV upload of real ledger and bank statement files via the sidebar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Dashboard & UI | [Streamlit](https://streamlit.io) |
| Data Processing | [Pandas](https://pandas.pydata.org) · [NumPy](https://numpy.org) |
| Visualisation | [Plotly](https://plotly.com/python/) |
| Testing | [Pytest](https://pytest.org) |
| Language | Python 3.12+ |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/recon-engine.git
cd recon-engine
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`. Select **Demo Data** in the sidebar to run immediately with synthetic data, or upload your own CSVs.

---

## Testing

The test suite contains **34 assertions** across 6 test classes. It verifies both the data generation integrity and the correct detection of all 4 planted gap types.

```bash
pytest test_recon.py -v
```

Expected output:

```
collected 34 items

test_recon.py::TestDataGeneration::test_ledger_has_expected_rows         PASSED
test_recon.py::TestDataGeneration::test_ledger_contains_duplicate_txn_id PASSED
test_recon.py::TestGap1CrossMonth::test_cross_month_detected             PASSED
test_recon.py::TestGap1CrossMonth::test_cross_month_txn_id_correct       PASSED
test_recon.py::TestGap2RoundingError::test_rounding_gap_amount_correct   PASSED
test_recon.py::TestGap3Duplicate::test_duplicate_detected                PASSED
test_recon.py::TestGap4OrphanedRefund::test_orphaned_refund_amount       PASSED
...

34 passed in ~4s
```

### What the tests assert

| Class | Coverage |
|---|---|
| `TestDataGeneration` | Schema integrity, planted gap presence in correct datasets |
| `TestGap1CrossMonth` | Detection, correct TXN ID, accrual guidance in suggested action |
| `TestGap2RoundingError` | Detection, exact $0.50 gap amount, batch ID flagged |
| `TestGap3Duplicate` | Detection, DUP123 identified, source is INTERNAL |
| `TestGap4OrphanedRefund` | Detection, REF456 identified, $50.00 gap, source is BANK |
| `TestReconEngineIntegrity` | All 4 types present, accuracy bounds, no cross-contamination |

---

## Reconciliation Logic & Assumptions

The following assumptions are hardcoded into the matching engine and displayed in the application sidebar.

| Assumption | Value / Rule |
|---|---|
| **Match window** | ± 2 calendar days between ledger date and settlement date |
| **Currency** | USD only; no multi-currency FX conversion applied |
| **Unique ID** | `txn_id` is expected to be unique per ledger entry; duplicates are flagged |
| **Amount tolerance** | Row-level match requires amounts within $1.00; batch rounding gaps are detected separately |
| **Month boundary** | Transactions dated in the current month that settle in the following month are classified as CROSS_MONTH and excluded from the current period's matched set |
| **Bank batching** | The bank may aggregate multiple platform transactions into a single batch settlement entry |

---

## Project Structure

```
recon-engine/
├── app.py              # Streamlit dashboard + reconciliation engine + data generation
├── test_recon.py       # Pytest suite (34 tests, 6 classes)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Production Scale Considerations

The current implementation is a high-fidelity prototype that correctly models the reconciliation problem and validates the core detection logic. The following section outlines the engineering roadmap required to operate this system at the transaction volumes of a production payments platform.

### 1. Scale & Computational Complexity → Distributed Query Engine

The current matching loop is O(n²) in the worst case: for every ledger row, the engine scans bank rows to find a candidate match. With Pandas DataFrames loaded entirely into memory, this approach is viable up to approximately 500,000 records on a standard machine. At the transaction volumes of a production payments platform — 10 million or more records per day across multiple merchants and currencies — this design collapses in two ways.

First, memory: a 10M-row DataFrame with 10 columns consumes several gigabytes of RAM, leaving no headroom for the intermediate join operations the matching logic requires. Second, latency: even with vectorised Pandas operations, a cross-join at this scale takes minutes to hours, which is incompatible with same-day or intraday reconciliation SLAs.

**Roadmap:** The matching logic must be pushed into a columnar distributed query engine. In a cloud-native stack, this means expressing the reconciliation as a SQL join in **BigQuery** or **Snowflake**, partitioned by settlement date and merchant ID. The ± 2-day window becomes a `DATE_DIFF` predicate evaluated server-side across distributed compute nodes, reducing wall-clock time from hours to seconds. For streaming intraday reconciliation, **Apache Flink** or **Kafka Streams** can match ledger events against settlement events as they arrive, eliminating the month-end batch entirely and surfacing exceptions within minutes of a gap opening.

---

### 2. Data Heterogeneity & Normalisation → Bank Connector Layer

This prototype consumes clean, schema-consistent CSV files with predictable column names and ISO 8601 dates. Real bank statements do not look like this. The global banking system communicates in formats that predate the web: **MT940** (a SWIFT message format with positional fixed-width fields and colon-delimited tags), **ISO 20022 XML** (verbose, deeply nested XML with namespace declarations and complex type hierarchies), and **BAI2** (a record-type-coded flat file with its own balance type taxonomy). Domestic rails introduce further variation: SEPA CAMT.053 in Europe, NACHA in the US, and IMPS/NEFT statement formats in India.

Beyond format, there are encoding issues (Latin-1 vs UTF-8), timezone ambiguities (settlement timestamps in bank-local time vs UTC), currency representation differences (comma vs period as decimal separator), and description field pollution (free-text bank references that must be regex-parsed to extract a recoverable transaction reference).

**Roadmap:** A production reconciliation system requires a **bank connector layer** — a dedicated normalisation service that sits between raw bank statement ingestion and the matching engine. Each bank integration is a separate connector implementing a common interface: `parse(raw_bytes) → NormalisedStatement`. The normalised schema is fixed (ISO 8601 timestamps in UTC, amounts as `Decimal` not `float`, explicit currency codes, a canonical `external_ref` field). New bank integrations add a connector; the matching engine never changes. This is the architectural pattern used by open banking aggregators such as TrueLayer and Plaid, and it is the correct separation of concerns for a multi-bank payments platform.

---

### 3. Idempotency & Auditability → System of Record

The current script is stateless. Every execution regenerates the data, re-runs the reconciliation, and discards all results when the process exits. There is no record of which exceptions were previously seen, which have been investigated, and which have been resolved. In a financial context, this is not merely a missing feature — it is a compliance risk.

Consider the failure mode: an engineer runs the reconciliation, exports the exceptions CSV, and begins working through the list. Before finishing, a colleague re-runs the script, which re-flags all exceptions including ones already resolved. The resolved ones now appear open again. Without a persistent exception state, there is no way to distinguish a new gap from a previously investigated and closed one. At best this wastes analyst time; at worst it causes a transaction to be accrued twice or a duplicate to be removed twice, introducing new errors in the process of correcting old ones.

**Roadmap:** A production reconciliation engine requires three layers of statefulness. The first is **idempotent job execution**: every reconciliation run is assigned a deterministic `job_id` (derived from the hash of the input files and the run date), and results are written to a database only if that `job_id` has not been processed before. Re-running with the same inputs is a no-op. The second is **exception lifecycle tracking**: each flagged exception is a first-class record with a status (`OPEN`, `IN_REVIEW`, `DISPUTED`, `RESOLVED`), an owner, and a full audit trail of state transitions. The third is a **system of record integration**: resolved exceptions write adjustment entries back to the general ledger via a controlled API, ensuring that the fix is reflected in the books and not just in the reconciliation tool. This is the architecture that satisfies both SOX auditability requirements and the operational needs of a finance team working through exceptions at scale.

---

## Author

Built as a technical assessment demonstrating production-grade payments engineering across data generation, reconciliation logic, interactive dashboarding, and test coverage.
