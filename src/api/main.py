"""
FastAPI Trading Bot Microservice
Main API application for 3-Tier MTF trading analysis
"""

import os
from datetime import datetime
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from dotenv import load_dotenv

from src.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    TradeAnalysis,
    HealthResponse,
    ErrorResponse,
    EdgeInfo,
    TradeType,
    Direction
)
from src.agents.analysis_engine import AnalysisEngine
from src.utils.schwab_api import SchwabAPIClient, AlphaVantageClient
from src.utils.news_api import NewsAggregator
from src.utils.yfinance_client import YFinanceClient
from src.database.db_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize logger
logger.add(
    "logs/api_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)

# Global instances (initialized on startup)
analysis_engine: AnalysisEngine = None
schwab_client: SchwabAPIClient = None
alpha_vantage_client: AlphaVantageClient = None
yfinance_client: YFinanceClient = None
news_aggregator: NewsAggregator = None
db_manager: DatabaseManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global analysis_engine, schwab_client, alpha_vantage_client, yfinance_client, news_aggregator, db_manager

    # Startup
    logger.info("Starting Trading Bot API...")

    try:
        # Initialize database
        db_manager = DatabaseManager(os.getenv('DATABASE_PATH', 'data/trading_bot.db'))
        # Database auto-initializes in __init__
        logger.info(" Database initialized")

        # Initialize analysis engine
        analysis_engine = AnalysisEngine()
        logger.info(" Analysis engine initialized")

        # Initialize Schwab API client
        schwab_api_key = os.getenv('SCHWAB_API_KEY')
        schwab_api_secret = os.getenv('SCHWAB_API_SECRET')
        schwab_redirect_uri = os.getenv('SCHWAB_REDIRECT_URI')

        if schwab_api_key and schwab_api_secret:
            schwab_client = SchwabAPIClient(
                api_key=schwab_api_key,
                api_secret=schwab_api_secret,
                redirect_uri=schwab_redirect_uri
            )
            logger.info("Schwab API client initialized")

            # Authenticate with refresh token
            schwab_refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')
            if schwab_refresh_token:
                schwab_client.refresh_token = schwab_refresh_token
                if schwab_client.authenticate():
                    logger.info("Schwab API authenticated successfully")
                else:
                    logger.warning("Schwab authentication failed, will use fallback")
                    schwab_client = None
            else:
                logger.warning("No Schwab refresh token found, will use fallback")
                schwab_client = None
        else:
            logger.warning("Schwab API credentials not found, using fallback")
            schwab_client = None

        # Initialize Alpha Vantage fallback
        alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if alpha_vantage_key:
            alpha_vantage_client = AlphaVantageClient(api_key=alpha_vantage_key)
            logger.info(" Alpha Vantage fallback initialized")

# Initialize YFinance fallback (always available, free)
        yfinance_client = YFinanceClient()
        logger.info("✅ YFinance fallback initialized")
        # Initialize news aggregator
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        newsapi_key = os.getenv('NEWSAPI_KEY')

        if finnhub_key or newsapi_key:
            news_aggregator = NewsAggregator(
                finnhub_key=finnhub_key,
                newsapi_key=newsapi_key
            )
            logger.info(" News aggregator initialized")
        else:
            logger.warning("  News API keys not found, news features disabled")

        logger.info("= Trading Bot API ready!")

    except Exception as e:
        logger.error(f"L Startup failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Trading Bot API...")


# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="3-Tier Multi-Timeframe trading analysis microservice",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your n8n Cloud URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message=str(exc),
            timestamp=datetime.now()
        ).model_dump()
    )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/debug/yfinance/{ticker}", tags=["Debug"])
async def debug_yfinance(ticker: str):
    """Debug endpoint to test yfinance data fetching"""
    if not yfinance_client:
        return {"error": "YFinance client not initialized"}

    try:
        # Test raw yfinance import
        import yfinance as yf
        stock = yf.Ticker(ticker)
        raw_data = stock.history(period="1d", interval="1h")

        # Test individual calls
        test_1h = yfinance_client.get_price_history(ticker, period="1mo", interval="1h")
        test_15m = yfinance_client.get_price_history(ticker, period="5d", interval="15m")
        test_5m = yfinance_client.get_price_history(ticker, period="1d", interval="5m")

        # Get full day data
        day_data = yfinance_client.get_day_trade_data(ticker)

        result = {
            "ticker": ticker,
            "yfinance_client_exists": yfinance_client is not None,
            "raw_yfinance_test": {
                "bars": len(raw_data) if not raw_data.empty else 0,
                "columns": list(raw_data.columns) if not raw_data.empty else [],
                "empty": raw_data.empty
            },
            "individual_tests": {
                "1h": test_1h is not None and len(test_1h) if test_1h is not None else "None",
                "15m": test_15m is not None and len(test_15m) if test_15m is not None else "None",
                "5m": test_5m is not None and len(test_5m) if test_5m is not None else "None"
            },
            "day_data": {
                "timeframes": len(day_data) if day_data else 0,
                "keys": list(day_data.keys()) if day_data else [],
                "details": {}
            }
        }

        if day_data:
            for key, df in day_data.items():
                if df is not None and hasattr(df, '__len__'):
                    result["day_data"]["details"][key] = {
                        "bars": len(df),
                        "columns": list(df.columns),
                        "latest_close": float(df['close'].iloc[-1]) if 'close' in df.columns else None
                    }
                else:
                    result["day_data"]["details"][key] = "None or invalid"

        return result
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns status of API and dependent services
    """
    services_status = {
        "schwab_api": schwab_client is not None,
        "news_api": news_aggregator is not None,
        "database": db_manager is not None,
        "llm": bool(os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY'))
    }

    return HealthResponse(
        status="healthy" if all(services_status.values()) else "degraded",
        timestamp=datetime.now(),
        version="1.0.0",
        services=services_status
    )


@app.post("/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_ticker(request: AnalysisRequest):
    """
    Analyze a ticker for trading opportunities

    This endpoint performs 3-Tier Multi-Timeframe analysis and returns
    trade ideas with confidence scores, entry/stop/target levels, and rationale.

    **Timeframes:**
    - Day Trade: 1h (trend), 15m (setup), 5m (entry)
    - Swing Trade: Weekly (trend), Daily (setup), 4h (entry)

    **Confidence Scoring (0-5):**
    - 0: No alignment
    - 1: Basic trend bias
    - 2: Trend + momentum aligned
    - 3: Entry trigger fired
    - 4: 1-2 edge filters applied
    - 5: All edges + positive news

    **Edge Filters:**
    - Slope Filter (EMA20 strength)
    - Volume Confirmation (1.5x avg)
    - Pullback Confirmation (VWAP + RSI)
    - Volatility Filter (candle range vs ATR)
    - Divergence Detection

    Args:
        request: AnalysisRequest with ticker and trade_type

    Returns:
        AnalysisResponse with trade plan(s)

    Raises:
        HTTPException: If analysis fails or data unavailable
    """
    logger.info(f"= Analyzing {request.ticker} ({request.trade_type})")

    try:
        # 1. Check cache first
        cache_key = f"analysis:{request.ticker}:{request.trade_type}"
        cached_result = db_manager.get_cached_data(cache_key)

        if cached_result:
            logger.info(f"= Returning cached result for {request.ticker}")
            return AnalysisResponse(**cached_result)

        # 2. Fetch price data
        price_data = await fetch_price_data(request.ticker, request.trade_type)

        if not price_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to fetch price data for {request.ticker}"
            )

        # 3. Fetch news data (optional, continue if fails)
        news_summary = {}
        if news_aggregator:
            try:
                news_summary = news_aggregator.aggregate_news(request.ticker, max_articles=5)
            except Exception as e:
                logger.warning(f"News fetch failed: {str(e)}")

        # 4. Run analysis
        analysis_result = analysis_engine.analyze_ticker(
            ticker=request.ticker,
            price_data=price_data,
            news_summary=news_summary,
            trade_type=request.trade_type.value
        )

        # 5. Convert to API models
        trade_plans = []
        for plan in analysis_result['plans']:
            trade_plans.append(convert_to_trade_analysis(plan))

        # 6. Build response
        response = AnalysisResponse(
            ticker=request.ticker,
            trade_type_requested=request.trade_type,
            plans=trade_plans,
            total_plans=len(trade_plans),
            highest_confidence=max([p.confidence for p in trade_plans]) if trade_plans else 0,
            analysis_timestamp=datetime.now()
        )

        # 7. Cache result (60 seconds TTL)
        db_manager.set_cached_data(
            cache_key=cache_key,
            ticker=request.ticker,
            timeframe="both",
            data=response.model_dump(mode='json'),
            ttl_seconds=60
        )

        # 8. Log API call
        db_manager.log_api_call({
            'api_name': 'trading_api',
            'endpoint': '/analyze',
            'ticker': request.ticker,
            'status_code': 200,
            'success': True
        })

        logger.info(f" Analysis complete: {len(trade_plans)} plans, confidence {response.highest_confidence}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"L Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


async def fetch_price_data(ticker: str, trade_type: TradeType) -> Dict:
    """
    Fetch price data for analysis

    Args:
        ticker: Stock ticker symbol
        trade_type: Type of trade (day, swing, both)

    Returns:
        Dictionary with timeframe DataFrames
    """
    price_data = {}

    try:
        # Determine timeframes based on trade type
        if trade_type in [TradeType.DAY, TradeType.BOTH]:
            # Use datetime ranges for Schwab API (more reliable than period/frequency)
            from datetime import datetime, timedelta
            now = datetime.now()

            day_configs = [
                {'name': 'higher', 'frequency_type': 'minute', 'frequency': 30, 'start_datetime': now - timedelta(days=5)},   # 30m bars (closest to 1h), 5 days
                {'name': 'middle', 'frequency_type': 'minute', 'frequency': 15, 'start_datetime': now - timedelta(days=3)},   # 15m bars, 3 days
                {'name': 'lower', 'frequency_type': 'minute', 'frequency': 5, 'start_datetime': now - timedelta(days=1)},     # 5m bars, 1 day
            ]

            # Try Schwab first, then fallback to yfinance
            day_data = None
            if schwab_client:
                try:
                    day_data = schwab_client.get_multiple_timeframes(ticker, day_configs)
                    if day_data:
                        price_data.update(day_data)
                except Exception as e:
                    logger.warning(f"Schwab day data fetch failed: {str(e)}")

            # Fallback to yfinance if Schwab didn't work
            if not day_data and yfinance_client:
                logger.info(f"Using YFinance for {ticker} day trade data")
                day_data = yfinance_client.get_day_trade_data(ticker)
                if day_data:
                    price_data.update(day_data)

        if trade_type in [TradeType.SWING, TradeType.BOTH]:
            from datetime import datetime, timedelta
            now = datetime.now()

            swing_configs = [
                {'name': 'higher', 'frequency_type': 'weekly', 'frequency': 1, 'start_datetime': now - timedelta(days=180)},  # Weekly bars, 6 months
                {'name': 'middle', 'frequency_type': 'daily', 'frequency': 1, 'start_datetime': now - timedelta(days=90)},    # Daily bars, 3 months
                {'name': 'lower', 'frequency_type': 'minute', 'frequency': 30, 'start_datetime': now - timedelta(days=7)},    # 30m bars (best available), 1 week
            ]

            # Try Schwab first, then fallback to yfinance
            swing_data = None
            if schwab_client:
                try:
                    swing_data = schwab_client.get_multiple_timeframes(ticker, swing_configs)
                    if swing_data:
                        price_data.update(swing_data)
                except Exception as e:
                    logger.warning(f"Schwab swing data fetch failed: {str(e)}")

            # Fallback to yfinance if Schwab didn't work
            if not swing_data and yfinance_client:
                logger.info(f"Using YFinance for {ticker} swing trade data")
                swing_data = yfinance_client.get_swing_trade_data(ticker)
                if swing_data:
                    price_data.update(swing_data)

        # Fetch SPY for market bias
        if schwab_client:
            spy_data = schwab_client.get_price_history('SPY', 'day', 'minute', 60, 1)
            price_data['spy'] = spy_data
        elif yfinance_client:
            spy_data = yfinance_client.get_price_history('SPY', period='5d', interval='1h')
            if spy_data is not None:
                price_data['spy'] = spy_data

        return price_data

    except Exception as e:
        logger.error(f"Price data fetch failed: {str(e)}")
        return None


def convert_to_trade_analysis(plan: Dict) -> TradeAnalysis:
    """
    Convert analysis engine output to TradeAnalysis model

    Args:
        plan: Raw trade plan dictionary

    Returns:
        TradeAnalysis Pydantic model
    """
    return TradeAnalysis(
        trade_id=plan['trade_id'],
        ticker=plan['ticker'],
        trade_type=TradeType(plan['trade_type']),
        direction=Direction(plan['direction']),
        entry=plan['entry'],
        stop=plan['stop'],
        target=plan['target'],
        target2=plan.get('target2'),
        risk_reward_ratio=plan['risk_reward_ratio'],
        risk_pct=plan['risk_pct'],
        reward_pct=plan['reward_pct'],
        confidence=plan['confidence'],
        edges=[
            EdgeInfo(
                name=edge['name'],
                applied=edge['applied'],
                value=edge.get('value'),
                description=edge.get('description')
            )
            for edge in plan.get('edges_applied', [])
        ],
        edges_count=len([e for e in plan.get('edges_applied', []) if e.get('applied')]),
        rationale=plan['rationale'],
        timeframe_signals=plan.get('timeframe_signals', {}),
        spy_bias=plan.get('spy_bias'),
        atr_value=plan['atr_value'],
        market_volatility=plan['market_volatility'],
        analysis_timestamp=datetime.now(),
        news_summary=plan.get('news_summary')
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        reload=True,
        log_level="info"
    )
