# GCode Lisa — Vision

## Purpose

GCode Lisa is evolving from a traditional G-Code editor into a CNC-domain-oriented engineering environment.

The long-term direction of the project is driven by a practical observation:

Modern CNC interaction requirements can no longer be represented cleanly through a purely text-centric editor architecture.

The original implementation model — based primarily on `QPlainTextEdit`, line-oriented synchronization, and document-centric selection semantics — was sufficient for early visualization and editing workflows.

However, increasing geometric interaction requirements exposed architectural limitations that cannot be solved reliably inside the boundaries of classical text editor abstractions.

This document describes the long-term architectural direction of GCode Lisa and the engineering principles that guide future evolution.


---

# Core Architectural Direction

## CNC Domain First

The CNC domain is the primary source of meaning inside the application.

Geometry, machine semantics, execution order, toolpath structure, and operational safety are treated as first-class concepts.

G-Code text remains important, but it is no longer considered the sole carrier of application semantics.

Instead:

- G-Code text is a representation of CNC-domain structures
- UI components are views and interaction adapters
- geometric and semantic relationships are explicit internal concepts
- editing operations operate on CNC meaning, not only text ranges

This shift is necessary to support reliable geometric interaction, semantic editing workflows, and future CNC-aware tooling.


---

# Limits of Classical Text Editor Models

## The Original Assumption

Traditional editor architectures assume:

- a document is fundamentally linear text
- selection is cursor-oriented
- editing operations are range-based
- interaction state belongs to the text widget
- geometry is derived visualization

This model works well for conventional source code editors.

It becomes increasingly problematic for CNC workflows.


## Why CNC Interaction Is Different

CNC programs are not only text documents.

They also describe:

- ordered machine operations
- geometric motion
- execution dependencies
- manufacturing intent
- spatial relationships
- stateful machine behavior

The user frequently interacts with these concepts geometrically rather than textually.

Examples include:

- selecting visible toolpaths directly in the canvas
- selecting multiple disconnected machining regions
- isolating operation groups
- navigating by geometry rather than line numbers
- applying transformations to semantic operation groups
- correlating warnings with machine motion

These workflows exceed the capabilities of traditional text widget selection systems.


## Multi-Selection as a Structural Problem

A critical architectural limitation emerged around selection handling.

Qt text widgets fundamentally model:

- a primary cursor
- transient text ranges
- document-relative selection state

This does not map reliably to CNC editing requirements such as:

- persistent geometric selections
- disconnected semantic groups
- stable selection identity during document updates
- synchronization between geometry and document structure
- selection tied to machining intent rather than visible text ranges

As geometric interaction became more important, selection itself became a CNC-domain problem rather than a text-widget problem.

This is a foundational architectural transition.


---

# Shared CNC Domain Model

## Motivation

Future functionality requires a shared internal representation that is independent from any single UI component.

Without a common domain model, every subsystem develops its own partial interpretation of the document.

This creates:

- synchronization fragility
- duplicated semantics
- inconsistent selection behavior
- unreliable geometric mapping
- unstable editing workflows
- poor scalability for future features

A unified CNC-domain model provides a stable foundation for the entire application.


## Long-Term Goal

The long-term architecture aims to establish shared CNC-domain structures used consistently across:

- editor
- canvas
- analyzer
- search/navigation
- comment systems
- transformation tools
- future automation systems
- future AI-assisted tooling

The UI should not own core semantics.

Instead, UI components should consume and manipulate shared CNC-domain state.


## Expected Characteristics

The shared domain model should support:

- stable identity for CNC entities
- explicit relationships between source text and geometry
- incremental updates
- deterministic synchronization
- semantic grouping
- operation-aware navigation
- dialect-aware interpretation
- traceable transformation history
- efficient handling of large files

The model must remain understandable, inspectable, and deterministic.


---

# Geometry as a Primary Interaction Layer

## Geometry Is Not Secondary Visualization

In many traditional editors, geometry is a rendering artifact.

In GCode Lisa, geometry is part of the operational meaning of the program.

The canvas is therefore not merely a preview widget.

It is an interaction surface for:

- navigation
- inspection
- verification
- selection
- analysis
- future editing workflows

This changes architectural priorities significantly.


## Bidirectional Structural Relationships

Future systems require stable relationships between:

- source document structures
- parsed semantic entities
- geometric representations
- machine operations
- analysis results
- user selections

These relationships must remain stable even as the document evolves.

Simple line-number synchronization is insufficient for long-term requirements.


## Incremental and Persistent State

Large CNC programs require efficient incremental behavior.

Future architectures should avoid:

- unnecessary full reparsing
- full geometry rebuilds
- transient selection invalidation
- widget-owned interaction state

Persistent semantic structures are preferred over temporary UI-derived state.


---

# Semantic Editing

## Beyond Text Replacement

Traditional text replacement is insufficient for many CNC workflows.

Future editing systems are expected to support operations such as:

- transforming operation groups
- manipulating geometric regions
- restructuring machining sequences
- applying coordinate transformations
- operation-aware commenting
- semantic filtering
- machine-state-aware validation

These operations require explicit semantic understanding.


## Source Fidelity Remains Critical

Semantic editing does not imply automatic rewriting of programs.

GCode Lisa prioritizes:

- explicit user control
- predictable output
- visible transformations
- traceable modifications
- preservation of intent

The system should never silently reinterpret or normalize machine instructions without clear user action.

When transformations occur, they must remain understandable and inspectable.


## Human-Readable Editing Pipeline

Even as semantic capabilities increase, generated or transformed G-Code must remain:

- reviewable
- debuggable
- inspectable
- attributable to explicit operations

The application should support engineering workflows, not obscure them.


---

# Safety and Traceability

## CNC Safety Is a Core Architectural Constraint

G-Code controls physical machine movement.

This affects architecture directly.

The system must prioritize:

- deterministic behavior
- explicit state transitions
- reliable synchronization
- predictable editing semantics
- traceable transformations

Convenience features must never compromise operational clarity.


## No Hidden Corrections

The application should avoid:

- silent command rewriting
- hidden geometry correction
- implicit dialect reinterpretation
- invisible optimization passes
- automatic semantic mutation

Warnings are preferred over silent correction.


## Editing History and Intent

Future architectures should preserve sufficient structural information to explain:

- what changed
- why it changed
- which semantic entities were affected
- how geometry was modified
- which operations introduced transformations

Traceability is part of operational safety.


---

# Role of the UI

## UI as Adapter Layer

The UI layer should progressively move toward an adapter-oriented role.

Responsibilities include:

- presentation
- interaction
- visualization
- input handling
- workflow orchestration

Core CNC semantics should remain outside the UI.


## Reducing Widget-Centric Semantics

Historically, important interaction state was embedded inside widgets.

Long-term architecture aims to reduce coupling between:

- widget state
- selection semantics
- document ownership
- operational meaning

Shared domain structures should become the authoritative source of truth.


## Editor Evolution

The current editor implementation remains valuable, but future requirements may exceed the capabilities of traditional text widgets.

Potential future directions may include:

- custom selection systems
- semantic overlays
- operation-aware navigation
- geometry-linked editing structures
- non-linear selection visualization
- domain-oriented editing interaction

Such evolution should remain incremental and compatibility-conscious.


---

# Architectural Principles Going Forward

## Deterministic Systems

Prefer:

- explicit ownership
- predictable state flow
- observable transformations
- stable synchronization boundaries

Avoid:

- hidden global state
- implicit mutation
- uncontrolled cache invalidation
- UI-driven semantic authority


## Incremental Evolution

Large architectural transitions should occur conservatively.

The project favors:

- gradual extraction
- compatibility-preserving refactors
- layered migration strategies
- stable intermediate architectures

Aggressive rewrites are intentionally avoided.


## Performance as a Design Constraint

Large CNC programs must remain responsive.

Future systems should prioritize:

- incremental processing
- lightweight synchronization
- bounded recalculation
- explicit cache ownership
- geometry reuse where possible

Performance is an architectural requirement, not a later optimization step.


## Cross-Platform Native Desktop Workflow

GCode Lisa remains a desktop-first engineering application.

The project intentionally prioritizes:

- native interaction models
- keyboard-oriented workflows
- precise interaction
- low-latency behavior
- operator efficiency

The architecture should support these priorities directly.


---

# Long-Term Vision

The long-term vision of GCode Lisa is not to become a generic text editor with CNC features layered on top.

The goal is to become a CNC-domain-oriented working environment where:

- geometry and semantics are first-class concepts
- document structure and machine behavior remain explicitly connected
- editing operations are understandable and traceable
- multiple interaction layers share a common semantic foundation
- safety and predictability guide architectural decisions
- UI systems remain adapters over a stable CNC core

This direction establishes the foundation for:

- future semantic editing systems
- advanced geometric interaction
- persistent multi-selection models
- operation-aware workflows
- safer transformation pipelines
- richer analysis systems
- future automation and AI-assisted tooling grounded in explicit CNC semantics

The architectural transition toward shared CNC-domain structures is therefore not an optional refactor.

It is a necessary foundation for the next generation of CNC interaction capabilities inside GCode Lisa.