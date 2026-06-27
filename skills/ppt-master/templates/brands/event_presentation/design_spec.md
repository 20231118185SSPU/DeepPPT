---
brand_id: event_presentation
kind: brand
summary: Event / launch presentation brand — dark, dramatic, product-focused. Inspired by Apple keynote style. Optimized for product launches, press events, and stage presentations.
primary_color: "#58A6FF"
---

# Event Presentation Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Event Presentation |
| Use Cases | Product launches, press events, keynotes, stage presentations, demo days |
| Tone | Dramatic, confident, minimal, product-focused, high-contrast |
| Density | Sparse — generous whitespace, few words per slide |
| Reference | Apple WWDC / Google I/O keynote style |

## II. Color Scheme

| Role | HEX | Notes |
|---|---|---|
| primary | `#58A6FF` | Cool blue — highlights, links, emphasis |
| secondary | `#388BFD` | Deeper blue — active states, buttons |
| accent (warm) | `#F78166` | Warm orange — callouts, warnings, energy |
| accent (highlight) | `#D29922` | Gold — achievements, key metrics |
| text (primary) | `#E6EDF3` | Light grey on dark — main body text |
| text (secondary) | `#8B949E` | Muted grey — captions, metadata |
| bg (primary) | `#0D1117` | Near-black — main background |
| bg (secondary) | `#161B22` | Dark grey — card backgrounds, panels |
| bg (tertiary) | `#1C1C2E` | Deep navy — accent sections |

## III. Typography

| Role | Family | Weight | Size guidance |
|---|---|---|---|
| hero title | `"SF Pro Display", "Microsoft YaHei", sans-serif` | 700 | 64–96px (cover), 48–72px (section) |
| section title | `"SF Pro Display", "Microsoft YaHei", sans-serif` | 600 | 40–56px |
| body | `"SF Pro Text", "Microsoft YaHei", sans-serif` | 400 | 20–24px |
| caption | `"SF Pro Text", "Microsoft YaHei", sans-serif` | 300 | 14–16px |
| data / KPI | `"SF Mono", "Cascadia Code", monospace` | 500 | 36–72px (hero numbers) |

## IV. Layout Principles

1. **One idea per slide** — maximum 80 Chinese characters or 60 words
2. **Full-bleed images** for hero/product pages — text overlaid on semi-transparent scrim (opacity ≥ 0.85)
3. **Dark background always** — never switch to light theme mid-deck
4. **Center-heavy composition** — titles and hero numbers centered; body text can be left-aligned within cards
5. **No bullet lists on key pages** — use single statements, numbers, or short phrases
6. **Generous margins** — safe area 80px from edges (stricter than default 50px)
7. **Product images are king** — when showing a product, it should occupy ≥ 60% of the canvas

## V. Animation Style

| Page type | Transition | Object animation | Duration |
|-----------|-----------|-----------------|----------|
| Cover | `fade` | `fade` cascade | 0.5–0.6s |
| Product reveal | `fade` | `zoom` hero + `fade` text | 0.5–0.7s |
| Data / KPI | `fade` | `appear` numbers | 0.3–0.4s |
| Comparison | `fade` | `fly` panels from sides | 0.4s |
| Section transition | `fade` | `fade` | 0.4–0.5s |
| Ending / CTA | `fade` | `fade` slow | 0.6s |

**Forbidden**: `wipe`, `blinds`, `checkerboard`, `random_bars`, `swivel`, `wheel` — these break the clean, professional keynote feel.

## VI. Image Strategy

- **Product images**: AI-generated high-quality renders or web-sourced official product photos. Full-bleed on hero pages.
- **Background images**: Abstract dark textures, gradients, or subtle patterns. Never busy or colorful.
- **Data visualizations**: Minimal, clean charts with the blue/gold accent palette. No 3D charts.
- **Icons**: Line-style icons (Phosphor, Lucide). White or `#8B949E` on dark backgrounds.
