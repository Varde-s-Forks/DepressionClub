# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "dumb-pypi>=1.15.0",
#     "niquests>=3.18.7",
# ]
# ///
"""
Generate a PEP 503 Simple Repository API index from GitHub Releases.
"""

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import niquests
from dumb_pypi.main import main as dumb_pypi_main  # type: ignore[import-untyped]

PACKAGES_URL_PLACEHOLDER = "https://__PACKAGES_PLACEHOLDER__"
OUTPUT_DIR = Path("_site")


def github_api_get(url: str, token: str | None) -> list[dict[str, Any]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with niquests.get(url, headers=headers) as resp:
        return resp.raise_for_status().json()


def fetch_releases(repo: str, token: str | None = None) -> list[dict[str, Any]]:
    releases = list[dict[str, Any]]()
    page = 1
    while True:
        batch = github_api_get(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}", token)
        if not batch:
            break
        releases.extend(batch)
        page += 1
    return releases


def calculate_sha256(url: str) -> str:
    sha256 = hashlib.sha256()
    with niquests.get(url, stream=True) as resp:
        for chunk in resp.raise_for_status().iter_content(chunk_size=8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def collect_assets(releases: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Return a {filename: {url, hash}} mapping for all dist assets."""
    assets = dict[str, dict[str, str]]()
    cache = load_cache()
    for release in releases:
        for asset in release.get("assets", []):
            name = asset["name"]
            if name.endswith(".whl") or name.endswith(".tar.gz"):
                url = asset["browser_download_url"]
                # Use cached hash if filename exists, otherwise calculate it
                file_hash = cache.get(name)
                if not file_hash:
                    print(f"Hashing new asset: {name}...", file=sys.stderr)
                    file_hash = calculate_sha256(url)

                assets[name] = {"url": url, "hash": file_hash}
    return assets


def load_cache() -> dict[str, str]:
    cache_path = OUTPUT_DIR / "packages.json"
    if not cache_path.exists():
        return {}

    cache = dict[str, str]()
    with cache_path.open("r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if "filename" in data and "hash" in data:
                # hash is stored as sha256=hex
                cache[data["filename"]] = data["hash"].split("=", 1)[-1]
    return cache


def run_dumb_pypi(assets: dict[str, dict[str, str]], title: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        package_list = Path(tmpdir) / "packages.json"

        # Write one JSON object per line (dumb-pypi --package-list-json format)
        with package_list.open("w", encoding="utf-8") as f:
            for filename in sorted(assets):
                entry = {"filename": filename, "hash": f"sha256={assets[filename]['hash']}"}
                json.dump(entry, f)
                f.write("\n")

        args = [
            "--package-list-json",
            str(package_list),
            "--packages-url",
            PACKAGES_URL_PLACEHOLDER,
            "--output-dir",
            str(OUTPUT_DIR),
            "--title",
            title,
            "--no-generate-timestamp",
            "--logo",
            "https://avatars.githubusercontent.com/u/137835541",
            "--logo-width",
            "45",
        ]
        dumb_pypi_main(args)

    _fixup_urls(assets)


def _fixup_urls(assets: dict[str, dict[str, str]]) -> None:
    for path in OUTPUT_DIR.rglob("*"):
        if path.is_file() and path.suffix in (".html", ".json"):
            content = path.read_text(encoding="utf-8")
            original = content

            for filename, data in assets.items():
                placeholder_url = f"{PACKAGES_URL_PLACEHOLDER}/{filename}"
                content = content.replace(placeholder_url, data["url"])

            if content != original:
                path.write_text(content, encoding="utf-8")


def main() -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "Jaded-Encoding-Thaumaturgy/vs-wheels")
    token = os.environ.get("GITHUB_TOKEN")
    title = os.environ.get("INDEX_TITLE", "JET Package Index")

    print(f"Generating index for {repo} -> {OUTPUT_DIR}", file=sys.stderr)

    releases = fetch_releases(repo, token)
    assets = collect_assets(releases)

    print(f"Found {len(assets)} distribution file(s) across {len(releases)} release(s)", file=sys.stderr)

    if not assets:
        print("WARNING: No distribution assets found in any release.", file=sys.stderr)
    else:
        run_dumb_pypi(assets, title)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
