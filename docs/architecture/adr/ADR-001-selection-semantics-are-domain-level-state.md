# ADR-001 — Selection Semantics Are Domain-Level State

## Status

Accepted

---

## Context

GCode Lisa originally relied heavily on Qt text editing primitives for interaction state.

Selection state was primarily represented through:
- `QTextCursor`
- text ranges
- widget-local highlight state
- editor-owned interaction logic

This approach worked sufficiently while the application behaved mostly like a traditional text editor with visualization capabilities.

As geometric interaction evolved, several structural limitations emerged.

The application increasingly requires:
- geometric selection in the canvas
- disconnected multi-selection
- persistent selection groups
- synchronization between geometry and source structure
- stable selection identity during document changes
- selection semantics tied to machining meaning rather than text ranges

Qt text widgets fundamentally model:
- a primary cursor
- transient document-relative selections
- widget-local interaction state

This does not map reliably to CNC-domain interaction requirements.

Selection behavior is no longer purely a UI concern.

It is now part of the application’s CNC-domain semantics.

---

## Decision

Selection semantics are treated as domain-level state rather than widget-local editor state.

Selections must become explicit application structures that can be shared consistently across:
- editor
- canvas
- analyzer
- navigation systems
- future semantic tooling

Qt selection APIs may still be used as rendering or interaction adapters, but they are not the authoritative representation of selection state.

The authoritative model must eventually:
- support disconnected selections
- preserve stable semantic identity
- survive incremental document updates
- map consistently between geometry and source structures
- remain independent from any individual UI widget

Selections are therefore modeled conceptually as CNC-domain entities rather than transient text-widget artifacts.

---

## Consequences

### Positive

- consistent selection behavior across UI systems
- stable geometry ↔ document synchronization
- enables future semantic editing operations
- enables persistent multi-selection
- reduces widget-centric coupling
- supports future custom editor implementations
- improves architectural clarity

### Negative

- additional synchronization complexity
- temporary duplication between widget state and domain state
- migration effort away from implicit Qt behavior
- increased architectural responsibility for interaction systems

---

## Architectural Implications

Future systems will likely require explicit structures such as:
- `SelectionState`
- `SelectionObject`
- semantic selection groups
- geometry-linked selection references

Selection ownership progressively moves:
- away from widgets
- toward shared domain infrastructure

Qt widgets become consumers and presenters of selection state rather than the source of truth.

---

## Rejected Alternatives

### “QTextCursor remains the authoritative model”

Rejected because:
- Qt selection semantics are fundamentally linear
- disconnected persistent selection is difficult to model reliably
- geometric workflows become fragile
- synchronization logic becomes increasingly implicit and error-prone

### “Canvas and editor maintain independent selection systems”

Rejected because:
- creates divergent state
- introduces synchronization fragility
- causes inconsistent interaction behavior
- scales poorly as semantic tooling increases

---

## Long-Term Direction

This ADR establishes the foundation for:
- shared interaction state
- semantic editing systems
- persistent multi-selection
- geometry-aware workflows
- future editor decoupling
- domain-oriented CNC interaction models