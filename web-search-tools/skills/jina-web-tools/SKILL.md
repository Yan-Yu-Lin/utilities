---
name: jina-web-tools
description: This skill teaches how to use Jina AI's Reader API (r.jina.ai) for web access via curl. Use when WebFetch or Firecrawl are unavailable, blocked, or when a lightweight curl-based approach is preferred. Covers fetching pages as markdown, scraping content, searching Google, and accessing APIs.
---

# Jina Web Tools

## Overview

Jina's Reader API (`r.jina.ai`) converts any URL to clean, readable content. By prefixing any URL with `https://r.jina.ai/`, the content is fetched and returned as markdown - accessible via simple `curl` commands.

This skill teaches how to use this technique as a flexible alternative to WebFetch or Firecrawl.

## When to Use

- WebFetch or Firecrawl are unavailable or auto-denied
- Working in restricted environments (subagents, sandboxes)
- Need lightweight, scriptable web access
- Want to avoid API rate limits from other services
- Building pipelines that chain curl commands

---

## Basic: Fetching Web Pages

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

Jina returns:
```
Title: Page Title

URL Source: https://original-url.com

Markdown Content:
# Heading
Content converted to markdown...
```

---

## Intermediate: Extracting Specific Content

### Get just the content (skip headers)

```bash
curl -s "https://r.jina.ai/https://example.com" | tail -n +6
```

### Extract links from a page

```bash
curl -s "https://r.jina.ai/https://example.com" \
  | grep -oE '\[.*\]\(https://[^)]+\)' \
  | head -20
```

### Limit output length

```bash
curl -s "https://r.jina.ai/https://example.com" | head -100
```

---

## Advanced: Google Search via Jina

Jina can fetch Google search results, which can be filtered to extract clean URLs.

### Basic Google search

```bash
curl -s "https://r.jina.ai/https://www.google.com/search?q=your+query+here"
```

### Clean Google search (extract URLs only)

```bash
curl -s "https://r.jina.ai/https://www.google.com/search?q=your+query" \
  | grep -oE '\]\(https://[^)]+\)' \
  | grep -v "google.com\|blob:" \
  | grep -v "gstatic.com\|ytimg.com\|\.png\|\.jpg\|\.svg\|\.gif" \
  | grep -v "youtube.com/watch" \
  | sed 's/\](//' \
  | sed 's/)$//' \
  | sed 's/#.*//' \
  | sed 's/?.*//' \
  | sort -u
```

### Using Google search operators

```bash
# Site-specific
curl -s "https://r.jina.ai/https://www.google.com/search?q=openai+api+site:github.com"

# Exclude sites
curl -s "https://r.jina.ai/https://www.google.com/search?q=claude+api+-site:reddit.com"

# File type
curl -s "https://r.jina.ai/https://www.google.com/search?q=machine+learning+filetype:pdf"
```

---

## Advanced: Accessing APIs via Jina

Jina passes through JSON from APIs. Use `sed` to extract the JSON, then parse with `jq`.

### GitHub API example

```bash
# Search GitHub repos
curl -s "https://r.jina.ai/https://api.github.com/search/repositories?q=org:openai&per_page=10" \
  | sed -n '/^{/,$p' \
  | jq -r '.items[] | "\(.full_name) - \(.stargazers_count) stars"'
```

### Get raw files from GitHub

```bash
curl -s "https://r.jina.ai/https://raw.githubusercontent.com/openai/openai-node/master/README.md"
```

---

## Utility Script: jina-google-search.sh

A pre-built script for clean Google searches is included:

```bash
./scripts/jina-google-search.sh "your search query"
```

### Features
- URL encodes the query automatically
- Filters out Google UI noise, images, videos
- Returns deduplicated, clean URLs
- Supports all Google search operators

### Example

```bash
./scripts/jina-google-search.sh "anthropic claude api site:github.com"
```

Output:
```
https://github.com/anthropics/anthropic-sdk-python
https://github.com/anthropics/anthropic-cookbook
...
```

---

## Comparison with Other Tools

| Feature | Jina + curl | WebFetch | Firecrawl |
|---------|-------------|----------|-----------|
| No API key needed | Yes | Yes | No |
| Works in subagents | Yes | Sometimes denied | Sometimes denied |
| Returns markdown | Yes | Yes | Yes |
| Scriptable/pipeable | Excellent | Limited | Limited |
| Google search | Yes (with filtering) | No | Yes |
| Rate limits | Jina free tier | Built-in | API limits |

---

## Tips & Patterns

### Chain with other tools
```bash
# Find URLs, then scrape with Firecrawl
./scripts/jina-google-search.sh "topic" | head -3 | xargs -I {} firecrawl scrape {}
```

### Save results to file
```bash
curl -s "https://r.jina.ai/https://example.com" > page.md
```

### Use in pipelines
```bash
# Get all OpenAI repos and clone them
curl -s "https://r.jina.ai/https://api.github.com/search/repositories?q=org:openai" \
  | sed -n '/^{/,$p' \
  | jq -r '.items[].clone_url' \
  | xargs -I {} git clone {}
```

---

## Limitations

- Rate limited by Jina's free tier
- Some JavaScript-heavy sites may not render fully
- Large pages may be truncated
- No authentication passthrough for protected content

## Resources

### scripts/

- `jina-google-search.sh` - Pre-built clean Google search utility
