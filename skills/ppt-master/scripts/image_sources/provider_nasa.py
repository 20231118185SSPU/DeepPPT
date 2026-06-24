"""NASA Image and Video Library provider.

Zero-config (no API key required). Excellent for space, Earth science,
aeronautics, and technology imagery. All content is public domain (US
government work).

API docs: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf
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


API_URL = "https://images-api.nasa.gov/search"
DEFAULT_PAGE_SIZE = 20
DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 2
_RETRY_BACKOFF = 2  # seconds; doubles each retry

_LICENSE_NAME = "Public Domain"
_LICENSE_URL = "https://www.nasa.gov/nasa-brand-center/images/"
_AUTHOR = "NASA"


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


def _pick_preview_link(links: list[dict]) -> str:
    """Extract the best preview image URL from ``links`` array.

    NASA search results include ``links`` with ``rel=preview`` entries.
    Prefer the first link whose ``rel`` is ``"preview"``; fall back to the
    first link overall.
    """
    for link in links or []:
        if link.get("rel") == "preview":
            return (link.get("href") or "").strip()
    # Fallback: first link with any href.
    for link in links or []:
        href = (link.get("href") or "").strip()
        if href:
            return href
    return ""


def parse_results(payload: dict) -> list[AssetCandidate]:
    """Translate a NASA Image API search payload into a list of candidates.

    Each item in the NASA response lives at
    ``payload["collection"]["items"][]`` and contains ``data`` (list of
    metadata dicts) and ``links`` (list of preview/thumbnail entries).
    """
    candidates: list[AssetCandidate] = []
    items = ((payload.get("collection") or {}).get("items") or [])

    for item in items:
        data_list = item.get("data") or []
        if not data_list:
            continue
        data = data_list[0]

        nasa_id = (data.get("nasa_id") or "").strip()
        if not nasa_id:
            continue

        download_url = _pick_preview_link(item.get("links") or [])
        if not download_url:
            continue

        candidates.append(
            AssetCandidate(
                provider="nasa",
                title=(data.get("title") or "").strip() or "Untitled",
                asset_id=nasa_id,
                source_page_url=f"https://images.nasa.gov/details-{nasa_id}",
                license_name=normalize_license_name(_LICENSE_NAME),
                license_url=_LICENSE_URL,
                license_tier=LICENSE_TIER_NO_ATTRIBUTION,
                width=0,   # NASA search results don't include dimensions
                height=0,  # in the listing; caller can fetch if needed.
                download_url=download_url,
                author=(data.get("photographer") or "").strip() or _AUTHOR,
                raw=item,
            )
        )

    return candidates


def _filter_by_orientation(
    candidates: list[AssetCandidate], orientation: str
) -> list[AssetCandidate]:
    """NASA API has no orientation parameter; filter client-side.

    Because search results lack width/height, orientation filtering can only
    act on items where the caller has previously resolved dimensions. When
    all candidates have unknown dimensions the filter is a no-op.
    """
    if not orientation or orientation == "any":
        return candidates
    # Only filter if at least some candidates carry non-zero dimensions.
    from image_sources.provider_common import normalize_orientation
    resolvable = [c for c in candidates if c.width > 0 and c.height > 0]
    if not resolvable:
        return candidates  # nothing to filter on
    matching = [
        c for c in resolvable if normalize_orientation(c.width, c.height) == orientation
    ]
    return matching or candidates


def search(
    request: ImageSearchRequest,
    *,
    license_tier_filter: str = "no-attribution-only",
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[AssetCandidate]:
    """Search the NASA Image and Video Library for candidates.

    All NASA images are public domain, so ``license_tier_filter`` is
    effectively ignored (everything is no-attribution). The parameter is
    accepted for interface consistency.

    Returns candidates from the first non-empty query in the progression.
    """
    if license_tier_filter not in {"no-attribution-only", "all"}:
        raise ValueError(f"unsupported license_tier_filter: {license_tier_filter!r}")

    orientation = (request.orientation or "").strip().lower()

    for query in build_query_progression(request.query):
        params: dict[str, str | int] = {
            "q": query,
            "media_type": "image",
            "page": 1,
        }

        response = _request_with_retry(
            requests.get,
            API_URL,
            params=params,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
        )
        all_candidates = parse_results(response.json())

        all_candidates = _filter_by_orientation(all_candidates, orientation)
        if all_candidates:
            return all_candidates[:page_size]

    return []
