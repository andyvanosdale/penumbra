"""Data fetcher: pulls the raw vendor files the spec names into a storage root
and keeps them current without re-downloading what is already there.

Storage root is a path or URL understood by fsspec: a directory on a laptop,
a mounted volume, or an S3-compatible bucket (``s3://bucket/prefix``).

Entry point: ``python -m ingest.fetch_data``.
"""
