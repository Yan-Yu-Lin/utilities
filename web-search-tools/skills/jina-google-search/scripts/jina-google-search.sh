#!/bin/bash
# jina-google-search.sh - Clean Google search results via Jina
# Usage: ./jina-google-search.sh "your search query"

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 \"search query\""
  echo "Example: $0 \"openai api documentation\""
  exit 1
fi

# URL encode the query
query=$(echo "$1" | sed 's/ /+/g')

# Fetch via Jina, extract and clean URLs
curl -s "https://r.jina.ai/https://www.google.com/search?q=${query}" \
  | grep -oE '\]\(https://[^)]+\)' \
  | grep -v "google.com\|blob:" \
  | grep -v "gstatic.com\|ytimg.com\|\.png\|\.jpg\|\.svg\|\.gif" \
  | grep -v "youtube.com/watch" \
  | sed 's/\](//' \
  | sed 's/)$//' \
  | sed 's/#.*//' \
  | sed 's/?.*//' \
  | sort -u
