"""Smithsonian Open Access provider.

Zero-config (no API key required, though providing one increases rate
limits). Strong on museum collections, historical artifacts, natural
history specimens, and American cultural heritage imagery.

API docs: https://edan.si.edu/openaccess/apidocs/
"""

from __future__ import annotations

import sys

if __name__ == "__main__":
    print(__doc__)
    print("Use via: python3 skills/ppt-master/scripts/image_search.py ...")
    raise SystemExit(0 if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]) else 1)

import requests

from image_sources.provider_common import (
    AssetCandidate,
    ImageSearchRequest,
    LICENSE_TIER_NO_ATTRIBUTION,
    USER_AGENT,
    build_query_progression,
    normalize_license_name,
)


API_URL = "https://api.si.edu/openaccess/api/v1.0/search"
DEFAULT_PAGE_SIZE = 20
DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 2
_RETRY_BACKOFF = 2  # seconds; doubles each retry

_LICENSE_NAME = "CC0"
_LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"


def _request_with_retry(method, url, *, retries=_MAX_RETRIES, **kwargs):
    """HTTP request with exponential backoff retry on transient errors."""
    import time
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = method(url, **kwargs)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(_RETRY_BACKOFF * (2 ** attempt))
        except requests.HTTPError:
            raise  # non-transient HTTP errors propagate immediately
    raise last_exc


def _extract_image_url(media_list: list[dict]) -> str:
    """Return the first full-size image URL from ``online_media.media``.

    Only considers entries whose ``type`` is ``"Images"``. Prefers the
    full ``content`` URL over ``thumbnail``.
    """
    for entry in media_list or []:
        if (entry.get("type") or "").lower() != "images":
            continue
        url = (entry.get("content") or "").strip()
        if url:
            return url
        # Fallback to thumbnail if full URL is missing.
        thumb = (entry.get("thumbnail") or "").strip()
        if thumb:
            return thumb
    return ""


def _extract_author(row_content: dict) -> str:
    """Best-effort author extraction from the deeply nested ``freetext``.

    Looks for ``content.freetext.name[].content`` entries and returns the
    first non-empty one, or ``"Smithsonian"`` as a safe default.
    """
    freetext = (row_content.get("freetext") or {})
    name_list = freetext.get("name") or []
    for entry in name_list:
        author = (entry.get("content") or "").strip()
        if author:
            return author
    return "Smithsonian"


def parse_results(payload: dict) -> list[AssetCandidate]:
    """Translate a Smithsonian Open Access search payload into candidates.

    The response lives at ``payload["response"]["rows"][]``. Each row has
    a deeply nested ``content`` object. We use ``.get()`` chains throughout
    to guard against structural surprises.
    """
    candidates: list[AssetCandidate] = []
    rows = ((payload.get("response") or {}).get("rows") or [])

    for row in rows:
        content = row.get("content") or {}

        # --- title and guid ---
        descriptive = content.get("descriptiveNonRepeating") or {}
        title_obj = descriptive.get("title") or {}
        title = (title_obj.get("content") or "").strip() or "Untitled"
        guid = (descriptive.get("guid") or "").strip()

        # --- image URL ---
        online_media = content.get("online_media") or {}
        media_list = online_media.get("media") or []
        download_url = _extract_image_url(media_list)
        if not download_url:
            continue  # skip items without images

        # --- license ---
        # Smithsonian Open Access items are CC0. Individual media entries
        # may carry a ``rights`` field; use it when present, fall back to CC0.
        rights = ""
        for entry in media_list:
            r = (entry.get("rights") or "").strip()
            if r:
                rights = r
                break
        license_name = rights or _LICENSE_NAME

        candidates.append(
            AssetCandidate(
                provider="smithsonian",
                title=title,
                asset_id=guid or (row.get("id") or ""),
                source_page_url=guid,
                license_name=normalize_license_name(license_name),
                license_url=_LICENSE_URL,
                license_tier=LICENSE_TIER_NO_ATTRIBUTION,
                width=0,   # Smithsonian listing doesn't include dimensions
                height=0,  # in the search response.
                download_url=download_url,
                author=_extract_author(content),
                raw=row,
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
    """Search the Smithsonian Open Access API for candidates.

    All Smithsonian Open Access items are CC0, so ``license_tier_filter``
    is effectively ignored. The parameter is accepted for interface
    consistency.

    Returns candidates from the first non-empty query in the progression.
    """
    if license_tier_filter not in {"no-attribution-only", "all"}:
        raise ValueError(f"unsupported license_tier_filter: {license_tier_filter!r}")

    for query in build_query_progression(request.query):
        params: dict[str, str | int] = {
            "q": query,
            "rows": min(page_size, 100),  # API max is 100
            "start": 0,
        }

        response = _request_with_retry(
            requests.get,
            API_URL,
            params=params,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
        )
        all_candidates = parse_results(response.json())
        if all_candidates:
            return all_candidates[:page_size]

    return []
