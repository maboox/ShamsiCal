"""Validate and smoke-test a locally built Windows ZIP in a fresh directory."""

import hashlib
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def verify(archive):
    archive = Path(archive).resolve()
    expected = archive.with_suffix(archive.suffix + ".sha256").read_text().split()[0]
    with archive.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise RuntimeError("Checksum mismatch")
    with (
        zipfile.ZipFile(archive) as bundle,
        tempfile.TemporaryDirectory(prefix="shamsical-release-") as target,
    ):
        names = bundle.namelist()
        required = [
            "ShamsiCal/ShamsiCal.exe",
            "ShamsiCal/LICENSE",
            "ShamsiCal/licenses/Python-LICENSE.txt",
            "ShamsiCal/licenses/icons/Phosphor-MIT.txt",
            "ShamsiCal/_internal/shamsical/assets/fonts/OFL.txt",
        ]
        if not all(name in names for name in required):
            raise RuntimeError("Missing executable, resources, or license notice")
        for name in names:
            resolved = (Path(target) / name).resolve()
            if not resolved.is_relative_to(Path(target).resolve()):
                raise RuntimeError("Archive path escapes extraction directory")
            if any(
                part in (".env", ".venv", ".git", "workspace.json", "workspace.json.bak", "events_cache.json")
                for part in Path(name).parts
            ):
                raise RuntimeError("Unexpected private or development data in archive")
            if "qtawesome/fonts/" in name and "phosphor" not in name:
                raise RuntimeError("Unused icon font was bundled")
        bundle.extractall(target)
        exe = Path(target) / "ShamsiCal/ShamsiCal.exe"
        result = subprocess.run(
            [str(exe), "--smoke-test"], timeout=60, env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}
        )
        if result.returncode:
            raise RuntimeError(f"Extracted app smoke test failed: {result.returncode}")
    print(f"Verified checksum, archive contents, licenses, and extracted GUI startup: {archive.name}")


if __name__ == "__main__":
    verify(sys.argv[1])
