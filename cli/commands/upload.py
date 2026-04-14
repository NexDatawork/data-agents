"""Upload command for the OpenGraph AI CLI.

Resolves a dataset folder by name under the input directory and uploads it to
Google Cloud Storage.
"""

import os
from pathlib import Path

import typer

from engine.upload.gcp import DEFAULT_GCS_PREFIX
from engine.upload.gcp import load_local_env
from engine.upload.gcp import upload_dataset_to_gcs


def _resolve_dataset_folder(dataset_name: str, input_root: str) -> Path:
    """Resolve a dataset folder by name from within the input root.

    The command accepts the dataset folder name, not a full path. The folder is
    searched recursively under ``input_root`` so datasets like
    ``input/User-DL/Airline+Loyalty+Program`` can be referenced simply as
    ``Airline+Loyalty+Program``.
    """
    root = Path(input_root)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Input root not found: {root}")

    matches = sorted(
        path for path in root.rglob("*") if path.is_dir() and path.name == dataset_name
    )

    if not matches:
        raise ValueError(
            f"Dataset folder '{dataset_name}' was not found under {root}"
        )
    if len(matches) > 1:
        options = ", ".join(str(path) for path in matches)
        raise ValueError(
            f"Multiple dataset folders named '{dataset_name}' were found under {root}: {options}"
        )

    return matches[0]


def upload(
    dataset_name: str = typer.Argument(
        ..., help="Dataset folder name to upload from the input directory."
    ),
    input_root: str = typer.Option(
        "./input",
        "--input-root",
        help="Root folder that contains dataset directories.",
    ),
    bucket: str | None = typer.Option(
        None,
        "--bucket",
        help="Override GCS bucket name. Defaults to GCS_BUCKET from .env.local.",
    ),
    project_id: str | None = typer.Option(
        None,
        "--project-id",
        help="Override GCP project ID. Defaults to GCP_PROJECT_ID from .env.local.",
    ),
    prefix: str | None = typer.Option(
        None,
        "--prefix",
        help="Destination folder prefix inside the bucket.",
    ),
    credentials: str | None = typer.Option(
        None,
        "--credentials",
        help="Path to a Google service-account JSON key file.",
    ),
) -> None:
    """Upload an input dataset folder to Google Cloud Storage."""
    load_local_env()

    try:
        source = _resolve_dataset_folder(dataset_name, input_root)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    resolved_project_id = project_id or os.environ.get("GCP_PROJECT_ID")
    resolved_bucket = bucket or os.environ.get("GCS_BUCKET")
    resolved_prefix = prefix or os.environ.get("GCS_PREFIX", DEFAULT_GCS_PREFIX)
    credentials_path = credentials or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_path:
        expanded_credentials_path = Path(credentials_path).expanduser()
        if not expanded_credentials_path.exists():
            typer.echo(
                f"Error: credentials file not found: {expanded_credentials_path}",
                err=True,
            )
            raise typer.Exit(code=1)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(expanded_credentials_path)

    if not resolved_project_id:
        typer.echo(
            "Error: missing GCP_PROJECT_ID. Set it in .env.local or pass --project-id.",
            err=True,
        )
        raise typer.Exit(code=1)
    if not resolved_bucket:
        typer.echo(
            "Error: missing GCS_BUCKET. Set it in .env.local or pass --bucket.",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(f"Uploading dataset folder '{dataset_name}' from {source} ...")

    try:
        uploaded = upload_dataset_to_gcs(
            source,
            project_id=resolved_project_id,
            bucket_name=resolved_bucket,
            prefix=resolved_prefix,
        )
    except Exception as exc:
        typer.echo(f"Upload failed: {exc}", err=True)
        if not credentials_path:
            typer.echo(
                "Tip: set GOOGLE_APPLICATION_CREDENTIALS in .env.local or pass --credentials /path/to/key.json",
                err=True,
            )
        raise typer.Exit(code=1) from exc

    typer.echo(
        f"Done. Uploaded {uploaded} file(s) for dataset '{dataset_name}' to gs://{resolved_bucket}/{resolved_prefix.strip('/')}/"
    )