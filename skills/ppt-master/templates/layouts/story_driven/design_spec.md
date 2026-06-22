---
layout_id: story_driven
kind: layout
summary: Deep research presentations, narrative-driven content decks, knowledge exploration, educational storytelling, topic deep-dives.
canvas_format: ppt169
page_count: 6
page_types: [cover, toc, chapter, content, content_alt, ending]
---

# Story-Driven Deep Research Presentation Template (story_driven)

> A narrative-first layout for research-heavy presentations. Every content page centers on a single AI-generated visual that tells the story, supported by minimal text. Transition pages carry explicit narrative text to guide the audience through the argument. Each page type uses a distinct AI image — nothing is reused.

---

## I. Template Overview

| Property         | Description                                                                 |
| ---------------- | --------------------------------------------------------------------------- |
| **Template Name**| story_driven (Story-Driven Deep Research Presentation)                      |
| **Use Cases**    | Deep research reports, narrative-driven content decks, knowledge exploration, educational storytelling, topic deep-dives |
| **Design Tone**  | Immersive, narrative-driven, visually rich, refined, story-first            |
| **Theme Mode**   | Dark theme — but background treatment varies per page type (not fixed to full-bleed AI) |
| **Color Strategy** | Color scheme is NOT fixed — determined per project by Eight Confirmations. Neutral placeholder values in SVGs. |

---

## II. Canvas Specification

| Property           | Value                        |
| ------------------ | ---------------------------- |
| **Format**         | Standard 16:9                |
| **Dimensions**     | 1280 × 720 px               |
| **viewBox**        | `0 0 1280 720`              |
| **Page Margins**   | Left/right 60px, top 40px, bottom 40px |
| **Content Safe Area** | x: 60-1220, y: 40-680    |

---

## III. Page Structure

### General Layout Philosophy

This template follows a **story-first** principle: AI-generated visuals carry the narrative weight; text is sparse, purposeful, and never competes with imagery. Each content page has exactly one core visual and one takeaway.

**Image Independence Rule**: Every page type uses its own distinct AI image. Cover, TOC, transition, content, and ending images are NEVER the same. Each image is purpose-generated for its page's narrative role.

### Page Type Summary

| Page Type | Background | AI Image | Text Content |
|-----------|-----------|----------|-------------|
| **Cover** | AI background + dark overlay | `{{COVER_BG}}` — story's first frame | Title + tagline |
| **TOC** | AI background + dark overlay | `{{TOC_BG}}` — sets thematic tone | Section cards |
| **Chapter (Transition)** | AI background + dark overlay | `{{TRANSITION_BG}}` — per-section, context-dependent | **承上启下 narrative bridge**: prev summary + chapter title + hook |
| **Content** | Clean solid dark | `{{CONTENT_IMAGE}}` — page-specific visual | Title + image + caption + takeaway |
| **Content Alt** | Clean solid dark (variant tone) | `{{CONTENT_IMAGE}}` — page-specific visual | Same structure, different visual rhythm |
| **Ending** | AI background + dark overlay | `{{ENDING_BG}}` — bookend with cover, different image | Closing + tagline |

---

## IV. Page Types

### 1. Cover Page (01_cover.svg)

- Cover-specific AI background image (`{{COVER_BG}}`)
- Semi-transparent gradient overlay for text legibility
- Centered main title (`{{TITLE}}`) in white, bold, large
- Subtitle/tagline (`{{SUBTITLE}}`) below title
- Bottom info bar: author, organization, date
- Design intent: immediate visual immersion, the cover IS the story's first frame

### 2. Table of Contents (02_toc.svg)

- TOC-specific AI background image (`{{TOC_BG}}`) with dark overlay
- Section cards in vertical list with section numbers
- 4 primary items + 2 optional dashed-border placeholders
- Cards use semi-transparent dark backgrounds for legibility

### 3. Chapter Transition (02_chapter.svg)

- Transition-specific AI background image (`{{TRANSITION_BG}}`) with dark overlay
- **This page has explicit narrative text — it is NOT a silent visual break**
- Three-part narrative structure:
  - **承上 (Looking back)**: Previous section label + one-sentence summary
  - **本章 (This chapter)**: Large chapter number + title + core description
  - **启下 (Looking forward)**: Divider line + narrative hook / guiding question
- Each transition page's text is context-dependent, connecting the previous section's conclusion to the next section's premise
- `{{TRANSITION_BG}}` is thematically linked to the upcoming section's content

### 4. Content Page (03_content.svg)

- Clean solid dark background (`#1A1A2E`)
- Content-specific AI image (`{{CONTENT_IMAGE}}`) — distinct from all other page types
- Three-part vertical structure:
  - **Title zone** (y=40-98): section name + page title + decorative line
  - **Core visual zone** (y=115-540): large AI image + caption text below
  - **Takeaway zone** (y=600-660): divider line + bold takeaway

### 5. Content Page Alt (03a_content.svg)

- Variant of content page for visual rhythm variety
- Slightly different background tone (`#16162A`)
- Image has a subtle border frame instead of edge-to-edge
- Dot decoration instead of line decoration under title
- Use for alternating pages within the same section

### 6. Ending Page (04_ending.svg)

- Ending-specific AI background image (`{{ENDING_BG}}`) — style-unified with cover but different image
- Centered closing message (`{{CLOSING}}`)
- Tagline (`{{TAGLINE}}`) below
- Bottom info bar: author, organization

---

## V. SVG Page Roster

| File | Role | Image Placeholder | Description |
|------|------|-------------------|-------------|
| `01_cover.svg` | cover | `{{COVER_BG}}` | Title slide with cover-specific AI background |
| `02_toc.svg` | toc | `{{TOC_BG}}` | Table of contents with TOC-specific AI background |
| `02_chapter.svg` | chapter | `{{TRANSITION_BG}}` | Transition page with narrative bridge text |
| `03_content.svg` | content | `{{CONTENT_IMAGE}}` | Three-part content page |
| `03a_content.svg` | content_alt | `{{CONTENT_IMAGE}}` | Content page visual variant |
| `04_ending.svg` | ending | `{{ENDING_BG}}` | Closing page with ending-specific AI background |

---

## VI. Layout Patterns (Recommended)

| Layout Name           | Applicable Scenarios             | Features                       |
| --------------------- | -------------------------------- | ------------------------------ |
| **Full-bleed + floating text** | Cover, ending | Image fills canvas, text overlays with gradient scrim |
| **Narrative bridge** | Transition pages | Backward summary + chapter hero + forward hook |
| **Three-zone vertical** | All content pages | Title → core visual → takeaway, clean vertical flow |
| **Single column centered** | Key conclusions | Maximum whitespace, one idea lands with weight |

---

## VII. Spacing Specification

| Spacing Type       | Value | Usage                            |
| ------------------ | ----- | -------------------------------- |
| **Page Margins**   | 60px  | Left/right safe zone             |
| **Top Margin**     | 40px  | Title zone start                 |
| **Bottom Margin**  | 40px  | Takeaway zone end                |
| **Zone Gap**       | 16-24px | Space between zones            |
| **Image Padding**  | 8px   | Spacing around core image        |
| **Line Height**    | 1.5   | Body/caption text line height    |

---

## VIII. SVG Technical Constraints

### Mandatory Rules

- viewBox fixed at `0 0 1280 720`
- Use `<rect>` elements for backgrounds
- Use `<tspan>` for text wrapping
- All colors in HEX format (no rgba)
- Use `fill-opacity` / `stroke-opacity` for transparency

### Placeholder Convention

All SVGs use neutral placeholder colors (dark grays, white text) since color scheme is determined per-project by Eight Confirmations. The Strategist and Executor will override these with project-confirmed colors.

### Image Placeholder Convention

Each page type has its own dedicated image placeholder — images are NEVER shared across page types:

| Placeholder | Pages | Purpose |
|-------------|-------|---------|
| `{{COVER_BG}}` | cover only | Story's opening visual frame |
| `{{TOC_BG}}` | toc only | Sets thematic tone |
| `{{TRANSITION_BG}}` | chapter only | Per-section context image |
| `{{CONTENT_IMAGE}}` | content, content_alt | Page-specific narrative visual |
| `{{ENDING_BG}}` | ending only | Story's closing visual frame |

### Prohibited Elements

| Prohibited Item      | Alternative                    |
| -------------------- | ------------------------------ |
| `mask` | Do not use masking |
| `<style>`            | Use inline styles              |
| `class`              | Use inline attributes          |
| `foreignObject`      | Use `<tspan>` for wrapping     |
| `textPath`           | Use standard `<text>`          |
| `animate*` / `set`   | Do not use animations          |
| `<g opacity>`        | Set opacity on each element individually |

---

## IX. Placeholder Specification

### Image Placeholders (all distinct, never reused)

| Placeholder         | Usage                        | Pages         |
| ------------------- | ---------------------------- | ------------- |
| `{{COVER_BG}}`      | Cover AI background image    | cover         |
| `{{TOC_BG}}`        | TOC AI background image      | toc           |
| `{{TRANSITION_BG}}` | Transition AI background     | chapter       |
| `{{CONTENT_IMAGE}}` | Content page core AI image   | content, content_alt |
| `{{ENDING_BG}}`     | Ending AI background image   | ending        |

### Text Placeholders

| Placeholder         | Usage                        | Pages         |
| ------------------- | ---------------------------- | ------------- |
| `{{TITLE}}`         | Cover main title             | cover         |
| `{{SUBTITLE}}`      | Cover subtitle/tagline       | cover         |
| `{{AUTHOR}}`        | Author / presenter name      | cover, ending |
| `{{ORGANIZATION}}`  | Organization name            | cover, ending |
| `{{DATE}}`          | Date                         | cover         |
| `{{TOC_ITEM_N_TITLE}}` | TOC section title (N=1..6) | toc        |
| `{{TOC_ITEM_N_DESC}}`  | TOC section description (N=1..4) | toc   |
| `{{PREV_SECTION_LABEL}}` | Previous section label   | chapter       |
| `{{PREV_SECTION_SUMMARY}}` | Previous section summary | chapter     |
| `{{CHAPTER_NUM}}`   | Chapter number               | chapter       |
| `{{CHAPTER_TITLE}}` | Chapter title                | chapter       |
| `{{CHAPTER_DESC}}`  | Chapter description          | chapter       |
| `{{NEXT_HOOK}}`     | Forward narrative hook       | chapter       |
| `{{PAGE_TITLE}}`    | Content page title           | content, content_alt |
| `{{SECTION_NAME}}`  | Section name indicator       | content, content_alt |
| `{{IMAGE_CAPTION}}` | Brief text below core image  | content, content_alt |
| `{{TAKEAWAY}}`      | Bottom takeaway / conclusion | content, content_alt |
| `{{CLOSING}}`       | Ending page main message     | ending        |
| `{{TAGLINE}}`       | Ending page tagline          | ending        |

---

## X. Usage Notes

### 1. Copy Template to Project

```bash
cp templates/layouts/story_driven/* projects/<project>/templates/
```

### 2. Color Strategy

This layout template does NOT prescribe colors. The Strategist determines the color scheme based on project topic and deep research content via Eight Confirmations. Neutral placeholder colors in SVGs are overridden by confirmed project colors.

### 3. AI Image Strategy

This template requires **5 distinct AI image categories** per project. Each category's image serves a different narrative role and must be visually distinct:

| Category | Count | Narrative Role |
|----------|-------|----------------|
| Cover background | 1 | Story's opening visual — the first emotional hook |
| TOC background | 1 | Sets thematic tone for the entire deck |
| Transition backgrounds | N (one per section) | Per-section context — bridges previous and upcoming content |
| Content images | M (one per content page) | Page-specific narrative visuals — the story's body |
| Ending background | 1 | Story's closing frame — bookend with cover, different image |

All AI images follow the project's confirmed rendering + palette strategy from Eight Confirmations, but each image's subject/composition is unique to its page.

### 4. Transition Page Narrative Design

Transition pages are the **narrative spine** of the deck. For each transition page, the Strategist must provide:

1. `PREV_SECTION_LABEL` — short label for the section just completed (e.g., "认识问题")
2. `PREV_SECTION_SUMMARY` — one-sentence takeaway from the previous section
3. `CHAPTER_NUM` — section number (e.g., "02")
4. `CHAPTER_TITLE` — section title
5. `CHAPTER_DESC` — section description / core question
6. `NEXT_HOOK` — forward-looking narrative hook (e.g., "那么，面对多种治疗方案，我们该如何选择？")

### 5. Content Page Rhythm

Alternate between `03_content.svg` and `03a_content.svg` for visual variety. Each section follows: transition page → 2-4 content pages → (next transition).
