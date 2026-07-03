#!/usr/bin/env python3
"""Generate the app sections of README.md from data/apps.yaml.

The README's category table-of-contents and app listings live between
marker comments and are overwritten by this script; everything outside
the markers is hand-written and left alone.

Usage:
    python scripts/generate.py           # rewrite README.md in place
    python scripts/generate.py --check   # exit 1 if README.md is out of sync (CI)
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DATA = ROOT / "data" / "apps.yaml"

BADGES = {"plain-files": "📄", "open-db": "🗃️", "offline": "📵", "sync": "🔁"}
TOC_START, TOC_END = "<!-- TOC:APPS:START -->", "<!-- TOC:APPS:END -->"
APPS_START, APPS_END = "<!-- APPS:START -->", "<!-- APPS:END -->"


def slug(name: str) -> str:
    """GitHub heading anchor: lowercase, strip punctuation, spaces to hyphens."""
    return re.sub(r"[^\w\- ]", "", name.lower()).replace(" ", "-")


def render_toc(cats: list) -> str:
    return "\n".join(f"- [{c['name']}](#{slug(c['name'])})" for c in cats)


def render_apps(cats: list) -> str:
    lines = []
    for c in cats:
        lines.append(f"## {c['name']}")
        lines.append("")
        if c.get("intro"):
            lines.append(c["intro"].strip())
            lines.append("")
        for a in c["apps"]:
            head = f"- [{a['name']}]({a['url']})"
            if a.get("suffix"):
                head += f" {a['suffix']}"
            if a.get("license"):
                head += f" `{a['license']}`"
            badges = " ".join(BADGES[b] for b in a.get("badges", []))
            if badges:
                head += f" {badges}"
            head += f" — {a['description']}"
            if a.get("disclosure"):
                head += f" *Disclosure: {a['disclosure']}*"
            lines.append(head)
            lines.append(f"  - *Exit: {a['exit']}*")
        lines.append("")
    return "\n".join(lines).rstrip()


def splice(text: str, start: str, end: str, payload: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        sys.exit(f"error: markers {start} … {end} not found in README.md")
    return pattern.sub(lambda _: f"{start}\n{payload}\n{end}", text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if README.md is out of sync with data/apps.yaml")
    args = parser.parse_args()

    cats = yaml.safe_load(DATA.read_text(encoding="utf-8"))["categories"]
    text = README.read_text(encoding="utf-8")
    new = splice(text, TOC_START, TOC_END, render_toc(cats))
    new = splice(new, APPS_START, APPS_END, render_apps(cats))

    if args.check:
        if new != text:
            sys.exit("README.md is out of sync with data/apps.yaml — run: python scripts/generate.py")
        print("README.md is in sync.")
    else:
        README.write_text(new, encoding="utf-8")
        n_apps = sum(len(c["apps"]) for c in cats)
        print(f"README.md regenerated: {len(cats)} categories, {n_apps} apps.")


if __name__ == "__main__":
    main()
