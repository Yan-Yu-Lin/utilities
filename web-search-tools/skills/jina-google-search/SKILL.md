---
name: jina-google-search
description: This skill performs clean Google searches via Jina AI's reader API, returning deduplicated URLs without noise. Use when needing to search Google and get actionable, clean results. Supports Google search operators like site:, filetype:, and quoted phrases.
---

# Jina Google Search

## Overview

This skill provides clean Google search results by using Jina's reader API (`r.jina.ai`) as a proxy. It filters out noise (Google UI elements, images, YouTube videos, tracking parameters) and returns only unique, actionable URLs.

## When to Use

- Searching Google for information without API keys
- Finding URLs related to a topic
- Using Google search operators (site:, filetype:, etc.)
- Getting clean search results for further scraping or analysis

## Usage

### Basic Search

Run the script with a search query:

```bash
./scripts/jina-google-search.sh "your search query"
```

### With Search Operators

Google search operators are fully supported:

```bash
# Site-specific search
./scripts/jina-google-search.sh "openai api site:github.com"

# Exclude sites
./scripts/jina-google-search.sh "claude api -site:reddit.com"

# File type
./scripts/jina-google-search.sh "machine learning filetype:pdf"

# Exact phrase
./scripts/jina-google-search.sh "\"openai python sdk\""

# Combined operators
./scripts/jina-google-search.sh "anthropic claude site:github.com -issues"
```

## How It Works

1. URL-encodes the search query
2. Fetches results via `https://r.jina.ai/https://www.google.com/search?q=...`
3. Extracts markdown links using grep
4. Filters out:
   - Google domains and redirects
   - Image files (gstatic, ytimg, .png, .jpg, .svg, .gif)
   - YouTube watch pages
   - URL fragments (#) and query parameters (?)
5. Deduplicates and sorts results

## Example Output

```
https://platform.openai.com/docs/api-reference/introduction
https://github.com/openai/openai-node
https://github.com/openai/openai-python
https://www.anthropic.com/api
...
```

## Limitations

- Rate limited by Jina's free tier
- Results depend on Google's response to Jina's requests
- Some dynamic content may not be captured

## Resources

### scripts/

- `jina-google-search.sh` - Main executable script for performing searches
