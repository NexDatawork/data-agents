from pathlib import Path

from engine.upload.gcp import destination_blob_name
from engine.upload.gcp import iter_source_files


def test_destination_blob_name_for_single_file() -> None:
    source = Path("input/data.csv")
    file_path = Path("input/data.csv")

    blob_name = destination_blob_name(source, file_path, "opengraph-ai/input")

    assert blob_name == "opengraph-ai/input/data.csv"


def test_destination_blob_name_for_directory() -> None:
    source = Path("input/Airline+Loyalty+Program")
    file_path = source / "customers.csv"

    blob_name = destination_blob_name(source, file_path, "opengraph-ai/input")

    assert blob_name == "opengraph-ai/input/Airline+Loyalty+Program/customers.csv"


def test_iter_source_files_recurses_and_sorts(tmp_path: Path) -> None:
    source = tmp_path / "dataset"
    nested = source / "nested"
    nested.mkdir(parents=True)
    (source / "b.csv").write_text("b", encoding="utf-8")
    (nested / "a.csv").write_text("a", encoding="utf-8")

    files = iter_source_files(source)

    assert [path.relative_to(source).as_posix() for path in files] == [
        "b.csv",
        "nested/a.csv",
    ]
