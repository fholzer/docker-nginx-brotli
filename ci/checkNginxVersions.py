#!/usr/bin/env python3
"""
Check for new nginx versions by comparing GitHub releases against versions.txt.

Fetches the latest releases from the nginx/nginx GitHub repository, classifies
them into stable (even minor version) and mainline (odd minor version) categories,
and compares against the versions tracked in versions.txt.

Usage:
    python3 checkNginxVersions.py --repo nginx/nginx --versions-file versions.txt [--output json] [--dry-run]

Output:
    JSON to stdout with missing versions per category.
    Exit code 0 on successful execution (regardless of whether missing versions were found).
    Exit code 2 on errors (e.g., API failure, missing files, invalid arguments).
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any


def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a version string 'X.Y.Z' into a tuple of ints."""
    parts = version_str.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version_str}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def is_stable(version_str: str) -> bool:
    """Stable versions have an even minor version number."""
    _, minor, _ = parse_version(version_str)
    return minor % 2 == 0


def classify_versions(versions: list[str]) -> dict[str, list[str]]:
    """Split versions into stable and mainline categories."""
    result: dict[str, list[str]] = {"stable": [], "mainline": []}
    for v in versions:
        if is_stable(v):
            result["stable"].append(v)
        else:
            result["mainline"].append(v)
    # Sort each category descending by version
    for category in result:
        result[category].sort(key=parse_version, reverse=True)
    return result


def extract_version_from_tag(tag: str) -> str | None:
    """Extract version from a GitHub release tag.

    Handles common nginx release tag formats:
    - 'release-1.30.4' -> '1.30.4'
    - 'v1.30.4' -> '1.30.4'
    """
    # Strip leading 'v' if present
    clean_tag = tag.lstrip("v")
    # Match 'release-X.Y.Z' or just 'X.Y.Z'
    match = re.match(r"^(?:release-)?(\d+\.\d+\.\d+)$", clean_tag)
    if match:
        return match.group(1)
    return None


def fetch_github_releases(owner: str, repo: str, per_page: int = 100) -> list[dict[str, Any]]:
    """Fetch releases from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    url += f"?per_page={per_page}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    # Add GITHUB_TOKEN if available for higher rate limit
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        req.add_header("Authorization", f"Bearer {github_token}")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.URLError as e:
        print(f"Error fetching GitHub releases: {e}", file=sys.stderr)
        sys.exit(2)


def find_missing_versions(
    releases: list[str], tracked: list[str]
) -> dict[str, list[str]]:
    """Find versions in releases that are not in tracked list.

    Only considers versions newer than the latest tracked version for each
    minor branch. Older deprecated minor branches are automatically excluded.
    """
    tracked_set = set(tracked)

    # Classify tracked versions to find the latest per minor branch
    classified_tracked = classify_versions(tracked)
    # Map: (major, minor) -> latest patch version for that minor branch
    latest_tracked_per_minor: dict[tuple[int, int], tuple[int, int, int]] = {}
    for category in classified_tracked:
        for v in classified_tracked[category]:
            major, minor, patch = parse_version(v)
            minor_key = (major, minor)
            if minor_key not in latest_tracked_per_minor:
                latest_tracked_per_minor[minor_key] = (major, minor, patch)

    missing: dict[str, list[str]] = {"stable": [], "mainline": []}

    for version in releases:
        # Skip if already tracked
        if version in tracked_set:
            continue

        v_tuple = parse_version(version)
        minor_key = (v_tuple[0], v_tuple[1])
        category = "stable" if is_stable(version) else "mainline"

        # Check if this minor branch has any tracked version
        if minor_key not in latest_tracked_per_minor:
            # No tracked version for this minor branch — skip (deprecated)
            continue

        # Only add if this version is newer than the latest tracked for this minor
        if v_tuple > latest_tracked_per_minor[minor_key]:
            missing[category].append(version)

    # Sort each category descending by version
    for category in missing:
        missing[category].sort(key=parse_version, reverse=True)

    return missing


def read_versions_file(filepath: str) -> list[str]:
    """Read and parse versions from versions.txt file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
        versions = [line.strip() for line in raw_lines if line.strip()]
        return versions
    except FileNotFoundError:
        print(f"Error: versions file not found: {filepath}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check for new nginx versions from GitHub releases"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="nginx/nginx",
        help="GitHub repository (owner/repo), default: nginx/nginx",
    )
    parser.add_argument(
        "--versions-file",
        type=str,
        default="versions.txt",
        help="Path to versions.txt file, default: versions.txt",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["json"],
        default="json",
        help="Output format, default: json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making any changes (for testing)",
    )
    args = parser.parse_args()

    # Parse repo owner and name
    parts = args.repo.split("/")
    if len(parts) != 2:
        print(f"Error: invalid repo format: {args.repo}", file=sys.stderr)
        sys.exit(2)
    owner, repo = parts

    # Read tracked versions
    tracked_versions = read_versions_file(args.versions_file)
    tracked_classified = classify_versions(tracked_versions)

    # Fetch GitHub releases
    releases_data = fetch_github_releases(owner, repo)

    # Extract versions from release tags
    github_versions: list[str] = []
    release_dates = {}
    for release in releases_data:
        tag = release.get("tag_name", "")
        version = extract_version_from_tag(tag)
        if version:
            github_versions.append(version)
            published_at = release.get("published_at", "")
            if published_at:
                release_dates[version] = published_at[:10]  # YYYY-MM-DD

    # Remove duplicates while preserving order (GitHub returns newest first)
    seen: set[str] = set()
    unique_versions: list[str] = []
    for v in github_versions:
        if v not in seen:
            seen.add(v)
            unique_versions.append(v)
    github_versions = unique_versions

    # Classify GitHub releases
    github_classified = classify_versions(github_versions)

    # Find missing versions
    missing = find_missing_versions(github_versions, tracked_versions)

    # Determine latest versions in each category
    latest_stable_in_versions = (
        tracked_classified["stable"][0] if tracked_classified["stable"] else None
    )
    latest_mainline_in_versions = (
        tracked_classified["mainline"][0]
        if tracked_classified["mainline"]
        else None
    )
    latest_stable_on_gh = (
        github_classified["stable"][0] if github_classified["stable"] else None
    )
    latest_mainline_on_gh = (
        github_classified["mainline"][0] if github_classified["mainline"] else None
    )

    # Build result
    result: dict[str, Any] = {
        "missing": missing,
        "latest_stable_in_versions": latest_stable_in_versions,
        "latest_mainline_in_versions": latest_mainline_in_versions,
        "latest_stable_on_gh": latest_stable_on_gh,
        "latest_mainline_on_gh": latest_mainline_on_gh,
        "release_dates": release_dates,
    }

    # Output
    print(json.dumps(result, indent=4))

    # Always exit with 0 on successful execution.
    # The presence of missing versions is communicated via JSON output,
    # not the exit code. Exit codes 1+ are reserved for actual errors.
    sys.exit(0)


if __name__ == "__main__":
    main()
