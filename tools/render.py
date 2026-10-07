#!/usr/bin/env python3
"""Render a DD Instagram carousel spec (JSON) to 1080x1350 PNGs.

Usage:
    python3 tools/render.py tools/carousels/bank-02.json --out out/bank-02
    python3 tools/render.py SPEC.json --out DIR --allow-fallback-font   # test only

Prints "OK" as its last line when every slide rendered and passed the checks.
Anything else is a failure and the PNGs must not be used.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

TOOLS = Path(__file__).resolve().parent
TEMPLATE = TOOLS / "template.html"
SERIF = TOOLS / "fonts" / "Fraunces-SemiBold.ttf"

# Hard content rules from the DD content spec. A hit fails the render.
BANNED = [
    (r"\bguaranteed\b", '"guaranteed"'),
    (r"\bwe delete\b", '"we delete"'),
    (r"\bany review\b", '"any review"'),
    (r"\bpermanent(ly)?\b", '"permanent"'),
    (r"\bwarrant(y|ies)\b", "a warranty"),
    (r"\d+(\.\d+)?\s?%", "a percentage (success rates need real case records)"),
    (r"\[[^\]]*\]", "an unfilled [placeholder]"),
]
# Australian/British spellings to flag (US English is required).
UK = ["enquir", "maths", "defence", "colour", "favour", "organis", "recognis", "realis",
      "licence", "cheque", "programme", "centre", "whilst", "labour", "behaviour", "suburb",
      "apologis", "prioritis", "travell", "cancell"]


# Extra banned terms (comma-separated) come from the environment so they stay out of this public repo.
EXTRA_BANNED = [w.strip() for w in os.environ.get("DD_BANNED_TERMS", "").split(",") if w.strip()]


def texts(spec):
    yield "tab", spec.get("tab", "")
    for i, s in enumerate(spec["slides"], 1):
        for k in ("headline", "button", "sub"):
            if s.get(k):
                yield f"slide {i} {k}", s[k]
        body = s.get("body") or []
        for p in [body] if isinstance(body, str) else body:
            yield f"slide {i} body", p


def lint(spec):
    errors, warnings = [], []
    slides = spec.get("slides") or []
    if not slides:
        errors.append("spec has no slides")
        return errors, warnings
    if slides[0].get("type") != "hook":
        errors.append("first slide must be type 'hook'")
    if slides[-1].get("type") != "cta":
        errors.append("last slide must be type 'cta'")
    if not 6 <= len(slides) <= 9:
        errors.append(f"{len(slides)} slides; carousels must have 6-9 (new ones 7-9)")
    elif len(slides) < 7:
        warnings.append(f"{len(slides)} slides; new carousels should have 7-9")
    for where, t in texts(spec):
        for pat, label in BANNED:
            if re.search(pat, t, re.I):
                errors.append(f"{where}: contains {label}: {t!r}")
        for w in EXTRA_BANNED:
            if w.lower() in t.lower():
                errors.append(f"{where}: contains a banned term from DD_BANNED_TERMS: {t!r}")
        for w in UK:
            if w in t.lower():
                warnings.append(f"{where}: non-US spelling ({w}...): {t!r}")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-fallback-font", action="store_true",
                    help="render without Fraunces (for testing only; output is not publishable)")
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    errors, warnings = lint(spec)
    for w in warnings:
        print("WARN", w)
    if not SERIF.exists() and not args.allow_fallback_font:
        errors.append(f"missing headline font {SERIF.relative_to(TOOLS.parent)} (see tools/README.md)")
    if errors:
        for e in errors:
            print("ERROR", e)
        print("FAILED")
        sys.exit(1)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("slide-*.png"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        page.goto(TEMPLATE.as_uri())
        page.evaluate("spec => build(spec)", spec)
        page.evaluate("() => document.fonts.ready")
        page.wait_for_function("() => [...document.images].every(i => i.complete && i.naturalWidth > 0)")
        if SERIF.exists() and not page.evaluate("() => document.fonts.check('600 72px \"DD Serif\"')"):
            errors.append("headline font did not load")
        errors += page.evaluate("() => check()")
        if not errors:
            for i, el in enumerate(page.query_selector_all(".slide"), 1):
                el.screenshot(path=str(out / f"slide-{i:02d}.png"))
        browser.close()

    if errors:
        for e in errors:
            print("ERROR", e)
        print("FAILED")
        sys.exit(1)
    n = len(list(out.glob("slide-*.png")))
    if n != len(spec["slides"]):
        print(f"ERROR rendered {n} of {len(spec['slides'])} slides")
        print("FAILED")
        sys.exit(1)
    if not SERIF.exists():
        print("WARN rendered with a fallback headline font; not publishable")
        print(f"TEST-ONLY {n} slides -> {out}")
        sys.exit(2)
    print(f"{n} slides -> {out}")
    print("OK")


if __name__ == "__main__":
    main()
