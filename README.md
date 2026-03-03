# yt-dlp WebUI

A modern, cross-platform web-based frontend for yt-dlp, ported from the Windows/.NET yt-dlp-gui application.

## Features

- **Web-based UI** - Access from any device via browser
- **Video Analysis** - Get video info, thumbnails, formats, chapters, and subtitles
- **Format Selection** - Choose from best quality, audio-only, or custom formats
- **Advanced Options** - Proxy support, rate limiting, time range downloads
- **Download Management** - View progress, cancel, and delete downloads
- **File Browser** - Download completed files directly from the browser
- **Cross-platform** - Runs anywhere Docker is supported

## Requirements

- Docker
- Docker Compose

## Quick Start

```bash
# Clone or download the files
cd /path/to/ytdlp-webui

# Build and start the container
docker compose up -d

# Access the web UI
open http://localhost:8080
```

## Installation Modes

### Standalone (Direct Python)

```bash
# Install dependencies
pip install yt-dlp bottle

# Install ffmpeg (system package)
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg

# Run the server
python3 app.py
```

### Docker

```bash
# Build image
docker build -t ytdlp-webui .

# Run container
docker run -d -p 8080:8080 -v ./downloads:/app/downloads ytdlp-webui
```

### Docker Compose

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Usage

1. Enter a video URL in the URL field
2. Click "Analyze" to fetch video information
3. Select desired format (video quality, audio-only, etc.)
4. Click "Download" to start the download
5. Access downloaded files in the "Files" tab

## Advanced Options

| Option | Description |
|--------|-------------|
| Proxy | HTTP/HTTPS/SOCKS proxy URL |
| Rate Limit | Download speed limit (e.g., 1M, 500K) |
| Time Range | Download specific section (seconds, e.g., 0-60) |
| Embed Thumbnail | Embed video thumbnail in output file |
| Embed Chapters | Include chapter markers |
| Embed Subtitles | Burn subtitles into video |

## Supported Sites

yt-dlp supports thousands of video websites. For a full list, visit:
https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8080 | Server port |
| DOWNLOADS_DIR | /app/downloads | Download directory |

### Docker Volume Mounts

Mount local directories to persist data:

```yaml
volumes:
  - ./downloads:/app/downloads  # Downloaded files
```

## Security

The web UI runs without authentication. For production deployments:

1. Use a reverse proxy with authentication (nginx, Apache)
2. Implement network-level access controls
3. Consider VPN-only access
4. Use `--network` flag to isolate container

## Troubleshooting

### YouTube extraction fails

- Ensure Node.js is installed in the container
- Check network connectivity from container
- Try using `--force-ipv4` flag in yt-dlp commands

### Download fails

- Check ffmpeg is installed
- Verify write permissions on downloads directory
- Check container logs: `docker compose logs`

### Port already in use

Change the port in docker-compose.yaml:

```yaml
ports:
  - "8090:8080"
```

## Project Structure

```
ytdlp-webui/
├── app.py              # Bottle backend server
├── index.html          # Web frontend
├── Dockerfile          # Docker image definition
├── docker-compose.yaml # Docker Compose configuration
├── downloads/          # Downloaded files (created on first run)
└── README.md           # This file
```

## Credits

- Original yt-dlp-gui: https://github.com/Laelia-Succubus/yt-dlp-gui
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- Bottle: https://bottlepy.org/
