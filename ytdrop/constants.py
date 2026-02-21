"""
ytdrop.constants
~~~~~~~~~~~~~~~~
Application-wide constants.  No imports from other ytdrop modules so that
every other module can import from here without risk of circular dependency.
"""

APP_NAME    = "YTDrop"
APP_VERSION = "1.0.0"
APP_DATE    = "2025-02-18"

# ── Resolution slider ──────────────────────────────────────────────────────────
RESOLUTIONS: list[int] = [2160, 1440, 1080, 720, 480]
DEFAULT_RES_INDEX: int = 2   # 1080p

# ── yt-dlp default parameter strings ──────────────────────────────────────────
# {res} is substituted at runtime with the slider value.
DEFAULT_VIDEO_PARAMS = (
    "-f 'bestvideo[ext=mp4][height<={res}]+bestaudio[ext=m4a]"
    "/best[ext=mp4][height<={res}]/best'"
    ' -o "%(title)s.%(ext)s"'
)
DEFAULT_AUDIO_PARAMS = (
    "--extract-audio --audio-format mp3 --audio-quality 0"
    ' -o "%(title)s.%(ext)s"'
)
