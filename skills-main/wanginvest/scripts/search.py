# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
# ]
# ///

"""Tavily web search for MR Dang stock analysis."""

import os
from typing import Any

import requests


def get_tavily_api_key() -> str:
    """Get Tavily API key from environment."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")
    return api_key


def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> dict[str, Any]:
    """Search the web using Tavily API.

    Args:
        query: Search query
        max_results: Maximum number of results to return
        search_depth: "basic" or "advanced"
        include_domains: List of domains to include
        exclude_domains: List of domains to exclude

    Returns:
        Dictionary with search results
    """
    api_key = get_tavily_api_key()

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
    }

    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()


def search_company_info(company_name: str, industry: str = "") -> dict[str, list[dict[str, Any]]]:
    """Search for comprehensive company information.

    Args:
        company_name: Company name to search
        industry: Industry type (e.g., "银行", "煤炭开采")

    Returns:
        Dictionary with categorized search results
    """
    results = {}

    # 1. 主营业务搜索
    results["business"] = tavily_search(
        query=f"{company_name} 主营业务 业务构成 产品结构",
        max_results=3,
        search_depth="advanced",
    ).get("results", [])

    # 2. 行业地位搜索
    results["position"] = tavily_search(
        query=f"{company_name} 行业地位 竞争优势 市场份额",
        max_results=3,
        search_depth="advanced",
    ).get("results", [])

    # 3. 周期性判断
    results["cycle"] = tavily_search(
        query=f"{company_name} 是否周期股 产能周期 行业景气度",
        max_results=3,
        search_depth="basic",
    ).get("results", [])

    # 4. 再融资情况
    results["financing"] = tavily_search(
        query=f"{company_name} 增发 配股 再融资 近三年",
        max_results=3,
        search_depth="basic",
    ).get("results", [])

    # 5. 资产属性判断
    results["asset_type"] = tavily_search(
        query=f"{company_name} 生产资料属性 重资产还是轻资产 产能投资",
        max_results=3,
        search_depth="basic",
    ).get("results", [])

    # 6. 银行股专用
    if industry == "银行":
        results["bank_risk"] = tavily_search(
            query=f"{company_name} 区域经济 房地产风险 不良率 拨备覆盖率",
            max_results=3,
            search_depth="basic",
        ).get("results", [])

    return results


def extract_search_content(results: list[dict[str, Any]], max_length: int = 500) -> str:
    """Extract and summarize content from search results.

    Args:
        results: List of search result dictionaries
        max_length: Maximum length of summary

    Returns:
        Summarized content string
    """
    if not results:
        return "无相关信息"

    contents = []
    total_length = 0

    for result in results:
        content = result.get("content", "")
        if content:
            # Truncate if needed
            if total_length + len(content) > max_length:
                remaining = max_length - total_length
                if remaining > 100:
                    contents.append(content[:remaining] + "...")
                break
            contents.append(content)
            total_length += len(content)

    return "\n".join(contents) if contents else "无相关信息"


def main() -> None:
    """CLI entry point for Tavily search."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Search the web using Tavily API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple search
  uv run scripts/search.py query "<搜索关键词>"

  # Search with more results and advanced depth
  uv run scripts/search.py query "<搜索关键词>" --max-results 10 --depth advanced

  # Search with domain filtering
  uv run scripts/search.py query "<搜索关键词>" --include-domains eastmoney.com

  # Company info search (comprehensive)
  uv run scripts/search.py company <公司名称> --industry <行业>

  # Extract content from search results JSON file
  uv run scripts/search.py extract results.json --max-length 1000
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Simple search command
    simple_parser = subparsers.add_parser("query", help="Perform a simple search")
    simple_parser.add_argument("query", help="Search query")
    simple_parser.add_argument("--max-results", type=int, default=5, help="Max results (default: 5)")
    simple_parser.add_argument("--depth", choices=["basic", "advanced"], default="basic", help="Search depth")
    simple_parser.add_argument("--include-domains", action="append", help="Domains to include (can be used multiple times)")
    simple_parser.add_argument("--exclude-domains", action="append", help="Domains to exclude (can be used multiple times)")

    # Company info command
    company_parser = subparsers.add_parser("company", help="Search comprehensive company info")
    company_parser.add_argument("name", help="Company name")
    company_parser.add_argument("--industry", default="", help="Industry type (e.g., 银行)")

    # Extract content command
    extract_parser = subparsers.add_parser("extract", help="Extract content from search results JSON file")
    extract_parser.add_argument("json_file", help="Path to JSON file containing search results")
    extract_parser.add_argument("--max-length", type=int, default=500, help="Max length of extracted content (default: 500)")

    args = parser.parse_args()

    if args.command == "query":
        result = tavily_search(
            args.query,
            max_results=args.max_results,
            search_depth=args.depth,
            include_domains=args.include_domains,
            exclude_domains=args.exclude_domains,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "company":
        results = search_company_info(args.name, args.industry)
        output = {}
        for category, items in results.items():
            output[category] = [
                {"title": r.get("title"), "url": r.get("url"), "content": r.get("content", "")[:200]}
                for r in items
            ]
        print(json.dumps(output, indent=2, ensure_ascii=False))

    elif args.command == "extract":
        with open(args.json_file, encoding="utf-8") as f:
            data = json.load(f)
        # Support both direct results list and nested results
        results = data if isinstance(data, list) else data.get("results", [])
        content = extract_search_content(results, args.max_length)
        print(content)


if __name__ == "__main__":
    main()
