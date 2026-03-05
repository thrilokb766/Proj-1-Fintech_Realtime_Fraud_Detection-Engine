"""
SentinelStream - Pydantic Data Models
Input validation and response schemas for the fraud detection API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class TransactionRequest(BaseModel):
    """Incoming transaction payload from the client."""

    user_id: str = Field(..., min_length=3, max_length=50, description="Unique user identifier")
    amount: float = Field(..., gt=0, description="Transaction amount in INR (must be > 0)")
    description: Optional[str] = Field(None, max_length=200, description="Purpose of transaction")
    ip_address: Optional[str] = Field(None, description="Client IP address")

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Transaction amount must be greater than zero.")
        return round(v, 2)

    @validator("user_id")
    def user_id_no_spaces(cls, v):
        if " " in v.strip():
            raise ValueError("user_id must not contain spaces.")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "user_id": "USR_10042",
                "amount": 7500.00,
                "description": "Online purchase - Electronics",
                "ip_address": "192.168.1.10"
            }
        }


# ─────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────

class TransactionResponse(BaseModel):
    """Response returned after evaluating a transaction."""

    transaction_id: str
    user_id: str
    amount: float
    currency: str = "INR"
    status: str                  # "Safe" or "Fraud"
    risk_level: str              # "Low", "Medium", "High", "Critical"
    risk_score: float            # 0.0 – 100.0
    flagged_reason: Optional[str]
    message: str
    timestamp: str


class TransactionRecord(BaseModel):
    """Full transaction record returned from the database."""

    id: int
    transaction_id: str
    user_id: str
    amount: float
    currency: str
    description: Optional[str]
    status: str
    risk_level: str
    risk_score: float
    flagged_reason: Optional[str]
    ip_address: Optional[str]
    timestamp: str


class StatsResponse(BaseModel):
    """Dashboard statistics summary."""

    total_transactions: int
    safe_transactions: int
    fraud_transactions: int
    total_volume: float
    fraud_volume: float
    fraud_rate: float
