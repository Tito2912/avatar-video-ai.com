#!/usr/bin/env python3
"""Regenerate minified CSS/JS assets."""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from rcssmin import cssmin  # type: ignore[import-not-found]
    from rjsmin import jsmin  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    sys.stderr.write(
        "Warning: optional dependencies missing (rcssmin, rjsmin).\n"
        "Falling back to a lightweight minifier (less optimal).\n"
        "To use the best minification, install:\n"
        "  python3 -m pip install --user rcssmin rjsmin\n\n"
    )

    _CSS_COMMENT_RE = re.compile(r"/\\*.*?\\*/", flags=re.DOTALL)
    _WS_RE = re.compile(r"\\s+")

    def cssmin(text: str) -> str:  # type: ignore[no-redef]
        # Simple, safe-ish CSS minifier: remove comments + collapse whitespace.
        out = _CSS_COMMENT_RE.sub("", text)
        out = _WS_RE.sub(" ", out)
        out = re.sub(r"\\s*([{}:;,>+~])\\s*", r"\\1", out)
        out = out.strip()
        return out + ("\n" if out else "")

    def jsmin(text: str) -> str:  # type: ignore[no-redef]
        # Conservative JS “minifier”: trim lines + drop empty lines.
        # (Avoids risky comment/string parsing without rjsmin.)
        lines = [ln.strip() for ln in text.splitlines()]
        out = "\n".join([ln for ln in lines if ln])
        return out + ("\n" if out else "")


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
