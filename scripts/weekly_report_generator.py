#!/usr/bin/env python3
"""
Weekly Report Generator
Generates comprehensive weekly trading performance reports

Analyzes:
- Overall win rate and R-multiple
- Best/worst performing edges
- Confidence level effectiveness
- Trade type breakdown (day vs swing)
- Recommendations for improvement

Designed to run weekly (Sunday evening)
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
from dotenv import load_dotenv
import asyncpg

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
env_file = project_root / '.env.supabase'
if env_file.exists():
    load_dotenv(env_file)


class WeeklyReportGenerator:
    """Generates weekly trading performance reports"""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.schema = "discord_trading"
        self.pool = None

    async def get_connection(self) -> asyncpg.Connection:
        """Get database connection"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=3)

        conn = await self.pool.acquire()
        await conn.execute(f"SET search_path TO {self.schema}, public")
        return conn

    async def get_week_trades(self, week_start: datetime, week_end: datetime) -> List[Dict]:
        """Get all trades for a specific week"""
        conn = await self.get_connection()
        try:
            query = """
                SELECT trade_id, ticker, trade_type, direction,
                       entry, stop, target, confidence,
                       edges, status, r_achieved, created_at, closed_at
                FROM trade_signals
                WHERE created_at >= $1 AND created_at < $2
                ORDER BY created_at DESC;
            """

            rows = await conn.fetch(query, week_start, week_end)

            trades = []
            for row in rows:
                trades.append({
                    'trade_id': row['trade_id'],
                    'ticker': row['ticker'],
                    'trade_type': row['trade_type'],
                    'direction': row['direction'],
                    'entry': float(row['entry']),
                    'stop': float(row['stop']),
                    'target': float(row['target']),
                    'confidence': row['confidence'],
                    'edges': json.loads(row['edges']) if row['edges'] else [],
                    'status': row['status'],
                    'r_achieved': float(row['r_achieved']) if row['r_achieved'] else None,
                    'created_at': row['created_at'],
                    'closed_at': row['closed_at']
                })

            return trades

        finally:
            await self.pool.release(conn)

    def calculate_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate summary metrics for trades"""
        total_trades = len(trades)
        wins = sum(1 for t in trades if t['status'] == 'WIN')
        losses = sum(1 for t in trades if t['status'] == 'LOSS')
        expired = sum(1 for t in trades if t['status'] == 'EXPIRED')
        pending = sum(1 for t in trades if t['status'] == 'PENDING')

        closed_trades = [t for t in trades if t['status'] in ('WIN', 'LOSS')]
        win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0

        r_multiples = [t['r_achieved'] for t in closed_trades if t['r_achieved'] is not None]
        avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0
        total_r = sum(r_multiples) if r_multiples else 0

        return {
            'total_trades': total_trades,
            'total_wins': wins,
            'total_losses': losses,
            'total_expired': expired,
            'total_pending': pending,
            'win_rate': round(win_rate, 2),
            'avg_r_multiple': round(avg_r, 2),
            'total_r_achieved': round(total_r, 2)
        }

    def analyze_edges(self, trades: List[Dict]) -> List[Dict]:
        """Analyze performance by edge"""
        closed_trades = [t for t in trades if t['status'] in ('WIN', 'LOSS')]
        if not closed_trades:
            return []

        # Collect edge stats
        edge_stats = {}
        for trade in closed_trades:
            for edge in trade.get('edges', []):
                edge_name = edge.get('name', 'Unknown')
                if edge_name not in edge_stats:
                    edge_stats[edge_name] = {
                        'total': 0,
                        'wins': 0,
                        'losses': 0,
                        'r_multiples': []
                    }

                edge_stats[edge_name]['total'] += 1
                if trade['status'] == 'WIN':
                    edge_stats[edge_name]['wins'] += 1
                else:
                    edge_stats[edge_name]['losses'] += 1

                if trade['r_achieved']:
                    edge_stats[edge_name]['r_multiples'].append(trade['r_achieved'])

        # Calculate win rates and sort
        edge_performance = []
        for edge_name, stats in edge_stats.items():
            win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_r = sum(stats['r_multiples']) / len(stats['r_multiples']) if stats['r_multiples'] else 0

            edge_performance.append({
                'name': edge_name,
                'total': stats['total'],
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_rate': round(win_rate, 2),
                'avg_r': round(avg_r, 2)
            })

        # Sort by win rate
        edge_performance.sort(key=lambda x: x['win_rate'], reverse=True)
        return edge_performance

    def analyze_confidence(self, trades: List[Dict]) -> Dict:
        """Analyze performance by confidence level"""
        closed_trades = [t for t in trades if t['status'] in ('WIN', 'LOSS')]
        if not closed_trades:
            return {}

        confidence_stats = {}
        for trade in closed_trades:
            conf = trade['confidence']
            if conf not in confidence_stats:
                confidence_stats[conf] = {'total': 0, 'wins': 0, 'r_multiples': []}

            confidence_stats[conf]['total'] += 1
            if trade['status'] == 'WIN':
                confidence_stats[conf]['wins'] += 1

            if trade['r_achieved']:
                confidence_stats[conf]['r_multiples'].append(trade['r_achieved'])

        # Calculate win rates
        confidence_breakdown = {}
        for conf, stats in confidence_stats.items():
            win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_r = sum(stats['r_multiples']) / len(stats['r_multiples']) if stats['r_multiples'] else 0

            confidence_breakdown[conf] = {
                'total': stats['total'],
                'wins': stats['wins'],
                'win_rate': round(win_rate, 2),
                'avg_r': round(avg_r, 2)
            }

        return confidence_breakdown

    def analyze_trade_types(self, trades: List[Dict]) -> Dict:
        """Analyze performance by trade type"""
        day_trades = [t for t in trades if t['trade_type'] == 'day' and t['status'] in ('WIN', 'LOSS')]
        swing_trades = [t for t in trades if t['trade_type'] == 'swing' and t['status'] in ('WIN', 'LOSS')]

        def calc_stats(trades_list):
            if not trades_list:
                return {'total': 0, 'wins': 0, 'win_rate': 0, 'avg_r': 0}

            wins = sum(1 for t in trades_list if t['status'] == 'WIN')
            r_multiples = [t['r_achieved'] for t in trades_list if t['r_achieved']]
            avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0

            return {
                'total': len(trades_list),
                'wins': wins,
                'win_rate': round(wins / len(trades_list) * 100, 2),
                'avg_r': round(avg_r, 2)
            }

        return {
            'day_trades': calc_stats(day_trades),
            'swing_trades': calc_stats(swing_trades)
        }

    def generate_recommendations(
        self,
        metrics: Dict,
        edge_performance: List[Dict],
        confidence_breakdown: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Win rate analysis
        if metrics['win_rate'] < 40:
            recommendations.append("Win rate below 40% - consider tightening entry criteria")
        elif metrics['win_rate'] > 70:
            recommendations.append("Excellent win rate! Consider increasing position sizes")

        # R-multiple analysis
        if metrics['avg_r_multiple'] < 1.0:
            recommendations.append("Average R-multiple below 1.0 - review risk/reward ratios")
        elif metrics['avg_r_multiple'] > 2.0:
            recommendations.append("Strong R-multiple performance - strategy working well")

        # Edge analysis
        if edge_performance:
            worst_edge = edge_performance[-1]
            if worst_edge['win_rate'] < 30 and worst_edge['total'] >= 5:
                recommendations.append(
                    f"Consider removing or revising '{worst_edge['name']}' edge (win rate: {worst_edge['win_rate']}%)"
                )

            best_edge = edge_performance[0]
            if best_edge['win_rate'] > 70 and best_edge['total'] >= 5:
                recommendations.append(
                    f"'{best_edge['name']}' edge performing exceptionally well - consider prioritizing"
                )

        # Confidence analysis
        if confidence_breakdown:
            high_conf = confidence_breakdown.get(5, {})
            low_conf = confidence_breakdown.get(2, {})

            if high_conf.get('win_rate', 0) < low_conf.get('win_rate', 0):
                recommendations.append("High confidence trades underperforming - review confidence scoring algorithm")

        # Trade volume
        if metrics['total_trades'] < 5:
            recommendations.append("Low trade volume this week - consider more active scanning")

        if not recommendations:
            recommendations.append("Performance is steady - continue current approach")

        return recommendations

    def generate_markdown_report(
        self,
        week_start: datetime,
        week_end: datetime,
        metrics: Dict,
        edge_performance: List[Dict],
        confidence_breakdown: Dict,
        trade_type_stats: Dict,
        recommendations: List[str]
    ) -> str:
        """Generate markdown formatted report"""

        report = f"""# Weekly Trading Report

**Week**: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total Trades | {metrics['total_trades']} |
| Wins | {metrics['total_wins']} |
| Losses | {metrics['total_losses']} |
| Pending | {metrics['total_pending']} |
| Expired | {metrics['total_expired']} |
| **Win Rate** | **{metrics['win_rate']}%** |
| **Avg R-Multiple** | **{metrics['avg_r_multiple']}R** |
| **Total R Achieved** | **{metrics['total_r_achieved']}R** |

---

## Edge Performance

"""

        if edge_performance:
            report += "| Edge | Total | Wins | Losses | Win Rate | Avg R |\n"
            report += "|------|-------|------|--------|----------|-------|\n"
            for edge in edge_performance[:10]:  # Top 10
                report += f"| {edge['name']} | {edge['total']} | {edge['wins']} | {edge['losses']} | {edge['win_rate']}% | {edge['avg_r']}R |\n"
        else:
            report += "*No closed trades this week*\n"

        report += "\n---\n\n## Confidence Level Analysis\n\n"

        if confidence_breakdown:
            report += "| Confidence | Total | Wins | Win Rate | Avg R |\n"
            report += "|------------|-------|------|----------|-------|\n"
            for conf in sorted(confidence_breakdown.keys(), reverse=True):
                stats = confidence_breakdown[conf]
                report += f"| {conf} | {stats['total']} | {stats['wins']} | {stats['win_rate']}% | {stats['avg_r']}R |\n"
        else:
            report += "*No data available*\n"

        report += "\n---\n\n## Trade Type Breakdown\n\n"

        day_stats = trade_type_stats['day_trades']
        swing_stats = trade_type_stats['swing_trades']

        report += "### Day Trades\n"
        report += f"- Total: {day_stats['total']}\n"
        report += f"- Win Rate: {day_stats['win_rate']}%\n"
        report += f"- Avg R-Multiple: {day_stats['avg_r']}R\n\n"

        report += "### Swing Trades\n"
        report += f"- Total: {swing_stats['total']}\n"
        report += f"- Win Rate: {swing_stats['win_rate']}%\n"
        report += f"- Avg R-Multiple: {swing_stats['avg_r']}R\n"

        report += "\n---\n\n## Recommendations\n\n"

        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"

        report += "\n---\n\n*Generated by Discord Trading Bot - Phase II*\n"

        return report

    async def save_report(
        self,
        week_start: datetime,
        week_end: datetime,
        metrics: Dict,
        edge_performance: List[Dict],
        confidence_breakdown: Dict,
        trade_type_stats: Dict,
        recommendations: List[str],
        report_markdown: str
    ):
        """Save report to database"""
        conn = await self.get_connection()
        try:
            week_number = week_start.strftime('%Y-W%U')

            # Prepare JSON data
            best_edges = edge_performance[:3] if edge_performance else []
            worst_edges = edge_performance[-3:] if len(edge_performance) >= 3 else []

            query = """
                INSERT INTO weekly_reports (
                    week_start, week_end, week_number,
                    total_trades, total_wins, total_losses, total_expired, total_pending,
                    win_rate, avg_r_multiple, total_r_achieved,
                    best_edges, worst_edges,
                    day_trade_stats, swing_trade_stats,
                    confidence_breakdown, recommendations,
                    report_markdown
                ) VALUES (
                    $1, $2, $3,
                    $4, $5, $6, $7, $8,
                    $9, $10, $11,
                    $12, $13,
                    $14, $15,
                    $16, $17,
                    $18
                )
                ON CONFLICT (week_start, week_end)
                DO UPDATE SET
                    total_trades = EXCLUDED.total_trades,
                    total_wins = EXCLUDED.total_wins,
                    total_losses = EXCLUDED.total_losses,
                    win_rate = EXCLUDED.win_rate,
                    avg_r_multiple = EXCLUDED.avg_r_multiple,
                    best_edges = EXCLUDED.best_edges,
                    worst_edges = EXCLUDED.worst_edges,
                    recommendations = EXCLUDED.recommendations,
                    report_markdown = EXCLUDED.report_markdown;
            """

            await conn.execute(
                query,
                week_start.date(), week_end.date(), week_number,
                metrics['total_trades'], metrics['total_wins'], metrics['total_losses'],
                metrics['total_expired'], metrics['total_pending'],
                metrics['win_rate'], metrics['avg_r_multiple'], metrics['total_r_achieved'],
                json.dumps(best_edges), json.dumps(worst_edges),
                json.dumps(trade_type_stats['day_trades']), json.dumps(trade_type_stats['swing_trades']),
                json.dumps(confidence_breakdown), recommendations,
                report_markdown
            )

            logger.info(f"Report saved to database for week {week_number}")

        finally:
            await self.pool.release(conn)

    async def generate(self, week_offset: int = 0):
        """
        Generate weekly report

        Args:
            week_offset: 0 for current week, -1 for last week, etc.
        """
        logger.info("=" * 60)
        logger.info("Weekly Report Generator")
        logger.info("=" * 60)

        # Calculate week boundaries
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday() + (7 * abs(week_offset)))
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)

        logger.info(f"Generating report for week: {week_start.date()} to {week_end.date()}")

        # Get trades
        trades = await self.get_week_trades(week_start, week_end)
        logger.info(f"Found {len(trades)} trades for this week")

        if not trades:
            logger.warning("No trades found - skipping report generation")
            return

        # Calculate metrics
        metrics = self.calculate_metrics(trades)
        edge_performance = self.analyze_edges(trades)
        confidence_breakdown = self.analyze_confidence(trades)
        trade_type_stats = self.analyze_trade_types(trades)
        recommendations = self.generate_recommendations(metrics, edge_performance, confidence_breakdown)

        # Generate report
        report_markdown = self.generate_markdown_report(
            week_start, week_end, metrics, edge_performance,
            confidence_breakdown, trade_type_stats, recommendations
        )

        # Save to database
        await self.save_report(
            week_start, week_end, metrics, edge_performance,
            confidence_breakdown, trade_type_stats,
            recommendations, report_markdown
        )

        # Print report
        logger.info("\n" + report_markdown)

        # Save to file
        reports_dir = project_root / 'reports'
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / f"weekly_report_{week_start.strftime('%Y%m%d')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_markdown)

        logger.info(f"Report saved to: {report_file}")

        await self.pool.close()

        logger.info("=" * 60)
        logger.info("Report Generation Complete")
        logger.info("=" * 60)


async def main():
    """Main entry point"""
    generator = WeeklyReportGenerator()

    # Generate report for last week by default
    await generator.generate(week_offset=-1)


if __name__ == '__main__':
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        project_root / "logs" / "weekly_report_{time}.log",
        rotation="1 month",
        retention="6 months",
        level="DEBUG"
    )

    asyncio.run(main())
