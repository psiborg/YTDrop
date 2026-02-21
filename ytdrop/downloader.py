"""
ytdrop.downloader
~~~~~~~~~~~~~~~~~
All yt-dlp interaction: command building, subprocess streaming, log file
management, title fetching, and cancellation.

The ``Downloader`` class is deliberately tkinter-free.  It communicates
back to the UI exclusively through three callbacks supplied at construction:

    write_output(text, tag=None)   — append text to the output console
    set_status(text)               — update the status bar label
    on_done()                      — called when a fetch/list run finishes
                                     (re-enables buttons, etc.)

This separation means the downloader can be unit-tested without a display.
"""

import re
import shlex
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from .constants import (
    DEFAULT_AUDIO_PARAMS,
    DEFAULT_VIDEO_PARAMS,
    RESOLUTIONS,
)


class Downloader:
    """
    Manages one concurrent yt-dlp operation at a time.

    Parameters
    ----------
    write_output : callable(text, tag=None)
        Send a line of text (with an optional colour tag) to the UI console.
    set_status : callable(text)
        Update the one-line status bar in the UI.
    on_done : callable()
        Called on the main thread when the current operation finishes or is
        cancelled.  Typically re-enables the Fetch button.
    """

    def __init__(
        self,
        write_output: Callable[[str, str | None], None],
        set_status:   Callable[[str], None],
        on_done:      Callable[[], None],
    ) -> None:
        self._write_output   = write_output
        self._set_status     = set_status
        self._on_done        = on_done

        self._proc:            subprocess.Popen | None = None
        self._cancel_event:    threading.Event         = threading.Event()
        self._current_log_fh                           = None   # open file handle

    # ── Public interface ───────────────────────────────────────────────────────

    def fetch(
        self,
        urls:         list[str],
        want_video:   bool,
        want_audio:   bool,
        config:       dict,
        use_cookie:   bool,
        res_index:    int,
    ) -> None:
        """
        Start a threaded download run for *urls*.
        Silently ignores calls when no mode is selected or url list is empty.
        """
        if not urls or (not want_video and not want_audio):
            return

        self._cancel_event.clear()
        modes = (["video"] if want_video else []) + (["audio"] if want_audio else [])

        threading.Thread(
            target=self._fetch_worker,
            args=(urls, modes, config, use_cookie, res_index),
            daemon=True,
        ).start()

    def list_formats(
        self,
        urls:       list[str],
        config:     dict,
        use_cookie: bool,
    ) -> None:
        """Start a threaded ``yt-dlp --list-formats`` run for *urls*."""
        if not urls:
            return
        self._cancel_event.clear()
        threading.Thread(
            target=self._list_formats_worker,
            args=(urls, config, use_cookie),
            daemon=True,
        ).start()

    def cancel(self) -> None:
        """Signal cancellation and kill the running subprocess immediately."""
        self._cancel_event.set()
        self._kill_proc()
        self._close_log()

    @property
    def is_running(self) -> bool:
        """True while a subprocess is active."""
        return self._proc is not None

    # ── Worker threads ─────────────────────────────────────────────────────────

    def _fetch_worker(
        self,
        urls:      list[str],
        modes:     list[str],
        config:    dict,
        use_cookie:bool,
        res_index: int,
    ) -> None:
        total    = len(urls)
        out_dir  = config.get("download_dir", str(Path.home() / "Downloads"))

        for i, url in enumerate(urls, 1):
            if self._cancel_event.is_set():
                break
            for mode in modes:
                if self._cancel_event.is_set():
                    break

                self._set_status(f"Downloading {i}/{total} [{mode}]: {url[:60]}…")
                cmd = self._build_cmd(url, mode, config, use_cookie, res_index)

                title_stem = self._fetch_title(url, config, use_cookie)
                if not title_stem:
                    title_stem = re.sub(r'[\\/:*?"<>|&=?]', "_", url)[-120:]

                self._open_log(out_dir, title_stem, mode)
                rc = self._run_cmd_streaming(cmd)
                self._close_log()

                if rc == -2:
                    break
                elif rc == 0:
                    self._write_output(f"✓ Done [{mode}]: {url}\n", "success")
                elif rc != -1:          # -1 already printed its own error
                    self._write_output(
                        f"✗ Failed (code {rc}) [{mode}]: {url}\n", "error"
                    )

        if self._cancel_event.is_set():
            self._set_status("Cancelled.")
        else:
            self._set_status("All downloads complete.")
            self._write_output("\n✓ All tasks finished.\n", "success")

        self._on_done()

    def _list_formats_worker(
        self,
        urls:       list[str],
        config:     dict,
        use_cookie: bool,
    ) -> None:
        self._set_status("Listing formats…")
        out_dir = config.get("download_dir", str(Path.home() / "Downloads"))

        for url in urls:
            if self._cancel_event.is_set():
                break
            cmd = ["yt-dlp", "--list-formats"]
            if use_cookie:
                cf = config.get("cookie_file", "")
                if cf:
                    cmd += ["--cookies", cf]
            cmd.append(url)

            safe = re.sub(r'[\\/:*?"<>|]', "_", url)[:120]
            self._open_log(out_dir, safe, "list-formats")
            self._run_cmd_streaming(cmd)
            self._close_log()

        self._set_status("Done listing formats.")
        self._on_done()

    # ── Command builder ────────────────────────────────────────────────────────

    def _build_cmd(
        self,
        url:        str,
        mode:       str,
        config:     dict,
        use_cookie: bool,
        res_index:  int,
    ) -> list[str]:
        cmd     = ["yt-dlp"]
        out_dir = config.get("download_dir", str(Path.home() / "Downloads"))

        if use_cookie:
            cf = config.get("cookie_file", "")
            if cf:
                cmd += ["--cookies", cf]

        res = RESOLUTIONS[res_index]
        if mode == "audio":
            params = config.get("audio_params", DEFAULT_AUDIO_PARAMS)
        else:
            params = config.get("video_params", DEFAULT_VIDEO_PARAMS)
            params = params.replace("{res}", str(res))

        # Inject the output directory into the -o template using a callable
        # replacer so yt-dlp tokens like %(title)s are never mis-parsed as
        # regex group references.
        def _inject_dir(m: re.Match) -> str:
            return f'-o "{out_dir}/{m.group(1)}"'

        new_params = re.sub(r'-o\s+["\']([^"\']+)["\']', _inject_dir, params)
        if new_params == params:
            new_params = re.sub(r"-o\s+(\S+)", _inject_dir, params)
        params = new_params

        try:
            extra = shlex.split(params)
        except ValueError:
            extra = params.split()

        cmd += extra
        cmd.append(url)
        return cmd

    # ── Subprocess streaming ───────────────────────────────────────────────────

    def _run_cmd_streaming(self, cmd: list[str]) -> int:
        """
        Run *cmd*, stream output to the UI console (and current log file),
        and return the exit code.

        Return values
        -------------
        ≥0   yt-dlp exit code
        -1   yt-dlp binary not found, or other launch error
        -2   cancelled by user
        """
        self._write_output(f"\n$ {' '.join(cmd)}\n", "info")
        if self._current_log_fh:
            try:
                self._current_log_fh.write(f"$ {' '.join(cmd)}\n\n")
                self._current_log_fh.flush()
            except Exception:
                pass

        kwargs: dict = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            self._proc = subprocess.Popen(cmd, **kwargs)

            for raw_line in self._proc.stdout:
                if self._cancel_event.is_set():
                    self._kill_proc()
                    self._write_output("\n⚠ Download cancelled by user.\n", "warn")
                    return -2

                stripped = raw_line.rstrip()
                tag      = self._classify_line(stripped)
                self._write_output(stripped + "\n", tag)

            self._proc.wait()
            rc = self._proc.returncode
            return -2 if self._cancel_event.is_set() else rc

        except FileNotFoundError:
            self._write_output(
                "ERROR: yt-dlp not found. Please install it: pip install yt-dlp\n",
                "error",
            )
            return -1
        except Exception as exc:
            self._write_output(f"ERROR: {exc}\n", "error")
            return -1
        finally:
            self._proc = None

    @staticmethod
    def _classify_line(line: str) -> str | None:
        """Return an output-console colour tag for *line*, or None."""
        low = line.lower()
        if any(k in low for k in ("error", "got error")):
            return "error"
        if any(k in low for k in ("warning", "retrying", "skipping fragment",
                                   "has already been downloaded")):
            return "warn"
        if line.startswith("[ExtractAudio]") or "Destination" in line:
            return "success"
        return None   # progress lines and generic info get no colour

    def _kill_proc(self) -> None:
        """Terminate the active subprocess as quickly as possible."""
        proc = self._proc
        if proc is None:
            return
        try:
            if sys.platform == "win32":
                proc.kill()
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass

    # ── Title fetcher (for log-file naming) ───────────────────────────────────

    def _fetch_title(self, url: str, config: dict, use_cookie: bool) -> str:
        """
        Run ``yt-dlp --print title`` (no download) to get the video title.
        Returns ``""`` on any failure; a 15-second timeout guards against hangs.
        """
        cmd = ["yt-dlp", "--print", "title", "--no-playlist"]
        if use_cookie:
            cf = config.get("cookie_file", "")
            if cf:
                cmd += ["--cookies", cf]
        cmd.append(url)

        kwargs: dict = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=15,
        )
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(cmd, **kwargs)
            lines  = result.stdout.strip().splitlines()
            return lines[0] if lines else ""
        except Exception:
            return ""

    # ── Log file helpers ───────────────────────────────────────────────────────

    def _open_log(self, out_dir: str, title_stem: str, mode: str) -> None:
        """Open a fresh log file for the current operation."""
        self._close_log()
        try:
            log_dir   = Path(out_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            safe_stem = re.sub(r'[\\/:*?"<>|]', "_", title_stem)[:180]
            log_name  = f"{safe_stem}.log"
            log_path  = log_dir / log_name
            self._current_log_fh = open(
                log_path, "w", encoding="utf-8", errors="replace"
            )
            self._current_log_fh.write(
                f"# YTDrop log — {datetime.now().isoformat()}\n\n"
            )
            self._write_output(f"📄 Log: {log_path}\n", "info")
        except Exception as exc:
            self._write_output(f"⚠ Could not open log file: {exc}\n", "warn")
            self._current_log_fh = None

    def _close_log(self) -> None:
        """Close the current log file handle if one is open."""
        if self._current_log_fh:
            try:
                self._current_log_fh.close()
            except Exception:
                pass
            self._current_log_fh = None
