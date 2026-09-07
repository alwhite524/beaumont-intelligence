"""Convert YouTube's rolling auto-caption VTT into a readable timestamped transcript."""
from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def clock(value: str) -> str:
    hours, minutes, seconds = value.split(":")
    total = int(hours) * 3600 + int(minutes) * 60 + int(float(seconds))
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}:{m:02d}:{s:02d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-url", required=True)
    args = parser.parse_args()

    blocks = re.split(r"\r?\n\r?\n", args.input.read_text(encoding="utf-8"))
    cues: list[tuple[str, str]] = []
    previous = ""
    for block in blocks:
        lines = block.splitlines()
        if not lines or " --> " not in lines[0]:
            continue
        start = lines[0].split(" --> ", 1)[0]
        text = " ".join(lines[1:])
        text = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        if not text or text == previous or previous.endswith(text):
            continue
        if previous and text.startswith(previous):
            text = text[len(previous):].strip()
        if text:
            cues.append((clock(start), text))
        previous = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", " ".join(lines[1:])))).strip()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{args.title}\n{args.source_url}\n\nTranscript:\n")
        for timestamp, text in cues:
            handle.write(f"({timestamp}) {text}\n")
    print(f"Transcript: {args.output} ({len(cues)} cues)")


if __name__ == "__main__":
    main()
