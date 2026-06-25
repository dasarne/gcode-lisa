# ADR-003 — Multi-Selection Is Preserved Despite Qt Limitations

## Status

Accepted

---

## Context

GCode Lisa increasingly relies on geometric interaction workflows.

Users must be able to:
- select multiple toolpath regions
- preserve disconnected selections
- combine geometric and textual interaction
- work with semantic operation groups
- navigate complex machining structures
- maintain selection state across interaction steps

Qt’s standard text editing infrastructure was not designed for these requirements.

`QTextCursor` and standard Qt text widgets fundamentally assume:
- one primary cursor
- contiguous text-oriented selections
- widget-owned interaction state
- transient UI-driven selection semantics

This creates significant limitations for CNC workflows.

In particular:
- disconnected semantic selections become fragile
- selection persistence becomes unreliable
- geometry ↔ editor synchronization becomes difficult
- selection identity is lost during updates
- canvas-driven workflows become constrained by editor internals

However, the required CNC workflows still demand reliable multi-selection behavior.

The application cannot reduce interaction capabilities simply because the underlying widget system lacks native support.

---

## Decision

GCode Lisa preserves domain-level multi-selection semantics independently from Qt widget limitations.

Qt selection systems may continue to provide:
- local interaction primitives
- visual feedback
- compatibility behavior
- text editing integration

But the application must not allow Qt limitations to define the interaction capabilities of the CNC domain model.

Persistent multi-selection behavior becomes an explicit architectural responsibility of the application itself.

The canonical selection state must therefore:
- support disconnected selections
- survive widget state changes
- remain stable across document updates
- map consistently to geometry and semantics
- remain independent from transient Qt cursor behavior

Qt widgets become compatibility layers rather than capability boundaries.

---

## Consequences

### Positive

- preserves required CNC interaction workflows
- enables geometry-first selection behavior
- supports future semantic editing systems
- avoids architectural lock-in to Qt limitations
- enables richer interaction models over time
- improves consistency between editor and canvas

### Negative

- additional infrastructure must be maintained
- synchronization complexity increases
- interaction behavior becomes more application-specific
- Qt-native behavior may require partial override logic

---

## Architectural Implications

Future systems may require:
- persistent selection registries
- virtual selection overlays
- semantic selection groups
- stable entity references
- widget-independent interaction state
- geometry-linked selection persistence

Selection rendering and selection ownership become separate concerns.

This is a major architectural distinction from traditional editor systems.

---

## Rejected Alternatives

### “Limit workflows to Qt-native selection behavior”

Rejected because:
- it constrains CNC workflows unnecessarily
- geometry interaction becomes inconsistent
- semantic grouping becomes unreliable
- future editing capabilities become blocked

### “Implement selection only inside the canvas”

Rejected because:
- editor and canvas diverge semantically
- synchronization becomes fragile
- document interaction loses consistency
- semantic editing becomes fragmented

### “Treat multi-selection as temporary UI state”

Rejected because:
- selections need persistence
- semantic operations require stable ownership
- geometry interaction requires durable mapping
- future tooling depends on reliable selection identity

---

## Long-Term Direction

This ADR establishes the direction toward:
- persistent multi-selection infrastructure
- geometry-aware interaction systems
- semantic operation grouping
- custom interaction overlays
- future editor abstraction layers
- domain-owned interaction semantics

The application architecture intentionally prioritizes CNC interaction requirements over limitations imposed by generic text editing widgets.