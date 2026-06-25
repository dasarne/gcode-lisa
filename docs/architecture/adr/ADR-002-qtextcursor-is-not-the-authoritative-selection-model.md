# ADR-002 — QTextCursor Is Not The Authoritative Selection Model

## Status

Accepted

---

## Context

The original editor interaction model in GCode Lisa relied heavily on Qt’s native text editing infrastructure.

`QTextCursor` was implicitly treated as the primary representation for:
- current selection
- active editing position
- highlight ownership
- navigation synchronization
- editor interaction state

This matched the assumptions of conventional text editor architectures.

As the project evolved toward geometry-aware CNC interaction, this assumption became increasingly problematic.

Several workflows exposed structural limitations:
- canvas-driven selection
- disconnected selection groups
- geometry-first interaction
- semantic operation grouping
- persistent multi-selection
- synchronization between geometric entities and source structures

`QTextCursor` fundamentally represents:
- linear text positions
- contiguous ranges
- widget-local interaction state
- transient editor state

It cannot reliably represent:
- semantic entity ownership
- disconnected domain selections
- stable selection identity across edits
- geometry-linked selection groups
- cross-component interaction state

The application increasingly requires interaction semantics that exist outside the capabilities of a traditional text cursor abstraction.

---

## Decision

`QTextCursor` is no longer considered the authoritative selection model of the application.

Qt cursor objects remain implementation tools for:
- rendering
- text interaction
- caret positioning
- compatibility with Qt editing behavior

However, authoritative interaction semantics must exist independently from Qt widget state.

Future selection ownership must progressively move toward shared domain-level structures.

The editor widget becomes:
- a consumer of selection state
- a presenter of interaction state
- an interaction adapter

rather than the source of truth.

---

## Consequences

### Positive

- enables geometry-driven interaction
- reduces coupling to Qt widget internals
- allows persistent semantic selections
- improves synchronization consistency
- enables future editor evolution
- supports alternative rendering and editing systems

### Negative

- additional synchronization layers are required
- editor integration becomes more complex
- implicit Qt behavior can no longer be relied upon
- migration effort increases

---

## Architectural Implications

Future interaction systems may require:
- explicit selection registries
- stable semantic identifiers
- geometry-linked references
- editor overlay systems
- widget-independent interaction state

Qt cursor state becomes derived state rather than authoritative state.

This reverses the original ownership direction of the architecture.

---

## Rejected Alternatives

### “Keep QTextCursor as the central interaction authority”

Rejected because:
- it tightly couples semantics to Qt internals
- disconnected multi-selection becomes fragile
- geometry-first interaction remains difficult
- semantic workflows become increasingly implicit

### “Mirror cursor state everywhere”

Rejected because:
- synchronization complexity grows rapidly
- ownership becomes unclear
- divergence between systems becomes likely
- semantic intent remains poorly represented

---

## Long-Term Direction

This ADR establishes the architectural direction toward:
- widget-independent interaction semantics
- domain-owned selection state
- future custom editor behavior
- semantic navigation systems
- geometry-aware interaction models
- stable cross-component synchronization

The Qt editor remains important, but it is no longer treated as the canonical owner of interaction semantics.