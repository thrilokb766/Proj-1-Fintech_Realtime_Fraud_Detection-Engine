"""
SentinelStream - Rule-Based Fraud Detection Engine
Core logic for evaluating transactions against predefined fraud rules
"""

import uuid
from datetime import datetime
from typing import Tuple


# ─────────────────────────────────────────────
# THRESHOLDS & RULES CONFIGURATION
# ─────────────────────────────────────────────

RULES = {
    "HIGH_AMOUNT_THRESHOLD":    5000.0,    # ₹5,000 — primary rule (as per spec)
    "CRITICAL_AMOUNT_THRESHOLD": 50000.0,   # ₹50,000 — critical risk
    "MEDIUM_AMOUNT_THRESHOLD":  2000.0,    # ₹2,000 — medium risk watch
}

SUSPICIOUS_KEYWORDS = [
    "casino", "gambling", "bet", "lottery", "offshore",
    "crypto transfer", "anonymous", "darkweb"
]


# ─────────────────────────────────────────────
# RULE ENGINE
# ─────────────────────────────────────────────

def evaluate_transaction(user_id: str, amount: float, description: str = None, ip_address: str = None) -> dict:
    """
    Apply rule-based fraud detection logic to a transaction.

    Rules Applied:
      1. Amount > ₹50,000      → CRITICAL risk → Fraud
      2. Amount > ₹5,000       → HIGH risk     → Fraud
      3. Amount > ₹2,000       → MEDIUM risk   → Safe (with warning)
      4. Suspicious description → Flagged       → Fraud
      5. Otherwise             → LOW risk       → Safe

    Returns a dict with status, risk_level, risk_score, and reason.
    """

    risk_score = 0.0
    flags = []

    # ── Rule 1: Critical amount threshold ─────────────────────────────────
    if amount > RULES["CRITICAL_AMOUNT_THRESHOLD"]:
        risk_score += 80.0
        flags.append(f"Transaction amount ₹{amount:,.2f} exceeds critical threshold of ₹{RULES['CRITICAL_AMOUNT_THRESHOLD']:,.0f}")

    # ── Rule 2: High amount threshold (core rule per spec) ─────────────────
    elif amount > RULES["HIGH_AMOUNT_THRESHOLD"]:
        risk_score += 55.0
        flags.append(f"Transaction amount ₹{amount:,.2f} exceeds safe threshold of ₹{RULES['HIGH_AMOUNT_THRESHOLD']:,.0f}")

    # ── Rule 3: Medium amount watch ────────────────────────────────────────
    elif amount > RULES["MEDIUM_AMOUNT_THRESHOLD"]:
        risk_score += 20.0
        flags.append(f"Moderate transaction amount ₹{amount:,.2f} — within watch zone")

    # ── Rule 4: Suspicious keywords in description ─────────────────────────
    if description:
        desc_lower = description.lower()
        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword in desc_lower:
                risk_score += 40.0
                flags.append(f"Suspicious keyword detected in description: '{keyword}'")
                break

    # ── Rule 5: Round-number suspicion heuristic ───────────────────────────
    if amount % 1000 == 0 and amount >= 5000:
        risk_score += 5.0
        flags.append("Round number large transaction — common in structuring attempts")

    # Cap risk score at 100
    risk_score = min(risk_score, 100.0)

    # ── Determine Risk Level & Status ──────────────────────────────────────
    if risk_score >= 75:
        risk_level = "Critical"
        status = "Fraud"
        message = "🚨 Transaction BLOCKED. Critical fraud risk detected."
    elif risk_score >= 50:
        risk_level = "High"
        status = "Fraud"
        message = "⚠️ Transaction FLAGGED. High fraud risk — amount exceeds ₹5,000 threshold."
    elif risk_score >= 20:
        risk_level = "Medium"
        status = "Safe"
        message = "🟡 Transaction ALLOWED with caution. Medium risk level detected."
    else:
        risk_level = "Low"
        status = "Safe"
        message = "✅ Transaction APPROVED. No suspicious activity detected."

    return {
        "transaction_id": f"TXN-{uuid.uuid4().hex[:10].upper()}",
        "user_id": user_id,
        "amount": amount,
        "currency": "INR",
        "status": status,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 2),
        "flagged_reason": " | ".join(flags) if flags else None,
        "message": message,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
# Week 3: Fraud logic enhancement
