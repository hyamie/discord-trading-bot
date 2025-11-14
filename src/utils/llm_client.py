"""
LLM Client for Trade Rationale Generation
Supports both Anthropic Claude and OpenAI GPT
"""

import os
from typing import Dict, Optional, List
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic library not installed")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed")


class LLMClient:
    """
    LLM client for generating trade rationales and weekly analysis
    Automatically uses available provider (Anthropic preferred, OpenAI fallback)
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 200
    ):
        """
        Initialize LLM client

        Args:
            anthropic_api_key: Anthropic API key (or set ANTHROPIC_API_KEY env)
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env)
            model: Model to use (auto-detected if not provided)
            temperature: LLM temperature (0-1, lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Determine which provider to use
        self.anthropic_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        if self.anthropic_key and ANTHROPIC_AVAILABLE:
            self.provider = 'anthropic'
            self.client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.model = model or os.getenv('LLM_MODEL', 'claude-3-5-sonnet-20241022')
            logger.info(f" LLM client initialized: Anthropic Claude ({self.model})")

        elif self.openai_key and OPENAI_AVAILABLE:
            self.provider = 'openai'
            self.client = openai.OpenAI(api_key=self.openai_key)
            self.model = model or os.getenv('LLM_MODEL', 'gpt-4o')
            logger.info(f" LLM client initialized: OpenAI GPT ({self.model})")

        else:
            self.provider = None
            self.client = None
            self.model = None
            logger.warning("�  No LLM provider available - rationale will be template-based")

    def generate_trade_rationale(
        self,
        ticker: str,
        trade_type: str,
        direction: str,
        signals: Dict,
        edges: List[Dict],
        news_summary: Optional[Dict] = None
    ) -> str:
        """
        Generate 2-3 sentence trade rationale using LLM

        Args:
            ticker: Stock ticker
            trade_type: 'day' or 'swing'
            direction: 'long' or 'short'
            signals: Dictionary with timeframe signals
            edges: List of applied edges
            news_summary: Optional news data

        Returns:
            2-3 sentence rationale explaining the trade
        """
        if not self.client:
            # Fallback to template-based rationale
            return self._generate_template_rationale(ticker, trade_type, direction, signals, edges)

        try:
            prompt = self._build_rationale_prompt(ticker, trade_type, direction, signals, edges, news_summary)

            if self.provider == 'anthropic':
                return self._call_anthropic(prompt)
            elif self.provider == 'openai':
                return self._call_openai(prompt)

        except Exception as e:
            logger.error(f"LLM rationale generation failed: {str(e)}")
            return self._generate_template_rationale(ticker, trade_type, direction, signals, edges)

    def generate_weekly_analysis(
        self,
        metrics: Dict,
        trades: List[Dict],
        edge_performance: Dict
    ) -> str:
        """
        Generate weekly performance analysis and suggestions

        Args:
            metrics: Overall metrics (win_rate, avg_r_multiple, etc.)
            trades: List of closed trades from the week
            edge_performance: Performance breakdown by edge filter

        Returns:
            Analysis text with pattern identification and suggestions
        """
        if not self.client:
            return self._generate_template_analysis(metrics, edge_performance)

        try:
            prompt = self._build_weekly_analysis_prompt(metrics, trades, edge_performance)

            if self.provider == 'anthropic':
                return self._call_anthropic(prompt, max_tokens=500)
            elif self.provider == 'openai':
                return self._call_openai(prompt, max_tokens=500)

        except Exception as e:
            logger.error(f"LLM weekly analysis failed: {str(e)}")
            return self._generate_template_analysis(metrics, edge_performance)

    def _call_anthropic(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Call Anthropic Claude API"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text.strip()

    def _call_openai(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Call OpenAI GPT API"""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": "You are a professional trading analyst. Provide concise, actionable trade rationales."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    def _build_rationale_prompt(
        self,
        ticker: str,
        trade_type: str,
        direction: str,
        signals: Dict,
        edges: List[Dict],
        news_summary: Optional[Dict]
    ) -> str:
        """Build prompt for trade rationale generation"""

        # Extract key signals
        higher_tf = signals.get('higher', {})
        middle_tf = signals.get('middle', {})
        lower_tf = signals.get('lower', {})

        # Build edges list
        applied_edges = [e['name'] for e in edges if e.get('applied')]
        edges_text = ', '.join(applied_edges) if applied_edges else 'None'

        # Build news context
        news_text = ""
        if news_summary and news_summary.get('articles'):
            top_headline = news_summary['articles'][0].get('headline', '')
            sentiment = news_summary.get('overall_sentiment', 'neutral')
            news_text = f"\n\nRecent News: {top_headline} (Sentiment: {sentiment})"

        prompt = f"""Generate a concise 2-3 sentence trade rationale for this setup:

**Ticker**: {ticker}
**Trade Type**: {trade_type.capitalize()} Trade
**Direction**: {direction.upper()}

**Technical Setup**:
- Higher TF Trend: {higher_tf.get('trend_bias', 'N/A')} (EMA20: {higher_tf.get('ema20', 'N/A')}, EMA50: {higher_tf.get('ema50', 'N/A')})
- Middle TF Momentum: {middle_tf.get('momentum_bias', 'N/A')} (RSI: {middle_tf.get('rsi', 'N/A')})
- Lower TF Entry: {'Triggered' if lower_tf.get('entry_trigger') else 'Not triggered'}
- Applied Edges: {edges_text}{news_text}

Write 2-3 sentences explaining:
1. What timeframe alignment supports this trade
2. Which edge(s) provide additional confirmation
3. Any risks or considerations

Be direct and specific. No disclaimers or fluff."""

        return prompt

    def _build_weekly_analysis_prompt(
        self,
        metrics: Dict,
        trades: List[Dict],
        edge_performance: Dict
    ) -> str:
        """Build prompt for weekly analysis"""

        # Format edge performance
        edge_text = "\n".join([
            f"- {edge}: {data['win_rate']:.1%} win rate ({data['wins']}/{data['total']} trades)"
            for edge, data in edge_performance.items()
        ])

        prompt = f"""Analyze this week's trading performance and suggest improvements:

**Overall Metrics**:
- Total Trades: {metrics['total_trades']}
- Win Rate: {metrics['win_rate']:.1%}
- Avg R-Multiple: {metrics['avg_r_multiple']:.2f}R
- Best Day: {metrics.get('best_day', 'N/A')}
- Worst Day: {metrics.get('worst_day', 'N/A')}

**Edge Filter Performance**:
{edge_text}

**Sample Trades** (showing variety):
{self._format_sample_trades(trades[:5])}

Provide:
1. **Pattern Identification**: What worked well? What didn't?
2. **Edge Analysis**: Which edges should be prioritized or disabled?
3. **Parameter Suggestions**: Specific threshold changes (e.g., "Increase volume threshold from 1.5x to 1.8x")
4. **Market Context**: Any broader market conditions affecting results?

Be specific and actionable. Suggest 2-3 concrete parameter changes."""

        return prompt

    def _format_sample_trades(self, trades: List[Dict]) -> str:
        """Format sample trades for LLM analysis"""
        if not trades:
            return "No trades to analyze"

        formatted = []
        for trade in trades:
            outcome = "WIN" if trade.get('actual_outcome') == 'win' else "LOSS"
            pl = trade.get('profit_loss_r', 0)
            edges = ', '.join([e['name'] for e in trade.get('edges_applied', []) if e.get('applied')])

            formatted.append(
                f"  {trade['ticker']} {trade['direction'].upper()} - {outcome} ({pl:+.2f}R) | Edges: {edges or 'None'}"
            )

        return "\n".join(formatted)

    def _generate_template_rationale(
        self,
        ticker: str,
        trade_type: str,
        direction: str,
        signals: Dict,
        edges: List[Dict]
    ) -> str:
        """Fallback template-based rationale when LLM unavailable"""

        higher_tf = signals.get('higher', {})
        middle_tf = signals.get('middle', {})
        applied_edges = [e['name'] for e in edges if e.get('applied')]

        # Build rationale from template
        trend_desc = f"{higher_tf.get('trend_bias', 'neutral').capitalize()} trend on higher timeframe"
        momentum_desc = f"with {middle_tf.get('momentum_bias', 'neutral')} momentum confirmation"

        if applied_edges:
            edges_desc = f"Additional confirmation from {', '.join(applied_edges[:2])}."
        else:
            edges_desc = "Entry trigger met with basic alignment."

        return f"{trend_desc} {momentum_desc}. {edges_desc} {direction.capitalize()} setup for {ticker} {trade_type} trade."

    def _generate_template_analysis(
        self,
        metrics: Dict,
        edge_performance: Dict
    ) -> str:
        """Fallback template-based weekly analysis"""

        win_rate = metrics['win_rate']
        avg_r = metrics['avg_r_multiple']

        # Find best/worst performing edge
        if edge_performance:
            best_edge = max(edge_performance.items(), key=lambda x: x[1]['win_rate'])
            worst_edge = min(edge_performance.items(), key=lambda x: x[1]['win_rate'])

            analysis = f"""Week in Review:
- Win Rate: {win_rate:.1%} | Avg R-Multiple: {avg_r:.2f}R

Best Performing Edge: {best_edge[0]} ({best_edge[1]['win_rate']:.1%} win rate)
Worst Performing Edge: {worst_edge[0]} ({worst_edge[1]['win_rate']:.1%} win rate)

Suggestion: Consider adjusting thresholds for {worst_edge[0]} or disabling if performance continues below 50%."""

        else:
            analysis = f"""Week in Review:
- Win Rate: {win_rate:.1%} | Avg R-Multiple: {avg_r:.2f}R

Continue monitoring performance. Need more data for edge analysis."""

        return analysis


# Singleton instance (optional - can be initialized per request)
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> Optional[LLMClient]:
    """Get or create LLM client singleton"""
    global _llm_client

    if _llm_client is None:
        try:
            _llm_client = LLMClient()
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            return None

    return _llm_client
