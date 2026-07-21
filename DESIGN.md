---
version: "alpha"
name: NBER Research Desk
description: A restrained academic desktop workspace for reviewing NBER working papers.
colors:
  primary: "#083F78"
  primary-deep: "#062C54"
  on-primary: "#FFFEFA"
  secondary: "#526174"
  tertiary: "#DF6F35"
  background: "#F7F5EF"
  surface: "#FFFEFA"
  surface-subtle: "#F2F0EA"
  text-primary: "#14233A"
  text-muted: "#5F6F82"
  border: "#DEDFDC"
  border-strong: "#C9CED2"
  selection: "#EDF4FA"
  focus: "#4B89BD"
  success: "#2C8062"
  error: "#8B2C1F"
typography:
  display:
    fontFamily: Source Serif 4
    fontSize: 2rem
    fontWeight: 520
    lineHeight: 1.08
    letterSpacing: -0.035em
  paper-title:
    fontFamily: Source Serif 4
    fontSize: 1.0625rem
    fontWeight: 620
    lineHeight: 1.28
    letterSpacing: -0.018em
  detail-title:
    fontFamily: Source Serif 4
    fontSize: 1.625rem
    fontWeight: 520
    lineHeight: 1.12
    letterSpacing: -0.03em
  body:
    fontFamily: Source Sans 3
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.55
  detail-body:
    fontFamily: Source Serif 4
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.68
  body-compact:
    fontFamily: Source Sans 3
    fontSize: 0.75rem
    fontWeight: 400
    lineHeight: 1.4
  label:
    fontFamily: Source Sans 3
    fontSize: 0.6875rem
    fontWeight: 650
    lineHeight: 1.25
    letterSpacing: 0.04em
  metadata:
    fontFamily: Source Sans 3
    fontSize: 0.6875rem
    fontWeight: 400
    lineHeight: 1.35
  identifier:
    fontFamily: ui-monospace
    fontSize: 0.625rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: 0.05em
rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 10px
  pill: 999px
spacing:
  xxs: 4px
  xs: 6px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
components:
  app-shell:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text-primary}"
  sidebar:
    backgroundColor: "{colors.primary-deep}"
    textColor: "{colors.on-primary}"
    width: 72px
  primary-button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
    padding: 10px
    height: 36px
  secondary-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.md}"
    padding: 10px
    height: 34px
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 10px
    height: 36px
  paper-row:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: 12px
  paper-row-selected:
    backgroundColor: "{colors.selection}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: 12px
  paper-row-read:
    backgroundColor: "{colors.background}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.sm}"
    padding: 12px
  detail-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
  tag-system:
    backgroundColor: "{colors.selection}"
    textColor: "{colors.primary-deep}"
    rounded: "{rounded.pill}"
    padding: 6px
  tag-user:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.pill}"
    padding: 6px
  divider:
    backgroundColor: "{colors.border}"
    height: 1px
  resize-divider:
    backgroundColor: "{colors.border-strong}"
    width: 1px
  focus-ring:
    backgroundColor: "{colors.focus}"
    rounded: "{rounded.xs}"
  accent-rule:
    backgroundColor: "{colors.tertiary}"
    width: 3px
  success-status:
    backgroundColor: "{colors.success}"
    rounded: "{rounded.pill}"
    size: 8px
  error-banner:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.error}"
    rounded: "{rounded.md}"
    padding: 12px
  muted-metadata:
    backgroundColor: "{colors.background}"
    textColor: "{colors.text-muted}"
---

## Overview

NBER Research Desk is a desktop inbox for economists who review new working papers repeatedly, often for long sessions. It should feel like a well-kept academic reading room: quiet, precise, trustworthy, and designed for concentrated work.

The memorable element is the combination of disciplined desktop density with editorial paper typography. It is not a journal website, a marketing page, or a generic SaaS dashboard. Visual character comes from typography, hierarchy, and the warm paper palette—not from oversized cards or decorative effects.

The interface follows three priorities:

1. Help the researcher decide whether a paper matters.
2. Make repeated processing fast with stable layout and clear states.
3. Keep local data, source provenance, and system status understandable.

## Colors

- **Primary / Primary Deep:** Institutional NBER blue. Use for navigation, selected indicators, primary actions, and trustworthy system structure.
- **Tertiary:** Warm orange reserved for small accents, unread markers, and moments needing attention. Never use it as a large background.
- **Background:** Warm paper for the main workspace. It reduces glare and establishes the academic identity.
- **Surface:** Near-white for the detail pane, inputs, menus, and temporary overlays.
- **Text Primary:** Deep ink for titles and important values.
- **Secondary / Text Muted:** Slate tones for authors, dates, counts, and supporting information. Do not use muted text for required instructions.
- **Selection:** Pale blue for selected rows and quiet system emphasis.
- **Focus:** A distinct medium blue used for keyboard focus rings. Focus must remain visible on every interactive control.
- **Success / Error:** Semantic colors only. Always pair them with text, icons, or explicit labels; color alone must not communicate state.

Maintain WCAG AA contrast for body text and controls. Borders may be lower contrast because they are never the only way to identify an interactive element.

## Typography

Source Serif 4 is the research voice. Use it for paper titles, detail titles, and rare page-level headings. Its job is to make scholarly content recognizable, not to decorate controls.

Source Sans 3 is the interface voice. Use it for navigation, buttons, search, filters, settings, authors, metadata, notices, and help text. Keep interface text compact but readable.

The paper preview body defaults to 16px and offers 14px, 16px, and 18px reading sizes. This preference changes the right-hand paper title, authors, abstract, and metadata together while leaving navigation and list density stable.

Use the display scale sparingly. Desktop page headings should normally stay near 32px and must not consume the first screen. Paper titles in lists use the paper-title token; detail titles use detail-title. Avoid clamp-based growth that turns headings into landing-page hero text on wide windows.

Use tabular numerals where alignment matters. Use the identifier style only for NBER paper numbers, citekeys, file-like values, and diagnostic identifiers. Do not use monospace for ordinary metadata.

Chinese fallback fonts are Source Han Sans SC or PingFang SC for interface text and Source Han Serif SC or Songti SC for paper titles. Preserve the same hierarchy in both languages.

## Layout

The default workspace is a stable desktop split view:

- A narrow global sidebar, approximately 72px wide.
- A flexible feed pane with a practical minimum width near 440px.
- A detail pane that starts at 420px, with a keyboard-accessible divider that resizes it from 360px to 640px and remembers the chosen width.

Prioritize usable content area over page decoration. Keep the feed header compact: title, current scope, search, refresh, and filters should fit without forcing the first paper below an oversized header.

Use the 4px-based spacing scale. Dense list content may use 6–12px internal spacing; major pane boundaries use 16–32px. Do not place every section inside a card. Prefer alignment, dividers, and whitespace for structure.

Paper rows should scan vertically. Title alignment must remain stable even when unread markers or tags are present. Reserve consistent areas for unread state and timestamp so rows do not shift between states.

The detail pane follows this order: source and identifier, title, authors, tags, abstract, publication metadata, citation action, source action. Preserve the order across loading, error, and populated states.

## Elevation & Depth

The workspace is primarily flat. Pane separation comes from background changes and one-pixel borders.

Use shadows only for content that temporarily sits above the workspace: menus, notices, dialogs, and drag previews. Selected paper rows should rely on pale selection color, a leading indicator, and border contrast rather than floating-card shadows.

Do not use glassmorphism, background blur, large ambient shadows, or decorative gradient meshes in the working area. A subtle paper texture or rule pattern is acceptable only when it does not reduce text contrast or suggest an interactive surface.

Motion communicates state, not spectacle. Use 120–180ms transitions for hover, selection, focus, and menu opening. Respect reduced-motion preferences. Do not translate list rows on hover and do not stagger-animate a feed of research items.

## Shapes

Controls use restrained 6–10px radii. Paper rows use 6px corners and should read as rows, not cards. Pills are reserved for tags, counts, and compact categorical values.

Circles are reserved for status dots and icon-only controls that are circular by platform convention. Do not mix many unrelated shape languages.

Borders are functional. Use them to separate panes, inputs, menus, and focused regions. Avoid nesting several bordered containers inside one another.

## Components

### Sidebar

The sidebar contains only global destinations and persistent local status. Each icon has an accessible label and tooltip. Selected navigation uses background, icon color, and a leading accent—not color alone. The logo must not visually outweigh navigation.

### Feed header and filters

The header is a compact command area rather than a hero section. Search is the dominant flexible control. Refresh is a standard-width primary action. Active filters remain visible and counts never become the most prominent text.

### Paper rows

Paper rows define five independent states: unread, read, hovered, selected, and keyboard-focused. Selected and focused may occur together and must both remain visible. Read papers reduce emphasis without becoming low-contrast.

Use title, authors, up to three visible tags, and timestamp. Additional tags collapse into a count. Avoid abstracts, thumbnails, charts, and multiple action buttons in the list unless a future workflow proves they improve review speed.

### Detail pane

The detail pane is a structured paper record, not a collection of cards. The abstract is the primary reading block. Metadata uses a compact definition layout. High-frequency actions—mark read, edit tags, copy citation, open source—remain directly available.

### Tags

System-supplied and user-created tags must be distinguishable by label or subtle treatment, not by color alone. Tags are organizational data. Keep them small, readable, editable, and stable in height.

### Settings

Settings use clear sections with direct labels and explanatory text. File paths may wrap or truncate with a way to reveal the full value. Destructive or externally networked actions must explain their effect before execution.

### Empty, loading, and error states

Loading skeletons match the final geometry and do not pulse aggressively. Empty states state what happened and offer the next useful action. Errors preserve already available local data whenever possible and provide a direct retry action.

## Do's and Don'ts

### Do

- Optimize for repeated daily review and keyboard-assisted use.
- Preserve stable pane positions and row alignment.
- Let paper titles and abstracts carry the visual identity.
- Use explicit language for local, online, cached, syncing, and failed states.
- Keep high-frequency actions one step away.
- Test at the minimum supported window size and at 200% text zoom.
- Use icons from one restrained, consistent stroke family.

### Don't

- Do not turn the feed header into a landing-page hero.
- Do not wrap every group in a rounded card.
- Do not add relationship graphs, trend dashboards, or AI scores as visual decoration.
- Do not hide critical state behind hover alone.
- Do not use orange for large surfaces or routine primary actions.
- Do not reduce information density merely to appear modern.
- Do not invent fake paper relevance, recommendation, or confidence indicators.
- Do not add motion that slows scanning or causes rows to shift.
