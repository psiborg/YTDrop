"""
ytdrop.ui.dialogs
~~~~~~~~~~~~~~~~~
Modal dialog windows: Settings and About.

Both dialogs are plain functions that accept the parent ``YTDropApp`` window
as their first argument and read/write through it, keeping all state in the
app and keeping the dialog code free of any global references.
"""

import tkinter as tk
from tkinter import filedialog, messagebox

from ..constants import APP_DATE, APP_NAME, APP_VERSION, DEFAULT_AUDIO_PARAMS, DEFAULT_VIDEO_PARAMS
from ..config import save_config
from ..themes import BUILTIN_THEMES


# ── Settings ──────────────────────────────────────────────────────────────────

def open_settings(app) -> None:
    """Open the Settings modal attached to *app* (a ``YTDropApp`` instance)."""

    dlg = tk.Toplevel(app)
    dlg.title("Settings")
    dlg.geometry("580x680")
    dlg.resizable(True, True)
    dlg.minsize(520, 580)
    dlg.transient(app)
    dlg.grab_set()
    t = app.theme
    dlg.configure(bg=t["bg"])

    # ── Local helpers ──────────────────────────────────────────────────────────

    def lbl(parent, text, **kw):
        widget = tk.Label(parent, text=text, bg=t["bg"], fg=t["fg"], **kw)
        widget.pack(anchor="w", pady=(10, 2))
        return widget

    def sep(parent=None):
        tk.Frame(parent or dlg, bg=t["border"], height=1).pack(fill=tk.X, pady=6)

    def retheme_widget(widget, t2):
        """Recursively re-colour dialog chrome after a theme switch."""
        try:
            if isinstance(widget, (tk.Frame, tk.LabelFrame)):
                widget.configure(bg=t2["bg"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=t2["bg"], fg=t2["fg"])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=t2["btn"], fg=t2["fg"])
            elif isinstance(widget, (tk.Text, tk.Entry)):
                widget.configure(bg=t2["entry_bg"], fg=t2["fg"])
        except Exception:
            pass
        for child in widget.winfo_children():
            retheme_widget(child, t2)

    # ── Layout ────────────────────────────────────────────────────────────────

    pad = tk.Frame(dlg, bg=t["bg"])
    pad.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

    # ── APPEARANCE ────────────────────────────────────────────────────────────
    lbl(pad, "APPEARANCE", font=("Helvetica", 9, "bold"))

    cur_lbl = tk.Label(
        pad, text=f"Active: {app._active_theme_name}",
        bg=t["bg"], fg=t["fg2"], font=("Helvetica", 9, "italic"),
    )
    cur_lbl.pack(anchor="w")

    # Scrollable theme list
    list_outer = tk.Frame(pad, bg=t["border"], bd=1, relief=tk.FLAT)
    list_outer.pack(fill=tk.X, pady=(4, 0))

    list_canvas = tk.Canvas(
        list_outer, bg=t["entry_bg"], highlightthickness=0, height=160
    )
    list_scroll = tk.Scrollbar(
        list_outer, orient=tk.VERTICAL, command=list_canvas.yview
    )
    list_canvas.configure(yscrollcommand=list_scroll.set)
    list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    list_inner  = tk.Frame(list_canvas, bg=t["entry_bg"])
    list_window = list_canvas.create_window((0, 0), window=list_inner, anchor="nw")

    def _on_inner_configure(_e):
        list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        list_canvas.itemconfig(list_window, width=list_canvas.winfo_width())

    list_inner.bind("<Configure>", _on_inner_configure)
    list_canvas.bind(
        "<Configure>",
        lambda e: list_canvas.itemconfig(list_window, width=e.width),
    )

    all_themes: dict = {}
    selected_var = tk.StringVar(value=app._active_theme_name)

    # ── Theme list callbacks ───────────────────────────────────────────────────

    def _apply_selected(name: str) -> None:
        td = all_themes.get(name)
        if td is None:
            return
        app.set_theme(name, td if name not in BUILTIN_THEMES else None)
        save_config(app.config_data)
        cur_lbl.configure(text=f"Active: {name}")
        t2 = app.theme
        dlg.configure(bg=t2["bg"])
        for w in dlg.winfo_children():
            if w is not list_outer:
                retheme_widget(w, t2)
        _rebuild_list()

    def _make_row(name: str, theme_dict: dict, _idx: int) -> None:
        is_custom = name not in BUILTIN_THEMES
        row_bg    = theme_dict["bg2"]
        row_fg    = theme_dict["fg"]

        row = tk.Frame(list_inner, bg=row_bg, cursor="hand2")
        row.pack(fill=tk.X, pady=1, padx=1)

        # Colour swatches
        swatch_frame = tk.Frame(row, bg=row_bg)
        swatch_frame.pack(side=tk.LEFT, padx=(6, 4), pady=4)
        for color in (
            theme_dict["bg"], theme_dict["fg"], theme_dict["accent"],
            theme_dict["success"], theme_dict["error"], theme_dict["warn"],
        ):
            sw = tk.Frame(swatch_frame, bg=color, width=12, height=12, relief=tk.FLAT)
            sw.pack(side=tk.LEFT, padx=1)
            sw.pack_propagate(False)

        tag_char = " ✦" if is_custom else ""
        name_lbl = tk.Label(
            row, text=f"  {name}{tag_char}",
            bg=row_bg, fg=row_fg, font=("Helvetica", 9), anchor="w",
        )
        name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)

        if name == app._active_theme_name:
            row.configure(bg=theme_dict["sel_bg"])
            name_lbl.configure(bg=theme_dict["sel_bg"], font=("Helvetica", 9, "bold"))

        def _select(_e=None, n=name):
            selected_var.set(n)
            _apply_selected(n)

        for w in (row, name_lbl, swatch_frame):
            w.bind("<Button-1>", _select)

        if is_custom:
            def _delete(_e=None, n=name):
                customs = app.config_data.get("theme_custom", {})
                customs.pop(n, None)
                if app._active_theme_name == n:
                    app.set_theme("Catppuccin Mocha")
                save_config(app.config_data)
                _rebuild_list()

            del_btn = tk.Label(
                row, text="✕",
                bg=row_bg, fg=theme_dict["error"],
                cursor="hand2", padx=6, font=("Helvetica", 9, "bold"),
            )
            del_btn.pack(side=tk.RIGHT, pady=4)
            del_btn.bind("<Button-1>", _delete)

    def _rebuild_list() -> None:
        for child in list_inner.winfo_children():
            child.destroy()
        all_themes.clear()
        all_themes.update(BUILTIN_THEMES)
        all_themes.update(app.config_data.get("theme_custom", {}))
        t_now = app.theme
        list_canvas.configure(bg=t_now["entry_bg"])
        list_inner.configure(bg=t_now["entry_bg"])
        for i, (name, td) in enumerate(all_themes.items()):
            _make_row(name, td, i)

    _rebuild_list()

    # Mousewheel scrolling
    def _on_wheel(e):
        list_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    list_canvas.bind_all("<MouseWheel>", _on_wheel)
    dlg.bind("<Destroy>", lambda _e: list_canvas.unbind_all("<MouseWheel>"))

    # Import VSCode theme button
    import_row = tk.Frame(pad, bg=t["bg"])
    import_row.pack(fill=tk.X, pady=(6, 0))

    def _do_import():
        app.import_vscode_theme()
        cur_lbl.configure(text=f"Active: {app._active_theme_name}")
        t2 = app.theme
        dlg.configure(bg=t2["bg"])
        for w in dlg.winfo_children():
            if w is not list_outer:
                retheme_widget(w, t2)
        _rebuild_list()

    tk.Button(
        import_row, text="⬆  Import VSCode Theme (.json)…",
        bg=t["btn"], fg=t["fg"], relief=tk.FLAT,
        padx=10, pady=5, cursor="hand2", command=_do_import,
    ).pack(side=tk.LEFT)

    tk.Label(
        import_row, text="✦ = imported",
        bg=t["bg"], fg=t["fg2"], font=("Helvetica", 8),
    ).pack(side=tk.RIGHT)

    sep(pad)

    # ── COOKIE FILE ───────────────────────────────────────────────────────────
    lbl(pad, "COOKIE FILE", font=("Helvetica", 9, "bold"))
    cookie_row = tk.Frame(pad, bg=t["bg"])
    cookie_row.pack(fill=tk.X)
    cookie_entry = tk.Entry(
        cookie_row, bg=t["entry_bg"], fg=t["fg"],
        insertbackground=t["fg"], relief=tk.FLAT, bd=1,
    )
    cookie_entry.insert(0, app.config_data.get("cookie_file", ""))
    cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

    def _browse_cookie():
        p = filedialog.askopenfilename(
            title="Select cookie file",
            filetypes=[("Cookie files", "*.txt *.json"), ("All files", "*.*")],
        )
        if p:
            cookie_entry.delete(0, tk.END)
            cookie_entry.insert(0, p)

    tk.Button(
        cookie_row, text="Browse…",
        bg=t["btn"], fg=t["fg"], relief=tk.FLAT,
        padx=8, pady=4, cursor="hand2", command=_browse_cookie,
    ).pack(side=tk.RIGHT)
    sep(pad)

    # ── PARAMETERS ────────────────────────────────────────────────────────────
    lbl(pad, "DEFAULT VIDEO PARAMETERS", font=("Helvetica", 9, "bold"))
    video_text = tk.Text(
        pad, height=3, bg=t["entry_bg"], fg=t["fg"],
        insertbackground=t["fg"], relief=tk.FLAT, bd=1,
        wrap=tk.WORD, font=("Courier", 9),
    )
    video_text.insert("1.0", app.config_data.get("video_params", DEFAULT_VIDEO_PARAMS))
    video_text.pack(fill=tk.X)

    lbl(pad, "DEFAULT AUDIO PARAMETERS", font=("Helvetica", 9, "bold"))
    audio_text = tk.Text(
        pad, height=3, bg=t["entry_bg"], fg=t["fg"],
        insertbackground=t["fg"], relief=tk.FLAT, bd=1,
        wrap=tk.WORD, font=("Courier", 9),
    )
    audio_text.insert("1.0", app.config_data.get("audio_params", DEFAULT_AUDIO_PARAMS))
    audio_text.pack(fill=tk.X)

    sep(pad)

    def _save():
        app.config_data["cookie_file"] = cookie_entry.get().strip()
        app.config_data["video_params"] = video_text.get("1.0", tk.END).strip()
        app.config_data["audio_params"] = audio_text.get("1.0", tk.END).strip()
        save_config(app.config_data)
        dlg.destroy()

    tk.Button(
        pad, text="Save & Close",
        bg=t["accent"], fg=t["bg"], relief=tk.FLAT,
        padx=14, pady=7, cursor="hand2",
        font=("Helvetica", 10, "bold"), command=_save,
    ).pack(pady=(4, 0))


# ── About ─────────────────────────────────────────────────────────────────────

def open_about(app) -> None:
    """Open the About modal attached to *app*."""

    dlg = tk.Toplevel(app)
    dlg.title("About YTDrop")
    dlg.geometry("320x240")
    dlg.resizable(False, False)
    dlg.transient(app)
    dlg.grab_set()
    t = app.theme
    dlg.configure(bg=t["bg"])

    c = tk.Canvas(dlg, width=64, height=64, bg=t["bg"], highlightthickness=0)
    c.pack(pady=(20, 4))
    c.create_oval(4, 4, 60, 60, fill=t["accent"], outline="")
    c.create_text(32, 32, text="⬇", font=("Helvetica", 24, "bold"), fill=t["bg"])

    tk.Label(dlg, text=APP_NAME,
             font=("Helvetica", 16, "bold"), bg=t["bg"], fg=t["fg"]).pack()
    tk.Label(dlg, text=f"Version {APP_VERSION}",
             font=("Helvetica", 10), bg=t["bg"], fg=t["fg2"]).pack()
    tk.Label(dlg, text=f"Released {APP_DATE}",
             font=("Helvetica", 10), bg=t["bg"], fg=t["fg2"]).pack()
    tk.Label(dlg, text="A friendly GUI wrapper for yt-dlp",
             font=("Helvetica", 9), bg=t["bg"], fg=t["fg2"]).pack(pady=(6, 0))
    tk.Button(
        dlg, text="Close",
        bg=t["btn"], fg=t["fg"], relief=tk.FLAT,
        padx=16, pady=5, cursor="hand2", command=dlg.destroy,
    ).pack(pady=16)
