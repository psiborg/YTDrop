"""
ytdrop.__main__
~~~~~~~~~~~~~~~
Entry point: ``python -m ytdrop``

Also imported by the top-level ``ytdrop.py`` shim for backward compatibility
with ``python ytdrop.py``.
"""

from .ui.app import YTDropApp


def main() -> None:
    app = YTDropApp()
    app.mainloop()


if __name__ == "__main__":
    main()
