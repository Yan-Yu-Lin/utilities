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

# Limit output length
curl -s "https://r.jina.ai/https://example.com" | head -100
```

---

## Extracting Links

Extract all links from a page as markdown links `[text](url)`:

```bash
curl -s "https://r.jina.ai/https://anthropic.com" | grep -oE '\[.*\]\(https?://[^)]+\)'
```

### Output

```
[Claude](https://claude.com/product/overview)
[Claude Code](https://claude.com/product/claude-code)
[API](https://docs.anthropic.com)
[Pricing](https://claude.com/pricing)
...
```

### Get URLs only

```bash
curl -s "https://r.jina.ai/https://anthropic.com" \
  | grep -oE '\[.*\]\(https?://[^)]+\)' \
  | grep -oE 'https?://[^)]+' \
  | sort -u
```

---

## Google Search

**Use the included Python script for Google searches.** It handles URL encoding, filters out noise, and returns clean results with titles and descriptions.

```bash
uv run ./scripts/jina-google-search.py "your search query"
uv run ./scripts/jina-google-search.py "your search query" --num 20
uv run ./scripts/jina-google-search.py "your search query" --json
```

### Features

- Returns title, URL, and description for each result
- `--num N` to control result count
- `--json` for structured JSON output
- Filters out Google UI noise, images, ads
- Supports all Google search operators

### Examples

```bash
# Basic search
uv run ./scripts/jina-google-search.py "anthropic claude api"

# Site-specific search
uv run ./scripts/jina-google-search.py "openai api site:github.com"

# JSON output
uv run ./scripts/jina-google-search.py "claude api" --json

# More results
uv run ./scripts/jina-google-search.py "machine learning" --num 20
```

### Output

```
## Claude
https://claude.ai/
Claude is a next generation AI assistant built by Anthropic...

## Introducing Claude
https://www.anthropic.com/news/introducing-claude
Claude is a next-generation AI assistant based on Anthropic's research...
```

### JSON Output

```json
[
  {
    "title": "Claude",
    "url": "https://claude.ai/",
    "description": "Claude is a next generation AI assistant..."
  }
]
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
# Search, get URLs from JSON, then scrape top results
uv run ./scripts/jina-google-search.py "topic" --json | jq -r '.[0:3][].url' | while read url; do
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

---

## When to Use Firecrawl

Use Jina as the default. Fall back to Firecrawl when:

### Site mapping with metadata

To discover all URLs on a site with titles and descriptions, use Firecrawl's map feature:

```
firecrawl_map("https://example.com/blog")
```

Then scrape the discovered URLs with Jina.

### Content not rendering

If Jina returns incomplete content (heavy JavaScript, authentication), try Firecrawl scrape as fallback.

### Summary

| Task | Default | Fallback |
|------|---------|----------|
| Fetch a page | Jina | Firecrawl scrape |
| Extract links from page | Jina + grep | - |
| Map entire site with metadata | Firecrawl map | - |
| Scrape mapped URLs | Jina | Firecrawl scrape |

## Resources

- `scripts/jina-google-search.py` - Google search script with title/description extraction (recommended)
