"""
app/r2.py

Cloudflare R2 storage helper (S3-compatible).

All project images are stored in R2 instead of the local filesystem so the
repository stays small and Railway deploys stay fast.

Public URL format:  {R2_PUBLIC_URL}/{key}
                    e.g. https://pub-xxx.r2.dev/images/projects/slug/card/img.jpg

R2 key mirrors the old static-file relative path so existing DB values can be
migrated by simply prepending the public base URL.

Environment variables required:
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET_NAME
    R2_ENDPOINT_URL   (https://<account-id>.r2.cloudflarestorage.com)
    R2_PUBLIC_URL     (https://pub-<id>.r2.dev  — no trailing slash)
"""

from __future__ import annotations

import os
from pathlib import Path


def _client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def _bucket() -> str:
    return os.environ["R2_BUCKET_NAME"]


def _public_base() -> str:
    return os.environ["R2_PUBLIC_URL"].rstrip("/")


def upload_file(file_obj, key: str, content_type: str | None = None) -> str:
    """
    Upload a file-like object to R2 under *key* and return its public URL.
    file_obj can be a Werkzeug FileStorage, a BytesIO, or any readable binary.
    """
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    _client().upload_fileobj(file_obj, _bucket(), key, ExtraArgs=extra or None)
    return f"{_public_base()}/{key}"


def upload_path(local_path: Path, key: str) -> str:
    """Upload a local file by path and return its public URL."""
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(local_path))
    with open(local_path, "rb") as f:
        return upload_file(f, key, content_type=content_type)


def delete_key(key: str) -> None:
    """Delete an object from R2 by key. Silently succeeds if the key does not exist."""
    try:
        _client().delete_object(Bucket=_bucket(), Key=key)
    except Exception:
        pass


def key_from_url(url: str) -> str | None:
    """
    Extract the R2 key from a public URL, or return None if the URL is not
    from this bucket.
    """
    base = _public_base()
    if url.startswith(base + "/"):
        return url[len(base) + 1:]
    return None


def is_r2_url(value: str) -> bool:
    """Return True if the value looks like an R2 public URL (not a relative path)."""
    return value.startswith("https://")
