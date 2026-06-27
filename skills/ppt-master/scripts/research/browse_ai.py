#!/usr/bin/env python3
"""AI Browser Search — Playwright-based automation for ChatGPT / Grok / Perplexity.

Usage:
    # Single search
    python browse_ai.py --ai chatgpt --prompt "What is X?" --output result.md

    # Batch search (reads search_plan.json)
    python browse_ai.py --batch search_plan.json --output-dir _research/step3_search/

    # Use specific Chrome profile (preserves login)
    python browse_ai.py --ai grok --prompt "..." --chrome-profile "C:/Users/.../User Data"

    # List supported AI services
    python browse_ai.py --list
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("ERROR: playwright is not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# ---------------------------------------------------------------------------
# AI service definitions
# ---------------------------------------------------------------------------

AI_SERVICES = {
    "chatgpt": {
        "name": "ChatGPT",
        "urls": ["https://chat.openai.com/", "https://chatgpt.com/"],
        "input_selector": "#prompt-textarea, textarea[data-id='root'], div#prompt-textarea",
        "submit_selector": "button[data-testid='send-button'], button[aria-label='Send prompt']",
        "response_selector": "div.markdown.prose, div[data-message-author-role='assistant']",
        "stop_selector": "button[aria-label='Stop generating'], button[data-testid='stop-button']",
        "new_chat_selector": "a[href='/'], nav a:first-child",
        "wait_ready_selector": "#prompt-textarea, textarea[data-id='root']",
    },
    "grok": {
        "name": "Grok",
        "urls": ["https://grok.com/", "https://x.com/i/grok"],
        "input_selector": "[contenteditable='true'], textarea",
        "submit_selector": "button[aria-label='提交'], button[aria-label='Send'], button[aria-label='Submit']",
        "response_selector": "article, div[class*='message'], div[class*='response']",
        "stop_selector": "button[aria-label='停止'], button[aria-label='Stop']",
        "new_chat_selector": "a[href='/'], button:has-text('New')",
        "wait_ready_selector": "[contenteditable='true'], textarea",
    },
    "perplexity": {
        "name": "Perplexity",
        "urls": ["https://www.perplexity.ai/", "https://perplexity.ai/"],
        "input_selector": "textarea, div[contenteditable='true'], [role='textbox']",
        "submit_selector": "button[aria-label='Submit'], button[aria-label='Ask']",
        "response_selector": "div.prose, div[class*='answer'], div[class*='response']",
        "stop_selector": "button:has-text('Stop')",
        "new_chat_selector": "a[href='/'], button:has-text('New')",
        "wait_ready_selector": "textarea, div[contenteditable='true']",
    },
}

# Fallback order when primary AI is unavailable
FALLBACK_ORDER = {
    "chatgpt": ["grok", "perplexity"],
    "grok": ["chatgpt", "perplexity"],
    "perplexity": ["chatgpt", "grok"],
}


def list_services():
    """Print supported AI services."""
    print("Supported AI services:")
    for key, svc in AI_SERVICES.items():
        print(f"  {key:12s}  {svc['name']}")


def connect_browser(chrome_profile: str | None = None, cdp_port: int | None = None):
    """Connect to or launch a Chromium browser.

    Connection priority:
    1. CDP (Chrome DevTools Protocol) — connect to an already-running Chrome
       at localhost:<cdp_port>. This is the recommended mode: launch Chrome
       with --remote-debugging-port first (see scripts/start-hermes-chrome.bat),
       then connect. Preserves all login sessions.
    2. Persistent context — launch Chrome with the given chrome_profile dir.
       Preserves login sessions but launches a new Chrome instance.
    3. Fresh Chromium — no profile, no persistence. Fallback only.
    """
    pw = sync_playwright().start()

    # Mode 1: CDP connection to already-running Chrome
    if cdp_port:
        cdp_url = f"http://localhost:{cdp_port}"
        try:
            browser = pw.chromium.connect_over_cdp(cdp_url)
            print(f"  Connected to Chrome via CDP at {cdp_url}")
            # connect_over_cdp returns a Browser; get or create a context
            if browser.contexts:
                context = browser.contexts[0]
            else:
                context = browser.new_context(viewport={"width": 1280, "height": 900})
            return pw, context, True
        except Exception as e:
            print(f"  CDP connection failed ({e}), falling back to launch mode")

    # Mode 2: Persistent context with chrome_profile
    if chrome_profile:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=chrome_profile,
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )
        return pw, browser, True  # True = persistent context

    # Mode 3: Fresh Chromium (no persistence)
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    return pw, context, False


def wait_for_input(page, svc: dict, timeout: int = 30000) -> bool:
    """Wait for the AI page to be ready for input."""
    try:
        page.wait_for_selector(svc["wait_ready_selector"], timeout=timeout)
        return True
    except PwTimeout:
        return False


def send_prompt(page, svc: dict, prompt: str) -> bool:
    """Type prompt into the AI input and submit."""
    try:
        # Try to find the input element
        input_el = page.wait_for_selector(svc["input_selector"], timeout=10000)
        if not input_el:
            return False

        # Click to focus
        input_el.click()
        time.sleep(0.5)

        # Contenteditable elements need keyboard.type() instead of fill()
        tag = input_el.evaluate("el => el.tagName.toLowerCase()")
        is_editable = input_el.evaluate("el => el.contentEditable === 'true'")
        if is_editable or tag == "div":
            page.keyboard.type(prompt, delay=20)
        else:
            input_el.fill(prompt)
        time.sleep(0.3)

        # Try to submit via button first, then Enter key
        try:
            submit_btn = page.query_selector(svc["submit_selector"])
            if submit_btn and submit_btn.is_visible():
                submit_btn.click()
            else:
                page.keyboard.press("Enter")
        except Exception:
            page.keyboard.press("Enter")

        return True
    except Exception as e:
        print(f"  Warning: send_prompt failed: {e}")
        return False


def wait_for_response(page, svc: dict, timeout: int = 120000) -> str | None:
    """Wait for the AI to finish responding and extract text."""
    start = time.time()
    last_text = ""
    stable_count = 0
    stable_threshold = 3  # Number of consecutive checks with same text = done

    time.sleep(3)  # Initial wait for response to start

    while (time.time() - start) * 1000 < timeout:
        # Check if still generating
        try:
            stop_btn = page.query_selector(svc["stop_selector"])
            if stop_btn and stop_btn.is_visible():
                time.sleep(2)
                continue
        except Exception:
            pass

        # Extract current response text
        try:
            responses = page.query_selector_all(svc["response_selector"])
            if responses:
                current_text = responses[-1].inner_text().strip()
                if current_text and len(current_text) > 10:
                    if current_text == last_text:
                        stable_count += 1
                        if stable_count >= stable_threshold:
                            return current_text
                    else:
                        stable_count = 0
                        last_text = current_text
        except Exception:
            pass

        time.sleep(2)

    # Timeout — return whatever we have
    if last_text:
        print("  Warning: Response wait timed out, returning partial result")
        return last_text
    return None


def search_single(ai: str, prompt: str, output: str | None, chrome_profile: str | None, timeout: int, cdp_port: int | None = None) -> str:
    """Perform a single AI search and return the result text."""
    if ai not in AI_SERVICES:
        print(f"ERROR: Unknown AI service '{ai}'. Use --list to see options.")
        sys.exit(1)

    svc = AI_SERVICES[ai]
    print(f"Searching with {svc['name']}...")
    print(f"  Prompt: {prompt[:80]}...")

    pw, ctx, is_persistent = connect_browser(chrome_profile, cdp_port)
    try:
        page = ctx.new_page() if is_persistent else ctx.new_page()

        # Navigate to AI service
        for url in svc["urls"]:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                break
            except Exception:
                continue

        # Wait for page to be ready
        if not wait_for_input(page, svc, timeout=30000):
            print(f"  ERROR: {svc['name']} page did not load properly")
            # Try fallback
            for fallback_ai in FALLBACK_ORDER.get(ai, []):
                print(f"  Trying fallback: {AI_SERVICES[fallback_ai]['name']}...")
                page.close()
                return search_single(fallback_ai, prompt, output, chrome_profile, timeout, cdp_port)
            return ""

        # Send the prompt
        if not send_prompt(page, svc, prompt):
            print(f"  ERROR: Could not send prompt to {svc['name']}")
            return ""

        # Wait for response
        result = wait_for_response(page, svc, timeout=timeout)
        if not result:
            print(f"  WARNING: No response from {svc['name']}")
            return ""

        print(f"  Got {len(result)} chars from {svc['name']}")

        # Save to file if output specified
        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result, encoding="utf-8")
            print(f"  Saved to {output}")

        return result

    finally:
        try:
            if is_persistent:
                ctx.close()
            else:
                ctx.close()
                pw.stop()
        except Exception:
            pass


def search_batch(batch_file: str, output_dir: str, chrome_profile: str | None, timeout: int, cdp_port: int | None = None):
    """Batch search: read search_plan.json and execute each item."""
    plan_path = Path(batch_file)
    if not plan_path.exists():
        print(f"ERROR: Batch file not found: {batch_file}")
        sys.exit(1)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # plan is a list of {page_id, topic, keywords, ai_target, ...}
    items = plan if isinstance(plan, list) else plan.get("pages", plan.get("items", []))

    manifest = []
    total = len(items)

    for i, item in enumerate(items):
        page_id = item.get("page_id", f"p{i+1:02d}")
        topic = item.get("topic", item.get("title", ""))
        keywords = item.get("keywords", [])
        ai_target = item.get("ai_target", "chatgpt")
        skip = item.get("skip_search", False)

        if skip:
            print(f"[{i+1}/{total}] Skipping {page_id} (skip_search=true)")
            manifest.append({"page_id": page_id, "status": "skipped"})
            continue

        # Build search prompt
        kw_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        prompt = f"请帮我搜索并整理以下主题的详细信息，包括具体数据、事实、来源URL：\n\n主题：{topic}\n关键词：{kw_str}\n\n请提供：\n1. 核心事实和数据（含具体数字）\n2. 来源链接\n3. 关键引述\n4. 相关图片建议（关键词）"

        filename = f"{page_id}_{topic[:30].replace(' ', '_').replace('/', '_')}.md"
        output_path = str(out_dir / filename)

        print(f"\n[{i+1}/{total}] {page_id}: {topic}")
        result = search_single(ai_target, prompt, output_path, chrome_profile, timeout, cdp_port)

        manifest.append({
            "page_id": page_id,
            "topic": topic,
            "ai_used": ai_target,
            "output_file": filename,
            "char_count": len(result),
            "status": "success" if len(result) > 200 else "low_quality",
        })

        # Brief pause between searches to avoid rate limiting
        if i < total - 1:
            time.sleep(3)

    # Save manifest
    manifest_path = out_dir / "search_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest saved to {manifest_path}")

    success = sum(1 for m in manifest if m.get("status") == "success")
    print(f"Done: {success}/{total} successful searches")


def _load_hermes_env() -> dict:
    """Load Hermes Chrome config from scripts/.hermes-chrome.env if available."""
    env = {}
    # Walk up from this script to find the project root's scripts/.hermes-chrome.env
    # This script: <skill>/scripts/research/browse_ai.py
    # Target:      <project>/scripts/.hermes-chrome.env
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts" / ".hermes-chrome.env",
        Path(__file__).resolve().parent.parent / ".hermes-chrome.env",
    ]
    for env_file in candidates:
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip()
            break
    return env


def main():
    # Pre-load Hermes Chrome config
    hermes_env = _load_hermes_env()

    parser = argparse.ArgumentParser(description="AI Browser Search — Playwright automation")
    parser.add_argument("--list", action="store_true", help="List supported AI services")
    parser.add_argument("--ai", choices=list(AI_SERVICES.keys()), help="AI service to use")
    parser.add_argument("--prompt", help="Search prompt")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--batch", help="Batch search plan JSON file")
    parser.add_argument("--output-dir", help="Output directory for batch mode")
    parser.add_argument("--cdp-port", type=int,
                        default=int(hermes_env.get("HERMES_CHROME_PORT", "0")) or None,
                        help="CDP port to connect to running Chrome (default: from .hermes-chrome.env or none)")
    parser.add_argument("--chrome-profile",
                        default=hermes_env.get("HERMES_CHROME_PROFILE"),
                        help="Chrome user data dir (preserves login; default: from .hermes-chrome.env)")
    parser.add_argument("--timeout", type=int, default=120000, help="Response timeout in ms")
    args = parser.parse_args()

    if args.list:
        list_services()
        return

    if args.batch:
        if not args.output_dir:
            args.output_dir = str(Path(args.batch).parent / "results")
        search_batch(args.batch, args.output_dir, args.chrome_profile, args.timeout, args.cdp_port)
        return

    if not args.ai or not args.prompt:
        parser.print_help()
        print("\nERROR: --ai and --prompt are required for single search mode")
        sys.exit(1)

    result = search_single(args.ai, args.prompt, args.output, args.chrome_profile, args.timeout, args.cdp_port)
    if not args.output and result:
        print("\n--- Result ---")
        print(result[:2000])
        if len(result) > 2000:
            print(f"\n... ({len(result)} chars total, truncated)")


if __name__ == "__main__":
    main()
