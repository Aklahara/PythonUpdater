import gzip
import json
import re
import subprocess
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class PythonRelease:
    version: str        # e.g. "3.13.1" or "3.15.0a2"
    prerelease: bool
    tarball_url: str = ""


@dataclass
class BuildFlags:
    optimizations: bool = False  # --enable-optimizations
    lto: bool = False            # --with-lto
    no_gil: bool = False         # --disable-gil
    jit: bool = False            # --enable-experimental-jit


@dataclass
class PythonMajorVersion:
    major_version: str                     # e.g. "3.13"
    releases: list                  # list[PythonRelease], sorted newest first
    installed_version: Optional[str] = None
    active: bool = True
    build_flags: Optional[BuildFlags] = None

    @property
    def latest(self) -> Optional[str]:
        return self.releases[0].version if self.releases else None

    @property
    def needs_update(self) -> bool:
        return (
            self.latest is not None
            and self.latest != self.installed_version
        )


def _version_tuple(v: str) -> tuple[int, int, int, str]:
    """Convert version string to comparable tuple. Pre-releases sort before finals."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)(.*)", v)
    if not match:
        return 0, 0, 0, "z"
    major, minor, patch, pre = match.groups()
    # Empty pre = final release (sorts highest). "rc" > "b" > "a" alphabetically but all < final.
    pre_key = pre if pre else "z"
    return int(major), int(minor), int(patch), pre_key


def get_installed_version(major_version: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [f"python{major_version}", "--version"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout + result.stderr
        match = re.search(r"(\d+\.\d+\.\d+\w*)", output)
        return match.group(1) if match else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_build_flags(major_version: str) -> BuildFlags:
    """Detect build-time flags from an installed Python interpreter."""
    code = (
        "import sysconfig; v = sysconfig.get_config_vars(); "
        "a = v.get('CONFIG_ARGS', ''); "
        "print(int('enable-optimizations' in a), "
        "int('with-lto' in a), "
        "int(bool(v.get('Py_GIL_DISABLED', 0))), "
        "int(bool(v.get('_Py_JIT')) or 'experimental-jit' in a))"
    )
    result = subprocess.run(
        [f"python{major_version}", "-c", code],
        capture_output=True, text=True, timeout=5
    )
    parts = result.stdout.strip().split()
    assert len(parts) == 4
    o, lto, no_gil, jit = (bool(int(p)) for p in parts)
    return BuildFlags(optimizations=o, lto=lto, no_gil=no_gil, jit=jit)


def fetch_github_releases() -> list:
    try:
        # --refs filters out the peeled tags (e.g., v3.8.0^{})
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "--refs", "https://github.com/python/cpython.git"],
            capture_output=True, text=True, timeout=15, check=True
        )

        tags = []
        # Output lines look like: <hash>\trefs/tags/v3.12.0
        for line in result.stdout.splitlines():
            # Extract just the tag name from the end of the ref path
            ref_path = line.split("\t")[-1]
            if ref_path.startswith("refs/tags/"):
                tag_name = ref_path.replace("refs/tags/", "")
                tags.append({"name": tag_name})
        return tags
    except (subprocess.SubprocessError, FileNotFoundError):
        return []


def build_major_version_data() -> list:
    """Return a sorted list of Python Major Version from live data."""
    raw_releases = fetch_github_releases()

    major_version_map: dict[str, list] = {}

    for r in raw_releases:
        # Tags API uses "name" field; pre-releases are identified by version suffix
        tag = r.get("name", "")
        match = re.match(r"v(\d+\.\d+\.\d+\w*)", tag)
        if not match:
            continue
        version = match.group(1)

        major_version_match = re.match(r"(\d+\.\d+)", version)
        if not major_version_match:
            continue
        major_version = major_version_match.group(1)

        base_version = re.match(r"(\d+\.\d+\.\d+)", version).group(1)
        tarball_url = (
            f"https://www.python.org/ftp/python/{base_version}/Python-{version}.tgz"
        )
        # Pre-releases have a suffix like a1, b2, rc1
        is_prerelease = bool(re.search(r"[a-z]", version.split(".")[-1]))

        release = PythonRelease(
            version=version,
            prerelease=is_prerelease,
            tarball_url=tarball_url,
        )
        major_version_map.setdefault(major_version, []).append(release)

    result = []
    for major_version, releases in major_version_map.items():
        releases.sort(key=lambda r_: _version_tuple(r_.version), reverse=True)
        installed = get_installed_version(major_version)
        flags = get_build_flags(major_version) if installed else None
        result.append(PythonMajorVersion(
            major_version=major_version,
            releases=releases,
            installed_version=installed,
            active=True,
            build_flags=flags,
        ))

    # Installed major_version first, then newest major_version to oldest
    def sort_key(s: PythonMajorVersion) -> tuple:
        major, minor = map(int, s.major_version.split("."))
        has_installed = 0 if s.installed_version else 1
        return has_installed, -major, -minor

    result.sort(key=sort_key)
    return result

