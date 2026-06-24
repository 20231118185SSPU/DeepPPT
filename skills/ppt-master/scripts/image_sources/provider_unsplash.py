"""Unsplash provider.

Requires ``UNSPLASH_ACCESS_KEY`` in the environment. Unsplash's site-wide
license allows commercial and non-commercial use without attribution, so all
returned candidates are classified as ``no-attribution``.

API docs: https://unsplash.com/documentation
"""

from __future__ import annotations

import sys

if __name__ == "__main__":
    print(__doc__)
    print("Use via: python3 skills/ppt-master/scripts/image_search.py ...")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import os

import requests

from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
    LICENSE_TIER_NO_ATTRIBUTION,
    USER_AGENT,
    build_query_progression,
    normalize_license_name,
)


API_URL = "https://api.unsplash.com/search/photos"
DEFAULT_PAGE_SIZE = 20
DEFAULT_TIMEOUT = 30

_ORIENTATION_MAP = {
    "landscape": "landscape",
    "portrait": "portrait",
    "square": "squarish",
}


def _require_api_key() -> str:
    key = (os.environ.get("UNSPLASH_ACCESS_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "UNSPLASH_ACCESS_KEY is not set. Add it to your environment or .env file. "
            "Get one at https://unsplash.com/developers"
        )
    return key


def parse_results(payload: dict) -> list[AssetCandidate]:
    """Translate an Unsplash response into candidates."""
    candidates: list[AssetCandidate] = []
    for item in payload.get("results", []) or []:
        urls = item.get("urls") or {}
        # Prefer "regular" (1080px) for good quality + reasonable size.
        download_url = (
            urls.get("regular")
            or urls.get("full")
            or urls.get("raw")
            or ""
        ).strip()
        if not download_url:
            continue

        links = item.get("links") or {}
        user = item.get("user") or {}
        # Unsplash returns "description" or "alt_description"; prefer the
        # explicit description when present.
        title = (item.get("description") or item.get("alt_description") or "").strip()

        candidates.append(
            AssetCandidate(
                provider="unsplash",
                title=title or "Unsplash photo",
                asset_id=str(item.get("id") or ""),
                source_page_url=(links.get("html") or "").strip(),
                license_name=normalize_license_name("Unsplash License"),
                license_url="https://unsplash.com/license",
                license_tier=LICENSE_TIER_NO_ATTRIBUTION,
                width=int(item.get("width") or 0),
                height=int(item.get("height") or 0),
                download_url=download_url,
                author=(user.get("name") or "").strip(),
                raw=item,
            )
        )
    return candidates


def search(
    request: ImageSearchRequest,
    *,
    license_tier_filter: str = "no-attribution-only",
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[AssetCandidate]:
    """Search Unsplash for candidates.

    Unsplash images are uniformly ``no-attribution``, so the ``"all"`` filter
    behaves identically to ``"no-attribution-only"``. Both are accepted to
    keep the dispatcher simple.
    """
    if license_tier_filter not in {"no-attribution-only", "all"}:
        raise ValueError(f"unsupported license_tier_filter: {license_tier_filter!r}")

    api_key = _require_api_key()
    orientation = (request.orientation or "").strip().lower()

    for query in build_query_progression(request.query):
        params: dict[str, str | int] = {
            "query": query,
            "per_page": min(page_size, 30),  # Unsplash max is 30
        }
        if orientation in _ORIENTATION_MAP:
            params["orientation"] = _ORIENTATION_MAP[orientation]

        response = requests.get(
            API_URL,
            params=params,
            headers={
                "Authorization": f"Client-ID {api_key}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        candidates = parse_results(response.json())
        if candidates:
            return candidates

    return []
