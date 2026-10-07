"""Download public CSV/ZIP files from Bonanza Creek LTER data pages."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

LTER_BASE = "http://www.lter.uaf.edu"
DOWNLOAD = f"{LTER_BASE}/php/download_data.php?f=/data_files/ascii/files"


def list_data_files(dataset_id: int) -> list[str]:
    """Return filenames linked from an LTER data-detail page."""
    url = f"{LTER_BASE}/data/data-detail/id/{dataset_id}"
    with urllib.request.urlopen(url, timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")
    pattern = rf'download_data\.php\?f=/data_files/ascii/files/([^"]+)'
    return sorted(set(re.findall(pattern, html)))


def download_file(filename: str, dest: Path, *, force: bool = False) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force and dest.stat().st_size > 500:
        return dest
    url = f"{DOWNLOAD}/{filename}"
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    if len(data) < 500 and b"<!DOCTYPE html" in data[:200]:
        raise RuntimeError(f"LTER download returned HTML for {filename}")
    dest.write_bytes(data)
    return dest


def download_dataset_files(
    dataset_id: int,
    cache_dir: Path,
    *,
    pattern: str | None = None,
    force: bool = False,
) -> list[Path]:
    """Download all (or pattern-matched) files for an LTER dataset."""
    names = list_data_files(dataset_id)
    if pattern:
        rx = re.compile(pattern)
        names = [n for n in names if rx.search(n)]
    paths = []
    for name in names:
        paths.append(download_file(name, cache_dir / name, force=force))
    return paths
