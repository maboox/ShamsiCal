"""Build a Windows portable release without installing packages or bundling user data."""

import hashlib
import importlib.metadata as metadata
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from shamsical import __version__

ROOT = Path(__file__).resolve().parent


def runtime_licenses(target):
    names = [
        line.split("==")[0]
        for line in (ROOT / "requirements.lock").read_text().splitlines()
        if line and not line.startswith(("#", " "))
    ]
    for name in [*names, "pyinstaller"]:
        dist = metadata.distribution(name)
        for entry in dist.files or []:
            path = Path(str(entry))
            if ".." in path.parts or not any(
                "license" in part.lower() or part.upper().startswith(("COPYING", "NOTICE"))
                for part in path.parts
            ):
                continue
            source = Path(dist.locate_file(entry))
            if source.is_file():
                destination = target / name / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.exists():
        shutil.copyfile(python_license, target / "Python-LICENSE.txt")
    shutil.copytree(ROOT / "shamsical/assets/licenses", target / "icons", dirs_exist_ok=True)


def main():
    if sys.platform != "win32":
        raise SystemExit("Build Windows releases on Windows. Source installation works on other platforms.")
    try:
        import PyInstaller
    except ImportError as error:
        raise SystemExit("Install requirements-dev.txt before building.") from error
    print(f"Building ShamsiCal {__version__} with PyInstaller {PyInstaller.__version__}")
    # Build tools must not accidentally collect unrelated DLLs from a host's
    # PATH (for example another application's incompatible ICU runtime).
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    clean_path = os.pathsep.join(
        [
            str(Path(sys.executable).parent),
            str(Path(sys.base_prefix)),
            str(system_root / "System32"),
            str(system_root),
        ]
    )
    env = {**os.environ, "PYTHONHASHSEED": "0", "PATH": clean_path}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--windowed",
            "--name",
            "ShamsiCal",
            "--additional-hooks-dir",
            str(ROOT / "tools/hooks"),
            "--collect-data",
            "shamsical",
            "--icon",
            str(ROOT / "shamsical/assets/app.ico"),
            "--version-file",
            str(ROOT / "tools/windows_version.txt"),
            str(ROOT / "shamsi_calendar_widget.pyw"),
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    folder = ROOT / "dist/ShamsiCal"
    for name in ("LICENSE", "README.md", "README.fa.md", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md"):
        shutil.copyfile(ROOT / name, folder / name)
    shutil.copytree(ROOT / "docs", folder / "docs", dirs_exist_ok=True)
    runtime_licenses(folder / "licenses")
    archive = ROOT / "dist" / f"ShamsiCal-{__version__}-windows-x64.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(folder.parent))
    digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
    archive.with_suffix(archive.suffix + ".sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="ascii"
    )
    print(f"Release ready: {archive.name}\nSHA256: {digest}")


if __name__ == "__main__":
    main()
