"""Validates that samples.yml covers every sample directory.

Rules enforced:
1. Every directory in the repo root that is not dot/underscore-prefixed,
    not gitignored, and not in excluded_dirs,
   must be listed in samples.yml.
2. Every sample with ci: true must have a test_command.
3. Every sample with docs: true must also have ci: true
   (if it's in the pynenc documentation, it must be tested).
4. No sample in samples.yml can point to a directory that doesn't exist.
"""

import pathlib
import subprocess

import pytest
import yaml

ROOT = pathlib.Path(__file__).parent
MANIFEST = ROOT / "samples.yml"


def _is_gitignored(path: pathlib.Path) -> bool:
    """Return True if path is ignored by git ignore rules."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", str(path.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
    except (FileNotFoundError, ValueError):
        # If git is unavailable or relative path can't be computed, don't auto-ignore.
        return False
    return result.returncode == 0


@pytest.fixture(scope="module")
def manifest():
    with open(MANIFEST) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def sample_dirs():
    """All directories in repo root that look like sample folders."""
    return {
        d.name for d in ROOT.iterdir() if d.is_dir() and not d.name.startswith((".", "_")) and not _is_gitignored(d)
    }


@pytest.fixture(scope="module")
def existing_dirs():
    """All existing root directories regardless of ignore status."""
    return {d.name for d in ROOT.iterdir() if d.is_dir()}


def test_manifest_exists():
    assert MANIFEST.exists(), "samples.yml not found at repo root"


def test_every_directory_is_listed(manifest, sample_dirs):
    """Every sample-like directory must appear in samples.yml."""
    excluded = set(manifest.get("excluded_dirs", []))
    listed = set(manifest.get("samples", {}).keys())
    unlisted = sample_dirs - listed - excluded
    assert not unlisted, f"Directories not listed in samples.yml: {unlisted}. Add them to 'samples' or 'excluded_dirs'."


def test_no_phantom_samples(manifest, existing_dirs):
    """Every sample in the manifest must have a corresponding directory."""
    listed = set(manifest.get("samples", {}).keys())
    missing = listed - existing_dirs
    assert not missing, f"Samples in manifest but directory not found: {missing}"


def test_ci_samples_have_test_command(manifest):
    """Samples with ci: true must define a test_command."""
    for name, cfg in manifest.get("samples", {}).items():
        if cfg.get("ci"):
            assert cfg.get("test_command"), f"Sample '{name}' has ci: true but no test_command"


def test_documented_samples_have_ci(manifest):
    """Samples referenced in pynenc docs (docs: true) must have CI enabled."""
    for name, cfg in manifest.get("samples", {}).items():
        if cfg.get("docs"):
            assert cfg.get("ci"), (
                f"Sample '{name}' is referenced in pynenc docs (docs: true) "
                f"but has ci: false. Documented samples must be tested."
            )
