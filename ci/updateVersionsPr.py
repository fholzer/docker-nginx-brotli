#!/usr/bin/env python3
"""
Create or update a GitHub PR to add missing nginx versions to versions.txt.

Reads the JSON output from checkNginxVersions.py and either:
- Creates a new PR with a branch `update-nginx-versions-YYYY-MM-DD-{run_id}`
- Updates an existing PR from github-actions[bot]

Usage:
    python3 updateVersionsPr.py \
        --result /tmp/versions-result.json \
        --base-branch main \
        --pr-number "123" \
        --pr-branch "update-nginx-versions-2026-01-01-12345" \
        --title-prefix "ci: add missing nginx versions" \
        --output "$GITHUB_OUTPUT"
"""

import argparse
import datetime
import json
import os
import subprocess
import sys


def run_command(cmd: list[str], capture: bool = True) -> tuple[str, str, int]:
    """Run a shell command and return (stdout, stderr, returncode).

    Raises subprocess.CalledProcessError with error details on non-zero exit codes.
    """
    result = subprocess.run(
        cmd, capture_output=capture, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        if result.stdout:
            print(f"stdout: {result.stdout}", file=sys.stderr)
        if result.stderr:
            print(f"stderr: {result.stderr}", file=sys.stderr)
        raise subprocess.CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )
    return result.stdout.strip(), result.stderr.strip(), 0


def get_current_date() -> str:
    """Get current date as YYYY-MM-DD."""
    return datetime.date.today().isoformat()


def get_all_versions_in_title(missing: dict[str, list[str]]) -> list[str]:
    """Get all missing versions formatted for PR title."""
    versions: list[str] = []
    for category in ["stable", "mainline"]:
        for v in missing.get(category, []):
            versions.append(f"v{v}")
    return versions


def read_versions_file(filepath: str) -> list[str]:
    """Read versions from file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
        return [line.strip() for line in raw_lines if line.strip()]
    except FileNotFoundError:
        return []


def write_versions_file(filepath: str, versions: list[str]) -> None:
    """Write versions to file, sorted descending."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(f"{v}\n" for v in versions)


def parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse version string to tuple for sorting."""
    parts = version_str.strip().split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def write_github_output(output_path: str | None, changes: int, branch_name: str, pr_number: str = "") -> None:
    """Write results to GitHub Actions output file.

    Args:
        output_path: Path to GITHUB_OUTPUT file, or None to skip writing.
        changes: 1 if changes were made, 0 if not.
        branch_name: Name of the branch for the PR.
        pr_number: PR number (empty string if N/A).
    """
    if output_path is None:
        return

    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"changes={changes}\n")
        f.write(f"branch={branch_name}\n")
        f.write(f"pr_number={pr_number}\n")


def create_pr(
    result_file: str, base_branch: str, title_prefix: str, output_path: str | None = None, pr_branch: str | None = None
) -> None:
    """Create a new PR with missing versions."""
    # Read result data
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing = data.get("missing", {})
    release_dates = data.get("release_dates", {})

    all_missing_versions: list[str] = []
    for category in ["stable", "mainline"]:
        all_missing_versions.extend(missing.get(category, []))

    if not all_missing_versions:
        print("No missing versions to add.")
        return

    # Generate branch name (include run ID for uniqueness across concurrent runs)
    date_str = get_current_date()
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    branch_name = f"update-nginx-versions-{date_str}-{run_id}" if run_id else f"update-nginx-versions-{date_str}"

    # Read existing versions
    existing_versions = read_versions_file("versions.txt")

    # Merge and deduplicate
    existing_set = set(existing_versions)
    all_versions = list(existing_set)
    for v in all_missing_versions:
        if v not in existing_set:
            all_versions.append(v)

    # Sort descending
    all_versions.sort(key=parse_version, reverse=True)

    # Create and checkout branch
    run_command(["git", "checkout", base_branch])
    run_command(["git", "checkout", "-b", branch_name])

    # Configure git user for commits (required in clean environments)
    run_command(["git", "config", "user.email", "github-actions@users.noreply.github.com"])
    run_command(["git", "config", "user.name", "GitHub Actions"])

    # Update versions.txt
    write_versions_file("versions.txt", all_versions)

    # Commit
    run_command(["git", "add", "versions.txt"])
    run_command(
        [
            "git",
            "commit",
            "-m",
            f"ci: add missing nginx versions {', '.join(f'v{v}' for v in all_missing_versions)}",
        ]
    )

    # Push
    run_command(["git", "push", "origin", branch_name])

    # Build PR title
    title_versions = get_all_versions_in_title(missing)
    pr_title = f"{title_prefix} {', '.join(title_versions)}"

    # Build PR body
    pr_body = build_pr_body(missing, release_dates, is_update=False)

    # Create PR
    repo = os.environ.get("GITHUB_REPOSITORY", "fholzer/docker-nginx-brotli-poc")

    stdout, stderr, rc = run_command(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--title",
            pr_title,
            "--body",
            pr_body,
            "--repo",
            repo,
        ]
    )

    if rc != 0:
        print(f"Error creating PR: {stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"PR created: {stdout}")

    # Extract PR number from the output URL (e.g., "https://github.com/owner/repo/pull/123")
    pr_number = ""
    if stdout:
        for part in stdout.split():
            if "/pull/" in part:
                pr_number = part.split("/pull/")[-1].strip(")")
                break

    # Write output: changes=1 (new PR created), branch_name, pr_number
    write_github_output(output_path, 1, branch_name, pr_number)


def update_pr(
    pr_number: str, result_file: str, base_branch: str, title_prefix: str, output_path: str | None = None, pr_branch: str | None = None
) -> None:
    """Update an existing PR with new missing versions."""
    # Read result data
    with open(result_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing = data.get("missing", {})
    release_dates = data.get("release_dates", {})

    all_missing_versions: list[str] = []
    for category in ["stable", "mainline"]:
        all_missing_versions.extend(missing.get(category, []))

    if not all_missing_versions:
        print("No new missing versions to add.")
        # Write output: changes=0 (no update needed), branch_name from --pr-branch, pr_number
        write_github_output(output_path, 0, pr_branch or "", pr_number)
        return

    # Use the branch name from --pr-branch argument
    if not pr_branch:
        print("Error: --pr-branch is required when updating an existing PR", file=sys.stderr)
        sys.exit(1)

    branch_name = pr_branch

    # Fetch and checkout the remote branch (shallow fetch, only need latest commit)
    run_command(["git", "fetch", "origin", branch_name])
    run_command(["git", "checkout", "-b", branch_name, "origin/" + branch_name])

    # Configure git user for commits (required in clean environments)
    run_command(["git", "config", "user.email", "github-actions@users.noreply.github.com"])
    run_command(["git", "config", "user.name", "GitHub Actions"])

    # Read existing versions from the PR branch
    pr_versions = read_versions_file("versions.txt")
    pr_versions_set = set(pr_versions)

    # Determine which missing versions are NOT already in the PR
    new_versions_for_pr: list[str] = []
    for v in all_missing_versions:
        if v not in pr_versions_set:
            new_versions_for_pr.append(v)

    # If all missing versions are already in the PR, exit early
    if not new_versions_for_pr:
        print(f"PR #{pr_number} already covers all newly-missing versions. No update needed.")
        # Write output: changes=0 (no update needed), branch_name, pr_number
        write_github_output(output_path, 0, branch_name, pr_number)
        return

    # Add only the new versions to the PR's versions
    all_versions = list(pr_versions_set)
    for v in new_versions_for_pr:
        all_versions.append(v)

    # Sort descending
    all_versions.sort(key=parse_version, reverse=True)

    # Update versions.txt
    write_versions_file("versions.txt", all_versions)

    # Amend commit
    run_command(["git", "add", "versions.txt"])
    run_command(
        [
            "git",
            "commit",
            "--amend",
            "--no-edit",
        ]
    )

    # Force push
    run_command(["git", "push", "origin", branch_name, "--force"])

    # Build updated PR title with all versions
    title_versions = get_all_versions_in_title(missing)
    pr_title = f"{title_prefix} {', '.join(title_versions)}"

    # Build PR body
    pr_body = build_pr_body(missing, release_dates, is_update=True)

    # Update PR title and body
    repo = os.environ.get("GITHUB_REPOSITORY", "fholzer/docker-nginx-brotli-poc")

    run_command(
        [
            "gh",
            "pr",
            "edit",
            pr_number,
            "--title",
            pr_title,
            "--body",
            pr_body,
            "--repo",
            repo,
        ]
    )

    print(f"PR #{pr_number} updated.")

    # Write output: changes=1 (PR was updated), branch_name, pr_number
    write_github_output(output_path, 1, branch_name, pr_number)


def build_pr_body(
    missing: dict[str, list[str]],
    release_dates: dict[str, str],
    is_update: bool = False,
) -> str:
    """Build the PR body text."""
    lines: list[str] = []

    if is_update:
        lines.append("## Update: New nginx versions detected")
        lines.append("")
        lines.append(
            "The daily version check detected additional nginx releases since the last update."
        )
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(
        "The following nginx versions have been released but are not yet included in this repository:"
    )
    lines.append("")

    # Stable versions
    stable = missing.get("stable", [])
    if stable:
        lines.append("### Stable")
        lines.append("")
        for v in stable:
            date = release_dates.get(v, "unknown")
            lines.append(f"- `v{v}` (released: {date})")
        lines.append("")

    # Mainline versions
    mainline = missing.get("mainline", [])
    if mainline:
        lines.append("### Mainline")
        lines.append("")
        for v in mainline:
            date = release_dates.get(v, "unknown")
            lines.append(f"- `v{v}` (released: {date})")
        lines.append("")

    lines.append("## Changes")
    lines.append("- Updated `versions.txt` with missing versions")
    lines.append("")
    lines.append(
        "This PR was auto-generated by the [version check workflow](https://github.com/"
        + os.environ.get("GITHUB_REPOSITORY", "fholzer/docker-nginx-brotli-poc")
        + "/actions/workflows/check-versions.yml)."
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or update a PR for missing nginx versions"
    )
    parser.add_argument(
        "--result",
        type=str,
        required=True,
        help="Path to JSON result file from checkNginxVersions.py",
    )
    parser.add_argument(
        "--base-branch",
        type=str,
        default="main",
        help="Base branch for PR, default: main",
    )
    parser.add_argument(
        "--pr-number",
        type=str,
        default="",
        help="Existing PR number to update (empty for new PR)",
    )
    parser.add_argument(
        "--title-prefix",
        type=str,
        default="ci: add missing nginx versions",
        help="PR title prefix",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to GitHub Actions output file (e.g. $GITHUB_OUTPUT)",
    )
    parser.add_argument(
        "--pr-branch",
        type=str,
        default=None,
        help="Existing PR branch name (used for output when no update is needed)",
    )
    args = parser.parse_args()

    if args.pr_number:
        update_pr(args.pr_number, args.result, args.base_branch, args.title_prefix, args.output, args.pr_branch)
    else:
        create_pr(args.result, args.base_branch, args.title_prefix, args.output, args.pr_branch)


if __name__ == "__main__":
    main()
