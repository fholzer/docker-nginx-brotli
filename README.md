# What is this?

This project is based on Alpine Linux, the official nginx image, and an nginx module that provides static and dynamic brotli compression. [Brotli](https://github.com/google/brotli) and the [nginx brotli module](https://github.com/google/ngx_brotli) are software by Google.

# How to use this image

Since this project is based on the official [nginx image](https://hub.docker.com/_/nginx/), refer to its documentation for usage instructions. In addition to the standard configuration directives, you can use the brotli module-specific ones — see the [official documentation](https://github.com/google/ngx_brotli#configuration-directives).

# Releases

## Available Tags

* `latest` will always track the latest stable release
* `mainline` will always track the latest mainline release
* `v<x.y.z>` will track a specific version
* `v<x.y>` will track a specific minor version

Use the `mainline` tag if you want the latest development release of nginx. Users who prefer a stable release — even if it may lack the newest features — should use the `latest` tag, which tracks the "stable" branch of nginx.

**Note that tags are not immutable!** If you want to ensure you're always running the exact same image, pin to the [image digest](https://docs.docker.com/dhi/explore/security-concepts/digests/). You can find the digest on the Docker Hub page for each tag.

## New Versions

Newly released nginx versions are typically added within 7 days of release. Critical security fixes are usually added sooner.

This repository uses an automated daily check ([`check-versions.yml`](.github/workflows/check-versions.yml)) that monitors the [nginx/nginx GitHub releases](https://github.com/nginx/nginx/releases) and automatically creates a PR to add any missing versions to [`versions.txt`](versions.txt). The PR is created by the `github-actions[bot]` user.

Please note that this is a personal project, so release timelines may vary. Recent changes to the build and release process should enable faster updates going forward.

## Security

Each tag is rebuilt weekly, and whenever a new Nginx version is released and added to this repository.

In addition to always using the latest [Alpine Linux 3.x](https://hub.docker.com/_/alpine) base image, packages are updated to the latest available version during build.

## Version Deprecation

Tags are maintained for the **two most recent** minor versions of each nginx release branch (stable and mainline).

Intermediate and untagged images may be removed 12 months after their last pull, or after 24 months regardless of activity.

---

## AI Disclosure

The build scripts in this repository were assisted in development by [Qwen 3.6](https://qwenlm.github.io/).
