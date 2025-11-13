# Discord Trading Bot

**Status**: Framework Ready - Needs Deployment
**Type**: n8n Workflow + Trading Framework

## Overview
Automated stock trading signals bot that responds to Discord messages with:
- Real-time price quotes (Finnhub API)
- Technical signals (ATR-based stops/targets)
- Latest news headlines (NewsAPI)

## Files
- **n8nworkflow.txt**: Complete n8n workflow JSON (ready to import)
- **trading framework.txt**: 3-Tier MTF analysis framework documentation
- **discord_ticker_research.json.txt**: Placeholder/template

## Deployment Checklist
- [ ] Import workflow to n8n Cloud (https://hyamie.app.n8n.cloud/)
- [ ] Configure Discord bot credentials
- [ ] Add Finnhub API key
- [ ] Add NewsAPI key
- [ ] Set Discord channel ID
- [ ] Test with sample ticker (e.g., AAPL)

## Next Steps
1. Import n8nworkflow.txt to n8n Cloud instance
2. Update API credentials in workflow
3. Test in development Discord channel
4. Document in KB under kb/topics/n8n-trading-bot.md

## Technical Details
- **Framework**: 3-Tier Multi-Timeframe (MTF) analysis
- **Risk Management**: ATR-based stops and targets
- **News Integration**: Real-time market news aggregation
- **APIs Required**: Finnhub, NewsAPI, Discord Bot Token

**Migrated from**: C:\AI\discord bot (2025-11-09)
