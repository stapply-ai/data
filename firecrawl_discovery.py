"""
Firecrawl-Based Company Discovery
Alternative to SERP API using Firecrawl's search endpoint

Advantages over SERP API:
- Returns full content (not just snippets)
- Combined search + scrape in one call
- Potentially cheaper ($16/mo Hobby vs $50/mo SERP API)
- 500 free credits to start

Pricing:
- 2 credits per 10 search results (without scraping)
- 1 credit per page scraped
- Hobby: $16/mo, Standard: $83/mo
- 500 free credits (no credit card needed)
"""

from firecrawl import FirecrawlApp
import pandas as pd
import re
import os
from typing import Set, List
from dotenv import load_dotenv
import time

load_dotenv()

# Platform configurations
PLATFORMS = {
    "ashby": {
        "domains": ["jobs.ashbyhq.com"],
        "pattern": r"(https://jobs\.ashbyhq\.com/[^/?#]+)",
        "csv_column": "ashby_url",
        "output_file": "ashby/companies.csv",
    },
    "greenhouse": {
        "domains": ["job-boards.greenhouse.io", "boards.greenhouse.io"],
        "pattern": r"(https://(?:job-boards|boards)\.greenhouse\.io/[^/?#]+)",
        "csv_column": "greenhouse_url",
        "output_file": "greenhouse/greenhouse_companies.csv",
    },
    "lever": {
        "domains": ["jobs.lever.co"],
        "pattern": r"(https://jobs\.lever\.co/[^/?#]+)",
        "csv_column": "lever_url",
        "output_file": "lever/lever_companies.csv",
    },
    "workable": {
        "domains": ["apply.workable.com", "jobs.workable.com"],
        "pattern": [
            r"(https://apply\.workable\.com/[^/?#]+)",
            r"(https://jobs\.workable\.com/company/[^/?#]+/[^/?#]+)",
        ],
        "csv_column": "workable_url",
        "output_file": "workable/workable_companies.csv",
    },
}

# Search query strategies
SEARCH_STRATEGIES = [
    # Basic searches
    lambda domain: f"site:{domain}",
    lambda domain: f"site:{domain} careers",
    lambda domain: f"site:{domain} jobs",
    lambda domain: f"site:{domain} hiring",
    # Role-based
    lambda domain: f"site:{domain} software engineer",
    lambda domain: f"site:{domain} product manager",
    lambda domain: f"site:{domain} designer",
    lambda domain: f"site:{domain} remote",
    # Location-based (top cities)
    lambda domain: f"site:{domain} San Francisco",
    lambda domain: f"site:{domain} New York",
    lambda domain: f"site:{domain} London",
    lambda domain: f"site:{domain} Berlin",
    lambda domain: f"site:{domain} Singapore",
    # Company type
    lambda domain: f"site:{domain} startup",
    lambda domain: f"site:{domain} YC",
]


def read_existing_urls(csv_file: str, column_name: str) -> Set[str]:
    """Read existing URLs from CSV file"""
    existing_urls = set()
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file)
            if column_name in df.columns:
                existing_urls = set(df[column_name].dropna().tolist())
                print(f"📖 Found {len(existing_urls)} existing URLs in {csv_file}")
            elif "url" in df.columns:
                existing_urls = set(df["url"].dropna().tolist())
                print(
                    f"📖 Found {len(existing_urls)} existing URLs in {csv_file} (legacy format)"
                )
        except Exception as e:
            print(f"⚠️  Error reading {csv_file}: {e}")
    return existing_urls


def extract_urls_from_results(
    results: List[dict], pattern: str | List[str], domains: List[str]
) -> Set[str]:
    """Extract company URLs from Firecrawl search results"""
    urls = set()

    if not results:
        return urls

    for result in results:
        # Handle both dict and SearchResultWeb objects
        if hasattr(result, "url"):
            url = result.url
        elif isinstance(result, dict):
            url = result.get("url", "")
        else:
            continue

        if not url:
            continue

        # Check if URL contains target domain
        if not any(domain in url for domain in domains):
            continue

        # Handle single pattern or list of patterns
        patterns = [pattern] if isinstance(pattern, str) else pattern

        for pat in patterns:
            match = re.match(pat, url)
            if match:
                urls.add(match.group(1))
                break

    return urls


def discover_platform(
    platform_name: str, max_queries: int = 15, limit_per_query: int = 10
):
    """
    Discover companies using Firecrawl search endpoint

    Args:
        platform_name: Platform to discover
        max_queries: Maximum search queries to use (default: 15)
        limit_per_query: Results per query (default: 10)
    """

    if platform_name not in PLATFORMS:
        print(f"❌ Unknown platform: {platform_name}")
        print(f"Available platforms: {', '.join(PLATFORMS.keys())}")
        return

    config = PLATFORMS[platform_name]

    print("=" * 80)
    print(f"🔥 Firecrawl Discovery: {platform_name.upper()}")
    print(f"📊 Max queries: {max_queries}")
    print(f"📊 Results per query: {limit_per_query}")
    print("=" * 80)

    # Check for API key
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("\n❌ FIRECRAWL_API_KEY not found in environment")
        print("\nSetup instructions:")
        print("1. Sign up at https://firecrawl.dev/")
        print("2. Get your API key from the dashboard")
        print("3. Add to .env file:")
        print("   FIRECRAWL_API_KEY=fc-your_key_here")
        print("\nFree tier: 500 credits (no credit card needed)")
        return

    # Initialize Firecrawl
    try:
        app = FirecrawlApp(api_key=api_key)
    except Exception as e:
        print(f"❌ Failed to initialize Firecrawl: {e}")
        return

    # Read existing URLs
    existing_urls = read_existing_urls(config["output_file"], config["csv_column"])

    all_urls = set()
    queries_used = 0
    total_credits_used = 0

    # Use search strategies
    strategies_to_use = SEARCH_STRATEGIES[:max_queries]

    for strategy_idx, strategy_func in enumerate(strategies_to_use, 1):
        if queries_used >= max_queries:
            print(f"\n⚠️  Reached query limit ({max_queries})")
            break

        query = strategy_func(config["domains"][0])
        print(f"\n[Query {queries_used + 1}/{max_queries}] {query}")

        try:
            # Firecrawl search (no scraping, just get URLs)
            # Cost: 2 credits per 10 results
            search_result = app.search(query=query)

            print(search_result)

            queries_used += 1
            credits_for_query = 2  # 2 credits per 10 results
            total_credits_used += credits_for_query

            # Extract results from SearchData object
            # Firecrawl returns SearchData with 'web' attribute containing list of SearchResultWeb
            results = (
                search_result.web
                if hasattr(search_result, "web") and search_result.web
                else []
            )

            if not results:
                print(f"  No results found")
                continue

            # Extract URLs
            query_urls = extract_urls_from_results(
                results, config["pattern"], config["domains"]
            )

            new_in_query = query_urls - all_urls
            all_urls.update(query_urls)

            print(f"  Found: {len(query_urls)} URLs (+{len(new_in_query)} new)")
            print(f"  Credits used: {credits_for_query} (Total: {total_credits_used})")

            # Small delay to be respectful
            time.sleep(10)

        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            continue

    # Calculate costs
    # Hobby plan: $16/month for 10,000 credits
    cost_per_credit = 16 / 10000
    cost = total_credits_used * cost_per_credit

    print(f"\n📊 Discovery Summary:")
    print(f"  🔍 Queries used: {queries_used}")
    print(f"  💳 Credits used: {total_credits_used}")
    print(f"  💰 Cost: ${cost:.3f} (Hobby plan pricing)")
    print(f"  🔍 Companies found: {len(all_urls)}")
    print(f"  🆕 New companies: {len(all_urls - existing_urls)}")

    # Save results
    combined_urls = existing_urls.union(all_urls)
    new_urls = all_urls - existing_urls

    if new_urls:
        print(f"\n🎉 Sample of new URLs (first 10):")
        for url in sorted(new_urls)[:10]:
            print(f"  ✨ {url}")
        if len(new_urls) > 10:
            print(f"  ... and {len(new_urls) - 10} more")

    df = pd.DataFrame({config["csv_column"]: sorted(combined_urls)})
    df.to_csv(config["output_file"], index=False)

    print(f"\n✅ Saved {len(df)} companies to {config['output_file']}")


def discover_all_platforms(max_queries_per_platform: int = 15):
    """Discover all platforms using Firecrawl"""

    print("=" * 80)
    print("🔥 Firecrawl Discovery - All Platforms")
    print(f"📊 Queries per platform: {max_queries_per_platform}")
    print("=" * 80)

    for platform_name in PLATFORMS.keys():
        print("\n" + "=" * 80)
        discover_platform(platform_name, max_queries=max_queries_per_platform)
        print("=" * 80)
        time.sleep(2)

    print("\n" + "=" * 80)
    print("✅ All platforms discovered!")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Firecrawl-based company discovery (SERP alternative)"
    )
    parser.add_argument(
        "--platform",
        choices=list(PLATFORMS.keys()) + ["all"],
        default="all",
        help="Platform to discover (default: all)",
    )
    parser.add_argument(
        "--max-queries",
        type=int,
        default=15,
        help="Maximum queries to use (default: 15)",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Results per query (default: 10)"
    )

    args = parser.parse_args()

    if args.platform == "all":
        discover_all_platforms(max_queries_per_platform=args.max_queries)
    else:
        discover_platform(
            args.platform, max_queries=args.max_queries, limit_per_query=args.limit
        )
