#!/bin/bash
# jina-google-search.sh - Clean Google search results via Jina
# Usage: ./jina-google-search.sh "your search query" [num_results]

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 \"search query\" [num_results]"
  echo "Example: $0 \"openai api documentation\""
  echo "Example: $0 \"openai api documentation\" 20"
  exit 1
fi

# URL encode the query
query=$(echo "$1" | sed 's/ /+/g')

# Optional: number of results (default: Google's default ~10)
num_param=""
if [ -n "$2" ]; then
  num_param="&num=$2"
fi

# Fetch via Jina, extract and clean URLs
curl -s "https://r.jina.ai/https://www.google.com/search?q=${query}${num_param}" \
  | grep -oE '\]\(https://[^)]+\)' \
  | grep -v "google.com\|blob:" \
  | grep -v "gstatic.com\|ytimg.com\|\.png\|\.jpg\|\.svg\|\.gif" \
  | grep -v "youtube.com/watch" \
  | sed 's/\](//' \
  | sed 's/)$//' \
  | sed 's/#.*//' \
  | sed 's/?.*//' \
  | sort -u
