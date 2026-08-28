"""Export canonical Council Intelligence pages to the sibling MBF repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DEFAULT_TARGET = ROOT.parent / "moving-beaumont-forward" / "public"
MANIFEST_NAME = ".bi-council-intelligence-manifest.json"
CANONICAL_BASE = "https://beaumontintelligence.com/"

ROOT_FILES = (
    "council-intelligence.html",
    "council-briefings-2026.html",
    "styles.css",
    "app.js",
    "data.js",
    "favicon.png",
    "mbf-logo.png",
)
DOCUMENT_FILES = (
    "documents/index.html",
    "documents/viewer.html",
    "documents/viewer.js",
    "documents/document-data.js",
)
RENDERED_ROOTS = (
    "official-documents/2026-08-04/rendered",
    "official-documents/2026-08-18/rendered",
)
URL_ATTRIBUTE = re.compile(r'(?P<prefix>\b(?:href|src)\s*=\s*["\'])(?P<url>[^"\']+)(?P<suffix>["\'])', re.IGNORECASE)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundle_paths() -> list[Path]:
    paths = [Path(name) for name in ROOT_FILES + DOCUMENT_FILES]
    paths.extend(path.relative_to(DOCS) for path in sorted((DOCS / "briefings").glob("*.html")))
    for relative_root in RENDERED_ROOTS:
        source_root = DOCS / relative_root
        if source_root.is_dir():
            paths.extend(path.relative_to(DOCS) for path in sorted(source_root.rglob("*")) if path.is_file())
    return sorted(set(paths), key=lambda path: path.as_posix())


def resolve_local_url(page: Path, url: str) -> Path | None:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or url.startswith(("#", "mailto:", "tel:", "javascript:", "//")):
        return None
    path = parts.path
    if not path:
        return None
    if path.startswith("/"):
        return Path(path.lstrip("/"))
    return Path(os.path.normpath((page.parent / path).as_posix()))


def rewrite_html(source_path: Path, data: bytes, bundled: set[Path]) -> bytes:
    page = source_path.relative_to(DOCS)
    text = data.decode("utf-8")

    def replace(match: re.Match[str]) -> str:
        url = match.group("url")
        local = resolve_local_url(page, url)
        if local is None:
            return match.group(0)
        normalized = Path(local.as_posix())
        if normalized in bundled:
            return match.group(0)
        if normalized == Path("index.html"):
            replacement = "/"
        elif normalized.suffix.lower() == ".html":
            replacement = CANONICAL_BASE + normalized.as_posix()
            query = urlsplit(url).query
            fragment = urlsplit(url).fragment
            if query:
                replacement += f"?{query}"
            if fragment:
                replacement += f"#{fragment}"
        else:
            return match.group(0)
        return f'{match.group("prefix")}{replacement}{match.group("suffix")}'

    return URL_ATTRIBUTE.sub(replace, text).encode("utf-8")


def build_bundle() -> dict[Path, bytes]:
    paths = bundle_paths()
    bundled = set(paths)
    result: dict[Path, bytes] = {}
    for relative in paths:
        source = DOCS / relative
        if not source.is_file():
            raise FileNotFoundError(f"Missing canonical source: {source.relative_to(ROOT)}")
        data = source.read_bytes()
        if source.suffix.lower() == ".html":
            data = rewrite_html(source, data, bundled)
        result[relative] = data
    return result


def manifest_bytes(bundle: dict[Path, bytes]) -> bytes:
    payload = {
        "canonical_source": "beaumont-intelligence",
        "destination": "moving-beaumont-forward/public",
        "files": [
            {"path": path.as_posix(), "bytes": len(data), "sha256": sha256(data)}
            for path, data in bundle.items()
        ],
    }
    return (json.dumps(payload, indent=2) + "\n").encode("utf-8")


def validate_local_links(bundle: dict[Path, bytes]) -> list[str]:
    available = set(bundle)
    errors: list[str] = []
    for page, data in bundle.items():
        if page.suffix.lower() != ".html":
            continue
        text = data.decode("utf-8")
        for match in URL_ATTRIBUTE.finditer(text):
            url = match.group("url")
            local = resolve_local_url(page, url)
            if local is None or url.startswith("/"):
                continue
            normalized = Path(local.as_posix())
            if normalized not in available:
                errors.append(f"{page.as_posix()}: missing exported dependency {url}")
    return errors


def check_target(target: Path, bundle: dict[Path, bytes]) -> list[str]:
    errors: list[str] = []
    expected = dict(bundle)
    expected[Path(MANIFEST_NAME)] = manifest_bytes(bundle)
    for relative, data in expected.items():
        destination = target / relative
        if not destination.is_file():
            errors.append(f"missing: {relative.as_posix()}")
        elif destination.read_bytes() != data:
            errors.append(f"out of date: {relative.as_posix()}")
    return errors


def sync_target(target: Path, bundle: dict[Path, bytes]) -> tuple[int, int]:
    written = 0
    unchanged = 0
    expected = dict(bundle)
    expected[Path(MANIFEST_NAME)] = manifest_bytes(bundle)
    for relative, data in expected.items():
        destination = target / relative
        if destination.is_file() and destination.read_bytes() == data:
            unchanged += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        written += 1
    return written, unchanged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize canonical Council Intelligence publication files to MBF public assets."
    )
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="MBF public directory")
    parser.add_argument("--check", action="store_true", help="Fail if the target is missing or out of date")
    args = parser.parse_args()

    target = args.target.resolve()
    bundle = build_bundle()
    local_errors = validate_local_links(bundle)
    if local_errors:
        print("Council Intelligence export has unresolved local links:", file=sys.stderr)
        for error in local_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.check:
        errors = check_target(target, bundle)
        if errors:
            print(f"Council Intelligence export is not current in {target}:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        print(f"Council Intelligence export is current ({len(bundle)} files).")
        return 0

    written, unchanged = sync_target(target, bundle)
    print(f"Synchronized Council Intelligence to {target}: {written} written, {unchanged} unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
