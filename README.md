# yt-get

A simple wrapper around `yt-dlp` for downloading YouTube videos and playlists with sensible defaults.

## Features

- Download videos in best quality (with multiple audio tracks and subtitles)
- Download audio-only in AAC format
- Process multiple URLs at once
- Read URLs from a file
- Geo-bypass support (though YouTube typically ignores this argument)
- Automatic `yt-dlp` updates (weekly check)
- Organized output: playlists saved in separate folders

## Requirements

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager
- FFmpeg (for audio extraction and subtitle embedding)

## Installation

```bash
# Clone the repository
git clone https://github.com/TuvQuarc/yt-get.git
cd yt-get

# Install dependencies
uv sync
```

## Usage

### Download a single video

```bash
uv run yt-get.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download audio only

```bash
uv run yt-get.py -a "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download a playlist

```bash
uv run yt-get.py "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

### Download multiple URLs

```bash
uv run yt-get.py "URL1" "URL2" "URL3"
```

### Download from a file with URLs

```bash
uv run yt-get.py -i urls.txt
```

File format (one URL per line, `#` or `;` for comments):

```
# My favorite videos
https://www.youtube.com/watch?v=VIDEO_ID1
https://www.youtube.com/watch?v=VIDEO_ID2
; This is also a comment
```

### Use geo-bypass

```bash
uv run yt-get.py -g US "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Update yt-dlp manually

```bash
uv run yt-get.py -u
```

## Options

- `-a`, `--audio-only` - Download only audio
- `-i`, `--input-file FILE` - Read URLs from file
- `-u`, `--update` - Update embedded yt-dlp before downloading
- `-g`, `--geo-bypass CODE` - Geo-bypass country code (two-letter ISO 3166-2)

## Output Format

**Single videos:**

```
Channel Name - Video Title.mkv
```

**Playlists:**

```
Channel Name - Playlist Title/
├── 001 - First Video.mkv
├── 002 - Second Video.mkv
└── ...
```
