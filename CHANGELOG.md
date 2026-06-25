# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog:
https://keepachangelog.com/en/1.1.0/

## [Unreleased]

### Added
- Ctrl-drag semantic multi-selection workflow in the editor
- Continuous add/remove selection painting for multi-range editing
- Regression tests for semantic Ctrl-drag selection behavior

### Improved
- Multi-selection interaction consistency between editor and canvas workflows
- Documentation for advanced semantic selection shortcuts

## [1.0.0] - 2026-06-14

### Added
- Dual-view G-Code editor and interactive 3D visualization
- Bidirectional synchronization between source editor and toolpath canvas
- Multi-dialect support for GRBL, LinuxCNC, and Marlin
- Dialect auto-detection and compatibility analysis
- Interactive comment browser
- Search and replace with regex support
- Graphics-based line selection workflow
- Feedrate scaling tools
- Workpiece dimension analysis
- Warning and optimization hint system
- Multi-language support (German and English)
- Linux desktop integration scripts
- Automated test suite and GitHub Actions CI

### Improved
- Modernized Python packaging configuration
- Added optional development dependency group
- Added CLI entry point (`gcode-lisa`)
- Removed obsolete matplotlib dependency