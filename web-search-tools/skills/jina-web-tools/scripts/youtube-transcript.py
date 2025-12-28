#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp", "pyperclip", "requests"]
# ///
"""
youtube-transcript.py - Download YouTube video transcripts

Usage:
    uv run youtube-transcript.py "https://youtube.com/watch?v=..."
    uv run youtube-transcript.py "https://youtube.com/watch?v=..." --lang zh-Hant
    uv run youtube-transcript.py "https://youtube.com/watch?v=..." --json
    uv run youtube-transcript.py "https://youtube.com/watch?v=..." --list-langs
"""

import argparse
import json
import re
import sys
from typing import Optional

import requests
import yt_dlp


class YouTubeTranscriptDownloader:
    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.ydl_opts = {
            'writeautomaticsub': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

    def log(self, msg: str):
        if not self.quiet:
            print(msg, file=sys.stderr)

    def extract_video_id(self, url: str) -> Optional[str]:
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_transcript(self, video_url: str, preferred_lang: Optional[str] = None) -> dict:
        """Get transcript and metadata"""
        self.log(f"Processing: {video_url}")

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                self.log("Fetching video info...")
                info = ydl.extract_info(video_url, download=False)

                title = info.get('title', 'Unknown')
                video_id = info.get('id', '')
                duration = info.get('duration', 0)
                channel = info.get('channel', info.get('uploader', 'Unknown'))

                self.log(f"Title: {title}")

                # Get captions
                auto_captions = info.get('automatic_captions', {})
                subtitles = info.get('subtitles', {})

                # Merge manual subtitles (they take priority)
                all_captions = {**auto_captions, **subtitles}

                if not all_captions:
                    return {"error": "No subtitles available for this video"}

                available_langs = list(all_captions.keys())

                # Select language
                selected_lang = None
                original_lang = info.get('language') or info.get('original_language')

                if preferred_lang:
                    if preferred_lang in all_captions:
                        selected_lang = preferred_lang
                    else:
                        # Partial match
                        for lang in all_captions:
                            if preferred_lang.lower() in lang.lower():
                                selected_lang = lang
                                break
                        if not selected_lang:
                            return {
                                "error": f"Language '{preferred_lang}' not found",
                                "available_languages": available_langs
                            }
                else:
                    # Auto-select: original language > English > first available
                    if original_lang and original_lang in all_captions:
                        selected_lang = original_lang
                    else:
                        for lang in ['en', 'en-US', 'en-GB']:
                            if lang in all_captions:
                                selected_lang = lang
                                break
                        if not selected_lang:
                            selected_lang = available_langs[0]

                self.log(f"Using language: {selected_lang}")

                # Get subtitle URL
                caption_url = None
                caption_format = None

                for caption in all_captions[selected_lang]:
                    ext = caption.get('ext')
                    if ext == 'vtt':
                        caption_url = caption['url']
                        caption_format = 'vtt'
                        break

                if not caption_url:
                    for caption in all_captions[selected_lang]:
                        ext = caption.get('ext')
                        if ext in ['srv1', 'srv2', 'srv3', 'json3']:
                            caption_url = caption['url']
                            caption_format = ext
                            break

                if not caption_url:
                    return {"error": "Could not get subtitle URL"}

                # Download subtitle
                self.log(f"Downloading subtitles ({caption_format})...")
                response = requests.get(caption_url)
                response.raise_for_status()

                # Parse
                if caption_format == 'json3':
                    transcript = self._parse_json3(response.text)
                else:
                    transcript = self._parse_vtt(response.text)

                return {
                    "title": title,
                    "video_id": video_id,
                    "channel": channel,
                    "duration": duration,
                    "language": selected_lang,
                    "available_languages": available_langs,
                    "transcript": transcript
                }

            except yt_dlp.utils.DownloadError as e:
                return {"error": f"Download error: {str(e)}"}
            except Exception as e:
                return {"error": f"Error: {str(e)}"}

    def _parse_vtt(self, text: str) -> str:
        # Handle M3U8 playlist
        if text.startswith('#EXTM3U'):
            urls = re.findall(r'https://[^\s]+', text)
            if urls:
                try:
                    response = requests.get(urls[0])
                    text = response.text
                except:
                    pass

        lines = []
        for line in text.split('\n'):
            if line.startswith('WEBVTT'):
                continue
            if '-->' in line:
                continue
            if not line.strip() or line.strip().isdigit():
                continue

            # Clean HTML tags
            clean = re.sub('<[^>]+>', '', line)
            clean = clean.replace('&nbsp;', ' ')
            clean = clean.replace('&amp;', '&')
            clean = clean.replace('&lt;', '<')
            clean = clean.replace('&gt;', '>')
            clean = clean.replace('&quot;', '"')

            if clean.strip():
                lines.append(clean.strip())

        # Remove consecutive duplicates
        result = []
        prev = None
        for line in lines:
            if line != prev:
                result.append(line)
                prev = line

        return '\n'.join(result)

    def _parse_json3(self, text: str) -> str:
        try:
            data = json.loads(text)
            lines = []

            if 'events' in data:
                for event in data['events']:
                    if 'segs' not in event:
                        continue
                    parts = []
                    for seg in event.get('segs', []):
                        if 'utf8' in seg:
                            parts.append(seg['utf8'])
                    if parts:
                        line = ''.join(parts).strip()
                        if line:
                            lines.append(line)

            # Remove consecutive duplicates
            result = []
            prev = None
            for line in lines:
                if line != prev:
                    result.append(line)
                    prev = line

            return '\n'.join(result)

        except json.JSONDecodeError:
            return self._parse_vtt(text)


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube video transcripts"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--lang", "-l", help="Preferred language code (e.g., en, zh-Hant)")
    parser.add_argument("--list-langs", action="store_true", help="List available languages")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--copy", action="store_true", help="Copy to clipboard")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress messages")

    args = parser.parse_args()

    downloader = YouTubeTranscriptDownloader(quiet=args.quiet or args.json)

    # Validate URL
    video_id = downloader.extract_video_id(args.url)
    if not video_id:
        print("Error: Invalid YouTube URL", file=sys.stderr)
        sys.exit(1)

    result = downloader.get_transcript(args.url, preferred_lang=args.lang)

    # Handle errors
    if "error" in result:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            if "available_languages" in result:
                print(f"Available: {', '.join(result['available_languages'])}", file=sys.stderr)
        sys.exit(1)

    # List languages only
    if args.list_langs:
        if args.json:
            print(json.dumps({"available_languages": result["available_languages"]}, indent=2))
        else:
            print("Available languages:")
            for lang in result["available_languages"]:
                print(f"  {lang}")
        sys.exit(0)

    # Output
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["transcript"])

    # Copy to clipboard
    if args.copy:
        try:
            import pyperclip
            pyperclip.copy(result["transcript"])
            print("\nCopied to clipboard!", file=sys.stderr)
        except Exception as e:
            print(f"\nCould not copy to clipboard: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
