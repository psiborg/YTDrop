#!/usr/bin/env bash
# ─────────────────────────────────────────────
#  YTDrop - yt-dlp GUI Launcher (Linux)
# ─────────────────────────────────────────────

set -euo pipefail

# Resolve the directory this script lives in
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="$SCRIPT_DIR/ytdrop.py"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ok()   { echo -e " ${GREEN}[OK]${NC}    $*"; }
warn() { echo -e " ${YELLOW}[WARN]${NC}  $*"; }
err()  { echo -e " ${RED}[ERROR]${NC} $*"; }
info() { echo -e " ${CYAN}[INFO]${NC}  $*"; }

echo ""
echo " ================================"
echo "   YTDrop - yt-dlp GUI Launcher"
echo " ================================"
echo ""

# ── Find Python 3 ─────────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            PYTHON="$candidate"
            ok "Python $ver found at $(command -v $candidate)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python 3.8+ is required but not found."
    echo ""
    echo " Install with your package manager, e.g.:"
    echo "   Ubuntu/Debian:  sudo apt install python3 python3-tk"
    echo "   Fedora:         sudo dnf install python3 python3-tkinter"
    echo "   Arch:           sudo pacman -S python tk"
    echo ""
    exit 1
fi

# ── Check tkinter ─────────────────────────────────────────────────────────────
if ! "$PYTHON" -c "import tkinter" &>/dev/null; then
    err "tkinter is not installed."
    echo ""
    echo " Install it with:"
    echo "   Ubuntu/Debian:  sudo apt install python3-tk"
    echo "   Fedora:         sudo dnf install python3-tkinter"
    echo "   Arch:           sudo pacman -S tk"
    echo ""
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
    echo "   sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \\"
    echo "        -o /usr/local/bin/yt-dlp && sudo chmod a+rx /usr/local/bin/yt-dlp"
    echo ""
    exit 1
fi
ok "yt-dlp found."

# ── Check ffmpeg (optional) ───────────────────────────────────────────────────
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg found."
else
    warn "ffmpeg not found. Audio extraction and video merging may fail."
    echo "        Install with: sudo apt install ffmpeg  (or your distro's equivalent)"
fi

# ── Check ytdrop.py ───────────────────────────────────────────────────────────
if [ ! -f "$APP" ]; then
    err "ytdrop.py not found in: $SCRIPT_DIR"
    echo " Please ensure launch.sh is in the same folder as ytdrop.py"
    exit 1
fi

# ── Launch ────────────────────────────────────────────────────────────────────
echo ""
info "Launching YTDrop..."
echo ""

# Detach from terminal so closing the terminal doesn't kill the app
nohup "$PYTHON" "$APP" >/dev/null 2>&1 &
disown
