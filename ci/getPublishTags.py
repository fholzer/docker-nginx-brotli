#!/usr/bin/env python3
"""
Determine Docker image tags for a specific nginx version.

Tag assignment rules:
- `v<x.y.z>` - always assigned to every published version
- `v<x.y>` - only assigned to the latest patch version for each minor version
- `latest` - only assigned to the latest stable release (even minor version)
- `mainline` - only assigned to the latest mainline release (odd minor version)

Usage:
    python3 getPublishTags.py <version>

The script reads versions.txt to determine:
- The latest stable and mainline versions (for 'latest' and 'mainline' tags)
- The latest patch per minor version (for 'v<x.y>' tags)

Output:
    When GITHUB_OUTPUT is set: Writes a multiline heredoc format to the file:
        NGINX_TAGS=<<EOF
        type=raw,value=<tag1>
        type=raw,value=<tag2>
        ...
        EOF
    When GITHUB_OUTPUT is not set: Prints a JSON array to stdout.
"""

import json
import os
import sys


def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a version string 'X.Y.Z' into a tuple of ints."""
    parts = version_str.strip().split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def is_stable(version_str: str) -> bool:
    """Stable versions have an even minor version number."""
    _, minor, _ = parse_version(version_str)
    return minor % 2 == 0


def get_latest_versions(versions: list[str]) -> tuple[str | None, str | None]:
    """
    Determine the latest stable and latest mainline versions from a list.

    Returns:
        Tuple of (latest_stable, latest_mainline)
    """
    stable = [v for v in versions if is_stable(v)]
    mainline = [v for v in versions if not is_stable(v)]

    stable.sort(key=parse_version, reverse=True)
    mainline.sort(key=parse_version, reverse=True)

    latest_stable = stable[0] if stable else None
    latest_mainline = mainline[0] if mainline else None

    return latest_stable, latest_mainline


def get_latest_patch_per_minor(versions: list[str]) -> dict[tuple[int, int], str]:
    """
    Get the latest patch version for each minor version.

    Returns:
        Dict mapping (major, minor) -> latest patch version string
    """
    minor_groups: dict[tuple[int, int], str] = {}
    for v in versions:
        major, minor, patch = parse_version(v)
        key = (major, minor)
        if key not in minor_groups or patch > parse_version(minor_groups[key])[2]:
            minor_groups[key] = v
    return minor_groups


def get_tags(version: str, latest_stable: str | None = None, latest_mainline: str | None = None, versions: list[str] | None = None) -> list[str]:
    """
    Generate Docker image tags for a given nginx version.

    Args:
        version: nginx version string (e.g., "1.30.4")
        latest_stable: the latest stable version (for 'latest' tag)
        latest_mainline: the latest mainline version (for 'mainline' tag)
        versions: list of all versions (to determine latest patch per minor)

    Returns:
        List of tag strings
    """
    major, minor, patch = parse_version(version)
    tags = [f"v{major}.{minor}.{patch}"]

    # Only add minor version tag if this is the latest patch for this minor
    if versions:
        latest_per_minor = get_latest_patch_per_minor(versions)
        if latest_per_minor.get((major, minor)) == version:
            tags.append(f"v{major}.{minor}")

    if is_stable(version):
        if latest_stable == version:
            tags.append("latest")
    else:
        if latest_mainline == version:
            tags.append("mainline")

    return tags


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print("Usage: getPublishTags.py <version>", file=sys.stderr)
        sys.exit(1)

    version = args[0]

    # Read versions.txt to determine latest stable and mainline
    with open("versions.txt", "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    versions = [line.strip() for line in raw_lines if line.strip()]

    if not versions:
        print("No versions found in versions.txt", file=sys.stderr)
        sys.exit(1)

    latest_stable, latest_mainline = get_latest_versions(versions)

    tags = get_tags(version, latest_stable, latest_mainline, versions)

    # Write to GITHUB_OUTPUT as multiline heredoc
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        lines = ["NGINX_TAGS<<EOF"]
        for tag in tags:
            lines.append(f"type=raw,value={tag}")
        lines.append("EOF")
        output = "\n".join(lines) + "\n"
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(output)
        print(f"Written to {github_output}: {output.strip()}")
    else:
        json_array = json.dumps(tags)
        print(json_array)


if __name__ == "__main__":
    main()
