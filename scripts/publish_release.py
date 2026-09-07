#!/usr/bin/env python3
"""Publish a checksum-verified upstream ZIP as bounded GitHub Release parts."""

import hashlib
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from download_data import download_chunk

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
        parts = []
        ranges = list(range(0, source["bytes"], PART_SIZE))
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = []
            for index, start in enumerate(ranges):
                end = min(start + PART_SIZE, source["bytes"]) - 1
                name = source["name"] + f".part{index:02d}"
                futures.append(
                    pool.submit(
                        download_chunk,
                        source["url"],
                        source["bytes"],
                        start,
                        end,
                        output / name,
                    )
                )
                parts.append({"name": name, "bytes": end - start + 1})
            for done, future in enumerate(as_completed(futures), 1):
                future.result()
                print(f"Downloaded {done}/{len(parts)} complete parts", flush=True)
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        for part in parts:
            digest = hashlib.sha256()
            with (output / part["name"]).open("rb") as stream:
                for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                    md5.update(block)
                    sha256.update(block)
                    digest.update(block)
            part["sha256"] = digest.hexdigest()
        if md5.hexdigest() != source["hashes"]["md5"]:
            raise RuntimeError("Official MD5 mismatch; nothing will be uploaded")
        manifest = {
            "archive": source["name"],
            "bytes": source["bytes"],
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
