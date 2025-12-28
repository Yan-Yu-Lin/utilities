#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""
jina-google-search.py - Google search via Jina with titles and descriptions

Usage:
    uv run jina-google-search.py "your search query"
    uv run jina-google-search.py "your search query" --num 20
    uv run jina-google-search.py "your search query" --json
"""

import argparse
import json
import re
import sys
from urllib.parse import quote_plus

import requests

# Domains to filter out
FILTER_DOMAINS = [
    "google.com",
    "gstatic.com",
    "ytimg.com",
    "googleapis.com",
    "googleusercontent.com",
]


def should_filter(url: str) -> bool:
    """Check if URL should be filtered out."""
    for domain in FILTER_DOMAINS:
        if domain in url:
            return True
    # Filter blob URLs and image files
    if url.startswith("blob:") or re.search(r'\.(png|jpg|gif|svg)$', url, re.I):
        return True
    return False


def fetch_jina(query: str, num: int | None = None) -> str:
    """Fetch Google search results via Jina."""
    encoded_query = quote_plus(query)
    url = f"https://r.jina.ai/https://www.google.com/search?q={encoded_query}"
    if num:
        url += f"&num={num}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def parse_results(content: str) -> list[dict]:
    """Parse Jina markdown output into structured results."""
    results = []
    seen_urls = set()

    lines = content.split('\n')

    # Pattern for search result headers: [### Title ...](URL)
    # Title can contain ] so we match greedily up to ](http
    result_pattern = re.compile(r'^\[### (.+)\]\((https?://[^)]+)\)$')

    i = 0
    while i < len(lines):
        line = lines[i]
        match = result_pattern.match(line)

        if match:
            raw_title = match.group(1)
            url = match.group(2)

            # Clean title - format is: "Title ![Image](blob) SiteName URL"
            # Remove everything from the image markdown onwards
            title = re.sub(r'\s*!\[.*$', '', raw_title)
            title = re.sub(r'[\\›»].*$', '', title)  # Remove breadcrumb stuff
            title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
            title = title.strip()

            # Clean URL
            clean_url = re.sub(r'[#?].*$', '', url)

            if should_filter(url) or clean_url in seen_urls or not title:
                i += 1
                continue

            seen_urls.add(clean_url)

            # Look for description in next ~10 lines
            description = ""
            for j in range(i + 1, min(i + 10, len(lines))):
                next_line = lines[j].strip()

                # Stop at next result or section
                if result_pattern.match(next_line) or next_line.startswith('##'):
                    break

                # Skip noise
                if (next_line.startswith('[') or
                    next_line.startswith('http') or
                    next_line.startswith('![') or
                    next_line.startswith('*') or
                    'feedback' in next_line.lower() or
                    re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', next_line, re.I) or
                    len(next_line) < 30):
                    continue

                # Found a description candidate
                # Clean it up
                desc = next_line
                desc = re.sub(r'_([^_]+)_', r'\1', desc)  # Remove _emphasis_
                desc = re.sub(r'\[Read more\].*$', '', desc)  # Remove [Read more]
                desc = re.sub(r'^[A-Z][a-z]{2} \d{1,2}, \d{4} — ', '', desc)  # Remove dates
                desc = desc.strip()

                if len(desc) > 30:
                    description = desc
                    break

            results.append({
                "title": title,
                "url": clean_url,
                "description": description
            })

        i += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="Google search via Jina")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--num", type=int, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        content = fetch_jina(args.query, args.num)
        results = parse_results(content)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                print(f"## {r['title']}")
                print(r['url'])
                if r['description']:
                    print(r['description'])
                print()

    except requests.RequestException as e:
        print(f"Error fetching results: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
