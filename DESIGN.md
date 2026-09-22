---
name: Jev Workbench
description: A calm local workbench for judgment functions — warm neutral surfaces, mist-blue accent, colour reserved for type and state.
colors:
  panel: "#19191b"
  panel-2: "#111112"
  panel-hover: "#242427"
  panel-press: "#28282f"
  text: "#e9e9ed"
  muted: "#96969f"
  line: "#2b2b2f"
  accent: "#a6afd5"
  accent-pressed: "#c5cde6"
  on-accent: "#2b3142"
  danger: "#e0b5a5"
  field: "#202023"
  well: "#222329"
  selection: "#4d5874"
  light-panel: "#fcfcfb"
  light-panel-2: "#f5f5f4"
  light-panel-hover: "#eeeeee"
  light-panel-press: "#e8e9ee"
  light-text: "#292a2e"
  light-muted: "#74757d"
  light-line: "#e8e8e6"
  light-accent: "#66709e"
  light-accent-pressed: "#4b5874"
  light-on-accent: "#faf9f6"
  light-danger: "#8c594b"
  light-field: "#eeeeed"
  light-well: "#f8f7f4"
  light-selection: "#d6dceb"
tones:
  slate: { ink: "#91a8dc", fill: "#3a4155", light-ink: "#647db5", light-fill: "#e7eaf2" }
  blue: { ink: "#8ab2d5", fill: "#354454", light-ink: "#5684aa", light-fill: "#e6ecf3" }
  ochre: { ink: "#c9a566", fill: "#4b4133", light-ink: "#a7803e", light-fill: "#f2ebdf" }
  plum: { ink: "#bc9ada", fill: "#4c3c4d", light-ink: "#9270b1", light-fill: "#efe6ef" }
  clay: { ink: "#d29c87", fill: "#4d3d37", light-ink: "#b27460", light-fill: "#f2e7e1" }
typography:
  page-title: { fontSize: "19px", fontWeight: 600, letterSpacing: "-0.025em" }
  section-mark: { fontFamily: mono, fontSize: "10px", fontWeight: 620, letterSpacing: "0.08em", textTransform: uppercase }
  row-title: { fontSize: "12.5px", fontWeight: 570 }
  body: { fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", system-ui, sans-serif', fontSize: "13px" }
  caption: { fontSize: "11px", lineHeight: 1.6 }
  code: { fontFamily: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace', fontSize: "11px" }
rounded:
  chip: "4px"
  row: "7px"
  control: "8px"
  pane: "9px"
  panel: "12px"
motion:
  duration: "180ms"
  ease: "cubic-bezier(.16, 1, .3, 1)"
---

# Design System: Jev Workbench

## Overview

**Creative north star: a quiet operating surface.**

The workbench replicates DropAgent's visual language, down to the palette in
that project's `Palette.swift`. Space serves one thing: defining a judgment,
running it on real input, and seeing exactly what a caller will get. Warm
neutral surfaces carry the work; a single mist-blue accent marks the primary
action, selection, and focus. Colour beyond that is reserved for small type
chips and icons.

This file records what is implemented. Product behaviour and acceptance scope
remain governed by `specs/v1/spec.md` and the confirmed revisions listed in
`AGENTS.md`; the UI contract is `specs/dropagent-visual/spec.md`. Differences
between an implementation value here and a contract are not new authorisation.

**Key characteristics**

- Dark by default, light from the top bar, persisted per browser. Both themes
  are first-class, including the JSON editor.
- One directory rail plus an inset content pane. Settings and history are
  secondary entries at the foot of the rail, never duplicated in the top bar.
- Desktop editing first: define and preview sit side by side and scroll
  independently, so the default state never scrolls the page.
- State is always stated in words. Colour never carries a status alone.

## Colour

Two greys build the room: the chrome (`panel-2`) and the inset content pane
(`panel`), separated by a hairline and a 9px radius rather than a shadow.
Grouped form rows sit on `panel-2` again, so grouping comes from a fill instead
of another border.

Mist blue is the only accent: primary buttons, selected navigation, focus rings,
meters, and the headline answer value. It is never used to decorate a block of
content.

Five tones carry type and state, each as an ink plus a matching fill: **slate**
for Noul and published, **blue** for Choice and HTTP methods, **ochre** for
Score and anything needing review, **plum** for secondary actions, **clay** for
errors and destructive intent. Green is not used at all.

**The visible-state rule.** Success, connection, and publication need words. A
dot, a chip colour, or an icon alone never proves them.

## Typography

One system sans stack with a Chinese fallback; a system mono for keys, paths,
code, and anything the caller will type verbatim.

Section marks are mono, uppercase, 10px, tracked, preceded by a 5px square —
they label a region without competing with its content. Page titles are 19px at
-0.025em. Row titles are 12.5px/570 with an 11px caption underneath. Body text
is 13px. Nothing below 10px carries meaning on its own.

## Layout

A 48px top bar spans brand, breadcrumb, and the right-hand controls, with the
brand aligned to the rail. The rail is 248px (218px under 1150px) and holds
search, the grouped directory, and the secondary entries. The content pane is
inset 7px with a 9px radius and a 1px hairline.

Inside the pane, a page is a fixed header, a scrolling body, and — in the editor
— a bottom action bar. At 1440 and 1024 the editor keeps two columns; each
column scrolls on its own under a sticky section mark, so expanding advanced
config never grows the page. Grouped rows collapse to one column by container
query, which is why the same markup works in the narrow editor column and on the
full-width settings page.

Below 760px the rail moves above the content, the editor stacks, and the page is
allowed to scroll. Full editing is still specified down to 768px; 390px
guarantees readability and no horizontal overflow.

## Elevation and depth

Structure comes from background steps and hairlines. Panels have no shadow. Only
things that float — the right-hand drawer, the row overflow menu, a selected
segment — carry one. The drawer is inset on all four sides on desktop and
becomes a bottom sheet under 760px.

Transitions are 180ms on `cubic-bezier(.16, 1, .3, 1)` and serve hover, press,
selection, and expansion. Buttons compress to 0.97 on press. Reduced-motion
switches all of it off.

## Shape

Panels and grouped rows are 12px, the content pane 9px, controls 8px, directory
rows 7px, chips 4–5px. Borders stay 1px. Nothing is fully pill-shaped.

## Components

### Buttons

Primary is a solid accent with dark ink; secondary is the panel colour with a
hairline; quiet is transparent until hover; danger is clay text with a hairline.
Minimum height 32px, 36px in the action bar. Disabled drops to 42% opacity and
shows a not-allowed cursor. Keyboard focus is a high-contrast accent outline and
is never replaced by the hover style.

### Inputs

Filled (`field`) with a transparent border that becomes a hairline on hover and
the accent on focus; 8px radius, 32px minimum. Labels sit above, help text
below. The JSON editor keeps its own border and scrolls internally, so long
payloads never stretch the page.

### Directory rows

46px rows: a primitive chip in a fixed left column, the name, and the status on a
second line. Hover and selection are fills, not borders. The overflow menu
appears on hover or selection and lifts above its neighbours while open.

### Grouped rows

A `sheet` is a 12px panel of rows separated by hairlines — title and caption on
the left, control on the right, collapsing to one column when the container gets
narrow. This is the shape for function definition, settings, and any
label/control pair.

### Action bar

The editor's footer carries the verbs: versions, call history, cases, save
draft, publish. Icons are tone-coloured, labels are always present, and the
primary action is the only filled one.

### Preview and result

The input group is the saved-case picker, a form/JSON switch, the fields, and
the run action with its cost note. The result group leads with the answer value
at 22px in the accent colour, then meters, then diagnostics behind a summary.
Once the config changes, the result is labelled stale and says to run again.
Unpublished, waiting, running, and failed are all stated plainly; progress is
never faked and accuracy is never implied.

### Notices and demo state

Notices are a tinted block with a 2px accent edge; errors use clay. Offline demo
and test mode sit at the top of the content pane on every screen and say that
answers are simulated, cost nothing, and reach no network. Demo is never a
degraded fallback for a failing provider.

### Grants and runtime status

Checkbox, function key, and pinned version stay legible together at every width.
Integration status separates planned, written, connection-tested, and actually
called. A selected card or a written config file never stands in for the words
that say a connection succeeded.

## Do's and don'ts

**Do**

- Keep the warm neutral surface and the current information density.
- Keep input groups, result groups, and grant fields legible together as the
  layout narrows.
- State stale config, unpublished, review, error, and simulated explicitly.

**Don't**

- Add a KPI home, invented usage, or a fabricated accuracy number.
- Use large gradients, glass, marketing illustration, or animated metrics.
- Present phone readability, a simulated success, or the presence of a config
  file as proof of full editing, real inference, or a connected runtime.
