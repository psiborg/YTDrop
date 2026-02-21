"""
ytdrop.config
~~~~~~~~~~~~~
Persistent configuration: load from / save to ~/.ytdrop_config.json.

Owns the canonical default values and handles one-time migration of the
legacy ``"theme": "dark"/"light"`` key to the newer ``"theme_name"`` key.
"""

import json
from pathlib import Path

from .constants import DEFAULT_VIDEO_PARAMS, DEFAULT_AUDIO_PARAMS

CONFIG_FILE: Path = Path.home() / ".ytdrop_config.json"

# Maps the old two-value "theme" field to a built-in theme name.
_LEGACY_THEME_MAP: dict[str, str] = {
    "dark":  "Catppuccin Mocha",
    "light": "Catppuccin Latte",
}

_DEFAULTS: dict = {
    "theme_name":   "Catppuccin Mocha",
    "theme_custom": {},          # imported VSCode themes stored here
    "cookie_file":  "",
    "video_params": DEFAULT_VIDEO_PARAMS,
    "audio_params": DEFAULT_AUDIO_PARAMS,
    "download_dir": str(Path.home() / "Downloads"),
}


def load_config() -> dict:
    """
    Return the merged config dict (file values overlaid on defaults).
    Silently ignores a missing or malformed config file.
    """
    cfg = dict(_DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as fh:
                saved: dict = json.load(fh)
            # ── one-time migration ─────────────────────────────────────────────
            if "theme" in saved and "theme_name" not in saved:
                saved["theme_name"] = _LEGACY_THEME_MAP.get(
                    saved.pop("theme"), "Catppuccin Mocha"
                )
            cfg.update(saved)
        except Exception:
            pass
    return cfg


def save_config(cfg: dict) -> None:
    """Persist *cfg* to disk.  Prints a warning on failure (non-fatal)."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2)
    except Exception as exc:
        print(f"[YTDrop] Could not save config: {exc}")
