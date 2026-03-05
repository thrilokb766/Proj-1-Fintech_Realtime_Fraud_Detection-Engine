"""
SentinelStream - API Routes
All REST API endpoints for the fraud detection system
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models import TransactionRequest, TransactionResponse, TransactionRecord, StatsResponse
from fraud_engine import evaluate_transaction
from database import get_connection

router = APIRouter()


# ─────────────────────────────────────────────
# POST /transaction — Core Fraud Detection
# ─────────────────────────────────────────────

@router.post(
    "/transaction",
    response_model=TransactionResponse,
    summary="Submit a Transaction for Fraud Analysis",
    tags=["Transactions"]
)
def submit_transaction(payload: TransactionRequest):
    """
    Accepts a transaction and runs it through the SentinelStream fraud detection engine.

    - **user_id**: Unique identifier of the user making the transaction
    - **amount**: Transaction amount in INR
    - **description**: Optional description/purpose of the transaction
    - **ip_address**: Optional client IP for logging

    Returns a verdict: **Safe** or **Fraud**, along with risk level and score.
    """
    # Run fraud detection logic
    result = evaluate_transaction(
        user_id=payload.user_id,
        amount=payload.amount,
        description=payload.description,
        ip_address=payload.ip_address
    )

    # Persist to database
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO transactions
                (transaction_id, user_id, amount, currency, description, status,
                 risk_level, risk_score, flagged_reason, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["transaction_id"],
            payload.user_id,
            payload.amount,
            result["currency"],
            payload.description,
            result["status"],
            result["risk_level"],
            result["risk_score"],
            result["flagged_reason"],
            payload.ip_address
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

    return TransactionResponse(**result)


# ─────────────────────────────────────────────
# GET /transactions — List All Transactions
# ─────────────────────────────────────────────

@router.get(
    "/transactions",
    response_model=List[TransactionRecord],
    summary="Retrieve All Transaction Records",
    tags=["Transactions"]
)
def get_all_transactions(
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    status: Optional[str] = Query(None, description="Filter by 'Safe' or 'Fraud'"),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """Returns a list of all processed transactions, with optional filters."""
    conn = get_connection()
    try:
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ─────────────────────────────────────────────
# GET /transaction/{transaction_id} — Single Record
# ─────────────────────────────────────────────

@router.get(
    "/transaction/{transaction_id}",
    response_model=TransactionRecord,
    summary="Get a Specific Transaction by ID",
    tags=["Transactions"]
)
def get_transaction(transaction_id: str):
    """Fetch a single transaction record by its unique transaction ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?",
            (transaction_id,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
        return dict(row)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# GET /stats — Dashboard Summary Statistics
# ─────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get Transaction Statistics",
    tags=["Analytics"]
)
def get_stats():
    """Returns aggregated statistics for the SentinelStream dashboard."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        safe = conn.execute("SELECT COUNT(*) FROM transactions WHERE status='Safe'").fetchone()[0]
        fraud = conn.execute("SELECT COUNT(*) FROM transactions WHERE status='Fraud'").fetchone()[0]
        total_vol = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions").fetchone()[0]
        fraud_vol = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE status='Fraud'").fetchone()[0]

        return StatsResponse(
            total_transactions=total,
            safe_transactions=safe,
            fraud_transactions=fraud,
            total_volume=round(total_vol, 2),
            fraud_volume=round(fraud_vol, 2),
            fraud_rate=round((fraud / total * 100) if total > 0 else 0, 2)
        )
    finally:
        conn.close()


# ─────────────────────────────────────────────
# DELETE /transactions/clear — Clear All Records
# ─────────────────────────────────────────────

@router.delete(
    "/transactions/clear",
    summary="Clear All Transaction Records",
    tags=["Admin"]
)
def clear_transactions():
    """Deletes all transaction records from the database (admin use only)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM transactions")
        conn.commit()
        return {"message": "All transaction records cleared successfully."}
    finally:
        conn.close()
