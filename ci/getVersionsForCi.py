#!/usr/bin/env python3
"""
Read versions.txt, split into stable (even minor) and mainline (odd minor),
select the latest patch for the 2 most recent minor versions from each list,
and write the result as a JSON array to GITHUB_OUTPUT.
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


def main() -> None:
    # Read versions from versions.txt
    with open("versions.txt", "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    versions = [line.strip() for line in raw_lines if line.strip()]

    if not versions:
        print("No versions found in versions.txt", file=sys.stderr)
        sys.exit(1)

    # Split into stable (even minor) and mainline (odd minor)
    stable = [v for v in versions if is_stable(v)]
    mainline = [v for v in versions if not is_stable(v)]

    # Sort each list by version descending to get most recent first
    stable.sort(key=parse_version, reverse=True)
    mainline.sort(key=parse_version, reverse=True)

    # Get the 2 most recent minor versions from each list
    # Group by minor version and pick the latest patch per minor
    def latest_patches(version_list: list[str], count: int) -> list[str]:
        """Get latest patch for the `count` most recent minor versions."""
        minor_groups: dict[tuple[int, int], str] = {}
        for v in version_list:
            major, minor, patch = parse_version(v)
            key = (major, minor)
            # Keep the highest patch for this minor version
            if key not in minor_groups or patch > parse_version(minor_groups[key])[2]:
                minor_groups[key] = v

        # Sort minor versions descending and take top `count`
        sorted_minors = sorted(minor_groups.keys(), reverse=True)[:count]
        result = [minor_groups[k] for k in sorted_minors]
        # Sort final result by full version descending for consistency
        result.sort(key=parse_version, reverse=True)
        return result

    stable_versions = latest_patches(stable, 2)
    mainline_versions = latest_patches(mainline, 2)

    # Combine all selected versions
    all_versions = sorted(set(stable_versions + mainline_versions), key=parse_version, reverse=True)

    # Serialize to JSON and write to GITHUB_OUTPUT
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        json_array = json.dumps(all_versions)
        output = f"NGINX_VERSIONS={json_array}\n"
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(output)
        print(f"Written to {github_output}: {output.strip()}")
    else:
        json_array = json.dumps(all_versions)
        print(json_array)


if __name__ == "__main__":
    main()
