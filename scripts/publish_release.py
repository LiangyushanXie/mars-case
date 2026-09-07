#!/usr/bin/env python3
"""Publish a checksum-verified upstream ZIP as bounded GitHub Release parts."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_SIZE = 1536 * 1024 * 1024


def main():
    source = json.loads((ROOT / "metadata/sources.json").read_text())["archives"][0]
    output = ROOT / "release-data"
    output.mkdir(exist_ok=True)
    if shutil.disk_usage(output).free < source["bytes"] + 1024**3:
        raise RuntimeError("Insufficient runner disk space for the official dataset")
    completed_manifest = output / "parts.json"
    if not completed_manifest.exists():
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        parts = []
        total = 0
        # Curl handles HTTPS redirects; no credentials are sent to the data source.
        process = subprocess.Popen(
            ["curl", "-fLsS", "--connect-timeout", "30", source["url"]],
            stdout=subprocess.PIPE,
        )
        try:
            while total < source["bytes"]:
                name = source["name"] + f".part{len(parts):02d}"
                path = output / name
                part_hash = hashlib.sha256()
                size = 0
                with path.open("wb") as part:
                    while size < PART_SIZE and total < source["bytes"]:
                        block = process.stdout.read(
                            min(
                                4 * 1024 * 1024,
                                PART_SIZE - size,
                                source["bytes"] - total,
                            )
                        )
                        if not block:
                            raise RuntimeError(
                                "Upstream download ended before its declared size"
                            )
                        part.write(block)
                        md5.update(block)
                        sha256.update(block)
                        part_hash.update(block)
                        size += len(block)
                        total += len(block)
                parts.append(
                    {"name": name, "bytes": size, "sha256": part_hash.hexdigest()}
                )
                print(f"Downloaded {total}/{source['bytes']} bytes", flush=True)
            if process.stdout.read(1) or process.wait() != 0:
                raise RuntimeError("Unexpected source size or failed curl transfer")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()
        if md5.hexdigest() != source["hashes"]["md5"]:
            raise RuntimeError("Official MD5 mismatch; nothing will be uploaded")
        manifest = {
            "archive": source["name"],
            "bytes": total,
            "md5": md5.hexdigest(),
            "sha256": sha256.hexdigest(),
            "source_url": source["url"],
            "license": "CC-BY-4.0",
            "parts": parts,
        }
        completed_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    manifest = json.loads(completed_manifest.read_text())
    notes = output / "release-notes.md"
    notes.write_text(
        "AI4MARS merged v0.6, redistributed in unchanged byte-order parts under CC BY 4.0.\n\nSource and attribution: https://zenodo.org/records/15995036 (NASA JPL / AI4Mars authors).\n\nThe complete stream was checked against the official MD5 before upload. Download parts.json and all listed parts, concatenate them in manifest order, and verify the complete hash before extracting. No model training or accuracy claim is associated with this data release.\n"
    )
    tag = "ai4mars-0.6-data"
    lookup = subprocess.run(
        ["gh", "release", "view", tag], capture_output=True, check=False
    )
    if lookup.returncode:
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                tag,
                "--draft",
                "--title",
                "AI4MARS 0.6 public data",
                "--notes-file",
                str(notes),
            ],
            check=True,
        )
    for name in ["parts.json", *[part["name"] for part in manifest["parts"]]]:
        subprocess.run(
            ["gh", "release", "upload", tag, str(output / name), "--clobber"],
            check=True,
        )
        print("Uploaded", name, flush=True)
    subprocess.run(["gh", "release", "edit", tag, "--draft=false"], check=True)


if __name__ == "__main__":
    main()
