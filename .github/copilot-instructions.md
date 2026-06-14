# GitHub Copilot Instructions

## Project Context

GCode Lisa is a Linux desktop application for editing, analyzing, and visualizing G-Code files.

The application targets:
- CNC workflows
- reliability
- predictable behavior
- fast interaction
- large-file responsiveness
- practical desktop UX

This is not:
- a web application
- a cloud platform
- a CAD system
- an experimental framework showcase

---

# Primary Goals

When generating code, prioritize:

1. Reliability
2. CNC safety
3. Readability
4. Maintainability
5. UX consistency
6. Performance on large G-Code files

Avoid unnecessary complexity.

---

# Architecture Expectations

Respect module boundaries:

- `src/gcode`
  - parsing
  - tokenization
  - dialect logic

- `src/geometry`
  - geometry
  - transforms
  - bounds
  - GUI-independent calculations

- `src/analyzer`
  - warnings
  - validation
  - optimization hints

- `src/ui`
  - Qt widgets
  - rendering
  - interaction
  - dialogs

Do not:
- move parsing logic into UI code
- introduce hidden global state
- mix rendering and filesystem operations
- tightly couple geometry code to Qt widgets

---

# UI and UX Rules

The UI is desktop-first and optimized for keyboard-heavy workflows.

Preserve:
- editor ↔ canvas synchronization
- responsiveness
- keyboard shortcuts
- multi-selection workflows
- undo/redo behavior
- low-friction editing

Avoid:
- unnecessary modal dialogs
- oversized controls
- web-style interaction patterns
- blocking UI operations
- animations without practical value

---

# Performance Requirements

Large G-Code files must remain responsive.

Avoid:
- reparsing entire documents unnecessarily
- rebuilding geometry too frequently
- expensive work during paint events
- blocking operations in UI callbacks

Prefer:
- incremental updates
- caching
- lazy evaluation
- lightweight data structures

---

# Safety Rules

Never:
- silently rewrite G-Code
- auto-correct machine commands
- remove warnings automatically
- guess dialect semantics

Always:
- preserve source fidelity
- expose transformations explicitly
- keep the operator in control

---

# Dependency Policy

Before adding dependencies:
- verify existing functionality does not already solve the problem
- prefer standard library solutions
- justify large dependencies

Avoid introducing:
- web frameworks
- async frameworks without strong justification
- ORM layers
- unnecessary rendering engines

---

# Testing Expectations

Changes should include tests whenever feasible.

Expected coverage:
- parser changes → parser tests
- dialect changes → compatibility tests
- geometry changes → regression tests
- UI fixes → reproducible interaction tests where practical

Never remove failing tests to hide regressions.

---

# Coding Style

Target:
- Python 3.10+
- explicit readable code
- small focused methods
- type hints where practical

Avoid:
- magic behavior
- hidden side effects
- duplicated logic
- speculative abstractions
- broad exception swallowing

---

# Documentation Expectations

When behavior changes:
- update README if user-visible
- update DEVELOPMENT.md if workflow-related
- update CHANGELOG.md for release-relevant changes
- keep German and English translations synchronized

---

# Preferred AI Behavior

Prefer:
- minimal targeted changes
- preserving architecture
- understanding existing implementations before extending them

Avoid:
- speculative refactors
- large rewrites without request
- introducing parallel implementations of existing functionality

When uncertain:
- choose the safer and simpler implementation.