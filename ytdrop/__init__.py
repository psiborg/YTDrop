"""
ytdrop
~~~~~~
YTDrop — a cross-platform GUI frontend for yt-dlp.

Run with::

    python -m ytdrop

or via the backward-compatible shim::

    python ytdrop.py
"""

from .constants import APP_NAME, APP_VERSION, APP_DATE

__all__ = ["APP_NAME", "APP_VERSION", "APP_DATE"]
