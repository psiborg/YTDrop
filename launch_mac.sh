#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  YTDrop - yt-dlp GUI Launcher (macOS)
# ─────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$SCRIPT_DIR/ytdrop.py"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e " ${GREEN}[OK]${NC}    $*"; }
warn() { echo -e " ${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e " ${RED}[ERROR]${NC} $*"; }
info() { echo -e " ${CYAN}[INFO]${NC}  $*"; }

echo ""
echo " ================================"
echo "   YTDrop - yt-dlp GUI Launcher"
echo "          macOS Edition"
echo " ================================"
echo ""

# ── Find Python 3 ─────────────────────────────────────────────────────────────
# Prefer Homebrew / pyenv / user-installed Python over the system stub
PYTHON=""
SEARCH_PATHS=(
    "$HOME/.pyenv/shims/python3"
    "/opt/homebrew/bin/python3"    # Apple Silicon Homebrew
    "/usr/local/bin/python3"       # Intel Homebrew
    "/usr/bin/python3"             # system (macOS 12+)
    "python3"
    "python"
)

for candidate in "${SEARCH_PATHS[@]}"; do
    if command -v "$candidate" &>/dev/null 2>&1; then
        # Reject the macOS "developer tools" stub that just opens Xcode dialog
        if "$candidate" --version &>/dev/null 2>&1; then
            ver=$("$candidate" --version 2>&1 | awk '{print $2}')
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
                PYTHON="$candidate"
                ok "Python $ver found at $(command -v $candidate 2>/dev/null || echo $candidate)"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python 3.8+ is required but not found."
    echo ""
    echo " Recommended installation options:"
    echo "   Homebrew (recommended): brew install python"
    echo "   Official installer:     https://www.python.org/downloads/"
    echo ""
    # Offer to open the download page
    read -r -p " Open python.org in browser? [y/N] " resp
    if [[ "$resp" =~ ^[Yy]$ ]]; then
        open "https://www.python.org/downloads/"
    fi
    exit 1
fi

# ── Check tkinter ─────────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import tkinter" &>/dev/null 2>&1; then
    err "tkinter is not available for this Python installation."
    echo ""
    echo " On macOS, tkinter requires Tcl/Tk. Fix options:"
    echo "   Homebrew Python:  brew install python-tk"
    echo "                     (or: brew install python@3.12 && brew install python-tk@3.12)"
    echo "   Official Python:  reinstall from https://www.python.org/downloads/"
    echo "                     (bundles its own Tcl/Tk)"
    echo ""
    read -r -p " Open Homebrew python-tk page? [y/N] " resp
    if [[ "$resp" =~ ^[Yy]$ ]]; then
        open "https://formulae.brew.sh/formula/python-tk"
    fi
    exit 1
fi
ok "tkinter found."

# ── Check yt-dlp ─────────────────────────────────────────────
if ! command -v yt-dlp &>/dev/null 2>&1; then
    err "yt-dlp not found on PATH."
    echo ""
    echo " Download the standalone binary from:"
    echo "   https://github.com/yt-dlp/yt-dlp/releases/latest"
    echo ""
    echo " Quick install:"
    echo "   sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos \\"
    echo "        -o /usr/local/bin/yt-dlp && sudo chmod a+rx /usr/local/bin/yt-dlp"
    echo ""
    read -r -p " Open the yt-dlp releases page in your browser? [y/N] " resp
    if [[ "$resp" =~ ^[Yy]$ ]]; then
        open "https://github.com/yt-dlp/yt-dlp/releases/latest"
    fi
    exit 1
fi
ok "yt-dlp found."
    exit 1
fi

# ── Check ffmpeg (optional) ───────────────────────────────────────────────────
if command -v ffmpeg &>/dev/null 2>&1; then
    ok "ffmpeg found."
else
    warn "ffmpeg not found. Audio extraction and video merging may fail."
    echo "        Install with: brew install ffmpeg"
fi

# ── Check ytdrop.py ───────────────────────────────────────────────────────────
if [ ! -f "$APP" ]; then
    err "ytdrop.py not found in: $SCRIPT_DIR"
    echo " Please ensure launch_mac.sh is in the same folder as ytdrop.py"
    exit 1
fi

# ── macOS: use the framework Python if available ───────────────────────────────
# tkinter on macOS works best when launched via the framework build.
# pythonw is the windowing-capable wrapper on macOS.
PYTHONW=""
PY_BASE=$(dirname "$(command -v $PYTHON 2>/dev/null || echo $PYTHON)")

for pw_candidate in \
    "$PY_BASE/pythonw" \
    "$(python3 -c 'import sys; print(sys.base_prefix)' 2>/dev/null)/bin/pythonw" \
    "pythonw"; do
    if command -v "$pw_candidate" &>/dev/null 2>&1; then
        PYTHONW="$pw_candidate"
        break
    fi
done

# ── Launch ────────────────────────────────────────────────────────────────────
echo ""
info "Launching YTDrop..."
echo ""

if [ -n "$PYTHONW" ]; then
    # pythonw suppresses the dock icon flash and handles macOS GUI properly
    nohup "$PYTHONW" "$APP" >/dev/null 2>&1 &
else
    nohup "$PYTHON" "$APP" >/dev/null 2>&1 &
fi
disown
