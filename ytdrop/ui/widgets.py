"""
ytdrop.ui.widgets
~~~~~~~~~~~~~~~~~
Self-contained tkinter widget helpers used by the main app window.

Classes
-------
DropZone
    The drag-and-drop / click-to-paste URL target at the top of the left
    panel.  Owns its own DnD binding and hover highlight logic.

OutputConsole
    A read-only ScrolledText widget with colour-tagged output and a paired
    log-file mirror.  Provides ``write(text, tag)`` and ``clear()``.
"""

import tkinter as tk
from tkinter import scrolledtext


class DropZone(tk.Frame):
    """
    A fixed-height frame that accepts URLs via:
      • native drag-and-drop (if tkinterdnd2 is installed)
      • left-click → paste from clipboard

    Calls *on_add_url(url)* for every URL it receives.
    """

    def __init__(self, parent: tk.Widget, on_add_url, **kwargs):
        height = kwargs.pop("height", 70)
        super().__init__(parent, height=height, relief=tk.RIDGE, bd=2,
                         cursor="hand2", **kwargs)
        self.pack_propagate(False)
        self._on_add_url = on_add_url

        self.label = tk.Label(
            self,
            text="🔗  Drop URLs here  (or paste below)",
            font=("Helvetica", 11),
        )
        self.label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        for w in (self, self.label):
            w.bind("<Button-1>", self._paste_clipboard)
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

        self._try_bind_dnd()

    # ── DnD ───────────────────────────────────────────────────────────────────

    def _try_bind_dnd(self) -> None:
        try:
            import tkinterdnd2  # noqa: F401
            self.drop_target_register("DND_Text", "DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event) -> None:
        for line in event.data.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("{"):
                self._on_add_url(line)

    # ── Clipboard paste ────────────────────────────────────────────────────────

    def _paste_clipboard(self, _event=None) -> None:
        try:
            for line in self.clipboard_get().splitlines():
                line = line.strip()
                if line:
                    self._on_add_url(line)
        except Exception:
            pass

    # ── Hover highlight ────────────────────────────────────────────────────────

    def _on_enter(self, _event=None) -> None:
        self.configure(relief=tk.SUNKEN)

    def _on_leave(self, _event=None) -> None:
        self.configure(relief=tk.RIDGE)

    # ── Theming ───────────────────────────────────────────────────────────────

    def apply_theme(self, t: dict) -> None:
        self.configure(
            bg=t["bg2"],
            highlightbackground=t["accent"],
            highlightcolor=t["accent"],
            highlightthickness=1,
        )
        self.label.configure(bg=t["bg2"], fg=t["fg2"])


class OutputConsole(tk.Frame):
    """
    A labelled, read-only ScrolledText with colour-tagged output lines.

    Usage
    -----
    console.write("some text\\n")               # plain
    console.write("ERROR: boom\\n", "error")    # coloured
    console.clear()
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, **kwargs)

        header = tk.Frame(self)
        header.pack(fill=tk.X)
        self._header_lbl = tk.Label(
            header, text="OUTPUT", font=("Helvetica", 9, "bold")
        )
        self._header_lbl.pack(side=tk.LEFT)
        self._clear_btn = tk.Button(
            header, text="Clear", relief=tk.FLAT,
            font=("Helvetica", 8), cursor="hand2", padx=6,
            command=self.clear,
        )
        self._clear_btn.pack(side=tk.RIGHT)

        self.text = scrolledtext.ScrolledText(
            self, height=10, font=("Courier", 9),
            wrap=tk.WORD, relief=tk.FLAT, state=tk.DISABLED,
        )
        self.text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    # ── Public API ─────────────────────────────────────────────────────────────

    def write(self, text: str, tag: str | None = None) -> None:
        """Append *text* to the console; *tag* selects a colour if given."""
        self.text.configure(state=tk.NORMAL)
        if tag:
            self.text.insert(tk.END, text, tag)
        else:
            self.text.insert(tk.END, text)
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)

    # ── Theming ───────────────────────────────────────────────────────────────

    def apply_theme(self, t: dict) -> None:
        self.configure(bg=t["bg"])
        self._header_lbl.configure(bg=t["bg"], fg=t["fg"])
        self._clear_btn.configure(
            bg=t["btn"], fg=t["fg"],
            activebackground=t["btn_hover"], activeforeground=t["fg"],
        )
        self.text.configure(
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"],
            selectbackground=t["sel_bg"],
        )
        self.text.tag_configure("error",   foreground=t["error"])
        self.text.tag_configure("success", foreground=t["success"])
        self.text.tag_configure("warn",    foreground=t["warn"])
        self.text.tag_configure("info",    foreground=t["accent"])
