from typing import Any, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

class VerifyRequest(BaseModel):
    session_id: str
    message_id: str
    ai_response: str


class ClaimResult(BaseModel):
    id: str
    text: str
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_snippet: Optional[str] = None


class VerifyResponse(BaseModel):
    claims: list[ClaimResult]


# ---------------------------------------------------------------------------
# Predict
# ---------------------------------------------------------------------------

class PredictionItem(BaseModel):
    claim_id: str
    predicted_inaccurate: bool
    prediction_label: Optional[str] = None  # 'accurate' | 'neutral' | 'false'
    reasoning: Optional[str] = None


class PredictRequest(BaseModel):
    session_id: str
    message_id: str
    predictions: list[PredictionItem]
    timestamp: Optional[str] = None


class PredictResponse(BaseModel):
    success: bool
    prediction_id: str


# ---------------------------------------------------------------------------
# Reveal
# ---------------------------------------------------------------------------

class RevealRequest(BaseModel):
    session_id: str
    message_id: str
    prediction_id: str


class VerdictResult(BaseModel):
    claim_id: str
    claim_text: str
    verdict: str
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    sources: list[dict[str, Any]] = []
    student_predicted_inaccurate: bool


class AccuracyMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    correct_predictions: int
    total_flagged_by_student: int
    total_unsupported_by_system: int


class RevealResponse(BaseModel):
    verdicts: list[VerdictResult]
    accuracy: AccuracyMetrics


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class LogRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: dict[str, Any] = {}
    timestamp: Optional[str] = None


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class SessionCreateRequest(BaseModel):
    participant_id: str


class SessionCreateResponse(BaseModel):
    session_id: str
