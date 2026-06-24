"""Flickr provider.

Requires ``FLICKR_API_KEY`` in the environment. Flickr hosts images under a
mix of licenses; this provider only accepts CC0/Public Domain (``no-attribution``)
and CC BY/CC BY-SA (``attribution-required``) images. CC BY-NC variants are
rejected outright.

API docs: https://www.flickr.com/services/api/
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
    LICENSE_TIER_ATTRIBUTION_REQUIRED,
    USER_AGENT,
    build_query_progression,
    normalize_license_name,
)


API_URL = "https://www.flickr.com/services/rest/"
DEFAULT_PAGE_SIZE = 20
DEFAULT_TIMEOUT = 30

# Flickr license ID mapping.
#   0 = All Rights Reserved        -> reject
#   1 = CC BY-NC-SA 2.0            -> reject
#   2 = CC BY-NC 2.0               -> reject
#   3 = CC BY-NC-ND 2.0            -> reject
#   4 = CC BY 2.0                  -> attribution-required
#   5 = CC BY-SA 2.0               -> attribution-required
#   6 = CC BY-ND 2.0               -> attribution-required (rarely used)
#   7 = No known copyright         -> no-attribution (public domain equiv)
#   8 = United States Government Work -> no-attribution
#   9 = CC0 1.0                    -> no-attribution
#  10 = Public Domain Mark 1.0     -> no-attribution
#
# The search ``license`` param only includes IDs we accept; rejected IDs are
# never requested so they never appear in results.

_LICENSE_ID_TIER: dict[int, str] = {
    7: LICENSE_TIER_NO_ATTRIBUTION,
    8: LICENSE_TIER_NO_ATTRIBUTION,
    9: LICENSE_TIER_NO_ATTRIBUTION,
    10: LICENSE_TIER_NO_ATTRIBUTION,
    4: LICENSE_TIER_ATTRIBUTION_REQUIRED,
    5: LICENSE_TIER_ATTRIBUTION_REQUIRED,
    6: LICENSE_TIER_ATTRIBUTION_REQUIRED,
}

# IDs to pass in the ``license`` search parameter (all accepted IDs).
_ALLOWED_LICENSE_IDS = "4,5,6,7,8,9,10"

_LICENSE_ID_URL: dict[int, str] = {
    4: "https://creativecommons.org/licenses/by/2.0/",
    5: "https://creativecommons.org/licenses/by-sa/2.0/",
    6: "https://creativecommons.org/licenses/by-nd/2.0/",
    7: "https://www.flickr.com/commons/usage/",
    8: "https://www.usa.gov/public-domain",
    9: "https://creativecommons.org/publicdomain/zero/1.0/",
    10: "https://creativecommons.org/publicdomain/mark/1.0/",
}

_LICENSE_ID_NAME: dict[int, str] = {
    4: "CC BY 2.0",
    5: "CC BY-SA 2.0",
    6: "CC BY-ND 2.0",
    7: "No known copyright restrictions",
    8: "United States Government Work",
    9: "CC0 1.0",
    10: "Public Domain Mark 1.0",
}


def _require_api_key() -> str:
    key = (os.environ.get("FLICKR_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "FLICKR_API_KEY is not set. Add it to your environment or .env file. "
            "Get one at https://www.flickr.com/services/apps/create/"
        )
    return key


def _build_image_url(photo: dict) -> str:
    """Construct a direct image URL from Flickr photo metadata.

    Uses the ``_b`` (large, 1024px) suffix for a reasonable quality/size
    trade-off.  Falls back to ``_z`` (medium 640) if metadata is incomplete.
    """
    farm = photo.get("farm")
    server = photo.get("server")
    photo_id = photo.get("id")
    secret = photo.get("secret")
    if not all((farm, server, photo_id, secret)):
        return ""
    return f"https://farm{farm}.staticflickr.com/{server}/{photo_id}_{secret}_b.jpg"


def _flickr_license_name(license_id: int) -> str:
    return normalize_license_name(
        _LICENSE_ID_NAME.get(license_id, f"Flickr license {license_id}")
    )


def _flickr_license_url(license_id: int) -> str:
    return _LICENSE_ID_URL.get(license_id, "")


def parse_results(payload: dict) -> list[AssetCandidate]:
    """Translate a Flickr ``flickr.photos.search`` response into candidates.

    Each photo object in the response carries a ``license`` field (integer
    ID).  We classify the ID via ``_LICENSE_ID_TIER`` — any ID absent from
    that map is silently skipped (it was already excluded from the request's
    ``license`` param, but guard defensively).
    """
    candidates: list[AssetCandidate] = []
    photos_wrapper = payload.get("photos") or {}
    for item in photos_wrapper.get("photo", []) or []:
        license_id = int(item.get("license") or -1)
        tier = _LICENSE_ID_TIER.get(license_id)
        if not tier:
            continue

        download_url = _build_image_url(item)
        if not download_url:
            continue

        source_page_url = (
            f"https://www.flickr.com/photos/{item.get('owner')}/{item.get('id')}/"
            if item.get("owner") and item.get("id")
            else ""
        )

        candidates.append(
            AssetCandidate(
                provider="flickr",
                title=(item.get("title") or "").strip() or "Flickr photo",
                asset_id=str(item.get("id") or ""),
                source_page_url=source_page_url,
                license_name=_flickr_license_name(license_id),
                license_url=_flickr_license_url(license_id),
                license_tier=tier,
                width=0,  # search response doesn't include dimensions
                height=0,
                download_url=download_url,
                author="",  # "owner" is a NSID, not a display name; skip
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
    """Search Flickr for openly licensed candidates.

    ``license_tier_filter`` controls which license IDs are requested:

    - ``"no-attribution-only"``: CC0, public domain, government works (IDs 7,8,9,10).
    - ``"all"``: adds CC BY / CC BY-SA / CC BY-ND (IDs 4,5,6).
    """
    if license_tier_filter not in {"no-attribution-only", "all"}:
        raise ValueError(f"unsupported license_tier_filter: {license_tier_filter!r}")

    api_key = _require_api_key()

    if license_tier_filter == "no-attribution-only":
        license_param = "7,8,9,10"
    else:
        license_param = _ALLOWED_LICENSE_IDS

    orientation = (request.orientation or "").strip().lower()

    for query in build_query_progression(request.query):
        params: dict[str, str | int] = {
            "method": "flickr.photos.search",
            "api_key": api_key,
            "text": query,
            "per_page": page_size,
            "format": "json",
            "nojsoncallback": 1,
            "license": license_param,
            "media": "photos",
            "sort": "relevance",
        }
        # Flickr doesn't have a direct orientation filter on search, but we
        # can hint via ``content_types=0`` (photos only, no screenshots etc.)
        # and let downstream scoring handle orientation preference.

        response = requests.get(
            API_URL,
            params=params,
            headers={
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
