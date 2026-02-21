"""
ytdrop.ui.app
~~~~~~~~~~~~~
The main application window (``YTDropApp``).

Responsibilities
----------------
- Build and lay out the top-level tkinter window.
- Own the active theme and drive ``apply_theme`` across all widgets.
- Instantiate ``Downloader`` with callbacks that update the UI.
- Delegate dialog creation to ``ytdrop.ui.dialogs``.
- Delegate drop-zone / output-console widget behaviour to
  ``ytdrop.ui.widgets``.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from ..constants import APP_NAME, DEFAULT_RES_INDEX, RESOLUTIONS
from ..config import load_config, save_config
from ..themes import BUILTIN_THEMES, vscode_theme_to_ytdrop
from ..downloader import Downloader
from .widgets import DropZone, OutputConsole
from . import dialogs


class YTDropApp(tk.Tk):

    def __init__(self) -> None:
        super().__init__()

        self.config_data: dict = load_config()

        # ── Active theme ───────────────────────────────────────────────────────
        self._active_theme_name: str = self.config_data.get(
            "theme_name", "Catppuccin Mocha"
        )
        self.theme: dict = self._resolve_theme(self._active_theme_name)

        # ── Window setup ───────────────────────────────────────────────────────
        self.title(APP_NAME)
        self.geometry("900x720")
        self.minsize(700, 560)
        self._set_icon()

        # ── Build UI (creates all self.* widget attributes) ────────────────────
        self._build_ui()

        # ── Downloader (after UI so callbacks can reference widgets) ───────────
        self._downloader = Downloader(
            write_output=self._write_output,
            set_status=lambda text: self.status_var.set(text),
            on_done=self._on_download_done,
        )

        self.apply_theme()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Icon ───────────────────────────────────────────────────────────────────

    def _set_icon(self) -> None:
        try:
            icon = tk.PhotoImage(width=32, height=32)
            self.iconphoto(True, icon)
        except Exception:
            pass

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Toolbar ───────────────────────────────────────────────────────────
        self.toolbar = tk.Frame(self, height=44)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        self.lbl_logo = tk.Label(
            self.toolbar, text="⬇  YTDrop", font=("Helvetica", 14, "bold")
        )
        self.lbl_logo.pack(side=tk.LEFT, padx=(14, 6), pady=4)

        self.btn_settings = tk.Button(
            self.toolbar, text="⚙  Settings", relief=tk.FLAT,
            cursor="hand2", padx=10, command=self.open_settings,
        )
        self.btn_settings.pack(side=tk.LEFT, padx=4, pady=6)

        self.btn_about = tk.Button(
            self.toolbar, text="ℹ  About", relief=tk.FLAT,
            cursor="hand2", padx=10, command=self.open_about,
        )
        self.btn_about.pack(side=tk.LEFT, padx=4, pady=6)

        self.lbl_dl_dir = tk.Label(self.toolbar, text="", font=("Helvetica", 9))
        self.lbl_dl_dir.pack(side=tk.RIGHT, padx=10)

        self.btn_dl_dir = tk.Button(
            self.toolbar, text="📁  Output Folder", relief=tk.FLAT,
            cursor="hand2", padx=10, command=self.choose_download_dir,
        )
        self.btn_dl_dir.pack(side=tk.RIGHT, padx=4, pady=6)

        # ── Main content ──────────────────────────────────────────────────────
        self.main = tk.Frame(self)
        self.main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        # Left panel
        self.left = tk.Frame(self.main)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Drop zone (custom widget)
        self.drop_zone = DropZone(self.left, on_add_url=self._add_url)
        self.drop_zone.pack(fill=tk.X, pady=(8, 6))

        # URL textarea
        tk.Label(
            self.left, text="URLs  (one per line)",
            font=("Helvetica", 10, "bold"), anchor="w",
        ).pack(fill=tk.X, pady=(4, 2))

        url_frame = tk.Frame(self.left)
        url_frame.pack(fill=tk.BOTH, expand=True)

        self.url_text = tk.Text(
            url_frame, height=8, wrap=tk.NONE,
            font=("Courier", 10), relief=tk.FLAT, bd=0,
        )
        url_sb_y = tk.Scrollbar(url_frame, command=self.url_text.yview)
        url_sb_x = tk.Scrollbar(
            url_frame, orient=tk.HORIZONTAL, command=self.url_text.xview
        )
        self.url_text.configure(
            yscrollcommand=url_sb_y.set, xscrollcommand=url_sb_x.set
        )
        url_sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        url_sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.url_text.pack(fill=tk.BOTH, expand=True)

        # Buttons below URL box
        btn_row = tk.Frame(self.left)
        btn_row.pack(fill=tk.X, pady=(6, 0))

        self.btn_list = tk.Button(
            btn_row, text="📋  List Formats", relief=tk.FLAT,
            padx=12, pady=5, cursor="hand2", command=self.list_formats,
        )
        self.btn_list.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_clear_urls = tk.Button(
            btn_row, text="✕  Clear", relief=tk.FLAT,
            padx=10, pady=5, cursor="hand2",
            command=lambda: self.url_text.delete("1.0", tk.END),
        )
        self.btn_clear_urls.pack(side=tk.LEFT)

        # Right panel – Options
        self.right = tk.Frame(self.main, width=230)
        self.right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0), pady=(8, 0))
        self.right.pack_propagate(False)

        tk.Label(
            self.right, text="OPTIONS", font=("Helvetica", 9, "bold")
        ).pack(anchor="w", pady=(6, 4))

        self.var_video = tk.BooleanVar(value=True)
        self.var_audio = tk.BooleanVar(value=False)

        self.chk_video = tk.Checkbutton(
            self.right, text="Video (mp4)", variable=self.var_video,
            font=("Helvetica", 10), anchor="w",
        )
        self.chk_video.pack(fill=tk.X, pady=1)

        self.chk_audio = tk.Checkbutton(
            self.right, text="Audio (mp3)", variable=self.var_audio,
            font=("Helvetica", 10), anchor="w",
        )
        self.chk_audio.pack(fill=tk.X, pady=1)

        tk.Label(
            self.right, text="Max Resolution",
            font=("Helvetica", 10, "bold"), anchor="w",
        ).pack(fill=tk.X, pady=(10, 2))

        self.res_var = tk.IntVar(value=DEFAULT_RES_INDEX)

        res_frame = tk.Frame(self.right)
        res_frame.pack(fill=tk.X)

        self.slider = tk.Scale(
            res_frame, from_=0, to=len(RESOLUTIONS) - 1,
            orient=tk.HORIZONTAL, variable=self.res_var,
            showvalue=False, command=self._on_slider,
            length=200, sliderlength=18, bd=0, highlightthickness=0,
        )
        self.slider.pack(fill=tk.X)

        self.lbl_res = tk.Label(
            self.right, text=f"{RESOLUTIONS[DEFAULT_RES_INDEX]}p",
            font=("Helvetica", 11, "bold"),
        )
        self.lbl_res.pack()

        self.var_cookie = tk.BooleanVar(value=False)
        self.chk_cookie = tk.Checkbutton(
            self.right, text="Use cookie file", variable=self.var_cookie,
            font=("Helvetica", 10), anchor="w",
        )
        self.chk_cookie.pack(fill=tk.X, pady=(10, 0))

        tk.Frame(self.right).pack(fill=tk.Y, expand=True)   # spacer

        self.btn_fetch = tk.Button(
            self.right, text="⬇  FETCH", relief=tk.FLAT,
            font=("Helvetica", 12, "bold"), pady=10,
            cursor="hand2", command=self.fetch,
        )
        self.btn_fetch.pack(fill=tk.X, pady=(8, 4))

        self.btn_cancel = tk.Button(
            self.right, text="■  Cancel", relief=tk.FLAT,
            font=("Helvetica", 10), pady=6,
            cursor="hand2", command=self.cancel, state=tk.DISABLED,
        )
        self.btn_cancel.pack(fill=tk.X, pady=(0, 4))

        # ── Output console (custom widget) ─────────────────────────────────────
        self.console = OutputConsole(self)
        self.console.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.statusbar = tk.Label(
            self, textvariable=self.status_var,
            anchor="w", font=("Helvetica", 9), pady=3,
        )
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM, padx=8)

        self._update_dl_dir_label()

    # ── Public actions ─────────────────────────────────────────────────────────

    def fetch(self) -> None:
        urls = self._get_urls()
        if not urls:
            messagebox.showwarning("No URLs", "Please enter at least one URL.")
            return
        if not self.var_video.get() and not self.var_audio.get():
            messagebox.showwarning("No Format", "Please select at least Video or Audio.")
            return
        self._set_busy(True)
        self._downloader.fetch(
            urls=urls,
            want_video=self.var_video.get(),
            want_audio=self.var_audio.get(),
            config=self.config_data,
            use_cookie=self.var_cookie.get(),
            res_index=self.res_var.get(),
        )

    def list_formats(self) -> None:
        urls = self._get_urls()
        if not urls:
            messagebox.showwarning("No URLs", "Please enter at least one URL.")
            return
        self._set_busy(True)
        self._downloader.list_formats(
            urls=urls,
            config=self.config_data,
            use_cookie=self.var_cookie.get(),
        )

    def cancel(self) -> None:
        self._downloader.cancel()
        self.status_var.set("Cancelling…")
        self.btn_cancel.configure(state=tk.DISABLED)

    def choose_download_dir(self) -> None:
        d = filedialog.askdirectory(
            title="Select download folder",
            initialdir=self.config_data.get("download_dir", str(Path.home())),
        )
        if d:
            self.config_data["download_dir"] = d
            save_config(self.config_data)
            self._update_dl_dir_label()

    def open_settings(self) -> None:
        dialogs.open_settings(self)

    def open_about(self) -> None:
        dialogs.open_about(self)

    # ── Theme API ──────────────────────────────────────────────────────────────

    def _resolve_theme(self, name: str) -> dict:
        if name in BUILTIN_THEMES:
            return BUILTIN_THEMES[name]
        custom = self.config_data.get("theme_custom", {})
        if name in custom:
            return custom[name]
        return BUILTIN_THEMES["Catppuccin Mocha"]

    def set_theme(self, name: str, theme_dict: dict | None = None) -> None:
        """Switch to *name*, optionally storing it as a custom imported theme."""
        if theme_dict is not None:
            self.config_data.setdefault("theme_custom", {})[name] = theme_dict
        self._active_theme_name     = name
        self.theme                  = self._resolve_theme(name)
        self.config_data["theme_name"] = name
        self.apply_theme()

    def import_vscode_theme(self) -> None:
        path = filedialog.askopenfilename(
            title="Import VSCode Theme (.json)",
            filetypes=[("VSCode theme JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            name, theme_dict = vscode_theme_to_ytdrop(path)
        except ValueError as exc:
            messagebox.showerror("Theme Import Failed", str(exc))
            return
        # Avoid clobbering a built-in name
        base, suffix = name, 1
        while name in BUILTIN_THEMES:
            name = f"{base} ({suffix})"
            suffix += 1
        self.set_theme(name, theme_dict)
        save_config(self.config_data)
        messagebox.showinfo("Theme Imported", f'Theme "{name}" applied successfully.')

    def apply_theme(self) -> None:
        """Recursively apply the active theme to every widget in the window."""
        t = self.theme
        self.configure(bg=t["bg"])

        widget_styles = {
            tk.Frame: {"bg": t["bg"]},
            tk.Label: {"bg": t["bg"], "fg": t["fg"]},
            tk.Button: {
                "bg": t["btn"], "fg": t["fg"],
                "activebackground": t["btn_hover"], "activeforeground": t["fg"],
                "bd": 0, "highlightthickness": 0,
            },
            tk.Checkbutton: {
                "bg": t["bg"], "fg": t["fg"],
                "activebackground": t["bg"], "activeforeground": t["accent"],
                "selectcolor": t["bg3"], "bd": 0,
            },
            tk.Scale: {
                "bg": t["bg"], "fg": t["fg"],
                "troughcolor": t["bg3"], "activebackground": t["accent"],
                "highlightthickness": 0,
            },
            tk.Text: {
                "bg": t["entry_bg"], "fg": t["fg"],
                "insertbackground": t["fg"],
                "selectbackground": t["sel_bg"], "selectforeground": t["fg"],
                "bd": 1, "highlightthickness": 1,
                "highlightcolor": t["border"], "highlightbackground": t["border"],
            },
        }

        def _recurse(widget: tk.Widget) -> None:
            for base, opts in widget_styles.items():
                if isinstance(widget, base):
                    try:
                        widget.configure(**opts)
                    except tk.TclError:
                        pass
            # Per-widget overrides
            if widget is self.toolbar:
                widget.configure(bg=t["bg2"])
            if widget is self.lbl_logo:
                widget.configure(bg=t["bg2"], fg=t["accent"])
            if widget is self.btn_fetch:
                widget.configure(
                    bg=t["accent"], fg=t["bg"],
                    activebackground=t["accent2"], activeforeground=t["bg"],
                )
            if widget is self.statusbar:
                widget.configure(bg=t["bg3"], fg=t["fg2"])
            for child in widget.winfo_children():
                _recurse(child)

        _recurse(self)

        # Delegate themed sub-widgets to their own apply_theme methods
        self.drop_zone.apply_theme(t)
        self.console.apply_theme(t)
        self.statusbar.configure(bg=t["bg3"], fg=t["fg2"])

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _write_output(self, text: str, tag: str | None = None) -> None:
        """Thread-safe bridge: schedule a console write on the main thread."""
        self.after(0, self.console.write, text, tag)

    def _on_download_done(self) -> None:
        """Called by Downloader when the current run finishes."""
        self.after(0, self._set_busy, False)

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_fetch.configure(state=state)
        self.btn_list.configure(state=state)
        self.btn_cancel.configure(state=tk.NORMAL if busy else tk.DISABLED)

    def _get_urls(self) -> list[str]:
        raw = self.url_text.get("1.0", tk.END).strip()
        return [u.strip() for u in raw.splitlines() if u.strip()]

    def _add_url(self, url: str) -> None:
        current = self.url_text.get("1.0", tk.END).strip()
        if url not in current:
            self.url_text.insert(tk.END, url + "\n")

    def _on_slider(self, val) -> None:
        idx = int(float(val))
        self.lbl_res.configure(text=f"{RESOLUTIONS[idx]}p")

    def _update_dl_dir_label(self) -> None:
        d = self.config_data.get("download_dir", "")
        if d:
            self.lbl_dl_dir.configure(text=f"→ {Path(d).name or d}")

    def _on_close(self) -> None:
        self._downloader.cancel()
        save_config(self.config_data)
        self.destroy()
