"""
test_recon.py
─────────────
Pytest suite for the Reconciliation Engine.
Asserts correct detection of all 4 planted gap types.

Run with:
    pytest test_recon.py -v
"""

import pytest
import pandas as pd
import sys
import os

# Allow importing from app.py in the same directory regardless of cwd
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import generate_data, run_reconciliation


# ──────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────

@pytest.fixture(scope="module")
def recon_result():
    """Run the reconciliation engine once; reuse across all tests."""
    ledger, bank = generate_data()
    return run_reconciliation(ledger, bank)


@pytest.fixture(scope="module")
def exceptions(recon_result):
    return recon_result["exceptions"]


@pytest.fixture(scope="module")
def ledger():
    ledger, _ = generate_data()
    return ledger


@pytest.fixture(scope="module")
def bank():
    _, bank = generate_data()
    return bank


# ──────────────────────────────────────────────
# DATA GENERATION SANITY CHECKS
# ──────────────────────────────────────────────

class TestDataGeneration:

    def test_ledger_has_expected_rows(self, ledger):
        """Ledger should have ~96 rows (90 base + 1 cross-month + 3 rounding + 2 duplicates)."""
        assert len(ledger) >= 90, f"Expected >= 90 ledger rows, got {len(ledger)}"

    def test_bank_has_expected_rows(self, bank):
        """Bank should have rows for 90 clean txns + 1 batch rounding + 1 duplicate + 1 refund."""
        assert len(bank) >= 90, f"Expected >= 90 bank rows, got {len(bank)}"

    def test_ledger_contains_duplicate_txn_id(self, ledger):
        """DUP123 must appear exactly twice in the ledger."""
        dup_count = (ledger["txn_id"] == "DUP123").sum()
        assert dup_count == 2, f"Expected DUP123 twice in ledger, found {dup_count}"

    def test_bank_contains_duplicate_txn_id_once(self, bank):
        """DUP123 must appear exactly once in the bank statement."""
        dup_count = (bank["bank_txn_id"] == "DUP123").sum()
        assert dup_count == 1, f"Expected DUP123 once in bank, found {dup_count}"

    def test_cross_month_txn_in_ledger(self, ledger):
        """TXN_XMON01 must exist in the ledger on Dec 31, 2024."""
        row = ledger[ledger["txn_id"] == "TXN_XMON01"]
        assert len(row) == 1, "TXN_XMON01 missing from ledger"
        assert row.iloc[0]["ledger_date"].month == 12
        assert row.iloc[0]["ledger_date"].day == 31

    def test_cross_month_txn_absent_from_december_bank(self, bank):
        """TXN_XMON01 must NOT appear in the December bank statement."""
        row = bank[
            (bank["bank_txn_id"] == "TXN_XMON01") &
            (bank["settlement_date"].dt.month == 12)
        ]
        assert len(row) == 0, "TXN_XMON01 should not settle in December bank"

    def test_orphaned_refund_in_bank(self, bank):
        """REF456 must appear in the bank with a negative amount."""
        row = bank[bank["bank_txn_id"] == "REF456"]
        assert len(row) == 1, "REF456 missing from bank statement"
        assert row.iloc[0]["settled_amount"] < 0, "REF456 should be a negative (refund) amount"
        assert row.iloc[0]["settled_amount"] == -50.00

    def test_orphaned_refund_absent_from_ledger(self, ledger):
        """REF456 must NOT appear in the internal ledger."""
        row = ledger[ledger["txn_id"] == "REF456"]
        assert len(row) == 0, "REF456 should not exist in the internal ledger"

    def test_rounding_txns_in_ledger(self, ledger):
        """TXN_RND01, TXN_RND02, TXN_RND03 must all exist in ledger."""
        for tid in ["TXN_RND01", "TXN_RND02", "TXN_RND03"]:
            assert (ledger["txn_id"] == tid).any(), f"{tid} missing from ledger"

    def test_rounding_batch_in_bank(self, bank):
        """Bank should have TXN_RND_BATCH as the aggregated rounding entry."""
        row = bank[bank["bank_txn_id"] == "TXN_RND_BATCH"]
        assert len(row) == 1, "TXN_RND_BATCH missing from bank"
        assert row.iloc[0]["settled_amount"] == 36.00

    def test_rounding_sum_discrepancy(self, bank, ledger):
        """Platform sum of rounding txns should not equal bank batch amount."""
        rnd_rows     = ledger[ledger["txn_id"].isin(["TXN_RND01", "TXN_RND02", "TXN_RND03"])]
        platform_sum = round(rnd_rows["amount"].sum(), 2)
        bank_batch   = bank[bank["bank_txn_id"] == "TXN_RND_BATCH"].iloc[0]["settled_amount"]
        assert platform_sum != bank_batch, (
            f"Expected rounding discrepancy: platform={platform_sum}, bank={bank_batch}"
        )
        assert round(abs(platform_sum - bank_batch), 2) == 0.50, (
            f"Expected $0.50 rounding gap, got ${abs(platform_sum - bank_batch):.2f}"
        )


# ──────────────────────────────────────────────
# GAP 1: CROSS-MONTH SETTLEMENT
# ──────────────────────────────────────────────

class TestGap1CrossMonth:

    def test_cross_month_detected(self, exceptions):
        """CROSS_MONTH root cause must appear in exceptions."""
        cross = exceptions[exceptions["root_cause"] == "CROSS_MONTH"]
        assert len(cross) >= 1, "CROSS_MONTH gap not detected"

    def test_cross_month_txn_id_correct(self, exceptions):
        """The flagged cross-month txn must be TXN_XMON01."""
        cross = exceptions[exceptions["root_cause"] == "CROSS_MONTH"]
        assert "TXN_XMON01" in cross["txn_id"].values, (
            "TXN_XMON01 not flagged as CROSS_MONTH"
        )

    def test_cross_month_suggested_action(self, exceptions):
        """Suggested action for cross-month must reference accrual."""
        cross = exceptions[
            (exceptions["root_cause"] == "CROSS_MONTH") &
            (exceptions["txn_id"] == "TXN_XMON01")
        ]
        assert len(cross) == 1
        action = cross.iloc[0]["suggested_action"].lower()
        assert "accrue" in action or "next month" in action or "jan" in action, (
            f"Expected accrual guidance, got: {action}"
        )


# ──────────────────────────────────────────────
# GAP 2: ROUNDING ERROR
# ──────────────────────────────────────────────

class TestGap2RoundingError:

    def test_rounding_error_detected(self, exceptions):
        """ROUNDING_ERROR root cause must appear in exceptions."""
        rnd = exceptions[exceptions["root_cause"] == "ROUNDING_ERROR"]
        assert len(rnd) >= 1, "ROUNDING_ERROR gap not detected"

    def test_rounding_gap_amount_correct(self, exceptions):
        """
        The rounding exception must involve the TXN_RND_BATCH
        and the gap must total $0.50.
        """
        rnd = exceptions[
            (exceptions["root_cause"] == "ROUNDING_ERROR") &
            (exceptions["txn_id"] == "TXN_RND_BATCH")
        ]
        assert len(rnd) >= 1, "TXN_RND_BATCH not flagged as ROUNDING_ERROR"
        gap = round(rnd.iloc[0]["gap_amount"], 2)
        assert gap == 0.50, f"Expected rounding gap of $0.50, got ${gap}"

    def test_rounding_suggested_action(self, exceptions):
        """Suggested action should mention investigation or dispute."""
        rnd = exceptions[exceptions["root_cause"] == "ROUNDING_ERROR"]
        action = rnd.iloc[0]["suggested_action"].lower()
        assert any(word in action for word in ["round", "discrepancy", "dispute", "batch"]), (
            f"Expected rounding guidance, got: {action}"
        )


# ──────────────────────────────────────────────
# GAP 3: DUPLICATE ENTRY
# ──────────────────────────────────────────────

class TestGap3Duplicate:

    def test_duplicate_detected(self, exceptions):
        """DUPLICATE root cause must appear in exceptions."""
        dup = exceptions[exceptions["root_cause"] == "DUPLICATE"]
        assert len(dup) >= 1, "DUPLICATE gap not detected"

    def test_duplicate_txn_id_correct(self, exceptions):
        """Flagged duplicate must be DUP123."""
        dup = exceptions[exceptions["root_cause"] == "DUPLICATE"]
        assert "DUP123" in dup["txn_id"].values, "DUP123 not in duplicate exceptions"

    def test_duplicate_source_is_internal(self, exceptions):
        """Duplicate exception must originate from the INTERNAL ledger."""
        dup = exceptions[
            (exceptions["root_cause"] == "DUPLICATE") &
            (exceptions["txn_id"] == "DUP123")
        ]
        assert all(dup["source"] == "INTERNAL"), (
            "Duplicate DUP123 should be flagged on the INTERNAL side"
        )

    def test_duplicate_suggested_action(self, exceptions):
        """Suggested action must reference duplicate review."""
        dup = exceptions[
            (exceptions["root_cause"] == "DUPLICATE") &
            (exceptions["txn_id"] == "DUP123")
        ]
        action = dup.iloc[0]["suggested_action"].lower()
        assert "duplicate" in action or "remove" in action, (
            f"Expected duplicate guidance, got: {action}"
        )


# ──────────────────────────────────────────────
# GAP 4: ORPHANED REFUND
# ──────────────────────────────────────────────

class TestGap4OrphanedRefund:

    def test_orphaned_refund_detected(self, exceptions):
        """ORPHANED_REFUND root cause must appear in exceptions."""
        ref = exceptions[exceptions["root_cause"] == "ORPHANED_REFUND"]
        assert len(ref) >= 1, "ORPHANED_REFUND gap not detected"

    def test_orphaned_refund_txn_id_correct(self, exceptions):
        """Flagged orphan refund must be REF456."""
        ref = exceptions[exceptions["root_cause"] == "ORPHANED_REFUND"]
        assert "REF456" in ref["txn_id"].values, "REF456 not in orphaned refund exceptions"

    def test_orphaned_refund_source_is_bank(self, exceptions):
        """Orphaned refund must originate from the BANK side."""
        ref = exceptions[
            (exceptions["root_cause"] == "ORPHANED_REFUND") &
            (exceptions["txn_id"] == "REF456")
        ]
        assert all(ref["source"] == "BANK"), (
            "REF456 orphaned refund should be flagged on the BANK side"
        )

    def test_orphaned_refund_amount(self, exceptions):
        """Gap amount for the orphaned refund must be $50.00."""
        ref = exceptions[
            (exceptions["root_cause"] == "ORPHANED_REFUND") &
            (exceptions["txn_id"] == "REF456")
        ]
        assert ref.iloc[0]["gap_amount"] == 50.00, (
            f"Expected gap of $50.00, got ${ref.iloc[0]['gap_amount']}"
        )

    def test_orphaned_refund_suggested_action(self, exceptions):
        """Suggested action must mention fraud or investigation."""
        ref = exceptions[
            (exceptions["root_cause"] == "ORPHANED_REFUND") &
            (exceptions["txn_id"] == "REF456")
        ]
        action = ref.iloc[0]["suggested_action"].lower()
        assert any(word in action for word in ["fraud", "investigate", "orphan", "data loss"]), (
            f"Expected fraud/investigate guidance, got: {action}"
        )


# ──────────────────────────────────────────────
# RECONCILIATION ENGINE INTEGRITY
# ──────────────────────────────────────────────

class TestReconEngineIntegrity:

    def test_all_four_gap_types_detected(self, exceptions):
        """All 4 distinct root causes must be present in exceptions."""
        required = {"CROSS_MONTH", "ROUNDING_ERROR", "DUPLICATE", "ORPHANED_REFUND"}
        found    = set(exceptions["root_cause"].unique())
        missing  = required - found
        assert not missing, f"Missing gap types: {missing}"

    def test_no_negative_gap_amounts(self, exceptions):
        """All gap amounts must be non-negative."""
        assert (exceptions["gap_amount"] >= 0).all(), (
            "Found negative gap_amount values — gaps should be absolute"
        )

    def test_accuracy_within_bounds(self, recon_result):
        """Accuracy % should be between 0 and 100."""
        acc = recon_result["accuracy_pct"]
        assert 0 <= acc <= 100, f"Accuracy out of bounds: {acc}"

    def test_accuracy_is_high_for_clean_data(self, recon_result):
        """Most transactions should match — accuracy > 80% expected."""
        assert recon_result["accuracy_pct"] > 80, (
            f"Accuracy too low: {recon_result['accuracy_pct']}% — engine may be broken"
        )

    def test_total_gap_is_positive(self, recon_result):
        """Total monetary gap must be > 0 given planted exceptions."""
        assert recon_result["exc_gap_total"] > 0, "Expected a non-zero gap given planted errors"

    def test_matched_records_have_no_gap(self, recon_result):
        """Matched records should not appear in exceptions."""
        if recon_result["matched"].empty:
            pytest.skip("No matched records to test")
        matched_ids = set(recon_result["matched"]["txn_id"])
        exc_ids     = set(recon_result["exceptions"]["txn_id"])
        # DUP123 may appear in both (one matched, one exception) — exclude it
        overlap = (matched_ids & exc_ids) - {"DUP123"}
        assert not overlap, f"Txn IDs appear in both matched and exceptions: {overlap}"

    def test_exceptions_have_suggested_actions(self, exceptions):
        """Every exception row must have a non-empty suggested_action."""
        blank = exceptions[
            exceptions["suggested_action"].isna() | (exceptions["suggested_action"] == "")
        ]
        assert len(blank) == 0, f"{len(blank)} exceptions missing suggested_action"

    def test_exceptions_source_is_valid(self, exceptions):
        """Source column must only contain INTERNAL or BANK."""
        valid = {"INTERNAL", "BANK"}
        invalid = set(exceptions["source"].unique()) - valid
        assert not invalid, f"Invalid source values: {invalid}"
