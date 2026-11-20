"""Retrieve and verify immutable dvm-dos-tem test-data bundles."""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class BundleError(RuntimeError):
    """Raised when a pinned test-data bundle cannot be used."""


@dataclass(frozen=True)
class BundleSpec:
    """The archive identity and location declared by a lock file."""

    bundle_id: str
    release: str
    asset_name: str
    url: str
    sha256: str
    size_bytes: int


def load_bundle_spec(lock_file):
    """Load and validate one bundle specification from JSON."""
    path = Path(lock_file)
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        bundle = data["bundle"]
        spec = BundleSpec(
            bundle_id=bundle["id"],
            release=bundle["release"],
            asset_name=bundle["asset_name"],
            url=bundle["url"],
            sha256=bundle["sha256"],
            size_bytes=bundle["size_bytes"],
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise BundleError("Invalid test-data bundle lock file: {}".format(path)) from exc

    if len(spec.sha256) != 64 or any(
        character not in "0123456789abcdef" for character in spec.sha256
    ):
        raise BundleError("Bundle lock file contains an invalid SHA-256 digest.")
    if spec.size_bytes < 1:
        raise BundleError("Bundle lock file contains an invalid archive size.")
    return spec


def _sha256_and_size(path):
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _verify_archive(path, spec):
    digest, size = _sha256_and_size(path)
    if digest != spec.sha256 or size != spec.size_bytes:
        raise BundleError(
            "Pinned test-data bundle verification failed for {}: expected "
            "SHA-256 {} and {} bytes, got {} and {} bytes. Remove the invalid "
            "cached archive and retry.".format(
                path, spec.sha256, spec.size_bytes, digest, size
            )
        )


def _download_archive(spec, destination):
    partial = Path(str(destination) + ".partial")
    try:
        with urllib.request.urlopen(spec.url) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output)
    except (OSError, urllib.error.URLError) as exc:
        partial.unlink(missing_ok=True)
        raise BundleError(
            "Unable to download pinned test-data bundle {} from {}: {}".format(
                spec.bundle_id, spec.url, exc
            )
        ) from exc
    partial.replace(destination)
    _verify_archive(destination, spec)


def _safe_members(archive):
    members = archive.getmembers()
    for member in members:
        member_path = Path(member.name)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise BundleError(
                "Refusing to extract unsafe path in test-data bundle: {}".format(
                    member.name
                )
            )
        if member.issym() or member.islnk():
            raise BundleError(
                "Refusing to extract links in test-data bundle: {}".format(member.name)
            )
    return members


def _extract_archive(archive_path, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=".extract-", dir=str(destination.parent))
    )
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(temporary, members=_safe_members(archive))
        temporary.replace(destination)
    except (OSError, tarfile.TarError, BundleError):
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def ensure_bundle(lock_file, cache_dir=None):
    """Return a verified extracted bundle path, downloading it when necessary."""
    spec = load_bundle_spec(lock_file)
    cache = Path(cache_dir or os.environ.get(
        "DVMDOSTEM_TEST_DATA_CACHE",
        os.path.expanduser("~/.cache/dvmdostem/test-data"),
    ))
    archive_path = cache / "archives" / spec.asset_name
    extracted_path = cache / "extracted" / "{}-{}".format(
        spec.bundle_id, spec.sha256[:12]
    )

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.exists():
        _verify_archive(archive_path, spec)
    else:
        _download_archive(spec, archive_path)

    if not extracted_path.exists():
        _extract_archive(archive_path, extracted_path)
    return extracted_path


def _parser():
    parser = argparse.ArgumentParser(
        description="Download and verify a pinned dvm-dos-tem test-data bundle."
    )
    parser.add_argument(
        "lock_file",
        help="JSON lock file containing the immutable bundle identity and digest.",
    )
    parser.add_argument(
        "--cache-dir",
        help="Cache directory (default: DVMDOSTEM_TEST_DATA_CACHE or ~/.cache/dvmdostem/test-data).",
    )
    return parser


def main(argv=None):
    """CLI entry point for fetching a pinned bundle."""
    args = _parser().parse_args(argv)
    try:
        print(ensure_bundle(args.lock_file, args.cache_dir))
    except BundleError as exc:
        print("Test-data bundle unavailable: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
