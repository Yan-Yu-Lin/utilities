#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp"]
# ///
"""
youtube-channel.py - Explore a YouTuber's channel

Usage:
    uv run youtube-channel.py "https://youtube.com/@HealthyGamerGG"
    uv run youtube-channel.py "@HealthyGamerGG" --limit 20
    uv run youtube-channel.py "@HealthyGamerGG" --sort views
    uv run youtube-channel.py "@HealthyGamerGG" --search "anxiety"
    uv run youtube-channel.py "@HealthyGamerGG" --json
    uv run youtube-channel.py "@HealthyGamerGG" --type shorts
"""

import argparse
import json
import re
import sys
from typing import Optional

import yt_dlp


class YouTubeChannelExplorer:
    def __init__(self, quiet: bool = False):
        self.quiet = quiet

    def log(self, msg: str):
        if not self.quiet:
            print(msg, file=sys.stderr)

    def normalize_channel_url(self, channel: str) -> str:
        """Convert various channel formats to a proper URL"""
        channel = channel.strip()

        # Already a full URL
        if channel.startswith("http"):
            # Ensure we have /videos suffix for proper listing
            if "/videos" not in channel and "/shorts" not in channel and "/streams" not in channel:
                channel = channel.rstrip("/") + "/videos"
            return channel

        # Handle @username format
        if channel.startswith("@"):
            return f"https://www.youtube.com/{channel}/videos"

        # Handle channel ID (UC...)
        if channel.startswith("UC") and len(channel) == 24:
            return f"https://www.youtube.com/channel/{channel}/videos"

        # Assume it's a handle without @
        return f"https://www.youtube.com/@{channel}/videos"

    def get_channel_videos(
        self,
        channel_url: str,
        limit: Optional[int] = None,
        sort_by: str = "recency",
        search: Optional[str] = None,
        content_type: str = "videos",
        with_dates: bool = False,
    ) -> dict:
        """Get videos from a channel with optional filtering and sorting"""

        # Adjust URL for content type
        base_url = re.sub(r"/(videos|shorts|streams)/?$", "", channel_url)
        if content_type == "shorts":
            channel_url = base_url + "/shorts"
        elif content_type == "streams":
            channel_url = base_url + "/streams"
        else:
            channel_url = base_url + "/videos"

        self.log(f"Fetching: {channel_url}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': not with_dates,  # Flat is faster but less info
            'ignoreerrors': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.log("Extracting channel info...")
                info = ydl.extract_info(channel_url, download=False)

                if not info:
                    return {"error": "Could not fetch channel information"}

                entries = info.get('entries', [])
                if not entries:
                    return {"error": "No videos found"}

                # Convert generator to list if needed
                entries = list(entries)

                channel_name = info.get('channel', info.get('uploader', 'Unknown'))
                channel_id = info.get('channel_id', info.get('uploader_id', ''))
                total_count = len(entries)

                self.log(f"Found {total_count} items")

                # Process entries
                videos = []
                for i, entry in enumerate(entries):
                    if entry is None:
                        continue

                    video = {
                        "index": i + 1,
                        "id": entry.get('id', ''),
                        "title": entry.get('title', 'Unknown'),
                        "url": f"https://youtube.com/watch?v={entry.get('id', '')}",
                        "duration": entry.get('duration') or 0,
                        "duration_human": self._format_duration(entry.get('duration')),
                        "views": entry.get('view_count') or 0,
                    }

                    # Add upload date if available (slower fetch mode)
                    if with_dates and entry.get('upload_date'):
                        video["upload_date"] = entry.get('upload_date')

                    # Add description snippet if available
                    desc = entry.get('description', '')
                    if desc:
                        video["description_snippet"] = desc[:200] + "..." if len(desc) > 200 else desc

                    videos.append(video)

                # Filter by search term
                if search:
                    search_lower = search.lower()
                    videos = [
                        v for v in videos
                        if search_lower in v['title'].lower()
                        or search_lower in v.get('description_snippet', '').lower()
                    ]
                    self.log(f"Filtered to {len(videos)} videos matching '{search}'")

                # Sort
                if sort_by == "views":
                    videos.sort(key=lambda x: x['views'], reverse=True)
                elif sort_by == "duration":
                    videos.sort(key=lambda x: x['duration'], reverse=True)
                elif sort_by == "duration_asc":
                    videos.sort(key=lambda x: x['duration'])
                # recency is already the default order from YouTube

                # Apply limit
                if limit and limit > 0:
                    videos = videos[:limit]

                return {
                    "channel": channel_name,
                    "channel_id": channel_id,
                    "channel_url": base_url,
                    "content_type": content_type,
                    "total_count": total_count,
                    "returned_count": len(videos),
                    "sort": sort_by,
                    "search": search,
                    "videos": videos,
                }

        except yt_dlp.utils.DownloadError as e:
            return {"error": f"Download error: {str(e)}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

    def _format_duration(self, seconds: Optional[float]) -> str:
        """Convert seconds to human-readable duration"""
        if not seconds:
            return "0:00"
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"


def main():
    parser = argparse.ArgumentParser(
        description="Explore a YouTuber's channel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "@HealthyGamerGG"                    # List recent videos
  %(prog)s "@HealthyGamerGG" --limit 10         # Get 10 most recent
  %(prog)s "@HealthyGamerGG" --sort views       # Sort by view count
  %(prog)s "@HealthyGamerGG" --search "anxiety" # Search in titles
  %(prog)s "@HealthyGamerGG" --type shorts      # List shorts only
  %(prog)s "@HealthyGamerGG" --json             # Output as JSON
        """
    )
    parser.add_argument("channel", help="YouTube channel URL, @handle, or channel ID")
    parser.add_argument("--limit", "-n", type=int, default=20,
                        help="Number of videos to return (default: 20, use 0 for all)")
    parser.add_argument("--sort", "-s", choices=["recency", "views", "duration", "duration_asc"],
                        default="recency", help="Sort order (default: recency)")
    parser.add_argument("--search", "-q", help="Filter videos by title keyword")
    parser.add_argument("--type", "-t", choices=["videos", "shorts", "streams"],
                        default="videos", help="Content type (default: videos)")
    parser.add_argument("--with-dates", action="store_true",
                        help="Include upload dates (slower)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    parser.add_argument("--ids-only", action="store_true",
                        help="Output only video IDs (one per line)")

    args = parser.parse_args()

    explorer = YouTubeChannelExplorer(quiet=args.quiet or args.json or args.ids_only)

    channel_url = explorer.normalize_channel_url(args.channel)

    # Use 0 as "no limit"
    limit = args.limit if args.limit > 0 else None

    result = explorer.get_channel_videos(
        channel_url,
        limit=limit,
        sort_by=args.sort,
        search=args.search,
        content_type=args.type,
        with_dates=args.with_dates,
    )

    # Handle errors
    if "error" in result:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Output formats
    if args.ids_only:
        for video in result["videos"]:
            print(video["id"])
    elif args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        print(f"Channel: {result['channel']}")
        print(f"Total {result['content_type']}: {result['total_count']}")
        print(f"Showing: {result['returned_count']} (sorted by {result['sort']})")
        if result.get('search'):
            print(f"Search: '{result['search']}'")
        print("-" * 60)

        for video in result["videos"]:
            views_str = f"{video['views']:,}" if video['views'] else "N/A"
            print(f"{video['index']:3d}. [{video['duration_human']:>8}] {video['title'][:50]}")
            print(f"     {views_str} views | {video['url']}")
            print()


if __name__ == "__main__":
    main()
