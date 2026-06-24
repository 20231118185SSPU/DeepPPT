"""Browser-based image search provider using Playwright.

Falls back when API providers (Openverse / Wikimedia / Pexels / Pixabay) fail
or return poor-quality candidates. Also provides URL screenshot capture for
deep-dive product/page slides.

Features:
  - Multi-engine search: Google Images, Bing Images, Yandex
  - Multi-dimensional query expansion from rich reference text
  - CLIP-based semantic filtering (graceful fallback when unavailable)
  - URL screenshot capture for specific product pages
  - Stealth headers to avoid bot detection
  - 3-second render wait for JS-heavy pages
  - Output: 1920x1080 JPEG, ≤300KB after compression
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import sys
import tempfile
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from image_sources.provider_common import (  # noqa: E402
    AssetCandidate,
    ImageSearchRequest,
    classify_license,
    compute_relevance,
    normalize_orientation,
    simplify_query,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMAGE_MAX_WIDTH = 1920
IMAGE_MAX_HEIGHT = 1080
JPEG_QUALITY_INITIAL = 85
JPEG_QUALITY_STEP = 10
JPEG_QUALITY_MIN = 40
JPEG_TARGET_BYTES = 300 * 1024  # 300KB

STEALTH_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
CLIP_MIN_SCORE = 0.3

SUPPORTED_ENGINES = ("google", "bing", "yandex")
VALID_ENGINES = set(SUPPORTED_ENGINES)

LICENSE_TIER_BROWSER = "Browser License (verify before public use)"

# ---------------------------------------------------------------------------
# CLIP (lazy import, graceful fallback)
# ---------------------------------------------------------------------------

_clip_model = None
_clip_processor = None
_clip_available: Optional[bool] = None


def _load_clip():
    """Lazy-load CLIP model. Returns True if available."""
    global _clip_model, _clip_processor, _clip_available
    if _clip_available is not None:
        return _clip_available
    try:
        from transformers import CLIPModel, CLIPProcessor  # type: ignore
        _clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
        _clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
        _clip_available = True
    except ImportError:
        _clip_available = False
    except Exception as exc:
        print(f"  [clip] load failed ({exc}), falling back to metadata scoring", file=sys.stderr)
        _clip_available = False
    return _clip_available


def score_image_relevance(image_bytes: bytes, query: str) -> float:
    """Score image-query relevance using CLIP. Returns 0.0–1.0.

    Falls back to 0.5 (neutral) when CLIP is unavailable.
    """
    if not _load_clip():
        return 0.5

    try:
        from PIL import Image  # type: ignore
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = _clip_processor(
            text=[query], images=img, return_tensors="pt", padding=True
        )
        import torch  # type: ignore
        with torch.no_grad():
            outputs = _clip_model(**inputs)
            logits = outputs.logits_per_text
            score = float(torch.sigmoid(logits).item())
        return max(0.0, min(1.0, score))
    except Exception:
        return 0.5


def score_candidate_visual(
    candidate: AssetCandidate, request: ImageSearchRequest
) -> float:
    """Score candidate by visual metadata (no CLIP download required)."""
    score = compute_relevance(candidate, request.query) * 10000.0

    cand_orient = normalize_orientation(candidate.width, candidate.height)
    requested = (request.orientation or "").strip().lower()
    if requested:
        score += 1000.0 if cand_orient == requested else -250.0
    if request.min_width and candidate.width < request.min_width:
        score -= 500.0
    if request.min_height and candidate.height < request.min_height:
        score -= 500.0
    score += min(candidate.width * candidate.height / 1000.0, 5000.0)
    return score


# ---------------------------------------------------------------------------
# Image download and quality validation
# ---------------------------------------------------------------------------


def _download_and_validate(
    url: str, timeout: int = 30
) -> Optional[tuple[bytes, str]]:
    """Download URL → (bytes, media_type) or None."""
    import requests  # type: ignore

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=STEALTH_HEADERS, timeout=timeout)
            if resp.status_code != 200:
                continue
            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type and "octet-stream" not in content_type:
                return None
            data = resp.content
            if len(data) < 10240:
                return None
            return data, content_type
        except Exception:
            if attempt < 2:
                import time
                time.sleep(1)
    return None


def _compress_to_jpeg(image_bytes: bytes, quality: int = JPEG_QUALITY_INITIAL) -> bytes:
    """Compress image to JPEG, resize if exceeding max dimensions."""
    from PIL import Image  # type: ignore

    img = Image.open(io.BytesIO(image_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    # Resize if exceeding max dimensions
    w, h = img.size
    if w > IMAGE_MAX_WIDTH or h > IMAGE_MAX_HEIGHT:
        ratio = min(IMAGE_MAX_WIDTH / w, IMAGE_MAX_HEIGHT / h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # Compress with progressive quality reduction
    current_quality = quality
    while current_quality >= JPEG_QUALITY_MIN:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=current_quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= JPEG_TARGET_BYTES:
            return data
        current_quality -= JPEG_QUALITY_STEP

    return data  # Best effort


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# URL screenshot capture
# ---------------------------------------------------------------------------


def capture_url_screenshots(
    url_targets: list[dict],
    output_dir: Path,
    wait_ms: int = 3000,
) -> list[AssetCandidate]:
    """Capture screenshots of specific URLs for deep-dive product pages.

    Each target dict: {"url": str, "filename": str, "title": str}

    Returns list of AssetCandidate objects.
    """
    try:
        _ensure_playwright()
    except RuntimeError as exc:
        print(f"  [url-capture] skipped: {exc}", file=sys.stderr)
        return []

    from playwright.sync_api import sync_playwright  # type: ignore

    results: list[AssetCandidate] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=_CHROMIUM_ARGS)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        for target in url_targets:
            url = target["url"]
            filename = target["filename"]
            title = target.get("title", "")

            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(wait_ms)

                # Auto-scroll for lazy-loaded content
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                page.wait_for_timeout(1000)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(500)

                screenshot_bytes = page.screenshot(type="jpeg", quality=85)
                compressed = _compress_to_jpeg(screenshot_bytes)

                save_path = output_dir / filename
                save_path.write_bytes(compressed)

                w, h = IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT

                results.append(AssetCandidate(
                    provider="browser",
                    title=title or f"Screenshot: {url}",
                    source_page_url=url,
                    license_name=LICENSE_TIER_BROWSER,
                    license_tier=LICENSE_TIER_BROWSER,
                    width=w,
                    height=h,
                    download_url=url,
                    author=url,
                ))
            except Exception as exc:
                print(f"  [url-capture] failed {url}: {exc}", file=sys.stderr)
                continue

        browser.close()

    return results


# ---------------------------------------------------------------------------
# Playwright availability
# ---------------------------------------------------------------------------

_CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
]


def _ensure_playwright():
    """Raise if Playwright is not installed or browsers not available."""
    try:
        import playwright  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed. Install: pip install playwright && "
            "python -m playwright install chromium"
        )
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        raise RuntimeError(
            "Playwright sync API unavailable. Run: python -m playwright install chromium"
        )


# ---------------------------------------------------------------------------
# Query expansion
# ---------------------------------------------------------------------------

_LOCATION_WORDS = {
    "paris", "london", "tokyo", "new york", "shanghai", "beijing", "rome",
    "berlin", "madrid", "moscow", "dubai", "singapore", "sydney", "toronto",
    "chongqing", "xiamen", "chengdu", "shenzhen", "guangzhou", "hangzhou",
    "nanjing", "wuhan", "xian", "故宫", "长城", "外滩", "解放碑", "洪崖洞",
    "磁器口", "鼓浪屿", "西湖", "东方明珠",
}

_TIME_WORDS = {
    "sunset", "sunrise", "dawn", "dusk", "night", "evening", "morning",
    "autumn", "spring", "winter", "summer", "黄昏", "日落", "夜景", "晨曦",
}

_VIEWPOINT_WORDS = {
    "aerial", "panoramic", "wide angle", "close-up", "macro", "bird's eye",
    "drone", "overhead", "interior", "exterior", "俯瞰", "全景", "航拍",
}


def expand_query_dimensions(reference: str, max_variations: int = 5) -> list[str]:
    """Expand rich reference text into multi-dimensional search queries.

    Extracts subject / location / time / viewpoint dimensions and generates
    targeted search variations. Returns de-duplicated list.
    """
    if not reference or not reference.strip():
        return []

    words = set(reference.lower().split())
    location = " ".join(w for w in _LOCATION_WORDS if w in words)
    time_dim = " ".join(w for w in _TIME_WORDS if w in words)
    viewpoint = " ".join(w for w in _VIEWPOINT_WORDS if w in words)

    variations = [reference]
    if location:
        variations.append(f"{location} landmark photo")
        variations.append(f"{location} skyline")
    if time_dim:
        subject = simplify_query(reference, max_words=3)
        variations.append(f"{subject} {time_dim}")
    if viewpoint:
        subject = simplify_query(reference, max_words=3)
        variations.append(f"{subject} {viewpoint}")

    variations.append(simplify_query(reference, max_words=4))
    variations.append(simplify_query(reference, max_words=3))

    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for v in variations:
        v = v.strip()
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out[:max_variations]


# ---------------------------------------------------------------------------
# Search engines
# ---------------------------------------------------------------------------


def _search_bing(page, query: str, orientation: str) -> list[str]:
    """Bing Images search."""
    url = "https://www.bing.com/images/search?" + urllib.parse.urlencode({
        "q": query,
        "qft": "+filterui:imagesize-large",
    })
    if orientation == "landscape":
        url += "+filterui:aspect-wide"
    elif orientation == "portrait":
        url += "+filterui:aspect-tall"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        items = page.query_selector_all(".mimg, .iusc img, .img_cont img")
        urls = [
            src for item in items
            if (src := (item.get_attribute("src") or item.get_attribute("data-src") or ""))
            and src.startswith("http")
            and len(src) > 50
        ][:20]
        if not urls:
            print("  [bing] WARNING: selectors returned 0 URLs — CSS selectors may need updating", file=sys.stderr)
        return urls
    except Exception as exc:
        print(f"  [bing] search error: {exc}", file=sys.stderr)
        return []


def _search_google(page, query: str, orientation: str) -> list[str]:
    """Google Images search."""
    url = "https://www.google.com/search?" + urllib.parse.urlencode({
        "q": query,
        "tbm": "isch",
    })
    if orientation == "landscape":
        url += "&tbs=isz:lt,islt:svga"
    elif orientation == "portrait":
        url += "&tbs=isz:lt,islt:svga,iar:t"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
        items = page.query_selector_all("img[class*='YQ4gaf'], img.rg_i, img[data-src]")
        urls = []
        for item in items:
            src = item.get_attribute("src") or item.get_attribute("data-src") or ""
            if src.startswith("http") and "google" not in src and len(src) > 50:
                urls.append(src)
        urls = urls[:20]
        if not urls:
            print("  [google] WARNING: selectors returned 0 URLs — CSS selectors may need updating", file=sys.stderr)
        return urls
    except Exception as exc:
        print(f"  [google] search error: {exc}", file=sys.stderr)
        return []


def _search_yandex(page, query: str, orientation: str) -> list[str]:
    """Yandex Images search."""
    url = "https://yandex.com/images/search?" + urllib.parse.urlencode({"text": query})
    if orientation == "landscape":
        url += "&iorien=horizontal"
    elif orientation == "portrait":
        url += "&iorien=vertical"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        items = page.query_selector_all("img.serp-item__thumb, .Organic-Preview img")
        urls = [
            src for item in items
            if (src := (item.get_attribute("src") or ""))
            and src.startswith("http")
            and len(src) > 50
        ][:20]
        if not urls:
            print("  [yandex] WARNING: selectors returned 0 URLs — CSS selectors may need updating", file=sys.stderr)
        return urls
    except Exception as exc:
        print(f"  [yandex] search error: {exc}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Main search entry point (called from image_search.py)
# ---------------------------------------------------------------------------


def search(
    request: ImageSearchRequest,
    *,
    license_tier_filter: str = "all",
    search_engines: Optional[list[str]] = None,
    max_results: int = 30,
) -> list[AssetCandidate]:
    """Search with Playwright when API providers fail.

    This is the fallback provider. Called by image_search.py after all API
    providers return empty results.

    Pipeline:
      1. expand_query_dimensions → multi-dimensional queries
      2. Search engines (Bing/Google/Yandex) × queries
      3. Deduplicate URLs
      4. Download, validate, compress
      5. CLIP scoring (if available)
      6. Return top results
    """
    try:
        _ensure_playwright()
    except RuntimeError as exc:
        raise RuntimeError(f"Browser search unavailable: {exc}") from None

    engines = [e for e in (search_engines or ["bing", "yandex"]) if e in VALID_ENGINES]
    if not engines:
        raise RuntimeError("No valid search engines specified")

    queries = expand_query_dimensions(request.query, max_variations=5)

    from playwright.sync_api import sync_playwright  # type: ignore

    all_urls: list[tuple[str, str, str]] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=_CHROMIUM_ARGS)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        ctx.set_extra_http_headers(STEALTH_HEADERS)
        page = ctx.new_page()

        for query in queries:
            for engine in engines:
                try:
                    if engine == "bing":
                        urls = _search_bing(page, query, request.orientation)
                    elif engine == "google":
                        urls = _search_google(page, query, request.orientation)
                    elif engine == "yandex":
                        urls = _search_yandex(page, query, request.orientation)
                    else:
                        continue
                    for url in urls:
                        all_urls.append((url, engine, query))
                except Exception:
                    continue

        browser.close()

    # Deduplicate URLs by hash
    seen_hashes: set[str] = set()
    unique_urls: list[tuple[str, str, str]] = []
    for url, engine, query in all_urls:
        h = _url_hash(url)
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique_urls.append((url, engine, query))

    if not unique_urls:
        return []

    # Download and rank
    ranked: list[tuple[float, str, str, bytes]] = []
    has_clip = _load_clip()

    # Phase 1: Concurrent download + compress
    def _download_and_compress(item: tuple[str, str, str]) -> tuple[bytes, str, str, str] | None:
        url, engine, query = item
        result = _download_and_validate(url)
        if result is None:
            return None
        data, content_type = result
        try:
            compressed = _compress_to_jpeg(data)
        except (OSError, ValueError):
            return None
        return compressed, url, engine, query

    downloaded: list[tuple[bytes, str, str, str]] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_download_and_compress, item): item
                   for item in unique_urls[:max_results]}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                downloaded.append(result)

    # Phase 2: Serial scoring (CLIP model is not thread-safe)
    for compressed, url, engine, query in downloaded:
        if has_clip:
            clip_score = score_image_relevance(compressed, request.query)
            if clip_score < CLIP_MIN_SCORE:
                continue
            relevance = clip_score
        else:
            relevance = 0.8  # Default for browser results

        ranked.append((relevance, url, engine, compressed))

    ranked.sort(key=lambda t: t[0], reverse=True)

    # Build AssetCandidates
    results: list[AssetCandidate] = []
    for relevance, url, engine, data in ranked:
        source_label = {
            "bing": "Bing Images",
            "google": "Google Images",
            "yandex": "Yandex Images",
        }.get(engine, engine)

        try:
            from PIL import Image  # type: ignore
            img = Image.open(io.BytesIO(data))
            w, h = img.size
        except Exception:
            w, h = IMAGE_MAX_WIDTH, IMAGE_MAX_HEIGHT

        results.append(AssetCandidate(
            provider="browser",
            title=f"[{source_label}] {request.query}",
            source_page_url=url,
            license_name=LICENSE_TIER_BROWSER,
            license_tier=LICENSE_TIER_BROWSER,
            width=w,
            height=h,
            download_url=url,
            author=f"{source_label} search",
        ))

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


__all__ = [
    "search",
    "capture_url_screenshots",
    "expand_query_dimensions",
    "score_image_relevance",
    "SUPPORTED_ENGINES",
    "LICENSE_TIER_BROWSER",
]
