#!/usr/bin/env python3
"""
Package a draw.io reconstruction project into a zip file.

Usage:
    python scripts/package_drawio_project.py /path/to/project output.zip
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def package_project(project_dir: Path, output_zip: Path) -> None:
    project_dir = project_dir.resolve()
    output_zip = output_zip.resolve()
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in project_dir.rglob("*"):
            if path.is_file() and path != output_zip:
                zf.write(path, path.relative_to(project_dir.parent))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python package_drawio_project.py /path/to/project output.zip", file=sys.stderr)
        sys.exit(1)
    package_project(Path(sys.argv[1]), Path(sys.argv[2]))
