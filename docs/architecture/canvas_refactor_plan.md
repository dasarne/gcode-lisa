# Canvas Panel Refactor Plan

## Purpose

This document serves as the long-term architectural reference for the conservative refactoring of:

- `src/ui/canvas_panel.py`

The goal is to preserve:
- rendering performance
- repaint stability
- interaction consistency
- editor ↔ canvas synchronization
- predictable viewport behavior

while gradually improving:
- maintainability
- testability
- subsystem separation
- profiling visibility
- future optimization readiness

This document is intended to outlive individual implementation sessions and provide continuity across:
- future AI-agent contexts
- contributors
- review sessions
- refactoring phases

This document follows the master phase structure defined in GitHub issue `#20`.

Issue `#20` is the authoritative execution roadmap.

This document serves as:
- the technical knowledge base
- the architectural risk registry
- the subsystem analysis reference
- the implementation guidance document

---

# Current Architectural Role

`canvas_panel.py` currently acts as a combined subsystem containing:

- rendering orchestration
- viewport state management
- coordinate projection
- geometry reprojection
- hit-testing
- selection handling
- highlight rendering
- overlay rendering
- navigation handling
- cache ownership
- repaint/update sequencing

The file is already strongly optimized toward:
- responsiveness
- reduced repaint overhead
- low-latency interaction
- explicit geometry preparation

The current implementation intentionally prioritizes:
- stability
- performance
- centralized paint control

over strict modular separation.

---

# Critical Render Paths

The following paths are considered performance critical.

## paintEvent()

The paint lifecycle is currently centralized and tightly coupled to:
- geometry caches
- highlight state
- viewport transforms
- zoom/pan state
- overlay rendering

### Important Constraints

Avoid:
- allocations inside render loops
- unnecessary geometry rebuilding
- duplicated coordinate transforms
- hidden O(n) repaint work
- expensive calculations during repaint

Preserve:
- batched rendering behavior
- incremental update capability
- lightweight repaint paths

---

## Geometry Reprojection

Critical methods:
- `_reproject_geometry()`
- projection helper paths
- viewport transform logic

These paths directly influence:
- repaint latency
- interaction smoothness
- selection accuracy
- overlay positioning

### Important Constraints

Coordinate-space consistency is critical.

Small mathematical inconsistencies can cause:
- selection offsets
- overlay drift
- hit-testing mismatches
- viewport jitter

---

## Highlight Rendering

Highlighting currently interacts directly with:
- redraw scheduling
- segment iteration
- geometry traversal

Potential future optimization areas:
- persistent line caches
- incremental highlight redraws
- separation of static and dynamic render layers

These optimizations are intentionally deferred.

---

# Current Subsystems

## Rendering Subsystem

Responsibilities:
- line rendering
- color handling
- overlay drawing
- highlight visualization
- repaint orchestration

Risk level:
HIGH

This area should remain centralized during early refactor phases.

---

## Viewport / Camera Subsystem

Responsibilities:
- zoom
- pan
- rotation
- projection
- coordinate transforms

Risk level:
HIGH

Coordinate-space consistency must remain stable across:
- rendering
- hit-testing
- overlays
- interaction

---

## Selection / Picking Subsystem

Responsibilities:
- hit-testing
- selection state
- highlighted segments
- synchronization with editor

Risk level:
MEDIUM-HIGH

Selection behavior is user-visible and tightly coupled to viewport math.

---

## Geometry / Projection Helpers

Responsibilities:
- pure transforms
- projection math
- viewport calculations
- geometry utility operations

Risk level:
LOW-MEDIUM

This is currently the safest extraction zone.

---

## Cache / Invalidation Subsystem

Responsibilities:
- geometry cache ownership
- redraw invalidation
- rebuild scheduling

Risk level:
HIGH

Incorrect invalidation sequencing may create:
- stale rendering
- repaint glitches
- excessive redraws
- interaction instability

---

# Safe Extraction Candidates

The following areas are considered relatively safe for conservative extraction.

## Phase 1 Candidates

### Coordinate Transform Helpers

Potential targets:
- camera transforms
- projection helpers
- viewport conversion helpers

Requirements:
- pure functions
- QWidget-independent
- fully testable

---

### Viewport Math Helpers

Potential targets:
- screen ↔ viewport conversion
- scale helpers
- coordinate normalization

Requirements:
- no rendering ownership
- no state mutation
- deterministic behavior

---

### Geometry Utilities

Potential targets:
- small reusable geometry calculations
- render-independent helper functions

Requirements:
- no repaint coupling
- no QWidget dependencies

---

# Deferred / High-Risk Areas

The following areas should remain inside the main viewport/widget layer unless future analysis proves otherwise.

## Paint Orchestration

Includes:
- `paintEvent()`
- repaint sequencing
- render ordering

Reason:
Highly coupled to performance behavior.

---

## Qt Event Sequencing

Includes:
- mouse interaction ordering
- drag lifecycle
- repaint triggering
- transient interaction state

Reason:
Ordering bugs are difficult to detect and reproduce.

---

## Viewport State Machine

Includes:
- pan/zoom/rotate coordination
- interaction ownership
- update synchronization

Reason:
High regression risk.

---

# Manual Regression Checklist

The following checks should be performed after every meaningful refactor step.

## Rendering

- no visual flicker
- no missing segments
- stable overlays
- correct highlight rendering
- stable zoom behavior

---

## Interaction

- pan remains smooth
- zoom anchor remains correct
- selection remains accurate
- lasso behavior remains stable
- editor ↔ canvas synchronization preserved

---

## Performance

- no obvious repaint slowdown
- no excessive CPU usage during pan/zoom
- no full redraw regressions
- no large allocation spikes during interaction

---

## Stability

- no stale geometry
- no repaint artifacts
- no inconsistent highlight state
- no desynchronization between selection systems

---

# Planned Refactor Areas

The execution phases are defined in GitHub issue `#20`.

This section only documents the currently identified technical work areas and constraints.

---

## Analysis & Safety-Net Work

Current focus areas:
- architecture documentation
- render/update path mapping
- invalidation ownership analysis
- subsystem boundary analysis
- regression checklist creation
- repaint-risk identification

---

## Safe Utility Extraction Areas

Candidate areas:
- coordinate transforms
- projection helpers
- viewport math
- geometry utilities

Primary constraints:
- no repaint behavior changes
- no ownership changes
- no event-sequencing changes

---

## Conservative Interaction Separation Areas

Candidate areas:
- hit-testing helpers
- selection geometry helpers
- overlay calculations
- invalidate/rebuild helpers

Primary constraints:
- preserve interaction semantics
- preserve repaint sequencing
- preserve coordinate-space consistency

---

## Deferred Performance Work

Potential future work:
- persistent line caches
- incremental reprojection
- redraw reduction
- highlight optimization

This work should remain separated from architectural cleanup where possible.

---

# Current Architectural Rules

## Rule: Paint Orchestration Remains Centralized

Avoid splitting repaint orchestration across multiple ownership layers.

Reason:
Centralized rendering behavior is currently important for stability and profiling visibility.

---

## Rule: Coordinate Spaces Must Remain Explicit

All transformations between:
- world space
- viewport space
- screen space

must remain:
- explicit
- deterministic
- testable

Avoid hidden coordinate conversions.

---

## Rule: Cache Invalidation Must Remain Explicit

Geometry rebuilds and redraw invalidation must remain:
- visible
- predictable
- traceable

Avoid implicit rebuild side effects.

---

## Rule: Rendering Performance Has Priority Over Architectural Purity

Prefer:
- predictable repaint behavior
- stable interaction
- explicit state ownership

over:
- aggressive abstraction
- deep indirection
- speculative architecture layers

---

# Progress Log

## 2026-06-14 — #20-0-"Architectural Role"

Validated architectural assumptions against the real implementation.

Key findings:
- `paintEvent()` is primarily a render orchestrator, not a geometry builder
- rendering consumes precomputed `QLineF`, `QPolygonF`, and `QPointF` caches
- highlight rendering performs repaint-only updates without reprojection
- `_SegGeom.world_points` acts as the persistent geometry source cache
- `seg.points` acts as the derived projection cache
- reprojection and repaint are already implicitly separated
- highlight/animation state is isolated from geometry rebuilding
- pan/zoom mostly affect viewport transforms, not geometry caches

Validated repaint-only paths:
- `set_highlight()`
- `_on_anim_tick()`
- wheel zoom
- panning
- lasso updates
- `fit_view()`

Validated reprojection paths:
- `_reproject_geometry()`
- `set_view_angles()`
- rotation drag handling
- `_build_geometry()`

Confirmed high-risk areas:
- paint orchestration
- repaint sequencing
- invalidate ordering
- coordinate-space consistency
- geometry rebuild lifecycle

Confirmed safe extraction candidates:
- `_proj()`
- `_camera_transform()`
- `_nice_integer_step()`
- `_axis_tick_steps()`
- viewport math helpers
- render-independent geometry utilities

Architectural conclusion:
The canvas system is already internally layered and performance-oriented.

Future refactoring should prioritize:
- making ownership explicit
- improving subsystem visibility
- conservative extraction

Avoid:
- aggressive decomposition
- repaint lifecycle fragmentation
- hidden invalidation paths
