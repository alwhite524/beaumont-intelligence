"""Create a timestamped Council-meeting transcript from a local media file."""
from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from faster_whisper import BatchedInferencePipeline, WhisperModel


def timestamp(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="small.en")
    parser.add_argument("--chunk-seconds", type=int, default=1800)
    args = parser.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    transcriber = BatchedInferencePipeline(model=model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="beaumont-transcript-") as temp_dir:
        chunk_pattern = str(Path(temp_dir) / "chunk-%03d.wav")
        subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
                "-i", str(args.input), "-f", "segment", "-segment_time",
                str(args.chunk_seconds), "-ac", "1", "-ar", "16000", chunk_pattern,
            ],
            check=True,
        )
        chunks = sorted(Path(temp_dir).glob("chunk-*.wav"))
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(
                "AI-generated transcript from the public City Council meeting recording. "
                "Verify quotations against the linked video.\n"
            )
            handle.write("Source: https://www.youtube.com/watch?v=K6OHlAsz0oA\n\n")
            for index, chunk in enumerate(chunks):
                segments, info = transcriber.transcribe(
                    str(chunk),
                    language="en",
                    vad_filter=True,
                    beam_size=1,
                    batch_size=16,
                )
                offset = index * args.chunk_seconds
                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        handle.write(f"({timestamp(offset + segment.start)}) {text}\n")
                        handle.flush()
                print(f"Completed chunk {index + 1} of {len(chunks)}", flush=True)
    print(f"Language: {info.language} ({info.language_probability:.3f})")
    print(f"Transcript: {args.output}")


if __name__ == "__main__":
    main()
