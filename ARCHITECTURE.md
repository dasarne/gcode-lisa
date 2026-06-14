# GCode Lisa — Architecture

## Module Organization

```
src/
├── gcode/
│   ├── commands.py       # GRBL command constants and GRBLCommand dataclass
│   ├── grbl_versions.py  # Version feature matrix and version-aware helpers
│   ├── parser.py         # G-Code line/file parser
│   └── tokens.py         # Tokenizer (lexer)
├── geometry/
│   ├── bounds.py         # BoundingBox calculation
│   ├── path.py           # ToolPath and PathSegment building
│   └── transforms.py     # Coordinate system transforms
├── analyzer/
│   ├── analyzer.py       # Warning and compatibility checker
│   └── optimizer.py      # Optimization hints
└── ui/
    ├── main_window.py    # QMainWindow — dual-view layout, menus, toolbar
    ├── editor_panel.py   # QPlainTextEdit-based G-Code editor
    ├── canvas_panel.py   # matplotlib FigureCanvas visualization panel
    ├── settings_dialog.py# GRBL version selector and feature table
    └── widgets.py        # Reusable custom widgets
```

## GRBL Version Support Matrix

| Feature          | GRBL 1.1 | GRBL 1.1H | GRBL 1.1j |
|------------------|----------|-----------|-----------|
| G00 Rapid        | ✅        | ✅         | ✅         |
| G01 Linear       | ✅        | ✅         | ✅         |
| G02/G03 Arc      | ✅        | ✅         | ✅         |
| G38.x Probing    | ✅        | ❌         | ✅         |
| M7/M8 Coolant    | ❌        | ❌         | ✅         |
| Spindle speed    | ✅        | ✅         | ✅         |

## Data Flow

```
File on disk
    │
    ▼
GCodeTokenizer   →  Token stream
    │
    ▼
GCodeParser      →  GCodeProgram (list of GCodeLine)
    │
    ├──▶  GCodeAnalyzer   →  list[AnalysisWarning]
    │
    ├──▶  build_toolpath  →  ToolPath (list of PathSegment)
    │         │
    │         └──▶  calculate_bounds  →  BoundingBox
    │
    └──▶  UI layer
              ├─  EditorPanel   (text, line highlighting)
              └─  CanvasPanel   (matplotlib rendering)
```

## Dual-View Interaction Model

The bidirectional binding between the editor and canvas is implemented via Qt signals:

- `EditorPanel.line_selected(int)` → `MainWindow._on_editor_line_selected(line_number)` → `CanvasPanel.highlight_segment(line_number)`
- `CanvasPanel.segment_selected(int)` → `MainWindow._on_canvas_segment_selected(line_number)` → `EditorPanel.highlight_line(line_number)`

Each `PathSegment` stores the source `line_number` from the parsed G-Code, enabling O(1) lookup in both directions.

## Canvas Rendering Architecture Notes

The canvas subsystem is performance critical and intentionally optimized for:
- predictable repaint behavior
- low-latency interaction
- explicit geometry preparation
- centralized paint orchestration

### Important Constraints

Avoid:
- unnecessary geometry rebuilds
- hidden repaint-trigger side effects
- expensive calculations inside repaint paths
- duplicated coordinate transforms
- implicit cache invalidation
- unnecessary allocations during rendering

Preserve:
- explicit coordinate-space handling
- centralized repaint sequencing
- stable editor ↔ canvas synchronization
- deterministic viewport behavior

### Coordinate Spaces

Canvas rendering currently relies on explicit transformation boundaries between:
- world space
- viewport space
- screen space

Coordinate-space consistency is critical for:
- hit-testing
- overlays
- selection accuracy
- highlight rendering
- viewport stability

### Cache Ownership

Geometry caches and invalidation behavior should remain:
- explicit
- traceable
- deterministic

Avoid introducing hidden rebuild side effects.

### Refactor Guidance

Conservative extraction is preferred over aggressive modularization.

Safer extraction targets:
- pure projection helpers
- viewport math helpers
- render-independent geometry utilities

Higher-risk areas that should remain centralized unless explicitly reworked:
- paint orchestration
- repaint sequencing
- viewport interaction state machine
- transient interaction coordination

See:
- `docs/architecture/canvas_refactor_plan.md`

## Technology Choices Rationale

| Choice | Reason |
|--------|--------|
| PyQt6  | Native look-and-feel on Linux/KDE, mature signal/slot system, good matplotlib integration |
| matplotlib | Proven 2D/3D plotting, FigureCanvas integrates cleanly with PyQt6 |
| dataclasses | Zero-boilerplate value objects for GCodeLine, PathSegment, etc. |
| numpy  | Efficient coordinate array operations for large G-Code files |
| pytest | Industry-standard, good fixture system, pytest-qt for Qt testing |
