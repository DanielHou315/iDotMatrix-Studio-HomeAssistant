"""Version and changelog helper for releases.

    python scripts/release.py check          # VERSION, manifest and CHANGELOG agree
    python scripts/release.py bump 0.2.0     # prepare a release (run on a chore/release branch)
    python scripts/release.py notes 0.2.0    # print that version's changelog section

``VERSION`` is the source of truth; ``manifest.json`` must carry the same
version because Home Assistant and HACS read it from there. Merging a PR that
changes ``VERSION`` makes the release workflow tag and publish it.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
MANIFEST = ROOT / "custom_components/idm_studio/manifest.json"
CHANGELOG = ROOT / "CHANGELOG.md"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
UNRELEASED = "## [Unreleased]"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def parse(version: str) -> tuple[int, int, int]:
    match = SEMVER.match(version)
    if not match:
        fail(f"{version!r} is not a semantic version like 1.2.3")
    return tuple(int(part) for part in match.groups())


def current() -> str:
    return VERSION_FILE.read_text().strip()


def section(version: str) -> str | None:
    """Body of the changelog section for ``version`` (or ``Unreleased``)."""
    text = CHANGELOG.read_text()
    heading = UNRELEASED if version == "Unreleased" else f"## [{version}]"
    start = text.find(heading)
    if start == -1:
        return None
    start = text.index("\n", start) + 1
    end = text.find("\n## [", start)
    return text[start : end if end != -1 else len(text)].strip()


def check() -> None:
    version = current()
    parse(version)
    manifest = json.loads(MANIFEST.read_text())["version"]
    if manifest != version:
        fail(f"manifest.json has {manifest}, VERSION has {version}")
    if section("Unreleased") is None:
        fail(f"CHANGELOG.md needs a '{UNRELEASED}' section")
    if version != "0.0.0" and section(version) is None:
        fail(f"CHANGELOG.md has no section for {version}")
    print(f"ok: {version}")


def bump(version: str) -> None:
    if parse(version) <= parse(current()):
        fail(f"{version} is not newer than {current()}")
    notes = section("Unreleased")
    if not notes:
        fail("the Unreleased section of CHANGELOG.md is empty; describe the changes first")

    VERSION_FILE.write_text(version + "\n")
    manifest = MANIFEST.read_text()
    manifest = re.sub(r'"version": "[^"]+"', f'"version": "{version}"', manifest)
    MANIFEST.write_text(manifest)
    today = datetime.date.today().isoformat()
    CHANGELOG.write_text(
        CHANGELOG.read_text().replace(UNRELEASED, f"{UNRELEASED}\n\n## [{version}] - {today}", 1)
    )
    check()
    print(
        f"Next: commit as 'chore(release): v{version}' on branch chore/release-v{version} "
        "and open a PR. Merging it tags and publishes the release."
    )


def notes(version: str) -> None:
    body = section(version)
    if body is None:
        fail(f"CHANGELOG.md has no section for {version}")
    print(body)


def main() -> None:
    match sys.argv[1:]:
        case ["check"]:
            check()
        case ["bump", version]:
            bump(version)
        case ["notes", version]:
            notes(version)
        case _:
            print(__doc__)
            sys.exit(2)


if __name__ == "__main__":
    main()
