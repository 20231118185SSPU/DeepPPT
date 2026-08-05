#!/usr/bin/env python3
"""
PPT Master - Script Smoke Check

Verifies that all top-level scripts under scripts/ plus selected nested
entry points can be imported and that their CLI entry points respond to
--help without crashing.

Usage:
    python3 skills/ppt-master/scripts/smoke_check.py
    python3 skills/ppt-master/scripts/smoke_check.py --scripts-dir <path>
    python3 skills/ppt-master/scripts/smoke_check.py --skip-help

Examples:
    python3 skills/ppt-master/scripts/smoke_check.py
    python3 skills/ppt-master/scripts/smoke_check.py --skip-help

Dependencies:
    None for import checks (--help checks may need project deps)

Notes:
    - Import check: verifies the module loads without ImportError
    - --help check: invokes each script's CLI with --help, catches crashes
    - Scripts that require interactive input or long startup are skipped
    - Selected nested entry points are included when they are workflow-facing
    - Exit 0 = all pass; exit 1 = failures found
"""

import os
import sys
import argparse
import importlib
import importlib.util
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

# Scripts that need interactive input or a running server — skip --help check.
_SKIP_HELP: set[str] = {
    "confirm_ui/server.py",
    "svg_editor/server.py",
    "server_common.py",
}

# Nested entry points that are directly exposed in SKILL.md / AGENTS.md.
_EXTRA_ENTRYPOINTS: set[str] = {
    "dashboard/server.py",
}

# Thin wrappers that delegate to a same-named sub-package.
# Import check is unreliable (name collision), but --help works fine.
_WRAP_ONLY: set[str] = {
    "svg_to_pptx.py",
    "pptx_to_svg.py",
    "template_fill_pptx.py",
}

# Scripts that have heavy import-time side effects (network, DB) — skip import.
_SKIP_IMPORT: set[str] = set()


def find_scripts(scripts_dir: Path) -> list[Path]:
    """Return smoke-covered script entry points."""
    scripts = [
        p for p in scripts_dir.glob("*.py")
        if p.name != "__init__.py" and p.name != "smoke_check.py"
    ]
    for rel in _EXTRA_ENTRYPOINTS:
        path = scripts_dir / rel
        if path.is_file():
            scripts.append(path)
    return sorted(scripts, key=lambda p: p.relative_to(scripts_dir).as_posix())


def check_import(script_path: Path, scripts_dir: Path) -> tuple[bool, str]:
    """Try to import the script as a module. Returns (ok, message)."""
    module_name = script_path.stem
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        return False, "cannot create module spec"

    try:
        # Import without executing __main__ block
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        del sys.modules[module_name]
        return True, "ok"
    except SystemExit:
        # Some scripts raise SystemExit(0) in __main__ guard — that's fine
        if module_name in sys.modules:
            del sys.modules[module_name]
        return True, "ok (SystemExit 0)"
    except ImportError as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        # Optional dependency failures are expected
        if "optional" in str(e).lower() or "not installed" in str(e).lower():
            return True, f"ok (optional dep missing: {e})"
        return False, f"ImportError: {e}"
    except Exception as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        return False, f"{type(e).__name__}: {e}"


def check_help(script_path: Path, python: str) -> tuple[bool, str]:
    """Run the script with --help. Returns (ok, message)."""
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        result = subprocess.run(
            [python, str(script_path), "--help"],
            capture_output=True,
            timeout=15,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return True, "ok"
        else:
            stderr_tail = result.stderr.strip().splitlines()[-1:] if result.stderr.strip() else []
            return False, f"exit {result.returncode}: {stderr_tail[0] if stderr_tail else 'no stderr'}"
    except subprocess.TimeoutExpired:
        return False, "timeout (15s)"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def dashboard_e2e_smoke(scripts_dir: Path) -> tuple[bool, str]:
    """Start two project dashboards and verify each URL serves its own project."""
    repo_root = scripts_dir.parents[2]
    projects_dir = repo_root / "projects"
    projects: list[Path] = []
    urls: list[str] = []
    stage = "init"
    try:
        from project_manager import ProjectManager
        from dashboard_launcher import launch_dashboard_daemon

        projects_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manager = ProjectManager(projects_dir)
        for suffix in ("a", "b"):
            name = f"_smoke_dashboard_{stamp}_{suffix}_{uuid.uuid4().hex[:6]}"
            projects.append(Path(manager.init_project(name, "ppt169")).resolve())

        stage = "launch"
        for project in projects:
            result = launch_dashboard_daemon(project, port=8765, no_browser=True)
            if result != 0:
                return False, f"launch returned {result}; project={project}"

        stage = "lock"
        for project in projects:
            lock = _wait_for_lock(project / ".dashboard.lock")
            if not lock:
                return False, f"dashboard lock not found; project={project}; log={_dashboard_log(project)}"
            port = int(lock.get("port", 0) or 0)
            url = str(lock.get("url") or f"http://127.0.0.1:{port}/")
            if not port:
                return False, f"dashboard lock missing port; project={project}; log={_dashboard_log(project)}"
            urls.append(url)
        if urls[0].rstrip("/") == urls[1].rstrip("/"):
            return False, f"dashboards reused one URL for two projects: {urls[0]}"

        stage = "state"
        for project, url in zip(projects, urls):
            config = _get_json(f"{url.rstrip('/')}/api/config")
            if Path(str(config.get("project_path") or "")).resolve() != project:
                return False, f"/api/config project mismatch; url={url}; project={project}"
            state = _get_json(f"{url.rstrip('/')}/api/state")
            missing = [
                key for key in (
                    "project_name",
                    "project_path",
                    "canvas_format",
                    "steps",
                    "current_step",
                    "confirm_ui",
                    "live_preview",
                )
                if key not in state
            ]
            if missing:
                return False, f"/api/state missing {missing}; url={url}; log={_dashboard_log(project)}"
            if Path(str(state.get("project_path") or "")).resolve() != project:
                return False, f"/api/state project mismatch; url={url}; project={project}"

        stage = "shutdown"
        for project, url in zip(projects, urls):
            _post_json(f"{url.rstrip('/')}/api/shutdown")
            if not _wait_for_down(f"{url.rstrip('/')}/api/state"):
                return False, f"dashboard still responds after shutdown; url={url}; log={_dashboard_log(project)}"

        stage = "cleanup"
        for project in projects:
            shutil.rmtree(project)
        return True, f"PASS dashboard-e2e urls={', '.join(urls)}"
    except Exception as exc:
        return False, f"dashboard-e2e failed at {stage}: {type(exc).__name__}: {exc}; projects={projects}"
    finally:
        for url in urls:
            try:
                _post_json(f"{url.rstrip('/')}/api/shutdown", timeout=1.0)
            except (urllib.error.URLError, TimeoutError, OSError):
                pass
        for project in projects:
            if project.name.startswith("_smoke_dashboard_") and project.exists():
                try:
                    shutil.rmtree(project)
                except OSError:
                    pass


def _wait_for_lock(lock_path: Path, timeout: float = 10.0) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            time.sleep(0.2)
            continue
        if isinstance(data, dict):
            return data
    return None


def _get_json(url: str, timeout: float = 3.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return data


def _post_json(url: str, timeout: float = 3.0) -> None:
    request = urllib.request.Request(
        url,
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout):
        pass


def _wait_for_down(url: str, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=0.5).close()
        except (urllib.error.URLError, TimeoutError, OSError):
            return True
        time.sleep(0.2)
    return False


def _dashboard_log(project: Path) -> Path:
    return project / "dashboard" / "dashboard.log"


def check_state_derivation(scripts_dir: Path, tmp_path: Path) -> tuple[bool, str]:
    """Exercise project_utils.derive_pipeline_state across the staged chain.

    Builds one artifact at a time in a temp project and asserts the derived
    step advances 1-init -> ... -> 8-export, plus determinism on repeat calls.
    Returns (ok, detail).
    """
    probe = '''import sys, pathlib
sys.path.insert(0, r"{SCRIPTS}")
from project_utils import derive_pipeline_state
p = pathlib.Path(r"{PROJ}")
def mk(*parts):
    (p.joinpath(*parts)).parent.mkdir(parents=True, exist_ok=True)
    (p.joinpath(*parts)).write_text("x", encoding="utf-8")
expect = ["1-init", "2-sources", "3-content-selection", "3-outline",
          "4-design-spec", "5-spec-lock", "6-images", "7a-svg-gen",
          "7b-postprocess", "7c-export", "8-export"]
got = [derive_pipeline_state(p)["step"]]
mk("sources", "s.md"); got.append(derive_pipeline_state(p)["step"])
mk("content_selection.json"); got.append(derive_pipeline_state(p)["step"])
mk("detailed_outline.json"); got.append(derive_pipeline_state(p)["step"])
mk("design_spec.md"); got.append(derive_pipeline_state(p)["step"])
mk("spec_lock.md"); got.append(derive_pipeline_state(p)["step"])
mk("images", "a.png"); got.append(derive_pipeline_state(p)["step"])
mk("svg_output", "01_a.svg"); got.append(derive_pipeline_state(p)["step"])
mk("notes", "total.md"); got.append(derive_pipeline_state(p)["step"])
mk("svg_final", "01_a.svg"); got.append(derive_pipeline_state(p)["step"])
mk("exports", "deck.pptx"); got.append(derive_pipeline_state(p)["step"])
assert got == expect, f"chain mismatch: {got} != {expect}"
assert derive_pipeline_state(p) == derive_pipeline_state(p), "non-deterministic"
print("state chain OK")
'''.replace("{SCRIPTS}", str(scripts_dir)).replace("{PROJ}", str(tmp_path / "state_project"))
    try:
        r = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20)
        return r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return False, "timed out (20s)"


def _officecli_binary_installed(installer: Path, python: str) -> bool:
    """Detect whether the pinned OfficeCLI binary is installed (offline)."""
    try:
        r = subprocess.run(
            [python, str(installer), "path", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
        if r.returncode == 0:
            return bool(json.loads(r.stdout).get("exists"))
    except Exception:
        pass
    return False


def integration_smoke(scripts_dir: Path) -> tuple[int, int, int]:
    """Run integration-level smoke tests on core scripts.

    Tests that core scripts produce correct output for known inputs,
    not just that they import. Returns (passed, failed, skipped).
    """
    python = sys.executable
    passed = failed = skipped = 0
    tmp_dir = Path(uuid.uuid4().hex[:8])
    tmp_path = scripts_dir.parent / "_smoke_test" / tmp_dir

    def _run(cmd: list[str], label: str, *, expect_exit: int = 0, timeout: int = 15) -> bool:
        nonlocal passed, failed
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
            if r.returncode == expect_exit:
                print(f"  [PASS] {label}")
                passed += 1
                return True
            else:
                print(f"  [FAIL] {label} — exit {r.returncode}, expected {expect_exit}")
                if r.stderr.strip():
                    print(f"         stderr: {r.stderr.strip()[:200]}")
                failed += 1
                return False
        except subprocess.TimeoutExpired:
            print(f"  [FAIL] {label} — timed out ({timeout}s)")
            failed += 1
            return False
        except Exception as e:
            print(f"  [FAIL] {label} — {type(e).__name__}: {e}")
            failed += 1
            return False

    try:
        tmp_path.mkdir(parents=True, exist_ok=True)

        # --- Test 1: config.py loads and has expected keys ---
        print("\n  [1] config.py module loads correctly")
        cfg_script = scripts_dir / "config.py"
        _run([python, "-c", (
            f"import sys; sys.path.insert(0, r'{scripts_dir}'); "
            "from config import CANVAS_FORMATS, Config; "
            "assert 'ppt169' in CANVAS_FORMATS, 'ppt169 missing'; "
            "assert Config.get_canvas_format('ppt169') is not None, 'get_canvas_format failed'; "
            "assert len(Config.get_all_canvas_formats()) >= 5, 'too few formats'; "
            "print('config OK')"
        )], "config.py loads + CANVAS_FORMATS + Config")

        # --- Test 2: console_encoding.py ---
        print("\n  [2] console_encoding.py works")
        _run([python, "-c", (
            f"import sys; sys.path.insert(0, r'{scripts_dir}'); "
            "from console_encoding import configure_utf8_stdio; "
            "configure_utf8_stdio(); "
            "print('encoding OK')"
        )], "console_encoding.py configure_utf8_stdio")

        # --- Test 3: spec_lock_digest.py round-trip ---
        print("\n  [3] spec_lock_digest.py generate + verify round-trip")
        spec_lock = tmp_path / "spec_lock.md"
        spec_lock.write_text(
            "## canvas\n- viewBox: 0 0 1280 720\n- format: PPT 16:9\n\n"
            "## mode\n- mode: narrative\n\n"
            "## visual_style\n- visual_style: swiss-minimal\n\n"
            "## colors\n- bg: #FFFFFF\n- primary: #1A1A2E\n\n"
            "## typography\n- font_family: Arial\n- body: 22\n\n"
            "## icons\n- library: tabler-outline\n\n"
            "## images\n- none\n\n"
            "## decisions\n- rationale: test\n\n"
            "## page_rhythm\n- page1: anchor\n\n"
            "## page_layouts\n- page1: 03_content.svg\n\n"
            "## page_charts\n- none\n\n"
            "## forbidden\n- no emoji\n",
            encoding="utf-8"
        )
        digest_script = scripts_dir / "spec_lock_digest.py"
        if digest_script.is_file():
            _run([python, str(digest_script), "generate", str(tmp_path)],
                 "spec_lock_digest.py generate")
            _run([python, str(digest_script), "verify", str(tmp_path)],
                 "spec_lock_digest.py verify (should pass)")
            # Tamper with spec_lock and verify should fail
            spec_lock.write_text(
                spec_lock.read_text(encoding="utf-8") + "\n## tampered\n- yes\n",
                encoding="utf-8"
            )
            _run([python, str(digest_script), "verify", str(tmp_path)],
                 "spec_lock_digest.py verify (tampered, should fail)", expect_exit=2)
        else:
            print(f"  [SKIP] spec_lock_digest.py not found")
            skipped += 1

        # --- Test 4: spec_lock_validate.py ---
        print("\n  [4] spec_lock_validate.py validates correctly")
        validate_script = scripts_dir / "spec_lock_validate.py"
        if validate_script.is_file():
            # Restore valid spec_lock
            spec_lock.write_text(
                "## canvas\n- viewBox: 0 0 1280 720\n- format: PPT 16:9\n\n"
                "## mode\n- mode: narrative\n\n"
                "## visual_style\n- visual_style: swiss-minimal\n\n"
                "## colors\n- bg: #FFFFFF\n- primary: #1A1A2E\n\n"
                "## typography\n- font_family: Arial\n- body: 22\n\n"
                "## icons\n- library: tabler-outline\n\n"
                "## images\n- none\n\n"
                "## decisions\n- rationale: test\n\n"
                "## page_rhythm\n- page1: anchor\n\n"
                "## page_layouts\n- page1: 03_content.svg\n\n"
                "## page_charts\n- none\n\n"
                "## forbidden\n- no emoji\n",
                encoding="utf-8"
            )
            _run([python, str(validate_script), str(tmp_path)],
                 "spec_lock_validate.py (valid spec)")
            # Test with missing sections
            incomplete = tmp_path / "incomplete_project"
            incomplete.mkdir(exist_ok=True)
            (incomplete / "spec_lock.md").write_text(
                "## canvas\n- viewBox: 0 0 1280 720\n", encoding="utf-8"
            )
            _run([python, str(validate_script), str(incomplete)],
                 "spec_lock_validate.py (incomplete, should fail)", expect_exit=1)
            # Test with missing file
            _run([python, str(validate_script), str(tmp_path / "nonexistent")],
                 "spec_lock_validate.py (missing file, should exit 2)", expect_exit=2)
        else:
            print(f"  [SKIP] spec_lock_validate.py not found")
            skipped += 1

        # --- Test 5: spec_compliance_check.py --help ---
        print("\n  [5] spec_compliance_check.py --help")
        scc = scripts_dir / "spec_compliance_check.py"
        if scc.is_file():
            _run([python, str(scc), "--help"], "spec_compliance_check.py --help")
        else:
            print(f"  [SKIP] spec_compliance_check.py not found")
            skipped += 1

        # --- Test 6: svg_quality_checker.py --help ---
        print("\n  [6] svg_quality_checker.py --help")
        sqc = scripts_dir / "svg_quality_checker.py"
        if sqc.is_file():
            _run([python, str(sqc), "--help"], "svg_quality_checker.py --help")
        else:
            print(f"  [SKIP] svg_quality_checker.py not found")
            skipped += 1

        # --- Test 7: project_utils canonical state derivation ---
        print("\n  [7] project_utils.derive_pipeline_state staged chain")
        state_script = scripts_dir / "project_utils.py"
        if state_script.is_file():
            ok, detail = check_state_derivation(scripts_dir, tmp_path)
            if ok:
                print("  [PASS] project_utils.derive_pipeline_state staged chain + determinism")
                passed += 1
            else:
                print("  [FAIL] project_utils.derive_pipeline_state staged chain + determinism")
                print(f"         {detail.strip()[:300]}")
                failed += 1
        else:
            print(f"  [SKIP] project_utils.py not found")
            skipped += 1

        # --- Test 8: confirm_ui_gate.py bad inputs (fail closed) ---
        print("\n  [8] confirm_ui_gate.py bad inputs (fail closed)")
        gate_script = scripts_dir / "confirm_ui_gate.py"
        if gate_script.is_file():
            bad_proj = tmp_path / "gate_bad"
            (bad_proj / "confirm_ui").mkdir(parents=True, exist_ok=True)
            (bad_proj / "confirm_ui" / "recommendations.stage3.json").write_text(
                "{}", encoding="utf-8"
            )
            result_path = bad_proj / "confirm_ui" / "result.json"

            def _write_result(content: str) -> None:
                result_path.write_text(content, encoding="utf-8")

            _write_result('{"stage": "final", "confirmed_at": "2026-08-04T00:00:00"}')
            _run([python, str(gate_script), str(bad_proj)],
                 "result.json missing status -> non-zero", expect_exit=1)
            _write_result('{"status": "confirmed", "confirmed_at": "2026-08-04T00:00:00"}')
            _run([python, str(gate_script), str(bad_proj)],
                 "result.json missing stage -> non-zero", expect_exit=1)
            _write_result('{"status": "confirmed", "stage": "final", "confirmed_at": "not-a-time"}')
            _run([python, str(gate_script), str(bad_proj)],
                 "result.json bad confirmed_at -> non-zero", expect_exit=1)
            _run([python, str(gate_script), str(tmp_path / "nonexistent_proj")],
                 "missing project -> exit 2", expect_exit=2)
            _write_result(
                '{"status": "confirmed", "stage": "final", '
                '"confirmed_at": "2099-01-01T00:00:00", '
                '"generation_mode": "continuous", "future_field": 42}'
            )
            _run([python, str(gate_script), str(bad_proj)],
                 "valid result with unknown field tolerated -> 0", expect_exit=0)
        else:
            print(f"  [SKIP] confirm_ui_gate.py not found")
            skipped += 1

        # --- Test 9: confirm_ui_gate.py state scenarios ---
        print("\n  [9] confirm_ui_gate.py state scenarios")
        gate_script = scripts_dir / "confirm_ui_gate.py"
        if gate_script.is_file():
            state_proj = tmp_path / "gate_state"
            (state_proj / "confirm_ui").mkdir(parents=True, exist_ok=True)
            (state_proj / "confirm_ui" / "recommendations.stage3.json").write_text(
                "{}", encoding="utf-8"
            )
            state_result = state_proj / "confirm_ui" / "result.json"

            def _write_state_result(content: str) -> None:
                state_result.write_text(content, encoding="utf-8")

            # pending template selection blocks the gate
            _write_state_result(
                '{"status": "confirmed", "stage": "final", '
                '"confirmed_at": "2099-01-01T00:00:00", '
                '"template_selection": {"action": "apply_template", "path": "templates/decks/x"}}'
            )
            _run([python, str(gate_script), str(state_proj)],
                 "pending template_selection -> non-zero", expect_exit=1)
            # chat fallback without --allow-fallback blocks; with it passes
            _write_state_result(
                '{"status": "confirmed", "stage": "final", '
                '"confirmed_at": "2099-01-01T00:00:00", "fallback_confirmed": true}'
            )
            _run([python, str(gate_script), str(state_proj)],
                 "chat fallback without --allow-fallback -> non-zero", expect_exit=1)
            _run([python, str(gate_script), str(state_proj), "--allow-fallback"],
                 "chat fallback with --allow-fallback -> 0", expect_exit=0)
            # stale result (confirmed_at before recommendations mtime) blocks
            _write_state_result(
                '{"status": "confirmed", "stage": "final", '
                '"confirmed_at": "2000-01-01T00:00:00"}'
            )
            _run([python, str(gate_script), str(state_proj)],
                 "stale confirmed_at -> non-zero", expect_exit=1)
            # fresh browser result passes
            _write_state_result(
                '{"status": "confirmed", "stage": "final", '
                '"confirmed_at": "2099-01-01T00:00:00"}'
            )
            _run([python, str(gate_script), str(state_proj)],
                 "fresh browser result -> 0", expect_exit=0)
        else:
            print(f"  [SKIP] confirm_ui_gate.py not found")
            skipped += 1

        # --- Test 10: route fixture contract checks (synthetic fixtures) ---
        print("\n  [10] route fixture contract checks")
        fixtures_dir = scripts_dir.parent / "fixtures"
        if not fixtures_dir.is_dir():
            print(f"  [SKIP] fixtures dir not found: {fixtures_dir}")
            skipped += 1
        else:
            import shutil  # bind before the finally-block's local import shadows it
            fixture_tmp = tmp_path / "fixtures_run"
            fixture_tmp.mkdir(parents=True, exist_ok=True)

            # F4: partial-state diagnostics (derive_pipeline_state stable steps)
            partial_dir = fixtures_dir / "partial"
            probe = '''import sys, pathlib
sys.path.insert(0, r"{SCRIPTS}")
from project_utils import derive_pipeline_state
states = {
    "only_sources": "2-sources",
    "confirmation_pending": "4-design-spec",
    "spec_lock_no_digest": "5-spec-lock",
    "svg_no_export": "7c-export",
    "exported": "8-export",
}
base = pathlib.Path(r"{FIX}")
for name, expect in states.items():
    step = derive_pipeline_state(base / name)["step"]
    assert step == expect, f"{{name}}: got {{step}} != {{expect}}"
    assert derive_pipeline_state(base / name)["step"] == step, "non-deterministic"
print("partial states OK")
'''.replace("{SCRIPTS}", str(scripts_dir)).replace("{FIX}", str(partial_dir))
            try:
                r = subprocess.run([python, "-c", probe], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=30)
                if r.returncode == 0:
                    print("  [PASS] partial-state diagnostics: 5 states stable + deterministic")
                    passed += 1
                else:
                    detail = ((r.stdout or "") + (r.stderr or "")).strip()[:200]
                    print(f"  [FAIL] partial-state diagnostics — {detail}")
                    failed += 1
            except subprocess.TimeoutExpired:
                print("  [FAIL] partial-state diagnostics — timed out (30s)")
                failed += 1
            _run([python, str(scripts_dir / "confirm_ui_gate.py"), str(partial_dir / "confirmation_pending")],
                 "confirm_ui_gate missing confirmation -> non-zero", expect_exit=1)
            _run([python, str(scripts_dir / "spec_lock_digest.py"), "verify", str(partial_dir / "spec_lock_no_digest")],
                 "spec_lock_digest verify missing digest -> non-zero", expect_exit=1)

            # F5: DOCX fidelity — run on a tmp copy; converters never write into fixtures/
            docx_copy = fixture_tmp / "docx"
            docx_copy.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fixtures_dir / "docx_complex" / "complex_v2.docx", docx_copy / "complex_v2.docx")
            docx_out = fixture_tmp / "docx_out.md"
            _run([python, str(scripts_dir / "source_to_md" / "doc_to_md.py"), str(docx_copy / "complex_v2.docx"),
                  "-o", str(docx_out)], "docx fidelity convert -> 0")
            docx_md = docx_out.read_text(encoding="utf-8", errors="replace") if docx_out.exists() else ""
            for token in ("原生表格", "① 区域一", "② 区域二", "2026 Q1", "12.4%",
                          "指标 A", "指标 B", "多段落 第二段内容", "42"):
                if token in docx_md:
                    print(f"  [PASS] docx fidelity token {token!r}")
                    passed += 1
                else:
                    print(f"  [FAIL] docx fidelity token missing: {token!r}")
                    failed += 1

            # F6: PPTX fidelity
            pptx_copy = fixture_tmp / "pptx"
            pptx_copy.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fixtures_dir / "pptx_complex" / "complex_source.pptx", pptx_copy / "complex_source.pptx")
            pptx_out = fixture_tmp / "pptx_out.md"
            _run([python, str(scripts_dir / "source_to_md" / "ppt_to_md.py"), str(pptx_copy / "complex_source.pptx"),
                  "-o", str(pptx_out)], "pptx fidelity convert -> 0")
            pptx_md = pptx_out.read_text(encoding="utf-8", errors="replace") if pptx_out.exists() else ""
            for token in ("核心指标", "1,234", "12.4%", "19,912", "Speaker Notes",
                          "本页备注", "①②③", "±2℃", "¥7.12"):
                if token in pptx_md:
                    print(f"  [PASS] pptx fidelity token {token!r}")
                    passed += 1
                else:
                    print(f"  [FAIL] pptx fidelity token missing: {token!r}")
                    failed += 1
            if (fixture_tmp / "pptx_out_files" / "image1.png").is_file():
                print("  [PASS] pptx fidelity media image1.png extracted")
                passed += 1
            else:
                print("  [FAIL] pptx fidelity media image1.png missing")
                failed += 1

            # Beautify 1:1: page split preserved verbatim through ppt_to_md
            beautify_copy = fixture_tmp / "beautify"
            beautify_copy.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fixtures_dir / "beautify_1to1" / "sources" / "beautify_source.pptx",
                         beautify_copy / "beautify_source.pptx")
            beautify_out = fixture_tmp / "beautify_out.md"
            _run([python, str(scripts_dir / "source_to_md" / "ppt_to_md.py"), str(beautify_copy / "beautify_source.pptx"),
                  "-o", str(beautify_out)], "beautify 1:1 convert -> 0")
            beautify_md = beautify_out.read_text(encoding="utf-8", errors="replace") if beautify_out.exists() else ""
            for token in ("Total slides: 3", "## Slide 1", "第一章 背景与动机",
                          "## Slide 2", "第二章 方案设计", "## Slide 3", "第三章 验证与结论"):
                if token in beautify_md:
                    print(f"  [PASS] beautify 1:1 token {token!r}")
                    passed += 1
                else:
                    print(f"  [FAIL] beautify 1:1 token missing: {token!r}")
                    failed += 1

            # F3: structured lock + checker (on a tmp copy)
            structured_copy = fixture_tmp / "structured"
            shutil.copytree(fixtures_dir / "structured", structured_copy)
            _run([python, str(scripts_dir / "spec_lock_validate.py"), str(structured_copy)],
                 "structured spec_lock_validate -> 0")
            _run([python, str(scripts_dir / "svg_quality_checker.py"), str(structured_copy)],
                 "structured svg_quality_checker -> 0")

        # --- Test 11: run_summary.py aggregation contract ---
        print("\n  [11] run_summary.py aggregation contract")
        calib_dir = fixtures_dir / "trace_calibration"
        if not calib_dir.is_dir():
            print("  [SKIP] trace_calibration fixture not found")
            skipped += 1
        else:
            calib_copy = fixture_tmp / "trace_calibration"
            shutil.copytree(calib_dir, calib_copy)
            summary_out = fixture_tmp / "run_summary_a.json"
            _run([python, str(scripts_dir / "run_summary.py"), str(calib_copy), "-o", str(summary_out)],
                 "run_summary on calibration trace -> 0")
            try:
                summary = json.loads(summary_out.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                summary = None
            if not isinstance(summary, dict):
                print("  [FAIL] run_summary output not valid JSON")
                failed += 1
            else:
                checks = [
                    ("schema v1", summary.get("schema") == "ppt-master.run-summary.v1"),
                    ("route generate", summary.get("route") == "generate"),
                    ("slide_count 3", summary.get("slide_count") == 3),
                    ("events_total 11", summary.get("events_total") == 11),
                    ("stage strategist 2000ms", summary.get("stages", {}).get("strategist", {}).get("duration_ms") == 2000),
                    ("stage images null (not measured)", summary.get("stages", {}).get("images", {}).get("duration_ms") is None),
                    ("stage noop 0 preserved (real zero)", summary.get("stages", {}).get("noop", {}).get("duration_ms") == 0),
                    ("gate svg_quality PASS", summary.get("gates", {}).get("svg_quality") == "PASS"),
                    ("error by_code IMG_E001", summary.get("errors", {}).get("by_code") == {"IMG_E001": 1}),
                    ("retry_count 1", summary.get("retry_count") == 1),
                    ("image_attempts 2", summary.get("image_attempts") == 2),
                    ("annotations live_preview 3", summary.get("annotations", {}).get("live_preview_count") == 3),
                    ("annotations reexport 1", summary.get("annotations", {}).get("pptx_reexport_count") == 1),
                    ("annotations svg_regen null", summary.get("annotations", {}).get("svg_regeneration_count") is None),
                    ("final e2e PASS", summary.get("final_results", {}).get("e2e") == "PASS"),
                    ("final visual null", summary.get("final_results", {}).get("visual") is None),
                ]
                for label, ok in checks:
                    if ok:
                        print(f"  [PASS] run_summary {label}")
                        passed += 1
                    else:
                        print(f"  [FAIL] run_summary {label}")
                        failed += 1
                # determinism: second aggregation must be identical
                summary_out2 = fixture_tmp / "run_summary_b.json"
                _run([python, str(scripts_dir / "run_summary.py"), str(calib_copy), "-o", str(summary_out2)],
                     "run_summary second aggregation -> 0")
                try:
                    summary2 = json.loads(summary_out2.read_text(encoding="utf-8"))
                    if summary2 == summary:
                        print("  [PASS] run_summary deterministic (identical JSON)")
                        passed += 1
                    else:
                        print("  [FAIL] run_summary non-deterministic")
                        failed += 1
                except (OSError, json.JSONDecodeError):
                    print("  [FAIL] run_summary second output unreadable")
                    failed += 1
            # sensitive fail-closed: forbidden key -> exit 1, no file written
            sensitive_proj = fixture_tmp / "trace_sensitive"
            sensitive_proj.mkdir(parents=True, exist_ok=True)
            (sensitive_proj / "trace.jsonl").write_text(
                '{"schema_version": 1, "ts": "2026-08-04T10:00:00+00:00", '
                '"type": "gate_result", "prompt": "secret body", "detail": "x"}\n',
                encoding="utf-8")
            sensitive_out = fixture_tmp / "sensitive_out.json"
            _run([python, str(scripts_dir / "run_summary.py"), str(sensitive_proj), "-o", str(sensitive_out)],
                 "run_summary sensitive key -> non-zero", expect_exit=1)
            if sensitive_out.exists():
                print("  [FAIL] run_summary wrote file on sensitive input")
                failed += 1
            else:
                print("  [PASS] run_summary no file written on sensitive input")
                passed += 1
            # bad project path -> exit 2
            _run([python, str(scripts_dir / "run_summary.py"), str(fixture_tmp / "no_such_project")],
                 "run_summary bad project path -> 2", expect_exit=2)

        # --- Test 12: interruption-recovery diagnosis (project_manager diagnose) ---
        print("\n  [12] interruption-recovery diagnosis")
        partial_dir = fixtures_dir / "partial"
        if not partial_dir.is_dir():
            print("  [SKIP] partial fixtures not found")
            skipped += 1
        else:
            pm_script = scripts_dir / "project_manager.py"
            scenarios = {
                "only_sources": ("2-sources", ["NO_SOURCES"], "NO_SOURCES", "blocked"),
                "confirmation_pending": ("4-design-spec", ["CONFIRMATION_PENDING"], "CONFIRMATION_PENDING", "blocked"),
                "confirmation_stale": ("4-design-spec", ["CONFIRMATION_STALE"], "CONFIRMATION_STALE", "blocked"),
                "confirmation_malformed": ("4-design-spec", ["CONFIRMATION_MALFORMED"], "CONFIRMATION_MALFORMED", "blocked"),
                "spec_lock_no_digest": ("5-spec-lock", ["SPEC_LOCK_DIGEST_MISMATCH"], "SPEC_LOCK_DIGEST_MISMATCH", "blocked"),
                "spec_lock_mode_conflict": ("5-spec-lock", ["SPEC_LOCK_MODE_CONFLICT"], "SPEC_LOCK_MODE_CONFLICT", "blocked"),
                "images_partial": ("6-images", ["IMAGES_PARTIAL"], "IMAGES_PARTIAL", "blocked"),
                "image_manifest_failed": ("6-images", ["IMAGE_MANIFEST_FAILED"], "IMAGE_MANIFEST_FAILED", "blocked"),
                "svg_count_mismatch": ("7a-svg-gen", ["SVG_COUNT_MISMATCH"], "SVG_COUNT_MISMATCH", "blocked"),
                "svg_naming_conflict": ("7a-svg-gen", ["SVG_NAMING_CONFLICT"], "SVG_NAMING_CONFLICT", "blocked"),
                "quality_failed": ("7b-postprocess", ["SVG_QUALITY_GATE_FAILED"], "SVG_QUALITY_GATE_FAILED", "blocked"),
                "svg_no_export": ("7c-export", [], "EXPORT_PENDING", "partial"),
                "exported": ("8-export", [], "VALIDATE_EXPORT", "ok"),
                "exported_failed": ("8-export", ["E2E_FAILED", "DELIVERY_FAILED"], "E2E_FAILED", "blocked"),
                "resume_phase_b": ("5-spec-lock", [], "RESUME_PHASE_B", "partial"),
            }
            for name, (exp_step, exp_codes, exp_next, exp_status) in scenarios.items():
                r = subprocess.run([python, str(pm_script), "diagnose", str(partial_dir / name)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
                if r.returncode != 0:
                    print(f"  [FAIL] diagnose {name} — rc={r.returncode}")
                    failed += 1
                    continue
                try:
                    d = json.loads(r.stdout)
                except json.JSONDecodeError:
                    print(f"  [FAIL] diagnose {name} — stdout not clean JSON")
                    failed += 1
                    continue
                codes = [b["code"] for b in d.get("blockers", [])]
                if (d.get("step") == exp_step and codes == exp_codes
                        and d.get("next_action", {}).get("code") == exp_next
                        and d.get("status") == exp_status):
                    print(f"  [PASS] diagnose {name} (step={exp_step}, blockers={exp_codes or 'none'})")
                    passed += 1
                else:
                    print(f"  [FAIL] diagnose {name} — got step={d.get('step')} "
                          f"codes={codes} next={d.get('next_action', {}).get('code')} "
                          f"status={d.get('status')}")
                    failed += 1
            # determinism (minus checked_at) on a fixed fixture
            probe_target = partial_dir / "svg_count_mismatch"

            def _run_diag() -> dict:
                r = subprocess.run([python, str(pm_script), "diagnose", str(probe_target)],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=30)
                d = json.loads(r.stdout)
                d.pop("checked_at", None)
                return d

            try:
                if _run_diag() == _run_diag():
                    print("  [PASS] diagnose deterministic (identical minus checked_at)")
                    passed += 1
                else:
                    print("  [FAIL] diagnose non-deterministic")
                    failed += 1
            except (json.JSONDecodeError, OSError):
                print("  [FAIL] diagnose determinism probe unreadable")
                failed += 1
            # read-only: no writes to the fixture tree during diagnosis
            before = {
                rel: (p.read_bytes() if p.is_file() else None)
                for rel, p in ((str(f.relative_to(partial_dir)), f)
                               for f in partial_dir.rglob("*") if f.is_file())
            }
            for name in scenarios:
                subprocess.run([python, str(pm_script), "diagnose", str(partial_dir / name)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            after = {
                rel: (p.read_bytes() if p.is_file() else None)
                for rel, p in ((str(f.relative_to(partial_dir)), f)
                               for f in partial_dir.rglob("*") if f.is_file())
            }
            if before == after:
                print("  [PASS] diagnose read-only (no fixture writes)")
                passed += 1
            else:
                print("  [FAIL] diagnose wrote into the fixture tree")
                failed += 1
            _run([python, str(pm_script), "diagnose", str(fixture_tmp / "no_such_project")],
                 "diagnose bad project path -> 2", expect_exit=2)

        # --- Test 13: read-only project space report ---
        print("\n  [13] space_report.py classification + archive plan")
        space_dir = fixtures_dir / "space_report"
        if not space_dir.is_dir():
            print("  [SKIP] space_report fixture not found")
            skipped += 1
        else:
            space_copy = fixture_tmp / "space_report"
            shutil.copytree(space_dir, space_copy)
            report_out = fixture_tmp / "space.json"
            _run([python, str(scripts_dir / "space_report.py"), str(space_copy),
                  "--json-out", str(report_out)], "space_report -> 0")
            try:
                report = json.loads(report_out.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                report = None
            if not isinstance(report, dict):
                print("  [FAIL] space_report output not valid JSON")
                failed += 1
            else:
                checks = [
                    ("schema v1", report.get("schema") == "ppt-master.space-report.v1"),
                    ("summary 2 projects", report.get("summary", {}).get("projects") == 2),
                    ("summary bytes 880", report.get("summary", {}).get("bytes") == 880),
                    ("summary renewable 350", report.get("summary", {}).get("renewable_bytes") == 350),
                    ("proj_a renewable 290", next((p["renewable_bytes"] for p in report.get("projects", []) if p["project"] == "proj_a"), None) == 290),
                    ("proj_a non-renewable 430", next((p["by_class"].get("non-renewable", {}).get("bytes") for p in report.get("projects", []) if p["project"] == "proj_a"), None) == 430),
                    ("proj_b renewable 60", next((p["renewable_bytes"] for p in report.get("projects", []) if p["project"] == "proj_b"), None) == 60),
                    ("top order proj_a first", report.get("top_projects", [{}])[0].get("project") == "proj_a"),
                ]
                for label, ok in checks:
                    if ok:
                        print(f"  [PASS] space_report {label}")
                        passed += 1
                    else:
                        print(f"  [FAIL] space_report {label}")
                        failed += 1
            plan_out = fixture_tmp / "space_plan.json"
            _run([python, str(scripts_dir / "space_report.py"), str(space_copy),
                  "--archive-plan", str(plan_out)], "space_report archive-plan -> 0")
            try:
                plan = json.loads(plan_out.read_text(encoding="utf-8"))
                items = {
                    item["path"]: item["bytes"]
                    for proj in plan.get("projects", [])
                    for item in proj.get("items", [])
                }
                if items == {"trace.jsonl": 40, "backup/old.bin": 200, "quality/harness.json": 50,
                             "validation/report.json": 60}:
                    print("  [PASS] space_report archive plan paths+sizes exact")
                    passed += 1
                else:
                    print(f"  [FAIL] space_report archive plan mismatch: {items}")
                    failed += 1
            except (OSError, json.JSONDecodeError):
                print("  [FAIL] space_report archive plan unreadable")
                failed += 1
            _run([python, str(scripts_dir / "space_report.py"), str(fixture_tmp / "no_such_root")],
                 "space_report bad root -> 2", expect_exit=2)

        # --- Test 14: trace wiring — image_gen manifest attempt events ---
        print("\n  [14] image_gen manifest attempt trace wiring")
        probe = '''import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, r"{SCRIPTS}")
import image_gen

class StubBackend:
    def generate(self, **kw):
        return "fake.png"

tmp = Path(tempfile.mkdtemp())
proj = tmp / "proj"
(proj / "images").mkdir(parents=True)
mp = proj / "images" / "image_prompts.json"
manifest = {
    "items": [{"filename": "cover_01.png", "prompt": "synthetic prompt body", "aspect_ratio": "1:1", "status": "Pending"}]
}
image_gen._run_manifest(
    manifest, str(mp), StubBackend(),
    initial_concurrency=1, image_size="1K", output_dir=str(proj / "images"),
    model="stub", backend_name="stub", fallback_enabled=False,
)
trace = proj / "trace.jsonl"
assert trace.is_file(), "trace.jsonl missing"
events = [json.loads(l) for l in trace.read_text(encoding="utf-8").splitlines() if l.strip()]
assert events, "no trace events emitted"
ev = events[0]
assert ev["operation"].startswith("image_gen:"), ev.get("operation")
assert ev["status"] in ("PASS", "FAIL"), ev.get("status")
dump = json.dumps(ev)
assert "prompt" not in dump and "synthetic prompt body" not in dump, "prompt body leaked"
print("image_gen trace OK:", ev["operation"], ev["status"])
'''.replace("{SCRIPTS}", str(scripts_dir))
        try:
            r = subprocess.run([python, "-c", probe], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
            if r.returncode == 0:
                print(f"  [PASS] image_gen attempt trace event (no prompt leak): {r.stdout.strip()[-60:]}")
                passed += 1
            else:
                print(f"  [FAIL] image_gen trace wiring — {(r.stdout + r.stderr).strip()[:200]}")
                failed += 1
        except subprocess.TimeoutExpired:
            print("  [FAIL] image_gen trace wiring probe timed out (60s)")
            failed += 1

        # --- Test 15: OfficeCLI pinned runtime + bridge contract ---
        print("\n  [15] OfficeCLI pinned runtime + bridge contract")
        installer = scripts_dir / "install_officecli.py"
        if not installer.is_file():
            print("  [SKIP] install_officecli.py not present")
            skipped += 1
        elif not _officecli_binary_installed(installer, python):
            print("  [SKIP] OfficeCLI binary not installed — run "
                  "python skills/ppt-master/scripts/install_officecli.py install")
            skipped += 1
        else:
                probe = r'''
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, r"{SCRIPTS}")
import install_officecli as inst
import officecli_bridge as br

# Installer public contract: check --json / path --json (offline)
out = subprocess.run(
    [sys.executable, r"{SCRIPTS}/install_officecli.py", "check", "--json"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
d = json.loads(out.stdout)
assert out.returncode == 0 and d.get("success") is True, out.stdout[:200]
assert d.get("status") == "ready" and d.get("version") == "1.0.143", d
print("installer check --json ready OK")

# Installer error paths rc != 0
for argv in (["bogus"], ["check", "--nope"]):
    r = subprocess.run([sys.executable, r"{SCRIPTS}/install_officecli.py"] + argv,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode != 0, f"installer {argv} rc=0"
print("installer error paths rc!=0 OK")

# Fail closed: checksum + version mismatch via mutated lock copy (no install change)
lock = inst._load_lock()
plat = inst._detect_platform(lock)
bad_sha = json.loads(json.dumps(lock))
bad_sha["platforms"] = {k: dict(v) for k, v in lock["platforms"].items()}
bad_sha["platforms"][plat]["sha256"] = "0" * 64
assert inst._check(bad_sha, plat, True) == 1, "checksum negative did not fail closed"
bad_ver = json.loads(json.dumps(lock))
bad_ver["version"] = "9.9.9"
real = inst._binary_path(lock, plat)
orig = inst._binary_path
inst._binary_path = lambda l, p: real
try:
    assert inst._check(bad_ver, plat, True) == 1, "version negative did not fail closed"
finally:
    inst._binary_path = orig
print("fail-closed checksum/version OK")

# Bridge: probe, envelope, error classification, validate
rt = br.probe_officecli()
assert rt.status == "ready" and rt.actual_version == "1.0.143", rt
r = br.run_officecli(["frobnicate", "--bogus"])
assert not r.success and r.error_code == "OFFICECLI_COMMAND_FAILED", r.error_code
r = br.run_officecli(["--version"])
assert r.success, r.error_code
r = br.validate_office_file(
    Path(r"{SCRIPTS}") / ".." / "fixtures" / "beautify_1to1" / "sources" / "beautify_source.pptx")
assert r.success, r.message
print("bridge probe/validate OK")
'''.replace("{SCRIPTS}", str(scripts_dir))
                try:
                    r = subprocess.run([python, "-c", probe], capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=120)
                    if r.returncode == 0:
                        print(f"  [PASS] OfficeCLI runtime + bridge contract: {r.stdout.strip()[-60:]}")
                        passed += 1
                    else:
                        print(f"  [FAIL] OfficeCLI runtime + bridge contract — {(r.stdout + r.stderr).strip()[:300]}")
                        failed += 1
                except subprocess.TimeoutExpired:
                    print("  [FAIL] OfficeCLI runtime + bridge contract probe timed out (120s)")
                    failed += 1

        # --- Test 16: native revision fixture lifecycle ---
        print("\n  [16] native revision fixture lifecycle (init/inspect/check-plan/apply/rollback)")
        if not installer.is_file() or not _officecli_binary_installed(installer, python):
            print("  [SKIP] OfficeCLI binary not installed — run "
                  "python skills/ppt-master/scripts/install_officecli.py install")
            skipped += 1
        else:
            probe = r'''
import sys, json, subprocess, hashlib, glob, shutil
from pathlib import Path
SCRIPTS = Path(r"{SCRIPTS}")
FIX = Path(r"{FIXTURES}")
TMP = Path(r"{TMP}")

def run(*args, timeout=300):
    r = subprocess.run([sys.executable, str(SCRIPTS / "native_revision_pptx.py")] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

src = FIX / "native_revision_source.pptx"
proj_dir = TMP / "nr16"
if proj_dir.exists():
    shutil.rmtree(proj_dir)
proj_dir.mkdir(parents=True)

rc, out = run("init", str(src), "--name", "nr16", "--project-dir", str(proj_dir))
assert rc == 0, out
proj = proj_dir / "_revision_nr16"
assert proj.is_dir(), "project not created under --project-dir"

rc, out = run("inspect", str(proj))
assert rc == 0 and "Slides: 4" in out, out
assert sha(proj / "sources" / src.name) == sha(src), "source copy mismatch"
src_hash = sha(proj / "sources" / src.name)

plan = {
    "schema": "ppt_master.native_revision_plan.v1",
    "status": "draft",
    "officecli_version": "1.0.143",
    "source": {"path": str(proj / "sources" / src.name), "sha256": src_hash,
               "slide_count": 4, "origin": "standalone"},
    "operations": [
        {"id": "R001", "command": "set", "path": "/slide[1]/shape[@id=2]",
         "props": {"text": "Smoke 修订"},
         "expect": {"type": "textbox", "text": "Page 1 - Text Shapes"},
         "reason": "smoke: 标题修订"}
    ],
    "invariants": {"preserve_slide_count": True, "preserve_masters": True,
                   "preserve_unaddressed_objects": True, "allow_svg_divergence": True},
    "confirmation": {"confirmed_at": None, "confirmed_by": None},
}
plan_path = proj / "analysis" / "native_revision_plan.json"
plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
rc, out = run("check-plan", str(proj))
assert rc == 0, out

# Negative: missing target fails closed
bad = json.loads(json.dumps(plan))
bad["operations"] = [dict(plan["operations"][0], path="/slide[1]/shape[@id=99999]")]
plan_path.write_text(json.dumps(bad, indent=2), encoding="utf-8")
rc, out = run("check-plan", str(proj))
assert rc != 0, "missing target must fail check-plan"

# Confirmed apply success
plan["status"] = "confirmed"
plan["confirmation"] = {"confirmed_at": "2026-08-05T00:00:00Z", "confirmed_by": "smoke"}
plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
exports_before = set(glob.glob(str(proj / "exports" / "*.pptx")))
rc, out = run("apply", str(proj))
assert rc == 0, out
new_exports = set(glob.glob(str(proj / "exports" / "*.pptx"))) - exports_before
assert len(new_exports) == 1, new_exports
assert sha(proj / "sources" / src.name) == src_hash, "source changed during apply!"
res = json.loads((proj / "analysis" / "native_revision_result.json").read_text(encoding="utf-8"))
assert res["success"] is True
assert res["visual_render"] in ("ok", "not_available"), res

# Atomic rollback: add a failing op (invalid prop) -> whole batch rolls back
plan2 = json.loads(json.dumps(plan))
plan2["operations"].append(
    {"id": "R002", "command": "set", "path": "/slide[2]/table[@id=3]",
     "props": {"text": "x", "height": "not-a-size"},
     "expect": {"type": "table"}, "reason": "smoke: 注入失败"})
plan_path.write_text(json.dumps(plan2, indent=2), encoding="utf-8")
exports_before = set(glob.glob(str(proj / "exports" / "*.pptx")))
rc, out = run("apply", str(proj))
assert rc != 0, "rollback apply must fail"
assert set(glob.glob(str(proj / "exports" / "*.pptx"))) == exports_before, "export published on failure!"
assert sha(proj / "sources" / src.name) == src_hash
res = json.loads((proj / "analysis" / "native_revision_result.json").read_text(encoding="utf-8"))
assert res["success"] is False and res["candidate_rolled_back"] is True, res
print("native revision lifecycle OK")
'''.replace("{SCRIPTS}", str(scripts_dir)).replace(
    "{FIXTURES}", str(scripts_dir.parent / "fixtures" / "officecli")).replace(
    "{TMP}", str(tmp_path))
            try:
                r = subprocess.run([python, "-c", probe], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300)
                if r.returncode == 0:
                    print(f"  [PASS] native revision lifecycle: {r.stdout.strip()[-60:]}")
                    passed += 1
                else:
                    print(f"  [FAIL] native revision lifecycle — {(r.stdout + r.stderr).strip()[:400]}")
                    failed += 1
            except subprocess.TimeoutExpired:
                print("  [FAIL] native revision lifecycle probe timed out (300s)")
                failed += 1

        # --- Test 17: office source inspect + copy-only repair lifecycle ---
        print("\n  [17] office source inspect + repair fixture lifecycle")
        if not installer.is_file() or not _officecli_binary_installed(installer, python):
            print("  [SKIP] OfficeCLI binary not installed — run "
                  "python skills/ppt-master/scripts/install_officecli.py install")
            skipped += 1
        else:
            probe = r'''
import sys, json, subprocess, hashlib, shutil
from pathlib import Path
SCRIPTS = Path(r"{SCRIPTS}")
FIX = Path(r"{FIXTURES}")
TMP = Path(r"{TMP}")

def run_script(name, *args, timeout=180):
    r = subprocess.run([sys.executable, str(SCRIPTS / name)] + list(args),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

proj = TMP / "os17"
if proj.exists():
    shutil.rmtree(proj)
(proj / "sources").mkdir(parents=True)
(proj / "analysis").mkdir()
(proj / "project.json").write_text(json.dumps({"name": "os17", "kind": "smoke"}), encoding="utf-8")
shutil.copy2(FIX / "docx_source.docx", proj / "sources" / "docx_source.docx")
shutil.copy2(FIX / "xlsx_source.xlsx", proj / "sources" / "xlsx_source.xlsx")
docx_hash = sha(proj / "sources" / "docx_source.docx")

# Inspection manifest with reconciled counts
rc, out = run_script("office_source_inspect.py", str(proj))
assert rc == 0, out
m = json.loads((proj / "analysis" / "office_sources.json").read_text(encoding="utf-8"))
assert m["schema"] == "ppt_master.office_sources.v1"
by_fmt = {s["format"]: s for s in m["sources"]}
assert by_fmt["docx"]["summary"]["tables"] == 2, by_fmt["docx"]["summary"]
assert by_fmt["docx"]["summary"]["images"] == 1
assert by_fmt["xlsx"]["summary"]["sheets"] == 2
assert by_fmt["xlsx"]["summary"]["formulas"] == 7
assert sha(proj / "sources" / "docx_source.docx") == docx_hash, "inspect mutated source!"

# Repair: unconfirmed rejected, confirmed apply publishes copy + markdown
rc, out = run_script("office_source_repair.py", "scaffold", str(proj), "--source", "sources/docx_source.docx")
assert rc == 0, out
plan_path = proj / "analysis" / "source_repair_plan.json"
plan = json.loads(plan_path.read_text(encoding="utf-8"))
plan["operations"] = [
    {"id": "P001", "command": "set", "path": "/body/p[1]",
     "props": {"text": "Smoke 修复"},
     "expect": {"type": "paragraph", "text": "OfficeCLI DOCX inspection fixture"},
     "reason": "smoke: 修复"}
]
plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
rc, out = run_script("office_source_repair.py", "check-plan", str(proj))
assert rc == 0, out
rc, out = run_script("office_source_repair.py", "apply", str(proj))
assert rc != 0, "unconfirmed apply must fail"
plan["status"] = "confirmed"
plan["confirmation"] = {"confirmed_at": "2026-08-05T00:00:00Z", "confirmed_by": "smoke"}
plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
rc, out = run_script("office_source_repair.py", "apply", str(proj))
assert rc == 0, out
repaired = list((proj / "sources" / "repaired").glob("docx_source_repaired_*.docx"))
assert len(repaired) == 1, repaired
assert sha(proj / "sources" / "docx_source.docx") == docx_hash, "repair mutated original!"
res = json.loads((proj / "analysis" / "source_repair_result.json").read_text(encoding="utf-8"))
assert res["operation_digest"] and res["converter"]["markdown_sha256"], res
print("source inspect + repair lifecycle OK")
'''.replace("{SCRIPTS}", str(scripts_dir)).replace(
    "{FIXTURES}", str(scripts_dir.parent / "fixtures" / "officecli")).replace(
    "{TMP}", str(tmp_path))
            try:
                r = subprocess.run([python, "-c", probe], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300)
                if r.returncode == 0:
                    print(f"  [PASS] source inspect + repair lifecycle: {r.stdout.strip()[-60:]}")
                    passed += 1
                else:
                    print(f"  [FAIL] source inspect + repair lifecycle — {(r.stdout + r.stderr).strip()[:400]}")
                    failed += 1
            except subprocess.TimeoutExpired:
                print("  [FAIL] source inspect + repair lifecycle probe timed out (300s)")
                failed += 1

    finally:
        # Cleanup temp directory
        import shutil
        smoke_dir = scripts_dir.parent / "_smoke_test"
        if smoke_dir.is_dir():
            shutil.rmtree(smoke_dir, ignore_errors=True)

    return passed, failed, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke check all PPT Master scripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--scripts-dir",
        help="Path to scripts/ directory (default: auto-detect relative to this file)",
    )
    parser.add_argument(
        "--skip-help",
        action="store_true",
        help="Only check imports, skip --help invocations",
    )
    parser.add_argument(
        "--dashboard-e2e",
        action="store_true",
        help="Run opt-in Dashboard daemon/API/shutdown smoke check",
    )
    parser.add_argument(
        "--governance",
        action="store_true",
        help="Run governance drift check (platform config consistency, routing, docs/rules)",
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration smoke tests for core scripts (config, spec_lock_digest, spec_lock_validate, etc.)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    scripts_dir = Path(args.scripts_dir) if args.scripts_dir else Path(__file__).resolve().parent
    if not scripts_dir.is_dir():
        print(f"Error: scripts directory not found: {scripts_dir}", file=sys.stderr)
        return 2

    scripts = find_scripts(scripts_dir)
    if not scripts:
        print(f"Error: no .py files found in {scripts_dir}", file=sys.stderr)
        return 2

    python = sys.executable
    passed = 0
    failed = 0
    skipped = 0

    print(f"Smoke check: {len(scripts)} scripts in {scripts_dir.name}/\n")

    # Phase 1: Import check
    print("Import check")
    print("-" * 50)
    for script in scripts:
        rel = script.relative_to(scripts_dir)
        if str(rel) in _SKIP_IMPORT:
            print(f"  [SKIP] {rel}")
            skipped += 1
            continue
        if rel.name in _WRAP_ONLY:
            print(f"  [SKIP] {rel} (thin wrapper, validated via --help)")
            skipped += 1
            continue
        ok, msg = check_import(script, scripts_dir)
        if ok:
            print(f"  [PASS] {rel} — {msg}")
            passed += 1
        else:
            print(f"  [FAIL] {rel} — {msg}")
            failed += 1

    # Phase 2: --help check
    if not args.skip_help:
        print(f"\n--help check")
        print("-" * 50)
        for script in scripts:
            rel = script.relative_to(scripts_dir)
            if str(rel) in _SKIP_HELP:
                print(f"  [SKIP] {rel} (interactive/server)")
                skipped += 1
                continue
            ok, msg = check_help(script, python)
            if ok:
                print(f"  [PASS] {rel}")
                passed += 1
            else:
                print(f"  [FAIL] {rel} — {msg}")
                failed += 1

    if args.dashboard_e2e:
        print("\nDashboard e2e")
        print("-" * 50)
        ok, msg = dashboard_e2e_smoke(scripts_dir)
        if ok:
            print(f"  [PASS] {msg}")
            passed += 1
        else:
            print(f"  [FAIL] {msg}")
            failed += 1

    if args.governance:
        print("\nGovernance drift check")
        print("-" * 50)
        gov_script = scripts_dir / "governance_drift_check.py"
        if not gov_script.is_file():
            print(f"  [SKIP] governance_drift_check.py not found")
            skipped += 1
        else:
            try:
                # governance_drift_check.py expects the repo root (parent of skills/)
                repo_root = scripts_dir.parent.parent.parent
                result = subprocess.run(
                    [python, str(gov_script), "--root", str(repo_root)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=30,
                )
                if result.returncode == 0:
                    print(f"  [PASS] No governance drift detected")
                    if result.stdout.strip():
                        print(f"         {result.stdout.strip()[:200]}")
                    passed += 1
                else:
                    print(f"  [FAIL] Governance drift detected (exit {result.returncode})")
                    if result.stdout.strip():
                        for line in result.stdout.strip().splitlines()[:10]:
                            print(f"         {line}")
                    if result.stderr.strip():
                        for line in result.stderr.strip().splitlines()[:5]:
                            print(f"         {line}")
                    failed += 1
            except subprocess.TimeoutExpired:
                print(f"  [FAIL] Governance check timed out (30s)")
                failed += 1
            except Exception as e:
                print(f"  [FAIL] {type(e).__name__}: {e}")
                failed += 1

    if args.integration:
        print("\nIntegration smoke tests")
        print("-" * 50)
        ip, if_, is_ = integration_smoke(scripts_dir)
        passed += ip
        failed += if_
        skipped += is_

    total = passed + failed + skipped
    print(f"\n{'=' * 50}")
    print(f"Result: {passed} passed, {failed} failed, {skipped} skipped / {total} checks")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    configure_utf8_stdio()
    raise SystemExit(main())
