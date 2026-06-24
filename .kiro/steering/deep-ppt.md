# DeepPPT — Kiro Steering Rules

## Project

DeepPPT: AI-driven presentation generation system.

## Workflow Authority

Read `skills/ppt-master/SKILL.md` before any PPT task.

## Core Rules

1. Serial pipeline. ⛔ BLOCKING = hard stop for user confirmation.
2. SVG pages hand-written one at a time. No batch scripts.
3. Re-read `spec_lock.md` per page. No memory-based values.
4. Use `analyze_images.py` for image info. Never open image files directly.
5. Topic-only → run `workflows/deep-research.md` first.

## Config

`.env.example` → `.env`. IMAGE_BACKEND + API key required.
