#!/usr/bin/env python3
"""Regenerate minified CSS/JS assets."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from rcssmin import cssmin
    from rjsmin import jsmin
except ImportError as exc:  # pragma: no cover - informative exit
    sys.stderr.write(
        "Missing dependencies. Install them with:\n"
        "  python3 -m pip install --user rcssmin rjsmin\n"
    )
    raise


def write_minified(src: Path, dest: Path, minify_func) -> None:
    dest.write_text(minify_func(src.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"Minified {src} -> {dest}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    css_src = root / "assets" / "styles.css"
    css_dest = root / "assets" / "styles.min.css"
    js_src = root / "assets" / "main.js"
    js_dest = root / "assets" / "main.min.js"

    write_minified(css_src, css_dest, cssmin)
    write_minified(js_src, js_dest, jsmin)


if __name__ == "__main__":
    main()
