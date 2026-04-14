#!/usr/bin/env python3
"""Upload a dataset file or folder to Google Cloud Storage.

Examples:
    python upload_gcp.py input/Fintech_user/Fintech_user.csv
    python upload_gcp.py input/User-DL/Airline+Loyalty+Program
    python upload_gcp.py input/Fintech_user/Fintech_user.csv --prefix opengraph-ai/datasets
"""

from engine.upload.gcp import main


if __name__ == "__main__":
    raise SystemExit(main())
