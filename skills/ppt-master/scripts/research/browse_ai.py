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


# --- Role-aware prompt templates ---

_ROLE_PROMPTS = {
    "hook": (
        "我需要一个引人注目的开场素材来展示「{topic}」这个主题。\n\n"
        "请帮我找到:\n"
        "1. 一个令人惊讶的事实或统计数据（必须有具体数字和来源）\n"
        "2. 一个相关的名人引述或行业观点（注明出处）\n"
        "3. 当前最热门的讨论话题或争议点\n\n"
        "要求: 信息新鲜（优先2024-2025年），有明确来源URL。"
    ),
    "evidence": (
        "我正在为PPT制作一个核心论点页面，主题是「{topic}」。\n"
        "论点: {data_hint}\n\n"
        "请帮我搜集支撑这个论点的证据:\n"
        "1. 至少2个具体数据点（含数字、百分比、金额、年份）\n"
        "2. 至少1个真实案例或行业标杆\n"
        "3. 至少1个权威来源的引述\n"
        "4. 来源URL（优先: 官方报告 > 权威媒体 > 行业博客）\n\n"
        "输出格式: 每条证据后标注 [来源: URL]"
    ),
    "deep_dive": (
        "我需要深度分析材料来支撑「{topic}」的详细讲解页面。\n"
        "分析角度: {data_hint}\n\n"
        "请深入研究并提供:\n"
        "1. 发展历程/时间线（关键节点 + 时间 + 事件）\n"
        "2. 多角度对比数据（至少2个维度的对比）\n"
        "3. 专家/机构观点（直接引述 + 出处）\n"
        "4. 未来趋势预测（含具体预测数字和来源）\n"
        "5. 反面观点或风险因素\n\n"
        "要求: 每条信息必须有来源URL，数据必须可验证，优先学术论文和官方报告。"
    ),
    "transition": (
        "我需要总结性材料来制作PPT的过渡页面，主题是「{topic}」。\n\n"
        "请帮我找到:\n"
        "1. 对主题的精炼总结（1-2句话概括核心观点）\n"
        "2. 适合放在PPT上的金句（不超过30字）\n"
        "3. 承上启下的过渡语\n\n"
        "要求: 简洁有力，适合PPT展示。"
    ),
    "synthesis": (
        "我需要总结性材料来制作PPT的总结页面，主题是「{topic}」。\n\n"
        "请帮我找到:\n"
        "1. 核心发现的精炼总结\n"
        "2. 行动建议或未来展望（具体、可执行）\n"
        "3. 令人印象深刻的收尾金句\n\n"
        "要求: 简洁有力，每条不超过30字。"
    ),
}

# Fallback for unknown roles
_DEFAULT_PROMPT = (
    "请帮我搜索并整理以下主题的详细信息。\n\n"
    "主题: {topic}\n关键词: {keywords}\n"
    "重点关注: {data_hint}\n\n"
    "请提供:\n"
    "1. 核心事实和数据（含具体数字和年份）\n"
    "2. 来源链接（URL）\n"
    "3. 关键引述\n\n"
    "要求: 信息必须有明确来源，数据必须包含具体数字。"
)


def _build_role_prompt(role: str, topic: str, keywords: str, data_hint: str) -> str:
    """Build a search prompt tailored to the page's narrative role."""
    template = _ROLE_PROMPTS.get(role, _DEFAULT_PROMPT)
    return template.format(topic=topic, keywords=keywords, data_hint=data_hint)


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

        # Build search prompt based on narrative role
        kw_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
        role = item.get("narrative_role", item.get("content_type", "evidence"))
        data_hint = item.get("data_hint", topic)

        prompt = _build_role_prompt(role, topic, kw_str, data_hint)

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


def validate_selectors(cdp_port: int | None = None, chrome_profile: str | None = None):
    """Test if CSS selectors for each AI service still work.

    Opens each AI service page and checks:
    1. Input element (textarea / contenteditable) is found and visible
    2. Submit button is found
    3. Page loads without errors

    Returns a dict of {service: {input: bool, submit: bool, error: str|None}}.
    """
    pw, ctx, is_persistent = connect_browser(chrome_profile, cdp_port)
    results = {}

    for key, svc in AI_SERVICES.items():
        print(f"\nValidating {svc['name']}...")
        result = {"input": False, "submit": False, "error": None}

        try:
            page = ctx.new_page()
            # Try each URL
            loaded = False
            for url in svc["urls"]:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    loaded = True
                    break
                except Exception:
                    continue

            if not loaded:
                result["error"] = "Failed to load any URL"
                page.close()
                results[key] = result
                print(f"  [FAIL] {result['error']}")
                continue

            # Wait for page to settle
            time.sleep(3)

            # Check input element
            input_el = page.query_selector(svc["input_selector"])
            if input_el and input_el.is_visible():
                result["input"] = True
                print(f"  [OK] Input element found")
            else:
                # Try fallback selectors
                for fallback_sel in ["textarea", "[contenteditable='true']", "[role='textbox']"]:
                    el = page.query_selector(fallback_sel)
                    if el and el.is_visible():
                        result["input"] = True
                        print(f"  [WARN] Input found via fallback: {fallback_sel}")
                        break
                if not result["input"]:
                    print(f"  [FAIL] No visible input element")

            # Check submit button
            submit_btn = page.query_selector(svc["submit_selector"])
            if submit_btn and submit_btn.is_visible():
                result["submit"] = True
                print(f"  [OK] Submit button found")
            else:
                # Submit buttons often appear after typing, so this is a soft check
                print(f"  [WARN] Submit button not immediately visible (may appear after typing)")

            page.close()

        except Exception as e:
            result["error"] = str(e)[:100]
            print(f"  [FAIL] {result['error']}")

        results[key] = result

    # Cleanup
    try:
        if is_persistent:
            ctx.close()
        else:
            ctx.close()
            pw.stop()
    except Exception:
        pass

    # Summary
    print("\n" + "=" * 50)
    print("Selector Validation Summary")
    print("=" * 50)
    all_ok = True
    for key, r in results.items():
        status = "OK" if r["input"] else "NEEDS UPDATE"
        if not r["input"]:
            all_ok = False
        print(f"  {AI_SERVICES[key]['name']:12s}: input={'OK' if r['input'] else 'FAIL'}  "
              f"submit={'OK' if r['submit'] else 'WARN'}  "
              f"error={r['error'] or 'none'}")

    if all_ok:
        print("\nAll selectors working.")
    else:
        print("\nSome selectors need updating. Check the AI service pages for DOM changes.")
        print("Update AI_SERVICES in browse_ai.py with new CSS selectors.")

    return results


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
    parser.add_argument("--validate", action="store_true", help="Test if AI service selectors still work")
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

    if args.validate:
        validate_selectors(args.cdp_port, args.chrome_profile)
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
