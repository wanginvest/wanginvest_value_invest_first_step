# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "tushare",
# ]
# ///

"""Tushare data fetching functions for MR Dang stock analysis."""

import os
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import tushare as ts

# Initialize Tushare with token from environment
_TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN")
if not _TUSHARE_TOKEN:
    raise ValueError("TUSHARE_TOKEN environment variable not set")

pro = ts.pro_api(_TUSHARE_TOKEN)


def search_stock(keyword: str) -> pd.DataFrame:
    """Search for stock by name or code.

    Args:
        keyword: Stock name or code to search

    Returns:
        DataFrame with columns: ts_code, name, area, industry, market, list_date
    """
    df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,area,industry,market,list_date")
    # Filter by keyword
    mask = df["name"].str.contains(keyword, case=False, na=False) | df["ts_code"].str.contains(
        keyword, case=False, na=False
    )
    result = df[mask]
    return result.reset_index(drop=True)


def get_stock_basic(ts_code: str) -> dict[str, Any]:
    """Get basic stock information.

    Args:
        ts_code: Tushare stock code (e.g., "600036.SH")

    Returns:
        Dictionary with basic stock info
    """
    df = pro.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,area,industry,market,list_date")
    if df.empty:
        return {"error": f"No data found for {ts_code}"}
    return df.iloc[0].to_dict()


def get_daily_basic(ts_code: str, trade_date: str | None = None) -> dict[str, Any]:
    """Get daily basic metrics (PE, PB, market cap, etc.).

    Args:
        ts_code: Tushare stock code
        trade_date: Trade date in format YYYYMMDD (defaults to latest)

    Returns:
        Dictionary with daily basic metrics
    """
    if trade_date is None:
        # Fetch recent records and take the latest — one API call instead of up to 10
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=14)).strftime("%Y%m%d")
        df = pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values("trade_date", ascending=False)
    else:
        df = pro.daily_basic(ts_code=ts_code, trade_date=trade_date)

    if df.empty:
        return {"error": f"No daily basic data found for {ts_code}"}

    row = df.iloc[0]
    return {
        "ts_code": row.get("ts_code"),
        "trade_date": row.get("trade_date"),
        "close": row.get("close"),
        "turnover_rate": row.get("turnover_rate"),
        "turnover_rate_f": row.get("turnover_rate_f"),
        "volume_ratio": row.get("volume_ratio"),
        "pe": row.get("pe"),  # PE(TTM)
        "pe_ttm": row.get("pe_ttm"),
        "pb": row.get("pb"),
        "ps": row.get("ps"),
        "ps_ttm": row.get("ps_ttm"),
        "dv_ratio": row.get("dv_ratio"),  # Dividend yield (TTM) in %
        "dv_ttm": row.get("dv_ttm"),
        "total_mv": row.get("total_mv"),  # Total market value in 10k RMB
        "circ_mv": row.get("circ_mv"),  # Circulating market value in 10k RMB
        "free_share": row.get("free_share"),
        "total_share": row.get("total_share"),
    }


def get_financial_indicator(ts_code: str, periods: int = 4) -> pd.DataFrame:
    """Get financial indicators for recent periods.

    Args:
        ts_code: Tushare stock code
        periods: Number of recent periods to fetch

    Returns:
        DataFrame with financial indicators
    """
    df = pro.fina_indicator(ts_code=ts_code, fields=[
        "ts_code", "ann_date", "end_date", "roe", "roa", "debt_to_assets",
        "ocfps", "basic_eps", "dt_eps", "cfps", "ebit_of_gr", "op_yoy",
        "ebt_of_gr", "roa_yearly", "roe_dt", "roe_yearly", "cfps_yoy",
        "current_ratio", "quick_ratio", "grossprofit_margin", "profit_dedt",
    ])
    if df.empty:
        return pd.DataFrame()

    # Sort by end_date descending and take top periods
    df = df.sort_values("end_date", ascending=False).head(periods)
    return df.reset_index(drop=True)


def get_financial_indicator_summary(ts_code: str) -> dict[str, Any]:
    """Get latest financial indicator summary.

    Args:
        ts_code: Tushare stock code

    Returns:
        Dictionary with key financial metrics
    """
    df = get_financial_indicator(ts_code, periods=1)
    if df.empty:
        return {"error": f"No financial indicator data found for {ts_code}"}

    row = df.iloc[0]
    return {
        "ts_code": row.get("ts_code"),
        "end_date": row.get("end_date"),
        "roe": row.get("roe"),  # ROE (%)
        "roa": row.get("roa"),  # ROA (%)
        "debt_to_assets": row.get("debt_to_assets"),  # Debt to assets ratio (%)
        "ocfps": row.get("ocfps"),  # Operating cash flow per share
        "basic_eps": row.get("basic_eps"),  # Basic EPS
        "current_ratio": row.get("current_ratio"),  # Current ratio
        "quick_ratio": row.get("quick_ratio"),  # Quick ratio
        "grossprofit_margin": row.get("grossprofit_margin"),  # Gross profit margin (%)
    }


def get_dividend_info(ts_code: str, years: int = 3) -> dict[str, Any]:
    """Get dividend information for recent years.

    Args:
        ts_code: Tushare stock code
        years: Number of years to analyze

    Returns:
        Dictionary with dividend metrics
    """
    # Get dividend records
    df = pro.dividend(ts_code=ts_code, fields="ts_code,end_date,div_proc,stk_div,cash_div,record_date,ex_date,ann_date")

    if df.empty:
        return {
            "ts_code": ts_code,
            "dividend_count": 0,
            "avg_cash_div": 0,
            "dividend_stability": "无分红记录",
            "dividend_years": [],
        }

    # Filter for cash dividends (实施完成)
    cash_div_df = df[df["div_proc"] == "实施"].copy()
    cash_div_df = cash_div_df.sort_values("end_date", ascending=False)

    # Get recent years
    current_year = datetime.now().year
    recent_years = [str(current_year - i) for i in range(years)]

    # Count dividends per year
    yearly_div = {}
    for _, row in cash_div_df.iterrows():
        year = str(row["end_date"])[:4]
        if year in recent_years:
            if year not in yearly_div:
                yearly_div[year] = 0
            if pd.notna(row["cash_div"]) and row["cash_div"] > 0:
                yearly_div[year] += row["cash_div"]

    dividend_years = list(yearly_div.keys())
    dividend_count = len(dividend_years)
    avg_cash_div = sum(yearly_div.values()) / years if years > 0 else 0

    # Determine stability
    if dividend_count >= years:
        stability = "稳定分红"
    elif dividend_count >= years - 1:
        stability = "基本稳定"
    elif dividend_count > 0:
        stability = "分红不稳定"
    else:
        stability = "无分红记录"

    return {
        "ts_code": ts_code,
        "dividend_count": dividend_count,
        "years_analyzed": years,
        "avg_cash_div_per_10_shares": round(avg_cash_div, 2),
        "dividend_stability": stability,
        "dividend_years": dividend_years,
        "yearly_details": yearly_div,
    }


def get_daily_ohlcv(ts_code: str, days: int = 250) -> pd.DataFrame:
    """Get daily OHLCV data.

    Args:
        ts_code: Tushare stock code
        days: Number of trading days to fetch

    Returns:
        DataFrame with columns: trade_date, open, high, low, close, vol, amount
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days * 1.5)).strftime("%Y%m%d")  # Buffer for non-trading days

    df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

    if df.empty:
        return pd.DataFrame()

    # Sort by date ascending
    df = df.sort_values("trade_date").reset_index(drop=True)

    # Take last 'days' records
    if len(df) > days:
        df = df.tail(days).reset_index(drop=True)

    return df[["trade_date", "open", "high", "low", "close", "vol", "amount"]]


def get_price_position(ts_code: str, days: int = 250) -> dict[str, Any]:
    """Calculate price position relative to recent history.

    Args:
        ts_code: Tushare stock code
        days: Number of trading days for history

    Returns:
        Dictionary with price position metrics
    """
    df = get_daily_ohlcv(ts_code, days)

    if df.empty:
        return {"error": f"No price data found for {ts_code}"}

    latest_close = df.iloc[-1]["close"]
    high_52w = df["high"].max()
    low_52w = df["low"].min()
    avg_close = df["close"].mean()

    # Position relative to 52-week range (0-100%)
    price_position = (latest_close - low_52w) / (high_52w - low_52w) * 100 if high_52w != low_52w else 50

    # Distance from high
    distance_from_high = (high_52w - latest_close) / high_52w * 100

    # Determine position level
    if price_position >= 80:
        position_level = "接近历史高位"
    elif price_position >= 60:
        position_level = "偏高位置"
    elif price_position >= 40:
        position_level = "中等位置"
    elif price_position >= 20:
        position_level = "偏低位置"
    else:
        position_level = "接近历史低位"

    return {
        "ts_code": ts_code,
        "latest_close": latest_close,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "avg_close": round(avg_close, 2),
        "price_position_pct": round(price_position, 1),
        "distance_from_high_pct": round(distance_from_high, 1),
        "position_level": position_level,
    }


def get_all_data(ts_code: str) -> dict[str, Any]:
    """Get all relevant data for a stock.

    Args:
        ts_code: Tushare stock code

    Returns:
        Dictionary with all stock data
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    tasks = {
        "basic": lambda: get_stock_basic(ts_code),
        "daily_basic": lambda: get_daily_basic(ts_code),
        "financial": lambda: get_financial_indicator_summary(ts_code),
        "dividend": lambda: get_dividend_info(ts_code),
        "price_position": lambda: get_price_position(ts_code),
    }

    results: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fn): key for key, fn in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e)}
    return results


def main() -> None:
    """CLI entry point for data fetching."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Fetch stock data from Tushare",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for a stock by name or code
  uv run scripts/data.py search <股票名称或代码>

  # Get all data for a specific stock code
  uv run scripts/data.py get <ts_code> --type all

  # Get specific data type
  uv run scripts/data.py get <ts_code> --type basic
  uv run scripts/data.py get <ts_code> --type daily --date YYYYMMDD
  uv run scripts/data.py get <ts_code> --type financial --periods 8
  uv run scripts/data.py get <ts_code> --type dividend --years 5
  uv run scripts/data.py get <ts_code> --type ohlcv --days 100
  uv run scripts/data.py get <ts_code> --type price --days 250
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for stock by name or code")
    search_parser.add_argument("keyword", help="Stock name or code to search")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get data for a stock")
    get_parser.add_argument("ts_code", help="Tushare stock code (e.g., 600036.SH)")
    get_parser.add_argument(
        "--type",
        choices=["basic", "daily", "financial", "financial-full", "dividend", "ohlcv", "price", "all"],
        default="all",
        help="Type of data to fetch (default: all)",
    )
    get_parser.add_argument("--date", help="Trade date for daily data (YYYYMMDD format)")
    get_parser.add_argument("--periods", type=int, default=4, help="Number of periods for financial data (default: 4)")
    get_parser.add_argument("--years", type=int, default=3, help="Number of years for dividend data (default: 3)")
    get_parser.add_argument("--days", type=int, default=250, help="Number of trading days for OHLCV/price data (default: 250)")

    args = parser.parse_args()

    if args.command == "search":
        result = search_stock(args.keyword)
        if result.empty:
            print(f"No stock found for: {args.keyword}")
        else:
            print(result[["ts_code", "name", "industry", "market", "list_date"]].to_string())

    elif args.command == "get":
        if args.type == "basic":
            print(get_stock_basic(args.ts_code))
        elif args.type == "daily":
            print(get_daily_basic(args.ts_code, args.date))
        elif args.type == "financial":
            print(get_financial_indicator_summary(args.ts_code))
        elif args.type == "financial-full":
            df = get_financial_indicator(args.ts_code, args.periods)
            if df.empty:
                print(f"No financial data found for {args.ts_code}")
            else:
                print(df.to_string())
        elif args.type == "dividend":
            print(get_dividend_info(args.ts_code, args.years))
        elif args.type == "ohlcv":
            df = get_daily_ohlcv(args.ts_code, args.days)
            if df.empty:
                print(f"No OHLCV data found for {args.ts_code}")
            else:
                print(df.to_string())
        elif args.type == "price":
            print(get_price_position(args.ts_code, args.days))
        else:
            data = get_all_data(args.ts_code)
            print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
