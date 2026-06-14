# AGENTS.md

## Project Mission

GCode Lisa is a professional desktop G-Code editor and analyzer focused on:

- Reliability
- CNC safety
- Clear visualization
- Fast interaction
- Practical Linux/KDE desktop workflows
- Multi-dialect compatibility

The project is intentionally not:
- A web application
- A cloud service
- A generic CAD/CAM system
- A rapid-prototype playground for unnecessary frameworks

AI agents should prioritize maintainability, predictability, and operator trust over novelty.

---

# Core Engineering Principles

## Safety First

This application operates on machine instructions.

Never:
- silently modify G-Code
- auto-correct motion commands without user interaction
- guess dialect semantics
- remove warnings to hide problems

Always:
- preserve source fidelity
- prefer warnings over automatic correction
- make transformations explicit and visible
- keep user control central

---

# Architecture Guardrails

## Separation of Concerns

Maintain strict boundaries:

- `src/gcode`
  - parsing
  - tokenization
  - dialect definitions
  - command semantics

- `src/geometry`
  - coordinate transformations
  - bounds
  - toolpath representation
  - GUI-independent calculations

- `src/analyzer`
  - warnings
  - optimization hints
  - compatibility analysis

- `src/ui`
  - presentation
  - interaction
  - rendering
  - dialogs

Do not:
- place parsing logic inside UI widgets
- couple geometry calculations to Qt widgets
- perform filesystem operations in rendering code
- introduce hidden global state

---

# File-Specific Guidance

## `main_window.py`

This file is already large.

Avoid:
- accumulating additional business logic
- embedding parser/analyzer internals
- adding unrelated helper utilities

Prefer:
- extracting reusable services
- delegating workflows to focused modules

## `editor_panel.py`

Critical UX component.

Protect:
- responsiveness
- selection behavior
- keyboard navigation
- multi-selection workflows
- undo/redo consistency

Do not introduce:
- expensive reparsing on every keypress
- blocking operations in editor callbacks

## `canvas_panel.py`

Rendering performance is critical.

Avoid:
- unnecessary full geometry rebuilds
- heavy allocations during paint events
- expensive calculations inside render loops

Prefer:
- caching
- incremental updates
- lightweight rendering paths

## Translation Files

When modifying UI text:
- keep German and English translations synchronized
- avoid hardcoded strings in widgets

---

# UX Principles

GCode Lisa is desktop-first software.

Prioritize:
- keyboard accessibility
- fast workflows
- precision
- low-friction editing
- visual clarity

Avoid:
- unnecessary modal dialogs
- oversized UI elements
- web-style interaction patterns
- animation-heavy interfaces

Core workflows must remain fast:
- editor ↔ canvas synchronization
- selection workflows
- search and replace
- comment navigation

---

# Performance Rules

The application must remain responsive for large G-Code files.

Avoid:
- reparsing the full document unnecessarily
- synchronous heavy operations in UI threads
- adding large dependencies without strong justification

Prefer:
- incremental updates
- lazy calculations
- lightweight dependencies
- profiling before optimization changes

---

# Dependency Policy

Before adding a dependency:
- verify that the functionality does not already exist
- justify the dependency cost
- consider package size and startup impact
- prefer standard library solutions where practical

Do not:
- introduce web frameworks
- introduce ORM layers
- introduce async frameworks unless clearly justified

---

# Testing Rules

All meaningful functionality changes should include tests.

Required expectations:
- parser changes require fixture tests
- dialect changes require compatibility tests
- geometry changes require regression checks
- UI bug fixes should include reproducible test coverage where feasible

Never:
- delete failing tests to make CI pass
- weaken assertions without explanation

---

# Coding Style

Target:
- Python 3.10+
- explicit code
- readable control flow
- small focused methods
- type hints preferred

Avoid:
- hidden side effects
- magic behavior
- broad exception swallowing
- duplicated utilities
- premature abstractions

---

# Documentation Rules

When behavior changes:
- update README if user-visible
- update DEVELOPMENT.md if workflow-related
- update translations if UI text changes
- update CHANGELOG.md for release-relevant changes

---

# Definition of Done

A task is only considered complete when:

- implementation is finished
- tests pass
- typing checks pass
- documentation is updated
- translations are synchronized
- no obvious regressions remain
- UX consistency is preserved

---

# AI-Agent Behavior

AI agents should:
- prefer minimal targeted changes
- preserve project structure
- avoid speculative refactors
- verify existing implementations before adding new abstractions
- keep changes understandable for human maintainers

If uncertain:
- choose the safer and simpler implementation.