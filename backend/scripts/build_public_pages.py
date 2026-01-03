#!/usr/bin/env python3
"""
Generate static public pages for keywords using Google Trends data.

Generates HTML pages containing:
- Keyword name
- Latest momentum score
- Last updated date
- Metrics breakdown (lift, acceleration, novelty, noise)
- Google Trends time series chart data

Usage:
    python -m scripts.build_public_pages --out <PUBLIC_DIR> --date <YYYY-MM-DD>
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.database import SessionLocal
from app.models.keyword import Keyword
from app.models.daily_snapshot import DailySnapshot
from app.models.google_trends_cache import GoogleTrendsCache
from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging()


def get_keywords_with_snapshots(
    db, snapshot_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Get keywords with their latest snapshots for public page generation.

    Args:
        db: Database session
        snapshot_date: Optional specific date to use (default: most recent)

    Returns:
        List of keyword data dictionaries
    """
    if snapshot_date is None:
        # Get most recent snapshot date
        latest_snapshot = (
            db.query(DailySnapshot.snapshot_date)
            .order_by(DailySnapshot.snapshot_date.desc())
            .first()
        )
        if latest_snapshot:
            snapshot_date = latest_snapshot[0]
        else:
            logger.warning("No snapshots found in database")
            return []

    # Get keywords with snapshots for the date
    keywords_data = []
    keywords = db.query(Keyword).all()

    for keyword in keywords:
        # Get snapshot for this date
        snapshot = (
            db.query(DailySnapshot)
            .filter(DailySnapshot.keyword_id == keyword.id)
            .filter(DailySnapshot.snapshot_date == snapshot_date)
            .first()
        )

        if not snapshot:
            continue

        # Get Google Trends cache (worldwide, 12 months)
        trends_cache = (
            db.query(GoogleTrendsCache)
            .filter(GoogleTrendsCache.keyword_id == keyword.id)
            .filter(GoogleTrendsCache.geo == "")
            .filter(GoogleTrendsCache.timeframe == "today 12-m")
            .order_by(GoogleTrendsCache.fetched_at.desc())
            .first()
        )

        keywords_data.append(
            {
                "id": keyword.id,
                "keyword": keyword.keyword,
                "keyword_type": (
                    keyword.keyword_type.value if keyword.keyword_type else "keyword"
                ),
                "first_seen": (
                    keyword.first_seen.isoformat() if keyword.first_seen else None
                ),
                "last_seen": (
                    keyword.last_seen.isoformat() if keyword.last_seen else None
                ),
                "snapshot": {
                    "date": snapshot.snapshot_date.isoformat(),
                    "momentum_score": snapshot.momentum_score,
                    "lift": snapshot.lift_value,
                    "acceleration": snapshot.acceleration_value,
                    "novelty": snapshot.novelty_value,
                    "noise": snapshot.noise_value,
                },
                "trends_data": trends_cache.time_series_data if trends_cache else None,
            }
        )

    # Sort by momentum score descending
    keywords_data.sort(key=lambda x: x["snapshot"]["momentum_score"], reverse=True)

    return keywords_data


def generate_keyword_page(keyword_data: Dict[str, Any], output_dir: Path) -> None:
    """
    Generate a static HTML page for a single keyword.

    Args:
        keyword_data: Keyword data dictionary
        output_dir: Output directory for pages
    """
    keyword = keyword_data["keyword"]
    snapshot = keyword_data["snapshot"]
    trends_data = keyword_data.get("trends_data")

    # Create keyword directory
    keyword_dir = output_dir / "keywords" / str(keyword_data["id"])
    keyword_dir.mkdir(parents=True, exist_ok=True)

    # Prepare time series data for chart
    chart_data = []
    if trends_data and "data" in trends_data:
        for record in trends_data["data"]:
            # Extract date and value from trends data
            # Format depends on pytrends output
            date_str = None
            value = None

            for key, val in record.items():
                if key == "date" or "date" in key.lower():
                    date_str = str(val)
                elif isinstance(val, (int, float)) and key != "isPartial":
                    value = float(val)

            if date_str and value is not None:
                chart_data.append({"date": date_str, "value": value})

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{keyword} - TrendEarly</title>
    <meta name="description" content="Google Trends data for {keyword}">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin-top: 0;
            color: #2563eb;
        }}
        .score {{
            font-size: 3em;
            font-weight: bold;
            color: #2563eb;
            margin: 20px 0;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric {{
            padding: 15px;
            background: #f9fafb;
            border-radius: 6px;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #6b7280;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #111827;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f9fafb;
            border-radius: 6px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 0.9em;
            color: #6b7280;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #2563eb;
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        
        <h1>{keyword}</h1>
        
        <div class="score">{snapshot['momentum_score']}/100</div>
        <p>Last updated: {snapshot['date']}</p>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Lift</div>
                <div class="metric-value">{snapshot['lift']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Acceleration</div>
                <div class="metric-value">{snapshot['acceleration']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Novelty</div>
                <div class="metric-value">{(snapshot['novelty'] * 100):.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Noise</div>
                <div class="metric-value">{snapshot['noise']:.2f}</div>
            </div>
        </div>
"""

    # Add chart if data available
    if chart_data:
        # Convert to JSON for JavaScript
        chart_json = json.dumps(chart_data)
        html += f"""
        <div class="chart-container">
            <h2>Google Trends (Past 12 Months)</h2>
            <canvas id="trendsChart" width="800" height="400"></canvas>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            <script>
                const chartData = {chart_json};
                const ctx = document.getElementById('trendsChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: chartData.map(d => d.date),
                        datasets: [{{
                            label: 'Search Interest',
                            data: chartData.map(d => d.value),
                            borderColor: '#2563eb',
                            backgroundColor: 'rgba(37, 99, 235, 0.1)',
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
"""

    html += f"""
        <div class="footer">
            <p>Data source: Google Trends</p>
            <p>Generated: {datetime.utcnow().isoformat()}</p>
        </div>
    </div>
</body>
</html>
"""

    # Write HTML file
    output_file = keyword_dir / "index.html"
    output_file.write_text(html, encoding="utf-8")
    logger.info(f"Generated page for keyword: {keyword} -> {output_file}")


def generate_index_page(keywords_data: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Generate index page listing all keywords.

    Args:
        keywords_data: List of keyword data dictionaries
        output_dir: Output directory
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrendEarly - Trending Keywords</title>
    <meta name="description" content="Discover trending keywords with strong momentum">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            margin-top: 0;
            color: #2563eb;
        }
        .keywords-list {
            display: grid;
            gap: 15px;
            margin-top: 30px;
        }
        .keyword-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: #f9fafb;
            border-radius: 6px;
            text-decoration: none;
            color: inherit;
            transition: background 0.2s;
        }
        .keyword-item:hover {
            background: #f3f4f6;
        }
        .keyword-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #111827;
        }
        .keyword-score {
            font-size: 2em;
            font-weight: bold;
            color: #2563eb;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 0.9em;
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>TrendEarly - Trending Keywords</h1>
        <p>Keywords ranked by momentum score based on Google Trends data</p>
        
        <div class="keywords-list">
"""

    for keyword_data in keywords_data:
        keyword = keyword_data["keyword"]
        score = keyword_data["snapshot"]["momentum_score"]
        keyword_id = keyword_data["id"]

        html += f"""
            <a href="/keywords/{keyword_id}/" class="keyword-item">
                <span class="keyword-name">{keyword}</span>
                <span class="keyword-score">{score}</span>
            </a>
"""

    html += (
        """
        </div>
        
        <div class="footer">
            <p>Data source: Google Trends</p>
            <p>Generated: """
        + datetime.utcnow().isoformat()
        + """</p>
        </div>
    </div>
</body>
</html>
"""
    )

    # Write index file
    output_file = output_dir / "index.html"
    output_file.write_text(html, encoding="utf-8")
    logger.info(f"Generated index page: {output_file}")


def main():
    """Main function to generate public pages."""
    parser = argparse.ArgumentParser(
        description="Generate static public pages for keywords"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output directory for public pages",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Snapshot date (YYYY-MM-DD), default: most recent",
    )

    args = parser.parse_args()

    # Determine output directory
    output_dir = args.out
    if output_dir is None:
        output_dir = getattr(settings, "public_pages_dir", "./public_generated")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Parse date if provided
    snapshot_date = None
    if args.date:
        try:
            snapshot_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)

    logger.info(f"Generating public pages to: {output_path}")
    if snapshot_date:
        logger.info(f"Using snapshot date: {snapshot_date}")
    else:
        logger.info("Using most recent snapshot date")

    # Get data from database
    db = SessionLocal()
    try:
        keywords_data = get_keywords_with_snapshots(db, snapshot_date)

        if not keywords_data:
            logger.warning("No keywords with snapshots found")
            sys.exit(1)

        logger.info(f"Found {len(keywords_data)} keywords with snapshots")

        # Generate pages
        for keyword_data in keywords_data:
            generate_keyword_page(keyword_data, output_path)

        # Generate index page
        generate_index_page(keywords_data, output_path)

        logger.info(
            f"Successfully generated {len(keywords_data)} keyword pages + index"
        )

    except Exception as e:
        logger.error(f"Error generating public pages: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
