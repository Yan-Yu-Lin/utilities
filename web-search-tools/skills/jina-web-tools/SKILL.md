---
name: jina-web-tools
description: Use Jina AI's Reader API (r.jina.ai) for web scraping and Google searches. Recommended approach for fetching web content - free, reliable, no API key required. Use the included script for Google searches.
---

# Jina Web Tools

## Overview

Jina's Reader API (`r.jina.ai`) is the recommended way to fetch web content. It's free, requires no API key, and reliably converts any URL to clean markdown.

Simply prefix any URL with `https://r.jina.ai/` and fetch it with curl:

```bash
curl -s "https://r.jina.ai/https://example.com"
```

### Why Jina?

- **Free** - No API key, no payment required
- **Reliable** - Less likely to be blocked than other methods
- **Simple** - Just curl, no complex setup
- **Clean output** - Returns well-formatted markdown

---

## Fetching Web Pages

Prefix any URL with `https://r.jina.ai/` to get its content as markdown:

```bash
# Fetch a webpage
curl -s "https://r.jina.ai/https://example.com"

# Fetch documentation
curl -s "https://r.jina.ai/https://docs.anthropic.com/en/docs/overview"

# Fetch a GitHub README
curl -s "https://r.jina.ai/https://github.com/openai/openai-node"
```

### Output Format

Jina returns content like this:

```
Title: Page Title

URL Source: https://original-url.com

Markdown Content:
# Heading
Content converted to markdown...
```

### Extracting Content

```bash
# Skip the header lines, get just content
curl -s "https://r.jina.ai/https://example.com" | tail -n +6

# Extract links from a page
curl -s "https://r.jina.ai/https://example.com" \
  | grep -oE '\[.*\]\(https://[^)]+\)' \
  | head -20

# Limit output length
curl -s "https://r.jina.ai/https://example.com" | head -100
```

---

## Google Search

**Use the included script for Google searches.** It handles URL encoding, filters out noise (Google UI, images, tracking), and returns clean, deduplicated URLs.

```bash
./scripts/jina-google-search.sh "your search query"
./scripts/jina-google-search.sh "your search query" 20  # more results
```

### Features

- Automatically URL-encodes the query
- Optional second argument to control result count
- Filters out Google UI noise, images, videos
- Removes tracking parameters and fragments
- Returns deduplicated, clean URLs
- Supports all Google search operators

### Examples

```bash
# Basic search
./scripts/jina-google-search.sh "anthropic claude api"

# Site-specific search
./scripts/jina-google-search.sh "openai api site:github.com"

# Exclude sites
./scripts/jina-google-search.sh "claude api -site:reddit.com"

# File type search
./scripts/jina-google-search.sh "machine learning filetype:pdf"

# Exact phrase
./scripts/jina-google-search.sh "\"openai python sdk\""
```

### Output

```
https://github.com/anthropics/anthropic-sdk-python
https://github.com/anthropics/anthropic-cookbook
https://docs.anthropic.com/en/api/getting-started
...
```

---

## Accessing APIs

Jina passes through JSON from APIs. Use `sed` to extract the JSON, then parse with `jq`.

### GitHub API Example

```bash
# Search GitHub repos
curl -s "https://r.jina.ai/https://api.github.com/search/repositories?q=org:openai&per_page=10" \
  | sed -n '/^{/,$p' \
  | jq -r '.items[] | "\(.full_name) - \(.stargazers_count) stars"'
```

### Get Raw Files from GitHub

```bash
curl -s "https://r.jina.ai/https://raw.githubusercontent.com/openai/openai-node/master/README.md"
```

---

## Tips

### Save to file

```bash
curl -s "https://r.jina.ai/https://example.com" > page.md
```

### Chain with other tools

```bash
# Search, then scrape top results
./scripts/jina-google-search.sh "topic" | head -3 | while read url; do
  curl -s "https://r.jina.ai/$url"
done
```

### Clone repos from search

```bash
curl -s "https://r.jina.ai/https://api.github.com/search/repositories?q=org:openai" \
  | sed -n '/^{/,$p' \
  | jq -r '.items[].clone_url' \
  | xargs -I {} git clone {}
```

---

## Handling Large Pages

If a page gets truncated, continue reading from the last line you remember:

```bash
curl -s "https://r.jina.ai/https://example.com" | sed -n '/last line you remember/,$p'
```

The `sed -n '/PATTERN/,$p'` prints from the matching line to the end.

---

## Limitations

- Rate limited by Jina's free tier
- Some JavaScript-heavy sites may not render fully

## Resources

- `scripts/jina-google-search.sh` - Google search script (recommended for all Google searches)
