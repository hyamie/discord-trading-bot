"""
Pydantic Models for Trading Bot API
Request and response schemas for FastAPI endpoints
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TradeType(str, Enum):
    """Trade type enumeration"""
    DAY = "day"
    SWING = "swing"
    BOTH = "both"


class Direction(str, Enum):
    """Trade direction enumeration"""
    LONG = "long"
    SHORT = "short"


class AnalysisRequest(BaseModel):
    """Request model for /analyze endpoint"""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, TSLA)")
    trade_type: TradeType = Field(
        default=TradeType.BOTH,
        description="Type of trade analysis: 'day', 'swing', or 'both'"
    )

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker symbol format"""
        v = v.strip().upper()
        if not v.isalpha() or len(v) > 5:
            raise ValueError("Ticker must be 1-5 alphabetic characters")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "trade_type": "both"
                },
                {
                    "ticker": "TSLA",
                    "trade_type": "day"
                }
            ]
        }
    }


class EdgeInfo(BaseModel):
    """Information about an applied edge filter"""
    name: str = Field(..., description="Edge filter name")
    applied: bool = Field(..., description="Whether this edge was triggered")
    value: Optional[float] = Field(None, description="Numeric value if applicable")
    description: Optional[str] = Field(None, description="What this edge means")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Slope Filter",
                    "applied": True,
                    "value": 0.15,
                    "description": "EMA20 rising 0.15% over 5 bars"
                },
                {
                    "name": "Volume Confirmation",
                    "applied": True,
                    "value": 1.8,
                    "description": "Volume 1.8x above average"
                }
            ]
        }
    }


class TimeframeSignals(BaseModel):
    """Signals for a specific timeframe"""
    timeframe: str = Field(..., description="Timeframe (e.g., 1h, 15m, 5m)")
    trend_bias: str = Field(..., description="Bullish, bearish, or neutral")
    momentum_bias: str = Field(..., description="Bullish, bearish, or neutral")
    entry_trigger: bool = Field(..., description="Whether entry trigger fired")
    ema20: float = Field(..., description="Current EMA20 value")
    ema50: float = Field(..., description="Current EMA50 value")
    rsi: float = Field(..., description="Current RSI value")
    atr: float = Field(..., description="Current ATR value")
    vwap: Optional[float] = Field(None, description="VWAP (intraday only)")


class TradeAnalysis(BaseModel):
    """Complete trade analysis result"""
    trade_id: str = Field(..., description="Unique trade identifier (e.g., AAPL-20251112-001)")
    ticker: str = Field(..., description="Stock ticker symbol")
    trade_type: TradeType = Field(..., description="Day or swing trade")
    direction: Direction = Field(..., description="Long or short")

    # Entry/Exit Levels
    entry: float = Field(..., description="Recommended entry price", gt=0)
    stop: float = Field(..., description="Stop loss price", gt=0)
    target: float = Field(..., description="Take profit target", gt=0)
    target2: Optional[float] = Field(None, description="Secondary target (optional)", gt=0)

    # Risk/Reward
    risk_reward_ratio: float = Field(..., description="R:R ratio (e.g., 2.0 = 1:2)")
    risk_pct: float = Field(..., description="Risk as percentage from entry")
    reward_pct: float = Field(..., description="Reward as percentage from entry")

    # Confidence & Edges
    confidence: int = Field(..., description="Confidence score 0-5", ge=0, le=5)
    edges: List[EdgeInfo] = Field(..., description="Applied edge filters")
    edges_count: int = Field(..., description="Number of edges triggered")

    # Analysis Details
    rationale: str = Field(..., description="2-3 sentence trade rationale")
    timeframe_signals: Dict[str, TimeframeSignals] = Field(
        ...,
        description="Signals for each timeframe (higher, middle, lower)"
    )

    # Market Context
    spy_bias: Optional[str] = Field(None, description="SPY market bias")
    atr_value: float = Field(..., description="ATR value used for stops")
    market_volatility: str = Field(..., description="Low, normal, or high")

    # Metadata
    analysis_timestamp: datetime = Field(..., description="When analysis was performed")
    news_summary: Optional[str] = Field(None, description="News impact summary")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "trade_id": "AAPL-20251112-001",
                    "ticker": "AAPL",
                    "trade_type": "day",
                    "direction": "long",
                    "entry": 175.50,
                    "stop": 174.25,
                    "target": 178.00,
                    "risk_reward_ratio": 2.0,
                    "risk_pct": -0.7,
                    "reward_pct": 1.4,
                    "confidence": 4,
                    "edges": [
                        {
                            "name": "Slope Filter",
                            "applied": True,
                            "value": 0.15
                        },
                        {
                            "name": "Volume Confirmation",
                            "applied": True,
                            "value": 1.8
                        }
                    ],
                    "edges_count": 2,
                    "rationale": "Strong bullish momentum on 1h timeframe with pullback to EMA20 support on 15m. Volume confirms breakout on 5m entry trigger.",
                    "timeframe_signals": {},
                    "atr_value": 1.25,
                    "market_volatility": "normal",
                    "analysis_timestamp": "2025-11-12T10:30:00Z"
                }
            ]
        }
    }


class AnalysisResponse(BaseModel):
    """Response model for /analyze endpoint"""
    ticker: str = Field(..., description="Stock ticker analyzed")
    trade_type_requested: TradeType = Field(..., description="Type of analysis requested")
    plans: List[TradeAnalysis] = Field(..., description="List of trade plans (1-2 depending on request)")
    total_plans: int = Field(..., description="Number of plans generated")
    highest_confidence: int = Field(..., description="Highest confidence score among plans")
    analysis_timestamp: datetime = Field(..., description="When analysis was performed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "AAPL",
                    "trade_type_requested": "both",
                    "plans": [
                        {
                            "trade_id": "AAPL-20251112-001",
                            "ticker": "AAPL",
                            "trade_type": "swing",
                            "direction": "long",
                            "entry": 174.80,
                            "stop": 171.50,
                            "target": 181.40,
                            "risk_reward_ratio": 2.0,
                            "risk_pct": -1.9,
                            "reward_pct": 3.8,
                            "confidence": 5,
                            "edges_count": 4,
                            "rationale": "Weekly uptrend intact with daily pullback setup. 4h shows early reversal signals.",
                            "atr_value": 3.30,
                            "market_volatility": "normal",
                            "analysis_timestamp": "2025-11-12T10:30:00Z"
                        },
                        {
                            "trade_id": "AAPL-20251112-002",
                            "ticker": "AAPL",
                            "trade_type": "day",
                            "direction": "long",
                            "entry": 175.50,
                            "stop": 174.25,
                            "target": 178.00,
                            "risk_reward_ratio": 2.0,
                            "risk_pct": -0.7,
                            "reward_pct": 1.4,
                            "confidence": 4,
                            "edges_count": 3,
                            "rationale": "Strong 1h momentum with 15m pullback confirmation. 5m breakout trigger fired.",
                            "atr_value": 1.25,
                            "market_volatility": "normal",
                            "analysis_timestamp": "2025-11-12T10:30:00Z"
                        }
                    ],
                    "total_plans": 2,
                    "highest_confidence": 5,
                    "analysis_timestamp": "2025-11-12T10:30:00Z"
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server time")
    version: str = Field(..., description="API version")
    services: Dict[str, bool] = Field(..., description="Status of dependent services")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "healthy",
                    "timestamp": "2025-11-12T10:30:00Z",
                    "version": "1.0.0",
                    "services": {
                        "schwab_api": True,
                        "news_api": True,
                        "database": True,
                        "llm": True
                    }
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="When error occurred")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "ValidationError",
                    "message": "Invalid ticker symbol: 'TOOLONG'",
                    "details": {
                        "field": "ticker",
                        "constraint": "max_length"
                    },
                    "timestamp": "2025-11-12T10:30:00Z"
                }
            ]
        }
    }
