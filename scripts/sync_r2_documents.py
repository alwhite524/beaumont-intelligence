"""Upload site PDFs to Cloudflare R2 and verify the public archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from pathlib import Path

import boto3
from botocore.config import Config


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CREDENTIALS = ROOT / ".r2.local.json"
MANIFEST = ROOT / "data" / "document-storage-manifest.json"


def pdf_files() -> list[Path]:
    roots = (DOCS / "official-documents", DOCS / "records" / "agenda-packets")
    return sorted(path for root in roots for path in root.rglob("*.pdf"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument(
        "--verify-manifest",
        action="store_true",
        help="Verify already-migrated objects without requiring local PDFs.",
    )
    args = parser.parse_args()

    settings = json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    client = boto3.client(
        "s3",
        endpoint_url=settings["endpoint"],
        aws_access_key_id=settings["accessKeyId"],
        aws_secret_access_key=settings["secretAccessKey"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    if args.verify_manifest:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for index, record in enumerate(manifest["documents"], start=1):
            remote = client.head_object(
                Bucket=settings["bucket"], Key=record["path"]
            )
            if remote["ContentLength"] != record["bytes"]:
                raise RuntimeError(f'Remote size mismatch: {record["path"]}')
            if remote.get("Metadata", {}).get("sha256") != record["sha256"]:
                raise RuntimeError(
                    f'Remote checksum metadata mismatch: {record["path"]}'
                )
            print(
                f'[{index}/{manifest["document_count"]}] verified '
                f'{record["path"]}'
            )
        return

    existing_records = {}
    if MANIFEST.exists():
        existing = json.loads(MANIFEST.read_text(encoding="utf-8"))
        existing_records = {
            record["path"]: record for record in existing.get("documents", [])
        }

    local_pdfs = pdf_files()
    for index, path in enumerate(local_pdfs, start=1):
        key = path.relative_to(DOCS).as_posix()
        checksum = sha256(path)
        remote = None
        try:
            remote = client.head_object(Bucket=settings["bucket"], Key=key)
        except client.exceptions.ClientError as error:
            if error.response.get("Error", {}).get("Code") not in {"404", "NoSuchKey"}:
                raise

        already_current = (
            remote is not None
            and remote["ContentLength"] == path.stat().st_size
            and remote.get("Metadata", {}).get("sha256") == checksum
        )
        if not args.verify_only and not already_current:
            client.upload_file(
                str(path),
                settings["bucket"],
                key,
                ExtraArgs={
                    "ContentType": mimetypes.guess_type(path.name)[0]
                    or "application/pdf",
                    "ContentDisposition": "inline",
                    "CacheControl": "public, max-age=3600",
                    "Metadata": {"sha256": checksum},
                },
            )

        remote = client.head_object(Bucket=settings["bucket"], Key=key)
        if remote["ContentLength"] != path.stat().st_size:
            raise RuntimeError(f"Remote size mismatch: {key}")
        if remote.get("Metadata", {}).get("sha256") != checksum:
            raise RuntimeError(f"Remote checksum metadata mismatch: {key}")

        existing_records[key] = {
            "path": key,
            "url": f'{settings["publicBaseUrl"].rstrip("/")}/{key}',
            "bytes": path.stat().st_size,
            "sha256": checksum,
        }
        print(f"[{index}/{len(local_pdfs)}] verified {key}")

    records = [existing_records[key] for key in sorted(existing_records)]

    MANIFEST.write_text(
        json.dumps(
            {
                "bucket": settings["bucket"],
                "public_base_url": settings["publicBaseUrl"],
                "document_count": len(records),
                "total_bytes": sum(record["bytes"] for record in records),
                "documents": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
