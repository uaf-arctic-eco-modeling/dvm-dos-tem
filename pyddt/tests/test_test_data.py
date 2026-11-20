import hashlib
import json
import tarfile
from pathlib import Path

import pytest

from pyddt.util.test_data import BundleError, ensure_bundle


def _write_bundle(tmp_path, contents=b"input"):
    source = tmp_path / "source"
    source.mkdir()
    (source / "data.txt").write_bytes(contents)
    archive = tmp_path / "bundle.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(source / "data.txt", arcname="data/data.txt")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive, digest, archive.stat().st_size


def _write_lock(path, archive, digest, size):
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "bundle": {
                    "id": "test-bundle",
                    "release": "v0.1.0",
                    "asset_name": "bundle.tar.gz",
                    "url": archive.as_uri(),
                    "sha256": digest,
                    "size_bytes": size,
                },
            }
        )
    )


def test_ensure_bundle_downloads_verifies_and_reuses_cache(tmp_path):
    archive, digest, size = _write_bundle(tmp_path)
    lock = tmp_path / "bundle-lock.json"
    _write_lock(lock, archive, digest, size)
    cache = tmp_path / "cache"

    extracted = ensure_bundle(lock, cache)

    assert (extracted / "data/data.txt").read_bytes() == b"input"
    archive.unlink()
    assert ensure_bundle(lock, cache) == extracted


def test_ensure_bundle_rejects_mismatched_cached_archive(tmp_path):
    archive, digest, size = _write_bundle(tmp_path)
    lock = tmp_path / "bundle-lock.json"
    _write_lock(lock, archive, digest, size)
    cache = tmp_path / "cache"
    ensure_bundle(lock, cache)

    cached_archive = cache / "archives/bundle.tar.gz"
    cached_archive.write_bytes(b"tampered")

    with pytest.raises(BundleError, match="verification failed"):
        ensure_bundle(lock, cache)


def test_ensure_bundle_rejects_unsafe_archive_member(tmp_path):
    archive = tmp_path / "unsafe.tar.gz"
    source = tmp_path / "payload.txt"
    source.write_text("unsafe")
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(source, arcname="../escape.txt")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    lock = tmp_path / "bundle-lock.json"
    _write_lock(lock, archive, digest, archive.stat().st_size)

    with pytest.raises(BundleError, match="unsafe path"):
        ensure_bundle(lock, tmp_path / "cache")
