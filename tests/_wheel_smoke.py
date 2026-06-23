from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def build_wheel_from_clean_source(
    python_cmd: list[str],
    *,
    root: Path,
    tmp_path: Path,
    wheel_dir: Path,
) -> None:
    """Build from a temp source copy so stale repo-local build/ artifacts cannot affect smoke tests."""

    source_dir = tmp_path / "wheel-source"
    if source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir()
    for filename in ("pyproject.toml", "README.md"):
        shutil.copy2(root / filename, source_dir / filename)
    shutil.copytree(root / "src", source_dir / "src")
    subprocess.run(
        [
            *python_cmd,
            "-m",
            "pip",
            "wheel",
            str(source_dir),
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheel_dir),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )
