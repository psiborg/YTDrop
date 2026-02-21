"""
ytdrop.themes
~~~~~~~~~~~~~
Theme data and the VSCode theme importer.  Deliberately tkinter-free so it
can be imported and tested without a display.

Public API
----------
BUILTIN_THEMES          dict[name → theme_dict]
vscode_theme_to_ytdrop(path) → (name, theme_dict)

Theme dict keys
---------------
bg  bg2  bg3          background tiers (main / toolbar / deep)
fg  fg2              foreground (primary / muted)
accent  accent2      highlight colour and its hover variant
btn  btn_hover       button background (normal / hover)
border               widget border / separator
success  error  warn  status colours for output console tags
entry_bg             text-input / scrolled-text background
sel_bg               selection highlight background
"""

import json
import re
from pathlib import Path

# ── Theme palette registry ─────────────────────────────────────────────────────
# All hex values are lowercase #rrggbb.  Every theme must supply all 15 keys.

BUILTIN_THEMES: dict[str, dict[str, str]] = {
    # ── Dark ──────────────────────────────────────────────────────────────────
    "Catppuccin Mocha": {
        "bg": "#1e1e2e", "bg2": "#2a2a3e", "bg3": "#313145",
        "fg": "#cdd6f4", "fg2": "#a6adc8",
        "accent": "#89b4fa", "accent2": "#74c7ec",
        "btn": "#313145", "btn_hover": "#45475a", "border": "#45475a",
        "success": "#a6e3a1", "error": "#f38ba8", "warn": "#fab387",
        "entry_bg": "#181825", "sel_bg": "#45475a",
    },
    "One Dark Pro": {
        "bg": "#282c34", "bg2": "#21252b", "bg3": "#2c313a",
        "fg": "#abb2bf", "fg2": "#636d83",
        "accent": "#61afef", "accent2": "#56b6c2",
        "btn": "#2c313a", "btn_hover": "#3e4452", "border": "#3e4452",
        "success": "#98c379", "error": "#e06c75", "warn": "#e5c07b",
        "entry_bg": "#1e2227", "sel_bg": "#3e4452",
    },
    "Tokyo Night": {
        "bg": "#1a1b26", "bg2": "#16161e", "bg3": "#1f2335",
        "fg": "#c0caf5", "fg2": "#565f89",
        "accent": "#7aa2f7", "accent2": "#7dcfff",
        "btn": "#1f2335", "btn_hover": "#292e42", "border": "#292e42",
        "success": "#9ece6a", "error": "#f7768e", "warn": "#e0af68",
        "entry_bg": "#13141c", "sel_bg": "#283457",
    },
    "Dracula": {
        "bg": "#282a36", "bg2": "#21222c", "bg3": "#343746",
        "fg": "#f8f8f2", "fg2": "#6272a4",
        "accent": "#bd93f9", "accent2": "#8be9fd",
        "btn": "#343746", "btn_hover": "#44475a", "border": "#44475a",
        "success": "#50fa7b", "error": "#ff5555", "warn": "#ffb86c",
        "entry_bg": "#1e1f29", "sel_bg": "#44475a",
    },
    "Nord": {
        "bg": "#2e3440", "bg2": "#3b4252", "bg3": "#434c5e",
        "fg": "#eceff4", "fg2": "#d8dee9",
        "accent": "#88c0d0", "accent2": "#81a1c1",
        "btn": "#434c5e", "btn_hover": "#4c566a", "border": "#4c566a",
        "success": "#a3be8c", "error": "#bf616a", "warn": "#ebcb8b",
        "entry_bg": "#242933", "sel_bg": "#4c566a",
    },
    "GitHub Dark": {
        "bg": "#0d1117", "bg2": "#161b22", "bg3": "#1c2128",
        "fg": "#e6edf3", "fg2": "#8b949e",
        "accent": "#58a6ff", "accent2": "#79c0ff",
        "btn": "#21262d", "btn_hover": "#30363d", "border": "#30363d",
        "success": "#3fb950", "error": "#f85149", "warn": "#d29922",
        "entry_bg": "#010409", "sel_bg": "#1f6feb",
    },
    "Gruvbox Dark": {
        "bg": "#282828", "bg2": "#3c3836", "bg3": "#504945",
        "fg": "#ebdbb2", "fg2": "#a89984",
        "accent": "#458588", "accent2": "#689d6a",
        "btn": "#3c3836", "btn_hover": "#504945", "border": "#665c54",
        "success": "#b8bb26", "error": "#cc241d", "warn": "#d79921",
        "entry_bg": "#1d2021", "sel_bg": "#504945",
    },
    "Monokai": {
        "bg": "#272822", "bg2": "#1e1f1c", "bg3": "#32332d",
        "fg": "#f8f8f2", "fg2": "#75715e",
        "accent": "#66d9e8", "accent2": "#a6e22e",
        "btn": "#32332d", "btn_hover": "#3e3d32", "border": "#3e3d32",
        "success": "#a6e22e", "error": "#f92672", "warn": "#e6db74",
        "entry_bg": "#1a1b16", "sel_bg": "#49483e",
    },
    "Solarized Dark": {
        "bg": "#002b36", "bg2": "#073642", "bg3": "#073642",
        "fg": "#839496", "fg2": "#657b83",
        "accent": "#268bd2", "accent2": "#2aa198",
        "btn": "#073642", "btn_hover": "#0a4155", "border": "#586e75",
        "success": "#859900", "error": "#dc322f", "warn": "#b58900",
        "entry_bg": "#00212b", "sel_bg": "#0a4155",
    },
    "Material Dark": {
        "bg": "#212121", "bg2": "#292929", "bg3": "#353535",
        "fg": "#eeffff", "fg2": "#89ddff",
        "accent": "#82aaff", "accent2": "#21c7a8",
        "btn": "#2d2d2d", "btn_hover": "#3a3a3a", "border": "#404040",
        "success": "#c3e88d", "error": "#f07178", "warn": "#ffcb6b",
        "entry_bg": "#1a1a1a", "sel_bg": "#3b3b3b",
    },
    # ── Light ─────────────────────────────────────────────────────────────────
    "Catppuccin Latte": {
        "bg": "#eff1f5", "bg2": "#e6e9ef", "bg3": "#dce0e8",
        "fg": "#4c4f69", "fg2": "#6c6f85",
        "accent": "#1e66f5", "accent2": "#04a5e5",
        "btn": "#dce0e8", "btn_hover": "#ccd0da", "border": "#bcc0cc",
        "success": "#40a02b", "error": "#d20f39", "warn": "#fe640b",
        "entry_bg": "#ffffff", "sel_bg": "#ccd0da",
    },
    "GitHub Light": {
        "bg": "#ffffff", "bg2": "#f6f8fa", "bg3": "#eaeef2",
        "fg": "#1f2328", "fg2": "#656d76",
        "accent": "#0969da", "accent2": "#218bff",
        "btn": "#f6f8fa", "btn_hover": "#eaeef2", "border": "#d0d7de",
        "success": "#1a7f37", "error": "#cf222e", "warn": "#9a6700",
        "entry_bg": "#ffffff", "sel_bg": "#ddf4ff",
    },
    "Solarized Light": {
        "bg": "#fdf6e3", "bg2": "#eee8d5", "bg3": "#ddd8c5",
        "fg": "#657b83", "fg2": "#839496",
        "accent": "#268bd2", "accent2": "#2aa198",
        "btn": "#eee8d5", "btn_hover": "#ddd8c5", "border": "#93a1a1",
        "success": "#859900", "error": "#dc322f", "warn": "#b58900",
        "entry_bg": "#fdf6e3", "sel_bg": "#d3cbb6",
    },
    "Gruvbox Light": {
        "bg": "#fbf1c7", "bg2": "#f2e5bc", "bg3": "#ebdbb2",
        "fg": "#3c3836", "fg2": "#7c6f64",
        "accent": "#076678", "accent2": "#427b58",
        "btn": "#ebdbb2", "btn_hover": "#d5c4a1", "border": "#bdae93",
        "success": "#79740e", "error": "#9d0006", "warn": "#b57614",
        "entry_bg": "#f9f5d7", "sel_bg": "#d5c4a1",
    },
    "One Light": {
        "bg": "#fafafa", "bg2": "#f0f0f0", "bg3": "#e5e5e6",
        "fg": "#383a42", "fg2": "#696c77",
        "accent": "#4078f2", "accent2": "#0184bc",
        "btn": "#e5e5e6", "btn_hover": "#d4d4d5", "border": "#c2c2c3",
        "success": "#50a14f", "error": "#e45649", "warn": "#c18401",
        "entry_bg": "#ffffff", "sel_bg": "#bfceff",
    },
}

# ── Colour math helpers ────────────────────────────────────────────────────────

def hex_normalize(color: str) -> str:
    """
    Convert any VSCode hex colour to lowercase ``#rrggbb``.
    Handles #RGB, #RGBA, #RRGGBB, #RRGGBBAA.  Returns ``""`` on failure.
    """
    if not color or not isinstance(color, str) or not color.startswith("#"):
        return ""
    h = color.lstrip("#")
    if len(h) == 3:   h = "".join(c * 2 for c in h)        # #RGB  → #RRGGBB
    elif len(h) == 4: h = "".join(c * 2 for c in h[:3])    # #RGBA → #RRGGBB
    elif len(h) == 8: h = h[:6]                             # #RRGGBBAA → #RRGGBB
    if len(h) != 6:
        return ""
    try:
        int(h, 16)
    except ValueError:
        return ""
    return "#" + h.lower()


def luminance(hex_color: str) -> float:
    """WCAG relative luminance of a ``#rrggbb`` colour (0 = black, 1 = white)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def blend(hex_a: str, hex_b: str, t: float) -> str:
    """
    Linear-interpolate between two ``#rrggbb`` colours.
    ``t=0`` → *hex_a*, ``t=1`` → *hex_b*.
    """
    def parts(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r1, g1, b1 = parts(hex_a)
    r2, g2, b2 = parts(hex_b)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── VSCode → YTDrop slot mapping ───────────────────────────────────────────────
# Each entry is a priority-ordered list of VSCode colour keys.
# The importer tries each in turn and uses the first valid hex it finds.

_VSCODE_MAP: dict[str, list[str]] = {
    "entry_bg": ["editor.background", "input.background"],
    "fg":       ["editor.foreground", "foreground"],
    "bg":       ["sideBar.background", "panel.background", "editor.background"],
    "bg2":      ["titleBar.activeBackground", "tab.activeBackground",
                 "sideBarSectionHeader.background"],
    "bg3":      ["activityBar.background", "statusBar.background",
                 "sideBarSectionHeader.background"],
    "accent":   ["button.background", "focusBorder", "terminal.ansiBrightBlue",
                 "activityBarBadge.background"],
    "accent2":  ["button.hoverBackground", "terminal.ansiCyan",
                 "terminal.ansiBrightCyan", "editorLink.activeForeground"],
    "fg2":      ["statusBar.foreground", "tab.inactiveForeground",
                 "sideBar.foreground", "descriptionForeground"],
    "btn":      ["tab.activeBackground", "button.secondaryBackground",
                 "input.background"],
    "btn_hover":["list.hoverBackground", "list.activeSelectionBackground"],
    "border":   ["focusBorder", "panel.border", "editorGroup.border",
                 "input.border", "widget.border"],
    "sel_bg":   ["list.activeSelectionBackground", "editor.selectionBackground",
                 "list.focusBackground"],
    "success":  ["gitDecoration.addedResourceForeground", "terminal.ansiGreen",
                 "terminal.ansiBrightGreen", "notificationsInfoIcon.foreground"],
    "error":    ["editorError.foreground", "statusBarItem.errorBackground",
                 "terminal.ansiRed", "terminal.ansiBrightRed",
                 "inputValidation.errorBorder"],
    "warn":     ["editorWarning.foreground", "terminal.ansiYellow",
                 "terminal.ansiBrightYellow", "inputValidation.warningBorder"],
}


# ── JSONC parser ───────────────────────────────────────────────────────────────

def _strip_jsonc(text: str) -> str:
    """
    Remove JSONC ``//`` and ``/* */`` comments and trailing commas without
    touching any ``//`` sequences inside quoted string values (e.g. the
    ``vscode://schemas/color-theme`` URI in ``$schema`` fields).
    """
    result: list[str] = []
    i, n = 0, len(text)
    in_string = False

    while i < n:
        ch = text[i]
        if in_string:
            result.append(ch)
            if ch == "\\" and i + 1 < n:   # escape: consume next char verbatim
                i += 1
                result.append(text[i])
            elif ch == '"':
                in_string = False
            i += 1
        else:
            if ch == "/" and i + 1 < n and text[i + 1] == "/":
                while i < n and text[i] != "\n":   # single-line comment
                    i += 1
            elif ch == "/" and i + 1 < n and text[i + 1] == "*":
                i += 2
                while i < n - 1 and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2                              # block comment
            elif ch == '"':
                in_string = True
                result.append(ch)
                i += 1
            else:
                result.append(ch)
                i += 1

    cleaned = "".join(result)
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)   # trailing commas
    return cleaned


# ── Public importer ────────────────────────────────────────────────────────────

def vscode_theme_to_ytdrop(path: str) -> tuple[str, dict[str, str]]:
    """
    Parse a VSCode ``.json`` / ``.jsonc`` theme file and return
    ``(theme_name, theme_dict)``.

    Raises ``ValueError`` with a human-readable message on parse failure.
    Missing colour slots are filled in via colour-math derivation so the
    result always contains all 15 required keys.
    """
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    raw = _strip_jsonc(raw)

    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse theme file:\n{exc}") from exc

    colors: dict = data.get("colors", {})
    if not isinstance(colors, dict):
        raise ValueError("Theme file has no 'colors' section.")

    def pick(*keys: str) -> str:
        for k in keys:
            v = hex_normalize(colors.get(k, ""))
            if v:
                return v
        return ""

    result: dict[str, str] = {slot: pick(*keys) for slot, keys in _VSCODE_MAP.items()}

    # ── Derive any still-missing slots ────────────────────────────────────────
    bg     = result.get("bg") or result.get("entry_bg") or "#1e1e2e"
    fg     = result.get("fg") or "#cccccc"
    accent = result.get("accent") or "#569cd6"
    dark   = luminance(bg) < 0.5
    mix    = 0.15 if dark else 0.08
    white_or_black = "#000000" if dark else "#ffffff"

    defaults = {
        "bg":        bg,
        "fg":        fg,
        "entry_bg":  bg,
        "bg2":       blend(bg, white_or_black, mix),
        "bg3":       blend(bg, white_or_black, mix * 2),
        "fg2":       blend(fg, bg, 0.35),
        "accent":    accent,
        "accent2":   blend(accent, fg, 0.3),
    }
    for k, v in defaults.items():
        if not result.get(k):
            result[k] = v

    if not result.get("btn"):       result["btn"]       = result["bg3"]
    if not result.get("btn_hover"): result["btn_hover"] = blend(result["bg3"], fg, 0.15)
    if not result.get("border"):    result["border"]    = blend(bg, fg, 0.25)
    if not result.get("sel_bg"):    result["sel_bg"]    = blend(accent, bg, 0.6)
    if not result.get("success"):   result["success"]   = "#3fb950" if dark else "#1a7f37"
    if not result.get("error"):     result["error"]     = "#f85149" if dark else "#cf222e"
    if not result.get("warn"):      result["warn"]      = "#d29922" if dark else "#9a6700"

    name: str = data.get("name") or Path(path).stem
    return name, result
